import gc
import os.path
import shutil
from collections import OrderedDict
from pathlib import Path
from typing import Union

import numpy as np
from sqlalchemy import create_engine, MetaData, Table, Column, String, Float, Integer
from sqlalchemy.dialects.sqlite import insert
import pandas as pd

from sqlalchemy import create_engine

from apsimNGpy.parallel.process import custom_parallel
from apsimNGpy.core.apsim import ApsimModel
from collections.abc import Iterable
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core_utils.database_utils import read_db_table, clear_all_tables

ID = 0


def is_my_iterable(value):
    """Check if a value is an iterable, but not a string."""
    return isinstance(value, Iterable) and not isinstance(value, str)


data_type = {}

from sqlalchemy import create_engine, text


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


class ParallelRunner:
    def __init__(self, db_path: Union[str, Path], agg_func=None):
        db_path = str(db_path)
        self.counter = 0
        self.db_path = db_path
        self.tables = setData if setData else set()
        self.agg_func = agg_func

    def insert_data(self, results, table):

        engine = create_engine(f"sqlite:///{self.db_path}")
        metadata = MetaData()

        # Define your schema manually for full control
        if isinstance(results, pd.DataFrame):
            results = results.select_dtypes(include='number')
            res = results
            cols = [Column(i, Float) for i in results.columns if res[i].dtype == np.float32]
        else:
            cols = [Column(i, Float) for i in results]
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

    def run_parallel(self, model):
        self.counter += 1
        model = ApsimModel(model, out_path=None)
        table_names = model.inspect_model('Models.Report', fullpath=False)
        crops = model.inspect_model('Models.PMF.Plant', fullpath=False)
        crop_table = [f"{a}_{b}" for a, b in zip(table_names, crops)]
        tables = '_'.join(crop_table)
        model.run()
        if self.agg_func:
            out = getattr(model.results, self.agg_func)(numeric_only=True)
            out = out.to_dict()

        else:
            out = model.results
        out['SimulationID'] = int(self.counter)

        self.insert_data(out, table=tables)

        model.clean_up()
        gc.collect()

    def get_simulated_output(self, axis=0):
        tb = read_db_table(self.db_path, report_name='table_names')
        tb_names = tb['table'].values.tolist()
        df = [read_db_table(self.db_path, report_name=rp) for rp in tb_names]
        return pd.concat(df, axis=axis)

    def clear_db(self):
        if not self.db_path.endswith('.db'):
            raise ValueError(f"Cannot clear invalid db path: {self.db_path}")
        if os.path.exists(self.db_path):
            clear_all_tables(self.db_path)

    def run_all_jobs(self, jobs, n_cores=6, threads=False):
        """
        runs all provided jobs using processes
        :param threads: threads or processes
        :param jobs: jobs to run
        :param n_cores: number of cores to use
        :return: None
        """
        self.clear_db()  # each simulation is fresh,
        # future updates include support for skipping some simulation
        for _ in custom_parallel(self.run_parallel, jobs, ncores=n_cores, use_threads=threads,
                                 progress_message='Processing all jobs. Please wait!: '):
            pass


# Example usage:
# df = pd.DataFrame([{"name": "Temperature", "value": 25.4, "unit": "C"}])
# model.results = df
# configure_db(model, "my_database.sqlite")
@timer
def configure_db(model, db):
    results = model.results
    engine = create_engine(f'sqlite:///{db}')
    if isinstance(results, pd.DataFrame):
        results.to_sql('results', engine, if_exists='replace', index=False)


# You can run many simulations in a distributed computing model either through using threads or processes

def run_parallel(model):
    global ID
    ID += 1
    model = ApsimModel(model, out_path=None)
    model.run()
    model.clean_up()
    configure_db(model=model, db='x.db')
    cc = gc.collect()


if __name__ == '__main__':
    job = ['Maize', 'Soybean', 'Barley', 'Canola', "Wheat", 'Oats', "Potato", 'MungBean']
    # clear_all_tables('my.db')
    create_jobs = [ApsimModel('Maize').path for _ in range(100)]
    Parallel = ParallelRunner(db_path='my.db', agg_func='mean')
    Parallel.run_all_jobs(create_jobs, n_cores=4, threads=False)
    df = Parallel.get_simulated_output(axis=0)
    wdr = Path(".").glob("*scratch")
    try:
        [shutil.rmtree(i) for i in wdr]
    except PermissionError:
        pass
