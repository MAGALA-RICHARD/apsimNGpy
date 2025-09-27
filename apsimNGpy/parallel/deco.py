import sys
import inspect
import pandas as pd
from functools import wraps
from pathlib import Path
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core_utils.database_utils import read_db_table
from apsimNGpy.core_utils.utils import timer
from threading import Lock
from apsimNGpy.parallel.data_manager import write_results_to_sql


@timer
def collect_apsim_results(db_path, table="Report", insert_fn=None):
    """
    Decorator: after the wrapped function returns, scan its local variables for
    ApsimModel instances and write their `.results` to `db_path`/`table`.
    Also handles if the function returns a DataFrame or an ApsimModel.
    """
    if insert_fn is None:
        # expects: insert_fn(db: str|Path, df: DataFrame, table: str)
        def insert_fn(db, df, table):
            from sqlalchemy import create_engine
            eng = create_engine(f"sqlite:///{db}")
            df.to_sql(table, eng, if_exists="append", index=False)

    db_path = str(Path(db_path).with_suffix(".db"))

    def decorator(func):
        code = func.__code__

        @wraps(func)
        def wrapper(*args, **kwargs):
            collected_models = []

            def tracer(frame, event, arg):
                # Only intercept the specific function's return event
                if event == "return" and frame.f_code is code:
                    for v in frame.f_locals.values():
                        if isinstance(v, ApsimModel):
                            collected_models.append(v)
                return tracer  # keep tracing within this call stack

            # settrace is per-thread (safer than setprofile for this)
            old_tracer = sys.gettrace()
            sys.settrace(tracer)
            try:
                result = func(*args, **kwargs)
            finally:
                sys.settrace(old_tracer)

            # Helper to insert a DataFrame
            def _insert_df(df: pd.DataFrame):
                if df is not None and not df.empty:
                    insert_fn(db_path, df, table)

            # 1) Any ApsimModel seen in locals
            for m in collected_models:
                _insert_df(getattr(m, "results", None))

            # 2) If worker returns a DataFrame
            if isinstance(result, pd.DataFrame):
                _insert_df(result)

            # 3) If worker returns an ApsimModel
            if isinstance(result, ApsimModel):
                _insert_df(getattr(result, "results", None))

            return result

        return wrapper

    return decorator


def collect_returned_results(db_path, table="Report", insert_fn=None):
    # same insert_fn default as above
    if insert_fn is None:
        # expects: insert_fn(db: str|Path, df: DataFrame, table: str)
        def insert_fn(db, df, table):
            from sqlalchemy import create_engine
            eng = create_engine(f"sqlite:///{db}")
            df.to_sql(table, eng, if_exists="append", index=False)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, pd.DataFrame):
                insert_fn(str(Path(db_path).with_suffix(".db")), result, table)
            elif isinstance(result, ApsimModel):
                if result.ran_ok:
                    df = getattr(result, "results", None)
                    if df is not None and not df.empty:
                        insert_fn(str(Path(db_path).with_suffix(".db")), df, table)
                else:
                    result.run(table)
                    if result.ran_ok:
                        df = result.results
                        if not df.empty:
                            insert_fn(str(Path(db_path).with_suffix(".db")), df, table)
                    raise ValueError("tried running results for you but in vain")
            else:
                raise TypeError(f"{func} Result is not a DataFrame or ApsimModel")
            return result

        return wrapper

    return decorator


@write_results_to_sql(db_path="dt.db", table="Report")
def worker(n):
    with Lock():
        model = ApsimModel('Maize')
        # model.edit_model("Models.Manager", model_name="Fertilise at sowing", Amount=nitrogen_rate)\

        model.run(report_name="Report", verbose=False)
        df = model.results
        df["nitrogen rate"] = str(n)
        model.clean_up()
        return df


if __name__ == '__main__':
    worker('Maize')
    from apsimNGpy.parallel.process import custom_parallel

    # df =read_db_table("DATAB.db", report_name="Report")
    jjs = (ApsimModel("Maize", out_path=f"_{idn}").path for idn in range(200))
    for _ in custom_parallel(worker, range(200), ncores=6):
        pass
