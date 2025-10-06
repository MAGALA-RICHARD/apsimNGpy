import copy
import gc
import math
import os.path
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
# Database connection
from dataclasses import field
from pathlib import Path
from typing import Union, Literal

import pandas as pd
from sqlalchemy import Table, Column, String, Float, Integer, MetaData
from sqlalchemy import create_engine, text

from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core_utils.database_utils import read_db_table, delete_all_tables
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.exceptions import ApsimRuntimeError
from apsimNGpy.parallel.process import custom_parallel
from apsimNGpy.settings import logger
from apsimNGpy.core_utils.database_utils import write_results_to_sql

ID = 0
# default cores to use
CORES = max(1, math.ceil(os.cpu_count() * 0.85))
csv_doc = pd.DataFrame().to_csv.__doc__


def is_my_iterable(value):
    """Check if a value is an iterable, but not a string."""
    return isinstance(value, Iterable) and not isinstance(value, str)


def simulation_exists(db_path: str, table_name: str, simulation_id: int) -> bool:
    """
    Check if a simulation_id exists in the specified table.

    Args:
        db_path (str): Path to the SQLite database file.
        table_name (str): Name of the table to query.
        simulation_id (int): ID of the simulation to check.

    Returns:
        bool: True if exists, False otherwise.
    """
    engine = create_engine(f"sqlite:///{db_path}")

    query = text(f"SELECT 1 FROM {table_name} WHERE SimulationID = :sim_id LIMIT 1")
    with engine.connect() as conn:
        result = conn.execute(query, {"sim_id": simulation_id}).first()
        return result is not None


@timer
def insert_data_with_pd(db, table, results, if_exists):
    engine = create_engine(f'sqlite:///{db}')
    results.to_sql(table, engine, index=False, if_exists=if_exists)


@dataclass(slots=True)
class MultiCoreManager:
    db_path: Union[str, Path, None] = None,
    agg_func: Union[str, None] = None
    ran_ok: bool = False
    tag = 'multi-core'
    default_db = 'manager_datastorage.db'
    incomplete_jobs: list = field(default_factory=list)

    def __post_init__(self):
        """
        Initialize the database, note that this database is cleaned up everytime the object is called, to avoid table name errors
        :return:
        """
        self.db_path = self.db_path or f"{self.tag}_{self.default_db}"
        self.db_path = Path(self.db_path).resolve().with_suffix('.db')

        try:
            self.db_path.unlink(missing_ok=True)
        except PermissionError:
            # failed? no worries, the database is still cleared later by deleting all tables this is because inserting data just append
            pass

    def insert_data(self, results, table):
        """
        Insert results into the specified table
        results: (Pd.DataFrame, dict) The results that will be inserted into the table
        table: str (name of the table to insert)
        """

        engine = create_engine(f"sqlite:///{str(self.db_path)}")
        metadata = MetaData()

        # there may be need for manual schema in future
        if isinstance(results, pd.DataFrame):
            results_num = results.select_dtypes(include='number')

            cols = [Column(i, Float) for i in results_num.columns]
            # Find all object (string-like) columns
            str_cols_df = results.select_dtypes(include='object')

            if not str_cols_df.empty:  # safer than "is not None"
                str_cols = [Column(col_name, String) for col_name in str_cols_df.columns]
                cols.extend(str_cols)

        else:
            cols = [
                Column(col_name, String) if isinstance(results[col_name], str) else Column(col_name, Float)
                for col_name in results
            ]
        results_table = Table(
            table,
            metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            *cols

        )
        table_meta_info = Table(
            'table_names',
            metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('table', String, primary_key=False)

        )
        table_info = {"table": table}
        # Create table if it doesn't exist
        metadata.create_all(engine)
        # if not simulation_exists(self.db_path, table, self.counter):
        # Insert data manually (append instead of replacement)
        with engine.begin() as conn:
            # Convert DataFrame rows into dicts
            if not isinstance(results, dict):
                data_dicts = results.to_dict(orient='records')
            else:
                data_dicts = results
            # keeping track of added tables

            conn.execute(results_table.insert(), data_dicts)
            conn.execute(table_meta_info.insert(), table_info)

    @property
    def tables(self):
        "Summarizes all the tables that have been created from the simulations"
        if os.path.exists(self.db_path) and os.path.isfile(self.db_path) and str(self.db_path).endswith('.db'):
            dt = read_db_table(self.db_path, report_name='table_names')
            # get only unique tables
            return set(dt.table.values)
        else:
            raise ValueError("Attempting to get results from database before running all jobs")
        return None

    def run_parallel(self, model):
        """
        This is the worker for each simulation.

        The function performs two things; runs the simulation and then inserts the simulated data into a specified
        database.

        :param model: str, dict, or Path object related .apsimx json file

        returns None
        """
        # initialize the apsimNGpy model simulation engine
        _model = ApsimModel(model, out_path=None)
        table_names = _model.inspect_model('Models.Report', fullpath=False)
        # we want a unique report for each crop, because they are likely to have different database schemas
        crops = _model.inspect_model('Models.PMF.Plant', fullpath=False)
        crop_table = [f"{a}_{b}" for a, b in zip(table_names, crops)]
        tables = '_'.join(crop_table)
        # run the model. without specifying report names, they will be detected automatically
        try:
            _model.run()
            # aggregate the data using the aggregated function
            if self.agg_func:
                if self.agg_func not in {'sum', 'mean', 'max', 'min', 'median', 'std'}:
                    raise ValueError(f"unsupported aggregation function {self.agg_func}")
                dat = _model.results.groupby('source_table')  # if there are more than one table, we do not want to
                # aggregate them together
                out = dat.agg(self.agg_func, numeric_only=True)

                out['source_name'] = Path(model).name

            else:
                out = _model.results
            # track the model id
            out['source_name'] = Path(model).name
            # insert the simulated dataset into the specified database
            self.insert_data(out, table=tables)
            # clean up files related _model object
            _model.clean_up(coerce=False)
            # collect garbage before gc comes in

        except ApsimRuntimeError:
            self.incomplete_jobs.append(_model.path)

    def get_simulated_output(self, axis=0):
        """
        Get simulated output from the API

        :param axis: if axis =0, concatenation is along the ``rows`` and if it is 1 concatenation is along the ``columns``
        """
        if axis not in {0, 1}:
            # Errors should go silently
            raise ValueError('Wrong value for axis should be either 0 or 1')

        data = (read_db_table(self.db_path, report_name=rp) for rp in self.tables)
        return pd.concat(data, axis=axis)

    @property
    def results(self):
        """property methods for getting simulated output"""
        return self.get_simulated_output(axis=0)

    def clear_db(self):
        """Clears the database before any simulations.

          First attempt a complete ``deletion`` of the database if that fails, existing tables are all deleted"""
        if not str(self.db_path).endswith('.db'):
            raise ValueError(f"Cannot clear invalid db path: {self.db_path}")
        if os.path.exists(self.db_path):

            try:
                os.remove(self.db_path)
            except (PermissionError, FileNotFoundError):
                # if removing it has failed due to permission errors, connect to it and remove all tables
                delete_all_tables(self.db_path)

    def clear_scratch(self):
        """clears the scratch directory where apsim files are cloned before being loaded. should be called after all simulations are completed

        """
        paths = Path.cwd().glob("*scratch")
        for path in paths:
            try:
                shutil.rmtree(str(path), ignore_errors=True)

            except PermissionError:
                pass

    def clean_up_data(self):
        """Clears the data associated with each job. Please call this method after run_all_jobs is complete"""

    def save_tosql(
            self,
            db_name: Union[str, Path],
            *,
            table_name: str = "aggregated_tables",
            if_exists: Literal["fail", "replace", "append"] = "fail",
    ) -> None:
        """
        Persist simulation results to a SQLite database table.

        This method writes `self.results` (a pandas DataFrame) to the given SQLite
        database. It is designed to be robust in workflows where some simulations
        may fail: any successfully simulated rows present in `self.results` are
        still saved. This is useful when an ephemeral/temporary database was used
        during simulation and you need a durable copy.

        Parameters
        ----------
        db_name : str | pathlib.Path
            Target database file. If a name without extension is provided, a
            ``.db`` suffix is appended. If a relative path is given, it resolves
            against the current working directory.
        table_name : str, optional
            Name of the destination table. Defaults to ``"Report"``.
        if_exists: {"fail", "replace", "append"}, optional.
            Write mode passed through to pandas:
            - ``"fail"``: raise if the table already exists.
            - ``"replace"``: drop the table, create a new one, then insert.
            - ``"append"``: insert rows into existing table (default).
            (defaults to fail if table exists, more secure for the users to know
         what they are doing)

        Raises
        ------
        ValueError
            If `self.results` is missing or empty.
        TypeError
            If `self.results` is not a pandas DataFrame.
        RuntimeError
            If the underlying database writes fails.

        Notes
        -----
        - Ensure that `self.results` contain only the rows you intend to persist with.
          If you maintain a separate collection of failed/incomplete jobs, they
          should not be included in `self.results`.
        - This method does not mutate `self.results`.

        Examples
        --------
        >>> mgr.results.head()
           sim_id  yield  n2o
        0       1   10.2  0.8
        >>> mgr.save("outputs/simulations.db")
        """

        # --- Validate results
        @write_results_to_sql(db_path=db_name, table=table_name, if_exists=if_exists)
        def _write():
            results = getattr(self, "results", None)
            if results is None or (isinstance(results, pd.DataFrame) and results.empty):
                raise ValueError("No simulation results to save: `self.results` is empty or missing.")
            if not isinstance(results, (pd.DataFrame, dict)):
                raise TypeError(f"`self.results` must be a pandas DataFrame,or dict  got {type(results)!r}.")
            return results

        _ = _write()

    def save_tocsv(self, path_or_buf, **kwargs):

        if self.results is not None and not self.results.empty:

            self.results.to_csv(path_or_buf, **kwargs)
        else:
            raise ValueError("results are empty or not yet simulated")

    def run_all_jobs(self, jobs, *, n_cores=CORES, threads=False, clear_db=True, **kwargs):
        """
        runs all provided jobs using ``processes`` or ``threads`` specified

        ``threads (bool)``: threads or processes

        ``jobs (iterable[simulations paths]``: jobs to run

        ``n_cores (int)``: number of cores to use

        ``clear_db (bool)``: clear the database existing data if any. defaults to True

        ``kwargs``:
          retry_rate (int, optional): how many times to retry jobs before giving up

        :return: None

        """
        assert n_cores > 0, 'n_cores must be an integer above zero'
        if clear_db:
            self.clear_db()  # each simulation is fresh,
        # future updates include support for skipping some simulation
        try:
            for _ in custom_parallel(self.run_parallel, jobs, ncores=n_cores, use_threads=threads,
                                     progress_message='Processing all jobs', unit='simulation'):
                pass  # holder to unzip jobs

            retry_rate = kwargs.get("retry_rate", 1)

            for _ in range(retry_rate):
                # how many jobs were uncompleted?
                len_incomplete = len(self.incomplete_jobs)
                if len_incomplete == 0:
                    self.ran_ok = True
                    return
                else:
                    # Back off if failures exceed core budget; otherwise cap by failures
                    cores = n_cores if len_incomplete > n_cores else min(len_incomplete, n_cores)

                    logger.info(f"Retrying {len_incomplete} failed job(s) with {cores} core(s).")
                    # iterable is replaced by the incomplete jobs, but we need to copy first
                    incomplete__jobs = tuple(copy.deepcopy(self.incomplete_jobs))
                    # clear to prepare for new assessments
                    self.incomplete_jobs.clear()  # at every simulation, an incomplete job is appended
                    for _ in custom_parallel(
                            self.run_parallel,
                            incomplete__jobs,
                            ncores=cores,
                            use_thread=False,
                            progress_message="Re-running failed jobs",
                    ):
                        pass  # holder to unzip jobs

                    if not self.incomplete_jobs:
                        self.ran_ok = True
                        gc.collect()
                        break  # no need to continue

            else:

                # at this point, the error causing the failures is more than serious, although it's being excepted as
                # an `ApsimRuntimeError`
                if self.incomplete_jobs:
                    logger.warning(
                        f"MultiCoreManager exited with {len(self.incomplete_jobs)} uncompleted job(s). "
                        "Inspect `incomplete_jobs` for details."
                    )
                gc.collect()

        finally:
            gc.collect()


MultiCoreManager.save_tocsv.__doc__ = """  Persist simulation results to a SQLite database table.

        This method writes `self.results` (a pandas DataFrame) to the given csv file. It is designed to be robust in workflows where some simulations
        may fail: any successfully simulated rows present in `self.results` are
        still saved. This is useful when an ephemeral/temporary database was used
        during simulation and you need a durable copy\n.
        """ + csv_doc

if __name__ == '__main__':
    import os, uuid, tempfile
    from tempfile import NamedTemporaryFile

    # quick tests
    create_jobs = [ApsimModel('Maize').path for _ in range(16 * 2)]
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / f"{uuid.uuid4().hex}.db"
        test_agg_db = Path(td) / f"{uuid.uuid4().hex}.db"

        Parallel = MultiCoreManager(db_path=test_agg_db, agg_func='mean')
        Parallel.run_all_jobs(create_jobs, n_cores=16, threads=False, clear_db=False, retry_rate=1)
        df = Parallel.get_simulated_output(axis=0)
        Parallel.clear_scratch()
        # test saving to already an existing table
        ve = False
        db_path.unlink(missing_ok=True)
        try:
            try:
                # ___________________first__________________________________
                Parallel.save_tosql(db_path, table_name='results', if_exists='replace')
                # ______________________ then _________________________________
                Parallel.save_tosql(db_path, table_name='results', if_exists='fail')
            except ValueError:
                ve = True
            assert ve == True, 'fail method is not raising value error'

            # ____________test saving by replacing existing table _______________
            ve = False
            try:

                Parallel.save_tosql(db_path, table_name='results', if_exists='replace')
            except ValueError:
                ve = True
            assert ve == False, 'replace method failed'

            # ____________test appending to an existing table _______________
            ve = False
            try:
                Parallel.save_tosql(db_path, table_name='results', if_exists='append')
            except ValueError:
                ve = True
            assert ve == False, 'append method failed'
        finally:
           pass
