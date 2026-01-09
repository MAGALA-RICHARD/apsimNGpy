from __future__ import annotations

import copy
import gc
import math
import os.path
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
# Database connection
from dataclasses import field
from functools import partial, cached_property, cache
from pathlib import Path
from typing import Union, Literal

import pandas as pd
from sqlalchemy import create_engine, text

from apsimNGpy.core._multi_core import single_runner
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core_utils.database_utils import write_results_to_sql, clear_table, get_db_table_names, read_db_table
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.parallel.process import custom_parallel
from apsimNGpy.settings import logger
from multiprocessing import Queue

ID = 0
# default cores to use
CORES = max(1, math.ceil(os.cpu_count() * 0.85))
csv_doc = pd.DataFrame().to_csv.__doc__


def core_count(user_core: int, threads: bool) -> int:
    total = os.cpu_count() or 1

    # Allow negative indexing (e.g., -1 → all but one core)
    core = total + user_core if user_core < 0 else user_core

    if core <= 0:
        raise ValueError(
            f"Resolved core count must be positive; got {core} "
            f"(user_core={user_core}, total={total})"
        )

    # For multiprocessing, avoid over subscription unless explicitly threaded
    if not threads and core > total:
        raise ValueError(
            f"Requested {core} cores exceeds available cores ({total})."
        )

    return core


def _is_my_iterable(value):
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
    db_path: Union[str, Path, None] = None
    agg_func: Union[str, None] = None
    ran_ok: bool = False
    tag = 'multi_core'
    default_db = 'manager_datastorage.db'
    incomplete_jobs: list = field(default_factory=list)
    table_prefix: str = '__core_table__'
    cleared_db: bool = field(default=False, init=False)

    def __post_init__(self):
        """
        Initialize the database, note that this database tables are cleaned up everytime the object is called, to avoid table name errors
        :return:
        """
        self.db_path = self.db_path or f"{self.tag}_{self.default_db}"

        self.db_path = Path(self.db_path).resolve().with_suffix('.db')
        self.cleared_db = False

        try:
            self.db_path.unlink(missing_ok=True)
        except PermissionError:
            # failed? no worries, the database is still cleared later by deleting all tables this is because inserting data just append
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        # clear all the temporally files if available
        self.clear_scratch()
        return None

    def __hash__(self):
        return hash((
            self.db_path,
            self.tag,
            self.table_prefix,
            self.ran_ok,
            self.cleared_db,
            tuple(self.incomplete_jobs),
        ))

    @property
    def tables(self):
        """
        Returns a list of tables that were created during multiprocessing

        """
        from apsimNGpy.core_utils.database_utils import get_db_table_names
        "Summarizes all the tables that have been created from the simulations"
        if os.path.exists(self.db_path) and os.path.isfile(self.db_path) and str(self.db_path).endswith(
                '.db') and self.ran_ok:
            tables = get_db_table_names(self.db_path)
            tables = {table for table in tables if table.startswith(self.table_prefix)}
            # get only unique tables
            return tuple(tables)
        else:
            raise ValueError("Attempting to get results from database before running all jobs")

    @cache
    def _get_simulated_results(self, axis, tables):
        print('loading simulated results.')
        if axis not in {0, 1}:
            # Errors should not go silently
            raise ValueError('Wrong value for axis should be either 0 or 1')
        from apsimNGpy.core_utils.database_utils import read_with_pandas
        read_db = partial(read_with_pandas, db=self.db_path)
        if len(tables) > 16:
            frames = list(
                custom_parallel(read_db, tables, void=False, progress_message='loading data', unit='table',
                                display_failures=True))
        else:
            frames = (read_db(i) for i in tables)
        # data = (read_db_table(self.db_path, report_name=rp) for rp in self.tables)

        return pd.concat(frames, axis=axis)

    def get_simulated_output(self, axis=0):
        """
        Get simulated output from the API.

        Results are retrieved based on the table prefix provided during the setup.

        Parameters
        ----------
        axis : int, optional
            Specifies how simulation outputs are concatenated.
            If ``axis=0``, outputs are concatenated along rows.
            If ``axis=1``, outputs are concatenated along columns.

        Notes
        -----
        Based on the source file name and execution context, two additional columns
        are appended to the returned dataset:

        - ``MetaExecutionID``
          A unique identifier assigned to each simulation run, independent of
          execution order or process.

        - ``MetaProcessID``
          Identifies the process responsible for executing the simulation. For example,
          when running on six cores, six distinct process IDs will be assigned.

        These identifiers facilitate traceability and reproducibility across serial
        and parallel execution workflows.
        """
        return self._get_simulated_results(axis=axis, tables=self.tables)

    @property
    def results(self):
        """property methods for getting simulated output.
        uses :meth:`~apsimNGpy.core.mult_cores.MultiCoreManager.get_simulated_output` under the hood
        to create results attribute of the simulated data
        """
        return self.get_simulated_output(axis=0)

    def clear_db(self):
        """Clears the database before any simulations."""
        if not str(self.db_path).endswith('.db'):
            raise ValueError(f"Cannot clear invalid db path: {self.db_path}")
        if os.path.exists(self.db_path):
            # clear only tables starting with the stated prefix
            tables = get_db_table_names(self.db_path)
            for tb in tables:
                try:
                    _ = clear_table(self.db_path, tb) if tb.startswith(f"{self.table_prefix}") else None
                except PermissionError:
                    pass
                except FileNotFoundError:
                    pass

    @staticmethod
    def clear_scratch():
        """clears the scratch directory where apsim files are cloned before being loaded. should be called after all simulations are completed

        """
        paths = Path.cwd().glob("*scratch")
        for path in paths:
            try:

                shutil.rmtree(str(path), ignore_errors=True)

            except PermissionError:
                pass

    def save_tosql(
            self,
            db_name: Union[str, Path],
            *,
            table_name: str = "aggregated_tables",
            if_exists: Literal["fail", "replace", "append"] = "fail",
    ) -> None:
        """
        Write simulation results to an SQLite database table.

        This method writes `self.results` (a pandas DataFrame) to the given SQLite
        database. It is designed to be robust in workflows where some simulations
        may fail: any successfully simulated rows present in `self.results` are
        still saved. This is useful when an ephemeral/temporary database was used
        during simulation, and you need a durable copy.

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

        .. seealso::

           :func:`~apsimNGpy.core_utils.database_utils.write_results_to_sql`
        """

        # --- Validate results
        @write_results_to_sql(db_path=db_name, table=table_name, if_exists=if_exists)
        def _write():
            results = getattr(self, "results", None)
            if results is None or (isinstance(results, pd.DataFrame) and results.empty):
                raise ValueError("No simulation results to save: `self.results` is empty or missing.")
            return results

        _write()

    def save_tocsv(self, path_or_buf, **kwargs):

        if self.results is not None and not self.results.empty:

            self.results.to_csv(path_or_buf, **kwargs)
        else:
            raise ValueError("results are empty or not yet simulated")

    def run_all_jobs(self, jobs, *, n_cores=-2, threads=False, clear_db=True, retry_rate=1, subset=None,
                     ignore_runtime_errors=True, display_failures=True, **kwargs):
        """
        Run all provided jobs using multiprocessing or multithreading.

        This method executes a collection of APSIM simulation jobs in parallel,
        using either processes (recommended) or threads. Each job is executed
        in isolation using a context-managed ``apsimNGpy`` model instance to
        ensure proper cleanup and reproducibility.

        Parameters
        ----------
        threads : bool, optional
            If ``True``, jobs are executed using threads; otherwise, jobs are
            executed using processes. The default is ``False`` (process-based
            execution), which is recommended for APSIM workloads. Threads may allow over subscription beyond the cpu budget but not processes

        jobs : iterable or dict
            A collection of job specifications identifying APSIM models to run.
            Each job must specify the APSIM ``.apsimx`` model to execute and may
            include additional metadata.

            Supported job definitions include:

            **1. Plain job definitions (no metadata, no edits)**
            This assumes that each model file is unique and has already been
            edited externally.

            .. code-block:: python

               jobs = {
                   'model_0.apsimx',
                   'model_1.apsimx',
                   'model_2.apsimx',
                   'model_3.apsimx',
                   'model_4.apsimx',
                   'model_5.apsimx',
                   'model_6.apsimx',
                   'model_7.apsimx'
               }

            **2. Job definitions with metadata**
            This format allows attaching identifiers or other metadata to each
            job. Models are assumed to be unique and pre-edited.

            .. code-block:: python

               [
                   {'model': 'model_0.apsimx', 'ID': 0},
                   {'model': 'model_1.apsimx', 'ID': 1},
                   {'model': 'model_2.apsimx', 'ID': 2},
                   {'model': 'model_3.apsimx', 'ID': 3},
                   {'model': 'model_4.apsimx', 'ID': 4},
                   {'model': 'model_5.apsimx', 'ID': 5},
                   {'model': 'model_6.apsimx', 'ID': 6},
                   {'model': 'model_7.apsimx', 'ID': 7}
               ]

            **3. Job definitions with internal model edits**
            In this format, each job specifies an ``inputs`` list with dicts representing each node to be edited internally by the runner. These
            edits must follow the rules of
            :meth:`~apsimNGpy.core.apsim.ApsimModel.edit_model_by_path`. The input dictionary is treated as metadata and is attached to the results' tables. When both inputs and additional metadata are provided, they are merged into a single metadata mapping prior to attachment, with former entries overriding earlier metadata keys and thereby avoiding duplicate keys in the results' tables.

            .. code-block:: python

              jobs=  [
                   {
                       'model': 'model_0.apsimx',
                       'ID': 0,
                       'inputs': [{
                           'path': '.Simulations.Simulation.Field.Fertilise at sowing',
                           'Amount': 0
                       }]
                   },
                   {
                       'model': 'model_1.apsimx',
                       'ID': 1,
                       'inputs': [{
                           'path': '.Simulations.Simulation.Field.Fertilise at sowing',
                           'Amount': 50
                       }]
                   },
                   {
                       'model': 'model_2.apsimx',
                       'ID': 2,
                       'inputs': [{
                           'path': '.Simulations.Simulation.Field.Fertilise at sowing',
                           'Amount': 100
                       }]
                   }
               ]

        n_cores : int
            Number of CPU cores to use for parallel execution.
            Default= total machine cpu counts minus 2 to reserve cores for other processes.

        clear_db : bool, optional
            If ``True``, existing database tables are cleared before writing new
            results. Defaults to ``True``.

        retry_rate : int, optional
            Number of times to retry a job upon failure before giving up.
        subset:
           subset of the data columns to forward to sql or save. It is handled silently if the subset does not exist, the entire table will be saved
        ignore_runtime_errors: bool, optional. Default is True
          Ignore ApsimRunTimeError, to avoid breaking the program during multiprocessing
          other processes can proceed, while we can keep the failed jobs
        display_failures: bool, optional, default=False
        if ``True``, func must return False or True. For simulations written to a database, this is adequate

        Returns
        -------
        None

        Notes
        -----
        - Each execution is isolated and uses a context-managed ``apsimNGpy``
          model instance to ensure proper cleanup.
        - Aggregation is applied only to numeric columns.
        - Result tables are uniquely named using a deterministic schema hash
          derived from column names to avoid database collisions. The hashed
          identifier is prefixed with the user-defined table prefix (default:
          ``__core_table__``), which is used internally to retrieve results.
        - Both execution and process identifiers are attached to all output rows
          to support reproducibility and parallel execution tracking. Execution
          identifiers are derived from column schemas, while process identifiers
          reflect the executing process or thread. To avoid unexpected behavior,
           avoid duplicate identifiers in both metadata and input data.

        Examples
        --------
        .. code-block:: python

           from apsimNGpy.core.mult_cores import MultiCoreManager

           if __name__ == "__main__":
               Parallel = MultiCoreManager(db_path=test_agg_db, agg_func=None)

               # Run jobs in parallel using processes
               Parallel.run_all_jobs(
                   jobs,
                   n_cores=12,
                   threads=False,
                   retry_rate=1
               )

               # Retrieve results
               df = Parallel.get_simulated_output(axis=0)

        .. versionadded:: 0.39.1.21+


        """
        assert n_cores > 0, 'n_cores must be an integer above zero'
        self.cleared_db = clear_db
        # because it is being deprecated, it cleared db is a must to avoid collsions
        if self.cleared_db:
            self.clear_db()  # each simulation is fresh,
            # below is retry code based on user-specified retry rate, the question of why not use tenacity is the added overhead from tenacity,
            # and also need to record the ones that failed

        worker = partial(single_runner, agg_func=self.agg_func,
                         ignore_runtime_errors=ignore_runtime_errors, retry_rate=retry_rate,
                         db=self.db_path, table_prefix=self.table_prefix, subset=subset)
        try:
            x = 0
            failed = []
            for res in custom_parallel(func=worker, iterable=jobs, ncores=n_cores, use_threads=threads,
                                       progress_message=f'APSIM running[{x}]', unit='sim', void=False,
                                       display_failures=display_failures):
                if res is True:
                    pass  # holder to unzip jobs
                else:
                    x += 1
                    failed.append(res)

        finally:
            gc.collect()
        # update incomplete jobs on the main class
        self.incomplete_jobs = failed
        self.ran_ok = True


MultiCoreManager.save_tocsv.__doc__ = """  Persist simulation results to a SQLite database table.

        This method writes `self.results` (a pandas DataFrame) to the given csv file. It is designed to be robust in workflows where some simulations
        may fail: any successfully simulated rows present in `self.results` are
        still saved. This is useful when an ephemeral/temporary database was used
        during simulation and you need a durable copy\n.
        """ + csv_doc

if __name__ == '__main__':
    import os, uuid, tempfile
    from apsimNGpy.core_utils.database_utils import read_db_table

    # quick tests. comprehensive tests are in the tests

    with tempfile.TemporaryDirectory() as td:
        create_jobs = [ApsimModel('Maize', out_path=Path(td) / f"{i}.apsimx").path for i in range(16 * 5)]
        db_path = Path(td) / f"{uuid.uuid4().hex}.db"
        test_agg_db = Path(td) / f"{uuid.uuid4().hex}.db"

        Parallel = MultiCoreManager(db_path=test_agg_db, agg_func=None)
        Parallel.run_all_jobs(create_jobs, n_cores=12, threads=False, clear_db=False, retry_rate=3, subset='Yield')
        df = Parallel.get_simulated_output(axis=0)
        print(len(Parallel.tables))
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
