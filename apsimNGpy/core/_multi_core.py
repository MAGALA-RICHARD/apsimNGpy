import os
import sqlite3
from functools import cache, lru_cache
from pathlib import Path

import sqlalchemy
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from uuid import uuid4
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core_utils.database_utils import write_df_to_sql
from apsimNGpy.exceptions import ApsimRuntimeError
import hashlib
from multiprocessing import Value, Lock
from typing import Tuple, Dict, Any, List

aggs = {'sum', 'mean', 'max', 'min', 'median', 'std'}

counter = Value("i", 0)
lock = Lock()


def process_id():
    with lock:
        counter.value += 1
        return counter.value


def schema_id(schema):
    _schema = tuple(schema) if not isinstance(schema, (tuple, str)) else schema
    payload = "|".join(map(str, _schema)).encode("utf-8")
    return hashlib.md5(payload).hexdigest()


def auto_generate_schema_id(columns, prefix):
    table_id = f"{prefix}_{schema_id(columns)}"
    return table_id


def merge_dict(data):
    merged = {}
    for d in data:
        d.pop('path', None)
        for k, v in d.items():
            merged.update({k: v})
    return merged


def _inspect_job(job) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Normalize a job specification into a model identifier and metadata.

    Parameters
    ----------
    job : str or dict
        Job specification. If a string is provided, it is interpreted as
        the model identifier and no metadata is assumed. If a dictionary
        is provided, it must contain a ``'model'`` key identifying the
        simulation model; all remaining key–value pairs are treated as
        metadata.

    Returns
    -------
    model : str
        The simulation model identifier.
    meta_data : dict
        Associated metadata for the job. Empty if ``job`` is a string.

    Raises
    ------
    ValueError
        If ``job`` is neither a string nor a dictionary, or if a dictionary
        job does not contain a ``'model'`` key.
    """

    match job:
        case str():
            return job, {}, []

        case dict():
            data = dict(job)  # shallow copy to avoid side effects
            try:
                model = data.pop("model")
            except KeyError as exc:
                raise ValueError(
                    "Job dictionary must contain a 'model' key."
                ) from exc
            inputs = data.pop("inputs", [])

            return model, data, inputs

        case _:
            raise ValueError(
                f"Unsupported job specification of type {type(job).__name__}"
            )


def make_table_name(table_prefix: str, schema_id: str, run_id: int) -> str:
    u = uuid4().hex[:8]
    return f"{table_prefix}_{schema_id}_r{run_id}_{u}"


def single_runner(
        job: str | dict,
        agg_func: str,
        db_conn,
        if_exists: str = "append",
        index: str | list | None = None,
        table_prefix: str = "___",
        timeout=1000,
        chunk_size: int = None,
        subset=None,
        call_back=None,
        ignore_runtime_errors=True,
        retry_rate=1):
    """
    Execute a single APSIM simulation job and persist its results to a database.

    This function acts as a lightweight orchestration layer around an APSIM
    simulation run. It resolves the job specification, executes the model,
    optionally aggregates simulation outputs, enriches results with execution
    metadata, and delegates persistence to a database via a decorator.

    The actual execution logic is encapsulated in an inner function to allow
    transparent interception by the ``write_results_to_sql`` decorator.

    Parameters
    ----------
    job : str or dict
        Job specification identifying the APSIM model to run. If a string is
        provided, it is interpreted as the path to an ``.apsimx`` file. If a
        dictionary is provided, it must contain a ``'model'`` key and may
        include additional metadata to be attached to the results. or inputs key word with list[dicts] for model editing
    agg_func : str
        Name of the aggregation function to apply to simulation outputs
        (e.g., ``'mean'``, ``'sum'``). If ``None`` or empty, raw simulation
        results are returned without aggregation.
    db_conn : str or database handle or connection object
        Target database path or connection used by the SQL writer decorator.
    if_exists : str, optional
        SQL table handling policy (e.g., ``'append'``, ``'replace'``),
        forwarded to the persistence layer. Default is ``'append'``.
    index : str or list of str, optional
        Column name(s) used to group results prior to aggregation. If not
        provided, grouping defaults to ``'source_table'`` to prevent
        aggregation across heterogeneous APSIM output tables.
    table_prefix : str, optional
        Prefix used when auto-generating unique database table names based
        on result schema. Default is ``'__'``.
    timeout: int, optional default is 1000
        timeout for each run
    chunk_size: int, optional default is None
       if data is too large
    call_back: callable, optional
       use it to do constant edits should take in a positional argument model.
    subset: str, list of str, optional
        used to subset the columns after simulation
    ignore_runtime_errors: bool, optional. Default is True
      Ignore ApsimRunTimeError, to avoid breaking the program during multiprocessing
      other processes can proceed, while we can keep the failed jobs.
    retry_rate: int, optional default is 1
       Number of times to retry by tenacity if ApsimRunTimeError is encountered, this suspects
       that it is due to timeout errors. Other errors may be fatal, and after this retrial, they will be displayed


    Returns
    -------
    None
        Results are written to the database as a side effect. Failed jobs are
        recorded in ``incomplete_jobs``.

    Notes
    -----
    - Each execution is isolated and uses a context-managed apsimNGpy model
      instance to ensure proper cleanup.
    - Aggregation is applied only to numeric columns.
    - Result tables are uniquely named using a schema hash derived from
      column names to avoid database collisions. The hash is deterministic and it is further prefixed with user table prefix id default is __
    - Execution and process identifiers are attached to all output rows to
      support reproducibility and parallel execution tracking. Execution is determined from columns schemas
      and process ID is stochastic from each process or threads
    """
    SUCCESS = {'success': False}  # none can mean different things

    @retry(stop=stop_after_attempt(retry_rate),
           retry=retry_if_exception_type((ApsimRuntimeError, TimeoutError, sqlite3.OperationalError)))
    def runner_it():
        def _inside_runner(sub):
            """
            Inner worker function executed under the SQL persistence decorator.

            This function runs the APSIM simulation, prepares the result dataset,
            and returns a dictionary describing both the data and its target table.
            """

            model, metadata, inputs = _inspect_job(job)
            ID = metadata.get("ID", None) if metadata else None
            with (ApsimModel(model) as _model):
                try:
                    if call_back and callable(call_back):
                        # there might be additional works that the user wants to enforce
                        call_back(model)
                    if inputs:
                        # set before running
                        for in_put in inputs:
                            _model.set_params(**in_put)
                    _model.run(timeout=timeout)

                    # Aggregate results if requested
                    if agg_func:
                        if agg_func not in aggs:
                            raise ValueError(
                                f"Unsupported aggregation function '{agg_func}'"
                            )

                        grp = index or "source_table"
                        dat = _model.results.groupby(grp)
                        out = dat.agg(agg_func, numeric_only=True)
                        out["source_name"] = Path(model).name
                    else:
                        grp = 'source_table'
                        out = _model.results

                    if sub:

                        sub = [sub] if isinstance(sub, str) else sub
                        if set(sub).issubset(out.columns):
                            out = out[[*sub]].copy()
                    # Attach execution metadata
                    PID = os.getpid()
                    out["MetaProcessID"] = PID
                    # avoid duplicates columns
                    merged_inputs = merge_dict(inputs)
                    metadata = {**metadata, **merged_inputs}
                    out = out.assign(**metadata)
                    schema_hash = schema_id(tuple(out.dtypes))
                    out["MetaExecutionID"] = ID or schema_hash
                    ##########################################################################################
                    # Generate a unique table identifier based on schema and process ID that way they cannot be resource sharing of the same table
                    ############################################################################################################
                    table_name = f"{table_prefix}_{schema_hash}_{PID}"
                    write_df_to_sql(out, db_or_con=db_conn, table_name=table_name, if_exists=if_exists, chunk_size=chunk_size)

                except ApsimRuntimeError as apr:
                    # Track failed jobs without interrupting the workflow
                    if ignore_runtime_errors:
                        return job
                    else:
                        raise ApsimRuntimeError(f"runtime errors occurred{apr}")
                except TimeoutError as te:
                    if ignore_runtime_errors:
                        return job
                    else:
                        raise TimeoutError(f'time out occurred: {te}')
                except sqlite3.OperationalError as oe:
                    if ignore_runtime_errors:
                        return job
                    else:
                        raise sqlite3.OperationalError(f"data base operation error occurred {oe}")

        _inside_runner(subset)
        SUCCESS['success'] = True
        return SUCCESS['success']

    return runner_it()
