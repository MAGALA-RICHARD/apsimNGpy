from __future__ import annotations

import gc
import math
import os.path
import shutil
import sqlite3
from collections.abc import Iterable
# Database connection
from functools import partial, cache
from pathlib import Path
from typing import Union, Literal
import tempfile

import loguru
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text

from apsimNGpy.core._multi_core import single_runner
from apsimNGpy.core_utils.database_utils import (write_results_to_sql, drop_table,
                                                 get_db_table_names, read_with_pandas, write_df_to_sql)
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.parallel.process import custom_parallel, custom_parallel_chunks
from parallel._process import JobTracker

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
            f"(user_core={user_core}, total budget={total})"
        )

    # For multiprocessing, avoid over subscription unless explicitly threaded
    if not threads and core > total:
        raise ValueError(
            f"Requested {core} cores exceeds available cores ({total})."
        )

    return max(2, core)


import re


def _get_id(fname: str) -> int:
    m = re.fullmatch(r"(.+)__(\d+)\.db", fname)
    base, num = m.group(1), int(m.group(2))
    return num


def get_results(file_name, db_or_con, prefix):
    stem_ID = _get_id(str(file_name))
    tables_names = [i for i in get_db_table_names(db=file_name) if not i.startswith('_')]
    df = (read_with_pandas(db_or_con=file_name, table=tn).assign(source_table=tn, ID=stem_ID) for tn in tables_names)
    df = pd.concat(df, ignore_index=True)
    table_name = f"{prefix}_id_{stem_ID}_{os.getpid()}"
    write_df_to_sql(out=df, db_or_con=db_or_con, table_name=table_name, if_exists='append', index=False,
                    chunk_size=None)


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


class MultiCoreManager:
    """
        Manager class for coordinating multi-core execution workflows and
        handling result aggregation and persistence.

        This class serves as a lightweight state container for parallel or
        multi-core processing tasks. It tracks execution status, incomplete
        jobs, database connections, and aggregation behavior, and is designed
        to be shared across worker processes or threads in a controlled manner.

        Parameters
        ----------
        db_path : str, pathlib.Path, default=resolved path 'manager_datastorage.db'
            Database  path used to persist results generated
            during multi-core execution. connections may not be picklable

        agg_func : str or None, optional
            Name of the aggregation function used to combine results from
            completed jobs. The interpretation of this value depends on the
            execution context and downstream processing logic. When the user provides an index for aggregation in run_all_jobs method,
            aggregation is performed on that index. 

        ran_ok : bool, optional
            Flag indicating whether the multi-core execution completed
            successfully. This value is updated internally after execution
            finishes. It is used a signal to data memory retrieval methods on this class that everything is ok to retrieve the results from sql database.

        incomplete_jobs : list, optional
            List used to track jobs that failed, were interrupted, or did not
            complete successfully during execution. This list is populated
            dynamically at runtime. Most of the time this container will be empty because the back-end retries silently in case of any perturbation

        table_prefix : str, optional
            Prefix used when creating database tables for storing intermediate
            or aggregated results. This helps avoid table name collisions when
            running multiple workflows. This prefix is also used to avoid table name collisions by clearing all tables that exists with that prefix, for every fresh restart.
            Why this is critical is that we don't want to mixe results from previous session with the current session

        Attributes
        ----------
        tag : str
            Identifier string used to label this manager instance in logs,
            database tables, or metadata.

        default_db : str
            Default SQLite database filename used when no database is
            explicitly provided.

        cleared_db : bool
            Internal flag indicating whether the database has been cleared
            during the current execution lifecycle. This attribute is managed
            internally and is not intended to be set by the user.
            
            By default, tables starting with the provided prefix are deleted for each initialization, to prepare for clean data collection
        """
    __slots__ = (
        "db_path",
        "agg_func",
        "tag",
        "default_db",
        "incomplete_jobs",
        "table_prefix",
        'ran_ok',
        'cleared_db',
        'run_external'
    )

    def __init__(self, db_path: Union[str, Path, None, sqlalchemy.engine.base.Engine, sqlite3.Connection] = None,
                 agg_func: Union[str, None] = None,
                 tag='multi_core',
                 default_db='manager_datastorage.db',
                 incomplete_jobs: list = None,
                 table_prefix: str = '__core_table__',
                 ):
        """
        Initialize the database, note that this database tables are cleaned up everytime the object is called, to avoid table name errors

        Parameters
        ----------
        db_path : str, pathlib.Path, default=resolved path 'manager_datastorage.db'
            Database  path used to persist results generated
            during multi-core execution. connections may not be picklable

        agg_func : str or None, optional
            Name of the aggregation function used to combine results from
            completed jobs. The interpretation of this value depends on the
            execution context and downstream processing logic. When the user provides an index for aggregation in run_all_jobs method,
            aggregation is performed on that index.

        ran_ok : bool, optional
            Flag indicating whether the multi-core execution completed
            successfully. This value is updated internally after execution
            finishes. It is used a signal to data memory retrieval methods on this class that everything is ok to retrieve the results from sql database.

        incomplete_jobs : list, optional
            List used to track jobs that failed, were interrupted, or did not
            complete successfully during execution. This list is populated
            dynamically at runtime. Most of the time this container will be empty because the back-end retries silently in case of any perturbation

        table_prefix : str, optional
            Prefix used when creating database tables for storing intermediate
            or aggregated results. This helps avoid table name collisions when
            running multiple workflows. This prefix is also used to avoid table name collisions by clearing all tables that exists with that prefix, for every fresh restart.
            Why this is critical is that we don't want to mixe results from previous session with the current session

        Attributes
        ----------
        tag : str
            Identifier string used to label this manager instance in logs,
            database tables, or metadata.

        default_db : str
            Default SQLite database filename used when no database is
            explicitly provided.

        cleared_db : bool
            Internal flag indicating whether the database has been cleared
            during the current execution lifecycle. This attribute is managed
            internally and is not intended to be set by the user.

            By default, tables starting with the provided prefix are deleted for each initialization, to prepare for clean data collection

        """
        self.db_path = db_path
        self.tag = tag
        self.default_db = default_db
        self.cleared_db = False
        self.agg_func = agg_func
        self.ran_ok: bool = False
        self.incomplete_jobs = incomplete_jobs or []
        self.table_prefix = table_prefix
        self._check_db_path()

        self.db_path = self.db_path or f"{self.tag}_{self.default_db}"
        if isinstance(self.db_path, (str, Path)):
            self.db_path = Path(self.db_path).resolve().with_suffix('.db')
        self.cleared_db = False
        self.run_external = False

    def __enter__(self):
        return self

    def _check_db_path(self):
        if isinstance(self.db_path, (sqlite3.Connection, sqlalchemy.engine.Connection, sqlalchemy.engine.base.Engine)):
            raise TypeError(
                f"db_path must be a database path (str | Path) got {type(self.db_path)}"
            )

    def __exit__(self, exc_type, exc, tb):
        # clear all the temporally files if available
        self.clear_scratch()
        return None

    def __hash__(self):
        db_hash = self.db_path if isinstance(self.db_path, (str, Path)) else 'connection'
        return hash((
            db_hash,
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
        if isinstance(self.db_path, (str, Path)):
            if not os.path.exists(self.db_path) and os.path.isfile(self.db_path) and self.ran_ok:
                raise ValueError("Attempting to get results from database before running all jobs")
        _tables = get_db_table_names(self.db_path)
        tables = {table for table in _tables if table.startswith(self.table_prefix)}
        return tuple(tables)

    @cache
    def _get_simulated_results(self, axis, tables):

        if axis not in {0, 1}:
            # Errors should not go silently
            raise ValueError('Wrong value for axis should be either 0 or 1')

        read_db = partial(read_with_pandas, db_or_con=self.db_path)
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
        if isinstance(self.db_path, (Path, str)):
            if not str(self.db_path).endswith('.db'):
                self.db_path = Path(self.db_path).with_suffix('.db')
            if not Path(self.db_path).exists():
                return self
            # clear only tables starting with the stated prefix
        tables = get_db_table_names(self.db_path)
        if not tables:
            return self
        for tb in tables:
            try:
                _ = drop_table(self.db_path, tb) if tb.startswith(f"{self.table_prefix}") else None
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
            db_or_con: Union[str, Path],
            *,
            table_name: str = "aggregated_tables",
            if_exists: Literal["fail", "replace", "append"] = "fail",
            chunk_size=None
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
        db_or_con : str | pathlib.Path
            Target database file or connection. If a name without extension is provided, a
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
         chunk_size: int, optional default is None
            For writing data in chunks

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
        @write_results_to_sql(db_or_con=db_or_con, table=table_name, if_exists=if_exists, chunk_size=chunk_size)
        def _write():
            results = getattr(self, "results", None)
            if results is None or (isinstance(results, pd.DataFrame) and results.empty):
                raise ValueError("No simulation results to save: `self.results` is empty or missing.")
            return results

        _write()

    def save_to_csv(self, path_or_buf, **kwargs):

        if self.results is not None and not self.results.empty:

            self.results.to_csv(path_or_buf, **kwargs)
        else:
            raise ValueError("results are empty or not yet simulated")

    def run_all_jobs(self, jobs, *, n_cores=-2, threads=False, clear_db=True, retry_rate=1, subset=None,
                     ignore_runtime_errors=True, engine='python', **kwargs):
        if engine == 'csharp':
            self.run_jobs_external(jobs=jobs, n_cores=n_cores, threads=threads, clear_db=clear_db)
        else:
            self._run_all_jobs(jobs=jobs, n_cores=n_cores, threads=threads,
                               clear_db=clear_db, retry_rate=retry_rate, ignore_runtime_errors=ignore_runtime_errors)

    def _run_all_jobs(self, jobs, *, n_cores=-2, threads=False, clear_db=True, retry_rate=1, subset=None,
                      ignore_runtime_errors=True, **kwargs):
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
            n_cores may be specified as a negative integer to indicate relative allocation from the total available CPU cores.
            In this case, the absolute value of n_cores is subtracted from the total CPU budget, and the remaining cores are used.
            If the resulting number of cores is less than or equal to zero, a ValueError is raised.

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
               Parallel = MultiCoreManager(db=test_agg_db, agg_func=None)

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
        n_cores = core_count(n_cores, threads=threads)
        self.cleared_db = clear_db
        if self.cleared_db:
            self.clear_db()  # each simulation is fresh,

        worker = partial(single_runner, agg_func=self.agg_func,
                         ignore_runtime_errors=ignore_runtime_errors, retry_rate=retry_rate,
                         db_conn=self.db_path, table_prefix=self.table_prefix, subset=subset)
        try:
            x = 0
            failed = []
            for res in custom_parallel(func=worker, iterable=jobs, ncores=n_cores, use_threads=threads,
                                       progress_message=f'APSIM running[{x}f]', unit='sim', void=False,
                                       ):
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

    def run_jobs_external(self, jobs, n_cores=-3, threads=False, clear_db=True):
        from apsimNGpy.core._multi_core import edit_to_folder
        from apsimNGpy.core.runner import _run_from_dir
        import time
        if clear_db:
            self.clear_db()
        db = self.db_path
        # job_tracker = JobTracker(db=db, completed_table='__completed__')
        pattern = f"{self.table_prefix}*.apsimx"

        def clear(folder_dir):
            PT = f"{self.table_prefix}*.apsimx"
            check = Path(folder_dir).glob(PT)
            for job in check:
                if job.is_file():
                    job.unlink(missing_ok=True)
            pt2 = f"{self.table_prefix}*.db"
            check = Path(folder_dir).glob(pt2)
            for job in check:
                if job.is_file():
                    job.unlink(missing_ok=True)

        n_cores = core_count(n_cores, threads)
        tmp = tempfile.TemporaryDirectory(prefix="apsim_")

        try:
            ted =tmp.name
            folder = Path(ted) / f"{uuid.uuid4().hex}"
            folder.mkdir(exist_ok=True)
            clear(folder)
            partial_editor = partial(edit_to_folder, folder_path=folder, prefix=self.table_prefix, db_or_conn=db)
            apsimx_pattern = f"{self.table_prefix}*.apsimx"

            def send_jobs():
                for _ in custom_parallel(func=partial_editor, iterable=jobs, ncores=n_cores, threads=threads,
                                         progress_message='Copying data..'):
                    pass
                loguru.logger.info("running APSIM now")
                gc.collect()

            send_jobs()
            a = time.perf_counter()

            def run():
                import Models
                gc.collect()
                from apsimNGpy.core.runner import invoke_csharp_gc
                invoke_csharp_gc()
                try:
                  _run_from_dir(folder, verbose=False, cpu_count=n_cores, run_only=True, pattern=apsimx_pattern)
                except Models.Core.SimulationException as mcse:
                    raise RuntimeError(mcse)

            run()
            print(time.perf_counter() - a, 'seconds')
            db_pattern = str(Path(apsimx_pattern).with_suffix('.db'))
            print(db_pattern)
            jobs = list(Path(folder).rglob(db_pattern))

            def collect():
                partial_collector = partial(get_results, db_or_con=self.db_path, prefix=self.table_prefix)
                for _ in custom_parallel(func=partial_collector, iterable=jobs, ncores=n_cores, threads=threads,
                                         progress_message='collecting data..'):
                    pass

            collect()
            time.sleep(0.3)
            gc.collect()

        finally:
            tmp.cleanup()
        print(list(folder.rglob('*.db')))


MultiCoreManager.save_to_csv.__doc__ = """  Persist simulation results to a SQLite database table.

        This method writes `self.results` (a pandas DataFrame) to the given csv file. It is designed to be robust in workflows where some simulations
        may fail: any successfully simulated rows present in `self.results` are
        still saved. This is useful when an ephemeral/temporary database was used
        during simulation and you need a durable copy\n.
        """ + csv_doc

if __name__ == '__main__':
    import os, uuid, tempfile

    # quick tests. comprehensive tests are in the tests

    # with tempfile.TemporaryDirectory() as td:
    #     create_jobs = ("Maize" for _ in range(1600))
    #     db_path = Path(td) / f"{uuid.uuid4().hex}.db"
    #     test_agg_db = Path(td) / f"_{uuid.uuid4().hex}.db"
    #
    #     Parallel = MultiCoreManager(db_path=test_agg_db, agg_func=None)
    #     # Parallel.run_all_jobs(create_jobs, n_cores=12, threads=False, clear_db=False, retry_rate=3, subset='Yield'          )
    #     Parallel.run_jobs_in_chunks(create_jobs, n_cores=12, threads=False, clear_db=False, retry_rate=3,
    #                                 subset='Yield', chunk_size=100,
    #                                 resume=False, db_session=test_agg_db)
    #     df = Parallel.get_simulated_output(axis=0)
    #     print(len(Parallel.tables))
    #     Parallel.clear_scratch()
    #     # test saving to already an existing table
    #     ve = False
    #     db_path.unlink(missing_ok=True)
    #     try:
    #         try:
    #             # ___________________first__________________________________
    #             Parallel.save_tosql(db_path, table_name='results', if_exists='replace')
    #             # ______________________ then _________________________________
    #             Parallel.save_tosql(db_path, table_name='results', if_exists='fail')
    #         except ValueError:
    #             ve = True
    #         assert ve == True, 'fail method is not raising value error'
    #
    #         # ____________test saving by replacing existing table _______________
    #         ve = False
    #         try:
    #
    #             Parallel.save_tosql(db_path, table_name='results', if_exists='replace')
    #         except ValueError:
    #             ve = True
    #         assert ve == False, 'replace method failed'
    #
    #         # ____________test appending to an existing table _______________
    #         ve = False
    #         try:
    #             Parallel.save_tosql(db_path, table_name='results', if_exists='append')
    #         except ValueError:
    #             ve = True
    #         assert ve == False, 'append method failed'
    #     finally:
    #         pass
    Parallel = MultiCoreManager(db_path=Path("test_agg_3.db").resolve(), agg_func=None)
    jobs = ({'model': 'Maize', 'ID': i, 'inputs': [{'path': '.Simulations.Simulation.Field.Fertilise at sowing',
                                                   'Amount': i}]} for i in range(40))
    Parallel.run_all_jobs(jobs=jobs, n_cores=2, engine='python')
    dff = Parallel.results
    print(dff.shape)
