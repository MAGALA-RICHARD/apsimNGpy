import dataclasses
import os
import shutil
from pathlib import Path

import pandas as pd
from pathlib import Path
from apsimNGpy.core.apsim import ApsimModel
from itertools import batched
from collections.abc import Iterable
from typing import Any
from apsimNGpy.core_utils.utils import timer, get_array_like
from apsimNGpy.parallel.process import custom_parallel
from enum import StrEnum
import uuid
from apsimNGpy.core_utils.database_utils import write_df_to_sql, read_db_table, get_db_table_names, drop_table
from apsimNGpy.core.runner import run_apsim_by_path
import psutil

MODEL_KEY = 'model'
IDENTIFICATION = 'ID'
PAYLOAD = 'payload'
INPUTS = 'inputs'
PATH = 'path'
INPUTS_KEY = 'inputs'
TEMP = Path('.batched.scratch')
TEMP.mkdir(exist_ok=True)
TOTAL_THREADS = psutil.cpu_count(logical=True)


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


@dataclasses.dataclass
class WDConfig:
    BASE_DIR = TEMP


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


def collect_results(db, tables=None):
    db = Path(db).with_suffix(".db")
    tables = get_array_like(tables or get_db_table_names(db))
    if tables is None:
        tables = get_db_table_names(db)

    tables = get_array_like(tables)

    if not tables:
        raise ValueError(f"No tables were found in database in database: `{db}`")
    return pd.concat((read_db_table(db, table).assign(source_table=table) for table in tables), ignore_index=True)


def agg_simulations(payload, reports=None, base_dir=None):
    """
    iterable of jobs
    @param payload:
    @param out_path:
    @return:
    """
    base_Dir = base_dir or TEMP

    if not Path(base_Dir).exists():
        raise ValueError(f"Base directory `{base_Dir}` does not exists on the computer")
    base_Dir = Path(base_Dir)
    WDConfig.BASE_DIR = base_Dir

    def _batch(jj):
        jobs = extract_jobs(jj)
        data = jobs[Config.DATA_KEY]
        model_v = jobs[Config.MODEL_KEY]
        tmp = uuid.uuid4().hex

        out_path = base_Dir / f"tmp_{tmp}_.apsimx"
        model = ApsimModel(model_v, out_path=out_path)
        if len(model) != 1:
            raise ValueError(f"Expected one simulation got {len(model)} simulations")
        in_puts = jobs[Config.INPUTS_KEY]
        ID = data.get(IDENTIFICATION, None) if data else None
        if ID is None:
            raise ValueError(f"identification {IDENTIFICATION} required")

        _ = [model.edit_model('Models.Report', rep, variable_spec=['[Simulation].Name as ID']
                              ) for rep in model.inspect_model('Models.Report', fullpath=False)]

        _ = [model.set_params(job) for job in in_puts]
        model[0].Name = f"{ID}"
        model.save()
        return model.path

    files = [_batch(jj) for _, jj in enumerate(payload)]
    cpu = max(1, int(TOTAL_THREADS / 2.5))
    ret = run_apsim_by_path(model=files, timeout=None, n_cores=cpu)
    if ret.returncode == 0:
        out = pd.concat(collect_results(db, tables=reports) for db in files)
        out['PID'] = os.getpid()
        del files, ret
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


def runner(batch: dict, tables, db_or_con, prefix='Batch', base_dir=None):
    batch_id = batch[Config.BATCH_ID_KEY]
    batch_data = batch['batch_data']
    fn = f"{prefix}_{batch_id}.apsimx"
    res = agg_simulations(batch_data, reports=tables, base_dir=base_dir)
    tables = Path(fn).stem
    write_df_to_sql(out=res, db_or_con=db_or_con, table_name=tables, if_exists='replace', index=False,
                    chunk_size=None)


@timer
def run_multiple_simulations(iterable, n_cores: int = 1, batch_size: int = 20, tables=None, db_or_con=None,
                             threads=False, base_dir=None, prefix='batch'):
    # all tables are from  the provided db before running
    if not dispose(db_or_con):
        raise ValueError("failed to dispose all database tables")
    if db_or_con is None:
        raise ValueError("db_or_con must be specified for storing the data")
    batches = split_jobs(iterable, batch_size)
    jobs = custom_parallel(runner, batches, tables, db_or_con, prefix, base_dir, ncores=n_cores, use_thread=threads,
                           unit='batch',
                           progressbar=True)
    for _ in jobs:
        pass
    # try to delete files
    wd = Path(WDConfig.BASE_DIR)
    if wd.exists():
        shutil.rmtree(wd, ignore_errors=True)


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

    nconc = np.arange(0.5, 3, 0.002)
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
    rt = run_multiple_simulations(job, n_cores=10, batch_size=6, tables="Report", db_or_con='db.db')
    df = load_all_results('db.db')
    assert len(df.ID.unique()) == len(nconc), 'Some entries are being left out perhaps'
    end = time.perf_counter()
    print((end - start) / len(nconc), 'seconds')
