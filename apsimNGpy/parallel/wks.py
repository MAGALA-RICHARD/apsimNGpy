import dataclasses
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures.process import ProcessPoolExecutor
from enum import StrEnum
from pathlib import Path

import pandas as pd
import psutil

from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.runner import run_apsim_by_path
from apsimNGpy.core_utils.database_utils import write_df_to_sql, read_db_table, get_db_table_names
from apsimNGpy.core_utils.utils import get_array_like

MODEL_KEY = 'model'
IDENTIFICATION = 'ID'
PAYLOAD = 'payload'
INPUTS = 'inputs'
PATH = 'path'
INPUTS_KEY = 'inputs'
TEMP = Path('../.batched.scratch')
TEMP.mkdir(exist_ok=True)
TOTAL_THREADS = psutil.cpu_count(logical=True)


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


def _batch(jj, base_dir):
    jobs = extract_jobs(jj)
    data = jobs[Config.DATA_KEY]
    model_v = jobs[Config.MODEL_KEY]
    tmp = uuid.uuid4().hex

    out_path = base_dir / f"tmp_{tmp}_.apsimx"
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


def agg_simulations(payload, reports=None, base_dir=None, inner_threads=4, threads=False):
    """
    iterable of jobs
    @param payload:
    @param out_path:
    @return:
    """
    base_Dir = base_dir or TEMP
    base_Dir.mkdir(exist_ok=True)
    if not Path(base_Dir).exists():
        raise ValueError(f"Base directory `{base_Dir}` does not exists on the computer")
    base_Dir = Path(base_Dir)
    WDConfig.BASE_DIR = base_Dir

    Pool = ThreadPoolExecutor if threads else ProcessPoolExecutor
    with Pool(max_workers=inner_threads) as executor:
        from itertools import repeat

        files = tuple(
            executor.map(_batch, payload, repeat(base_Dir))
        )

    # files = [_batch(jj) for _, jj in enumerate(payload)]
    cpu = max(1, int(TOTAL_THREADS / 1.5))
    ret = run_apsim_by_path(model=files, timeout=None, n_cores=inner_threads)
    if ret.returncode == 0:
        out = pd.concat(collect_results(db, tables=reports) for db in files)
        out['PID'] = os.getpid()
        del files, ret
        del executor
        return out


def runner(batch: dict, tables, db_or_con, prefix='Batch', base_dir=None, inner_threads=4, threads=False):
    batch_id = batch[Config.BATCH_ID_KEY]
    batch_data = batch['batch_data']
    fn = f"{prefix}_{batch_id}.apsimx"
    res = agg_simulations(batch_data, reports=tables, base_dir=base_dir, inner_threads=inner_threads)
    tables = Path(fn).stem
    write_df_to_sql(out=res, db_or_con=db_or_con, table_name=tables, if_exists='replace', index=False,
                    chunk_size=None)


if __name__ == '__main__':
    pp = Path(r'G:/')
    for i in pp.rglob('*apsim_watershed_optimization_2026*.docx'):
        print(i)
