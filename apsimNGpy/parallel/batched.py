"""
The `batched.py` script is designed to run APSIM files in batches, where send a specified number of edited apsimx files to Models.exe or Models
 while still supporting parallel execution.
 The initial approach was to combine multiple simulations into a single APSIM file and run them together.
 However, this became computationally expensive as the number of simulations increased because appending
 simulations to one file introduced substantial overhead.

 The implementation of that approach is retained in `batch_simulator`. Although this method has not
  been rigorously benchmarked, it may still be useful in specific cases where batching simulations into a
  single file is more convenient or where the overhead remains manageable.

  The underlying motivation for both batching approaches is that starting the APSIM executable, `Models.exe` on Windows
   or `Models` on other platforms can be computationally expensive. Each new process launch introduces startup overhead
   because the executable must initialize, load model assemblies, parse input files, and prepare the simulation environment
    before any actual simulation work begins. For large simulation workflows, repeatedly starting APSIM for individual files
    can therefore waste substantial time. These batching utilities attempt to reduce that overhead by grouping simulations so
     that each APSIM process simulate more at a go after startup.


"""
import dataclasses
import os
import shutil
import sys
from concurrent.futures.process import ProcessPoolExecutor
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
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
TEMP = Path('./../.batched.scratch')
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
    if not 2 <= size <= 200:
        raise ValueError("'size' must be between 2 and 200 inclusive")
    for counter, jy in enumerate(batched(jobs, size)):
        yield {'batch_id': counter, 'batch_data': jy}




@timer
def run_multiple_simulations(iterable, n_cores: int = 1, batch_size: int = 20, tables=None, db_or_con=None,
                             threads=False, base_dir=None, prefix='batch', inner_threads=None):
    # all tables are from  the provided db before running
    if not dispose(db_or_con):
        raise ValueError("failed to dispose all database tables")
    if db_or_con is None:
        raise ValueError("db_or_con must be specified for storing the data")
    batches = split_jobs(iterable, batch_size)
    inner = inner_threads or n_cores
    print(f'selected core: {inner}')
    inner_threads = inner
    from apsimNGpy.parallel.wks import agg_simulations, runner, WDConfig
    size= 0
    ba = 0
    import time
    start = time.perf_counter()
    try:
        print(f'Processing batched jobs...', end="", file=sys.stderr)
        while True:

            batch = next(batches, None)

            if batch is None:

                break
            bs = len(batch['batch_data'])
            runner(batch, tables, db_or_con, prefix, base_dir, int(inner_threads), threads)
            wd = Path(WDConfig.BASE_DIR)
            if wd.exists():
                shutil.rmtree(wd, ignore_errors=True)
            elapsed = time.perf_counter() - start
            h, rem = divmod(int(elapsed), 3600)
            m, s = divmod(rem, 60)
            size+=bs
            ba += 1
            print(
                f"\rProgress: {size} simulations ({ba} batches) completed "
                f"| Elapsed: {h:02}:{m:02}:{s:02}",
                end="",
                flush=True,
                file=sys.stderr,
            )
        print(file=sys.stderr)  # Move to a new line after completion.
    finally:
        print(file=sys.stderr)


    # jobs = custom_parallel(runner, batches, tables, db_or_con, prefix, base_dir, inner_threads, ncores=n_cores,
    #                        use_thread=threads,
    #                        unit='batch',
    #                        progressbar=True)
    # for _ in jobs:
    #     pass
    # # try to delete files



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

    radiations = np.arange(0.5, 3, 0.0055)
    for i, data in enumerate(radiations):
        ip = {"model": "Maize", 'ID': i,
              "inputs": [
                         {'path': ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82",
                          'commands': {"[Leaf].Photosynthesis.RUE.FixedValue": data},
                          'managers': {'Sow using a variable rule': 'CultivarName'}, 'plant': 'Maize'},
                         ]
              }
        job.append(ip)

    # rt = agg_simulations(job, 's.apsimx')
    start = time.perf_counter()
    from apsimNGpy.core_utils.database_utils import get_db_table_names, drop_table

    rt = run_multiple_simulations(job, n_cores=6, batch_size=100,inner_threads=10, tables="Report", db_or_con='db.db')
    mdf = load_all_results('db.db')
    assert len(mdf.ID.unique()) == len(radiations), 'Some entries are being left out perhaps'
    end = time.perf_counter()
    print((end - start) / len(radiations), 'seconds')

    from apsimNGpy import ApsimModel

    #  tmp = uuid.uuid4()
    wd = Path('.scrat')
    wd.mkdir(parents=True, exist_ok=True)


    @timer
    def single():
        data = []
        for ID, rue in enumerate(radiations):
            tmp = uuid.uuid4()
            print(f'Simulating: , {ID}')
            file_name = wd / f"{tmp}.apsimx"
            model = ApsimModel('Maize', out_path=file_name)
            model.set_params(path=".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82",
                             commands={"[Leaf].Photosynthesis.RUE.FixedValue": rue},
                             managers={'Sow using a variable rule': 'CultivarName'}, plant='Maize')
            model.run('Report')
            d = model.results
            d['ID'] = ID
            data.append(d)
        sgd = pd.concat(data, ignore_index=True)
        shutil.rmtree(wd, ignore_errors=True)
        return sgd


    sgf = single()
    xd = df = pd.DataFrame(
        {
            "rue": radiations,
            "ID": range(len(radiations)),
        }
    )
    single = sgf.merge(xd, on="ID", how="inner")
    single.sort_values(by='ID', inplace=True)
    mdf['ID'] = mdf['ID'].astype('int')
    multiple = mdf.merge(xd, on="ID", how="inner")
    multiple.sort_values(by='ID', inplace=True)
    import shutil
    shutil.rmtree(wd, ignore_errors=True)
    yd = multiple['Yield'] - single['Yield']
    assert yd.mean() == 0, 'data is different'
    from apsimNGpy import logger
    logger.info('As of the above test no major differences between single and multiple processing in the simulation output')
