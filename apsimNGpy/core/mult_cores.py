import gc
import os.path
import shutil
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Union
from apsimNGpy.core_utils.utils import timer
import pandas as pd
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core_utils.database_utils import read_db_table, clear_all_tables, get_db_table_names
from apsimNGpy.parallel.process import custom_parallel
from sqlalchemy import MetaData, Table, Column, String, Float, Integer, MetaData
from sqlalchemy import create_engine, text

# Database connection

ID = 0


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


# Example usage:
# if simulation_exists("my_database.sqlite", "results", 42):
#     print("Simulation exists!")
# else:
#     print("Simulation not found.")

setData = set()


@timer
def insert_data_with_pd(db, table, results, if_exists):
    engine = create_engine(f'sqlite:///{db}')
    results.to_sql(table, engine, index=False, if_exists=if_exists)


def delete_table(db, table_name):
    """deletes the table in a database. Proceed with caution"""
    # database connection
    db = os.path.realpath(db)
    engine = create_engine(f"sqlite:///{db}")
    metadata = MetaData()

    # Load table
    table_to_drop = Table(f"{table_name}", metadata, autoload_with=engine)

    # Drop it
    table_to_drop.drop(engine)


@dataclass(slots=True)
class MultiCoreManager:
    db_path: Union[str, Path]
    counter: int = 0
    agg_func: Union[str, None] = None
    ran_ok: bool = False

    def insert_data(self, results, table):
        """
        Insert results into the specified table
        results: (Pd.DataFrame, dict) The results that will be inserted into the table
        table: str (name of the table to insert)
        """

        engine = create_engine(f"sqlite:///{str(self.db_path)}")
        metadata = MetaData()

        # Define your schema manually for full control
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
        if self.ran_ok:
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

        :param model: str, dict, or Path object related APSIMX json file

        returns None
        """
        # initialize the apsimNGpy model simulation engine
        _model = ApsimModel(model, out_path=None)
        table_names = _model.inspect_model('Models.Report', fullpath=False)
        # we want a unique report for each crop, because they are likely to have different report schema
        crops = _model.inspect_model('Models.PMF.Plant', fullpath=False)
        crop_table = [f"{a}_{b}" for a, b in zip(table_names, crops)]
        tables = '_'.join(crop_table)
        # run the model. without specifying report names, they will be detected automatically
        _model.run()
        # aggregate the data using the aggregated function
        if self.agg_func:
            if self.agg_func not in {'sum', 'mean', 'max', 'min', 'median', 'std'}:
                raise ValueError(f"unsupported aggregation function {self.agg_func}")
            dat = _model.results.groupby('source_table')  # if there are more than one table, we do not want to
            # aggregate them together
            out = dat.agg(self.agg_func, numeric_only=True)

            out['modelName'] = model

        else:
            out = _model.results
        # track the model id
        out['modelName'] = model
        # insert the simulated dataset into the specified database
        self.insert_data(out, table=tables)
        # clean up files related _model object
        _model.clean_up()
        # collect garbage before gc comes in
        gc.collect()

    def get_simulated_output(self, axis=0):
        """
        Get simulated output from the API
        :param axis: if axis =0, concatenation is along the rows and if it is 1 concatenation is along the columns
        """
        if axis not in {0, 1}:
            # Errors should go silently
            raise ValueError('Wrong value for axis should be either 0 or 1')

        data = [read_db_table(self.db_path, report_name=rp) for rp in self.tables]
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
                # if removing it has failed, connect to it and remove all tables
                tables = get_db_table_names(self.db_path)
                [delete_table(self.db_path, table_name=db) for db in tables]

    def clear_scratch(self):
        """clears the scratch directory where apsim files are cloned before being loaded. should be called after all simulations are completed

        """
        paths = Path.cwd().glob("*scratch")
        for path in paths:
            try:
                shutil.rmtree(str(path), ignore_errors=True)
            except PermissionError:
                ...

    def run_all_jobs(self, jobs, n_cores=6, threads=False, clear_db=True, clean_up=False):
        """
        runs all provided jobs using ``processes`` or ``threads`` specified
        :param ``threads (bool)``: threads or processes
        :param ``jobs (iterable[simulations paths]``: jobs to run
        :param ``n_cores (int)``: number of cores to use
        :param ``clear_db (bool)``: clear the database existing data if any. defaults to True
        :return: None
        """
        if clear_db:
            self.clear_db()  # each simulation is fresh,
        # future updates include support for skipping some simulation
        try:
            for _ in custom_parallel(self.run_parallel, jobs, ncores=n_cores, use_threads=threads,
                                     progress_message='Processing all jobs. Please wait!: '):
                ...
            self.ran_ok = True
        finally:
            time.sleep(0.5)  # buy some time to ensure all resources are released
            if clean_up:
                self.clear_scratch()


if __name__ == '__main__':
    # quick tests
    create_jobs = (ApsimModel('Maize').path for _ in range(10))

    Parallel = MultiCoreManager(db_path='testing.db', agg_func=None)
    Parallel.run_all_jobs(create_jobs, n_cores=4, threads=False, clear_db=True, clean_up=True)
    df = Parallel.get_simulated_output(axis=0)

    insert_data_with_pd('tss.db', 'my', df, 'replace')
