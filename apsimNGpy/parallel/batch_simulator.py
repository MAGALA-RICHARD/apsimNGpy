# Retained for cases where combining simulations into one APSIM file is useful,
# although appending many simulations can become computationally expensive.
import os
from pathlib import Path

import pandas as pd
from pathlib import Path
from apsimNGpy.core.apsim import ApsimModel
from itertools import batched
from collections.abc import Iterable
from typing import Any
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.parallel.process import custom_parallel
from enum import StrEnum
import uuid
from apsimNGpy.core_utils.database_utils import write_df_to_sql, read_db_table, get_db_table_names, drop_table

MODEL_KEY = 'model'
IDENTIFICATION = 'ID'
PAYLOAD = 'payload'
INPUTS = 'inputs'
PATH = 'path'
INPUTS_KEY = 'inputs'
TEMP = Path('.scratch')
TEMP.mkdir(exist_ok=True)


def dispose(db):
    """drop all tables in a database"""
    tables = get_db_table_names(db)
    drop = [drop_table(db, tb) for tb in tables]
    return all(drop)


class Config(StrEnum):
    MODEL_KEY = "model"
    IDENTIFICATION = "ID"
    PAYLOAD = "payload"
    INPUTS_KEY = "inputs"
    PATH_KEY = "path"
    BATCH_ID_KEY = "batch_id"
    BATCH_DATA_KEY = "batch_data"
    DATA_KEY = 'data'


def extract_jobs(job):
    match job:
        case dict():
            data = dict(job)  # shallow copy to avoid side effects
            try:
                _model = data.pop(Config.MODEL_KEY)
            except KeyError as exc:
                raise ValueError(
                    f"Job dictionary must contain a {Config.MODEL_KEY} key."
                ) from exc
            inputs = data.pop(INPUTS, [])

            # users are also free to use the key word payload
            payload = data.pop(PAYLOAD, [])
            inputs = inputs or payload
            return {Config.MODEL_KEY: _model, Config.DATA_KEY: data, Config.INPUTS_KEY: inputs}

        case _:
            raise ValueError(
                f"Unsupported job specification of type {type(job).__name__}"
            )


def agg_simulations(payload, out_path, reports=None):
    """
    iterable of jobs
    @param payload:
    @param out_path:
    @return:
    """
    model = None

    for cou, jj in enumerate(payload):
        jobs = extract_jobs(jj)
        data = jobs[Config.DATA_KEY]
        model_v = jobs[Config.MODEL_KEY]
        in_puts = jobs[Config.INPUTS_KEY]
        ID = data.get(IDENTIFICATION, None) if data else None
        if ID is None:
            raise ValueError(f"identification {IDENTIFICATION} required")
        if not model:
            f_name = Path(out_path).stem
            tmp = uuid.uuid4().hex
            out_path = TEMP / f"tmp_{tmp}_{f_name}.apsimx"
            model = ApsimModel(model_v, out_path=out_path)
            [model.edit_model('Models.Report', rep, variable_spec=['[Simulation].Name as ID']
                              ) for rep in model.inspect_model('Models.Report', fullpath=False)]
            if len(model) != 1:
                raise ValueError(f"Expected one simulation got {len(model)} simulations")
        if cou == 0:
            model.save()
            for job in in_puts:
                model.set_params(job)
            model[0].Name = f"{ID}"
        else:
            model.append_simulation(model[0], rename=f"{ID}", payload=jobs[Config.INPUTS_KEY], fp=True)
    with model.run(reports):
        pid = os.getpid()
        out = model.results
        out['PID'] = pid
        return out


def split_jobs(jobs: Iterable[Any], size: int = 10):
    """
    Split jobs into batches of a specified size.

    Parameters
    ----------
    jobs : Iterable
        Collection of jobs to split.
    size : int
        Number of jobs per batch.

    Yields
    ------
    tuple
        A batch containing up to ``size`` jobs.
    """
    if not 5 <= size <= 15:
        raise ValueError("'size' must be between 5 and 15 inclusive")
    for counter, jy in enumerate(batched(jobs, size)):
        yield {'batch_id': counter, 'batch_data': jy}


def runner(batch: dict, tables, db_or_con, prefix='Batch'):
    batch_id = batch[Config.BATCH_ID_KEY]
    batch_data = batch['batch_data']
    print(len(batch_data))
    fn = f"{prefix}_{batch_id}.apsimx"
    res = agg_simulations(batch_data, out_path=fn, reports=tables)
    tables = Path(fn).stem
    write_df_to_sql(out=res, db_or_con=db_or_con, table_name=tables, if_exists='replace', index=False,
                    chunk_size=None)


@timer
def run_multiple_simulations(iterable, n_cores: int = 1, batch_size: int = 20, tables=None, db_or_con=None,
                             threads=False):
    if not dispose(db_or_con):
        raise ValueError("failed to dispose all database tables")
    if db_or_con is None:
        raise ValueError("db_or_con must be specified for storing the data")
    batches = split_jobs(iterable, batch_size)
    jobs = custom_parallel(runner, batches, tables, db_or_con, ncores=n_cores, use_thread=threads, unit='batch',
                           progressbar=True)
    for _ in jobs:
        pass


@timer
def load_all_results(db):
    return pd.concat(
        (read_db_table(db, table)
         for table in get_db_table_names(db)),
        ignore_index=True
    )


if __name__ == '__main__':
    import time

    job = []
    import numpy as np

    nconc = np.arange(0.5, 3, 0.02)
    for i, data in enumerate(nconc):
        ip = {"model": "Maize", 'ID': i,
              "inputs": [{'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': 12},
                         {'path': ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82",
                          'commands': {"[Leaf].Photosynthesis.RUE.FixedValue": data},
                          'managers': {'Sow using a variable rule': 'CultivarName'}, 'plant': 'Maize'},
                         ]
              }
        job.append(ip)

    # rt = agg_simulations(job, 's.apsimx')
    start = time.perf_counter()
    from apsimNGpy.core_utils.database_utils import get_db_table_names, drop_table, clear_all_tables

    [drop_table('db.db', tb) for tb in get_db_table_names('db.db')]
    tabs = get_db_table_names('db.db')
    print(tabs)
    rt = run_multiple_simulations(job, n_cores=10, batch_size=11, tables="Report", db_or_con='db.db')
    df = load_all_results('db.db')
    end = time.perf_counter()
    print((end - start) / len(nconc), 'seconds')
