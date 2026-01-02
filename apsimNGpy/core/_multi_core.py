from functools import cache, lru_cache
from pathlib import Path
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core_utils.database_utils import write_results_to_sql
from apsimNGpy.exceptions import ApsimRuntimeError
import hashlib
from multiprocessing import Value, Lock

aggs = {'sum', 'mean', 'max', 'min', 'median', 'std'}

counter = Value("i", 0)
lock = Lock()


def process_id():
    with lock:
        counter.value += 1
        return counter.value


@lru_cache(maxsize=100)
def schema_id(schema):
    _schema = tuple(schema) if not isinstance(schema, (tuple, str)) else schema
    payload = "|".join(map(str, _schema)).encode("utf-8")
    return hashlib.md5(payload).hexdigest()[:8]


def auto_generate_schema_id(columns, prefix):
    table_id = f"{prefix}_{schema_id(columns)}"
    return table_id


def _runner(model: str,
            agg_func: str,
            incomplete_jobs: set | list,
            db, if_exists='append',
            index: str | list = None,
            table_prefix='__'):
    @write_results_to_sql(db_path=db)
    def _inside_runner():
        """
        This is the worker for each simulation.

        The function performs two things; runs the simulation and then inserts the simulated data into a specified
        database.

        :param model: str, dict, or Path object related .apsimx json file

        returns None
        """
        # initialize the apsimNGpy model simulation engine
        # aim is to run and return results hash the columns to create a unique table name to avoid schema collisions
        with ApsimModel(model) as _model:
            try:
                _model.run(timeout=200)
                # aggregate the data using the aggregated function
                if agg_func:
                    if agg_func not in aggs:
                        raise ValueError(f"unsupported aggregation function {agg_func}")
                    grp = index or 'source_table'
                    dat = _model.results.groupby(grp)  # if there are more than one table, we do not want to
                    # aggregate them together
                    out = dat.agg(agg_func, numeric_only=True)

                    out['source_name'] = Path(model).name

                else:
                    out = _model.results
                run_id = process_id()

                # track the model id
                out['ExecutionID'] = schema_id(str(model))
                out['ProcessID'] = run_id
                # return data in a format that can be used by the decorator writing data to sql
                # generated unique table id is based on schema
                tables = auto_generate_schema_id(columns=tuple(out.columns), prefix=table_prefix)

                out= {'data': out, 'table': tables}
                return out

            except ApsimRuntimeError:
                if isinstance(incomplete_jobs, list):
                    incomplete_jobs.append(_model.path)
                elif isinstance(incomplete_jobs, set):
                    incomplete_jobs.add(_model.path)

    _inside_runner()
