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


from typing import Tuple, Dict, Any


def _inspect_job(job) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
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
    job = {'model':job,  'inputs': {
                           'path': '.Simulations.Simulation.Field.Fertilise at sowing',
                           'Amount': 100
                       }}
    match job:
        case str():
            return job, {}, {}

        case dict():
            data = dict(job)  # shallow copy to avoid side effects
            try:
                model = data.pop("model")
            except KeyError as exc:
                raise ValueError(
                    "Job dictionary must contain a 'model' key."
                ) from exc
            inputs = data.pop("inputs", {})
            return model, data, inputs

        case _:
            raise ValueError(
                f"Unsupported job specification of type {type(job).__name__}"
            )


def _runner(
        job: str | dict,
        agg_func: str,
        incomplete_jobs: set | list,
        db,
        if_exists: str = "append",
        index: str | list | None = None,
        table_prefix: str = "__",
        timeout=1000,
        call_back=None):
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
        include additional metadata to be attached to the results.
    agg_func : str
        Name of the aggregation function to apply to simulation outputs
        (e.g., ``'mean'``, ``'sum'``). If ``None`` or empty, raw simulation
        results are returned without aggregation.
    incomplete_jobs : set or list
        A mutable container used to track jobs that fail during execution.
        Failed model paths are appended or added depending on container type.
    db : str or database handle
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
        timeout for each individual run

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

    @write_results_to_sql(db_path=db, if_exists=if_exists)
    def _inside_runner():
        """
        Inner worker function executed under the SQL persistence decorator.

        This function runs the APSIM simulation, prepares the result dataset,
        and returns a dictionary describing both the data and its target table.
        """

        model, metadata, inputs = _inspect_job(job)

        with ApsimModel(model) as _model:
            try:
                if call_back and callable(call_back):
                    # there might be additional works that the user wants to enforce
                    call_back(model)
                if inputs:
                    # set before running
                    _model.set_params(**inputs)
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
                    out = _model.results

                # Attach execution metadata
                run_id = process_id()
                out["ExecutionID"] = schema_id(tuple(out.columns))
                out["ProcessID"] = run_id
                # avoid duplicates columns
                metadata = {**metadata, **inputs}
                out = out.assign(**metadata)

                # Generate a unique table identifier based on schema
                table_name = auto_generate_schema_id(
                    columns=tuple(out.columns),
                    prefix=table_prefix,
                )

                return {
                    "data": out,
                    "table": table_name,
                }

            except ApsimRuntimeError:
                # Track failed jobs without interrupting the workflow
                if isinstance(incomplete_jobs, list):
                    incomplete_jobs.append(_model.path)
                elif isinstance(incomplete_jobs, set):
                    incomplete_jobs.add(_model.path)

    _inside_runner()
