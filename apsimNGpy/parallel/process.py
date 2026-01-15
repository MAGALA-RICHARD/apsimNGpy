from __future__ import annotations

import gc
import os
from multiprocessing import cpu_count
from pathlib import Path
from typing import Any, Callable, Iterable, List, Sequence, Optional

import pandas as pd
from tqdm import tqdm
from apsimNGpy.core_utils.database_utils import read_db_table
from apsimNGpy.core_utils.run_utils import run_model
from apsimNGpy.parallel.data_manager import chunker
from apsimNGpy.settings import NUM_CORES
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

CPU = int(int(cpu_count()) * 0.5)
CORES = NUM_CORES
import time


def select_type(use_thread: bool, n_cores: int):
    return ThreadPoolExecutor(n_cores) if use_thread else ProcessPoolExecutor(n_cores)


def custom_parallel(func, iterable: Iterable, *args, **kwargs):
    """
    Run a function in parallel using threads or processes.

    Parameters
    ----------
    func : callable
        The function to run in parallel.
    iterable : iterable
        An iterable of items to be processed by ``func``.
    *args
        Additional positional arguments to pass to ``func``.

    Yields
    ------
    Any
        The result of ``func`` for each item in ``iterable``.

   kwargs
    ----------------
    use_thread : bool, optional, default=False
        If ``True``, use threads; if ``False``, use processes (recommended for CPU-bound work).
    ncores : int, optional
        Number of worker threads/processes. Defaults to ~50% of available CPU cores.
    verbose : bool, optional, default=True
        Whether to display a progress indicator.
    progress_message : str, optional
        Message shown alongside the progress indicator.
        Defaults to ``f"Processing multiple jobs via {func.__name__}, please wait!"``.
    void : bool, optional, default=False
        If ``True``, consume results internally (do not yield). Useful for
        side-effect–only functions.
    unit : str, optional, default="iteration"
        Label for the progress indicator (cosmetic only).
    display_failures: bool, optional, default=False
        if ``True``, func must return False or True. For simulations written to a database, this adquate
        .. versionadded:: 1.0.0

    Examples
    --------
    Run with processes (CPU-bound):

    >>> list(run_parallel(work, range(5), use_thread=False, ncores=4))

    Run with threads (I/O-bound):

    >>> for _ in run_parallel(download, urls, use_thread=True, verbose=True):
    ...     pass

    .. seealso::

           :func:`~apsimNGpy.parallel.process.custom_parallel_chunks`
    """
    if isinstance(iterable, str):
        raise ValueError('jobs must an iterable but not strings')
    use_thread, cpu_cores = kwargs.get('use_thread', False), kwargs.get('ncores', CORES)
    progress_message = kwargs.get('progress_message', f"Processing..!")
    void = kwargs.get('void', False)
    unit = kwargs.get('unit', 'iteration')
    display_failures = kwargs.get('display_failures')
    selection = select_type(use_thread=use_thread,
                            n_cores=cpu_cores)

    with selection as pool:
        futures = [pool.submit(func, i, *args) for i in iterable]
        total = len(futures)
        start = time.perf_counter()
        with tqdm(
                total=total,
                desc=progress_message,
                unit=unit,  # no leading space
                bar_format=("{desc} {bar} {percentage:3.0f}% "
                            "({n_fmt}/{total}) >> completed (elapsed=>{elapsed}, eta=>{remaining}) {postfix}"),
                dynamic_ncols=True,
                miniters=1, ) as pbar:
            FAILURES = 0
            for future in as_completed(futures):
                result = future.result()
                pbar.update(1)
                # completed so far: pbar.n
                elapsed = time.perf_counter() - start
                avg_rate = elapsed / pbar.n if elapsed > 0 else 0.0
                sim_rate = pbar.n / elapsed if elapsed > 0 else 0.0

                if display_failures and result is False:
                    FAILURES += 1
                    pbar.set_postfix_str(f"({avg_rate:.4f} s/{unit} or {sim_rate:,.3f} {unit}/s failed={FAILURES})")

                else:
                    pbar.set_postfix_str(f"({avg_rate:.4f} s/{unit} or {sim_rate:,.3f} {unit}/s)")

                if not void:
                    yield result
        if void:
            return None
        return None


# _______________________________________________________________


def _read_result_in_parallel(iterable_files: Iterable, ncores: int = None, use_threads: bool = False,
                             report_name: str = "Report", **kwargs):
    """
   @deprecated and will be removed in the future versions

    Read APSIMX simulation databases result from multiple files in parallel.

    Args:
    ``iterable_files`` (list): A list of APSIMX db files to be read in parallel.

    ``ncores`` (int, optional): The number of CPU cores or threads to use for parallel processing. If not provided, it defaults to 50% of available CPU cores.

    ``use_threads`` (bool, optional): If set to True, the function uses thread pool execution; otherwise, it uses process pool execution. Default is False.

    ``report_name`` the name of the report table defaults to "Report" you can use None to return all

    Returns:
    - ``generator``: A generator yielding the simulation data read from each file.

    Example:

    # Example usage of read_result_in_parallel function

    # Using processes for parallel execution
    result_generator = read_result_in_parallel(simulation_files, ncores=4, use_threads=False)

    # Iterate through the generator to process results
    for data in result_generator:
        print(data)
    it depends on the child of data but pd.concat could be a good option on the returned generator
    Kwargs
        func custom method for reading data
    ```

    Notes:
    - This function efficiently reads db file results in parallel.
    - The choice of thread or process execution can be specified with the `use_threads` parameter.
    - By default, the function uses 50% of available CPU cores or threads if `ncores` is not provided.
    - Progress information is displayed during execution.
    - Handle any exceptions that may occur during execution for robust processing.
    """

    func = kwargs.get('func', None)
    progress_msg = 'Reading data from path: '
    Ncores = ncores
    if Ncores:
        ncores_2use = Ncores
    else:
        ncores_2use = int(cpu_count() * 0.50)
    worker = func or read_db_table
    return custom_parallel(worker, iterable_files, report_name, ncores=ncores_2use, progress_message=progress_msg,
                           use_threads=use_threads)


def _process_chunk(
        chunk: Iterable[Any],
        func: Callable[..., Any],
        args: Sequence[Any],
        func_kwargs: dict
) -> List[Any]:
    """Run func over a single chunk locally inside the worker process/thread."""
    # Convert to list once in worker to avoid re-iterating generators
    local = list(chunk)
    return [func(item, *args, **func_kwargs) for item in local]


def custom_parallel_chunks(
        func: Callable[..., Any],
        jobs: Iterable[Iterable[Any]],  # generator of iterables (chunks)
        *args,
        **kwargs,
):
    """
    Run a function in parallel using threads or processes.
    The iterable is automatically divided into chunks, and each chunk is submitted to worker processes or threads.

    Parameters
    ----------
    func : callable
        The function to run in parallel.

    iterable : iterable
        An iterable of items that will be processed by ``func``.

    *args
        Additional positional arguments to pass to ``func``.

    Yields
    ------
    Any
        The results of ``func`` for each item in the iterable.
        If ``func`` returns ``None``, the results will be a sequence of ``None``.
        Note: The function returns a generator, which must be consumed to retrieve results.

    Other Parameters supplied as keyword arguments
    ----------------
    use_thread : bool, optional, default=False
        If ``True``, use threads for parallel execution;
        if ``False``, use processes (recommended for CPU-bound tasks).

    ncores : int, optional
        Number of worker processes or threads to use.
        Defaults to 50% of available CPU cores.

    verbose : bool, optional, default=True
        Whether to display a progress bar.

    progress_message : str, optional default ="Processing.. wait!"
        Message to display alongside the progress bar.

    void : bool, optional, default=False
        If ``True``, results are consumed internally (not yielded).
        Useful for functions that operate with side effects and do not return results.

    unit : str, optional, default="iteration"
        Label for the progress bar unit (cosmetic only).

    n_chunks : int, optional
        Number of chunks to divide the iterable into.
        For example, if the iterable length is 100 and ``n_chunks=10``, each chunk will have 10 items.

    chunk_size : int, optional
        Size of each chunk.
        If specified, ``n_chunks`` is determined automatically.
        For example, if the iterable length is 100 and ``chunk_size=10``, then ``n_chunks=10``.
    resume : bool, optional, default=False
        tracks the progress of completed chunks and resumes from the last completed chunk in case the session is interrupted. make sure the previous chunks are not changed
    db_session : DatabaseSession, optional, default=None
      if None, and resume __data_db__{number of chunks}.db is used and stored in the cwd
    clean_db_track:
        refresh_tracker : bool, optional, default=False
        if True, the database table containing the completed chunk ID is dropped or cleared.
        This is important if jobs from the Previous session have changed.
    Examples
    --------
    Run with processes (CPU-bound):

    .. code-block:: python

         def worker():
            # some code here
        if __name__ == __main__:
            list(run_parallel(work, range(5), use_thread=False, ncores=4))

    Run with threads (I/O-bound):

    .. code-block:: python

         for _ in run_parallel(download, urls, use_thread=True, verbose=True):
            pass

   .. note::

      resume acts for the previous and future session in case a process is interrupted.

    .. seealso::

           :func:`~apsimNGpy.parallel.process.custom_parallel`


    """
    if isinstance(jobs, str):
        raise ValueError('jobs must an iterable but not strings')

    use_thread: bool = kwargs.pop("use_thread", False)
    ncores_kw: Optional[int] = kwargs.pop("ncores", None)
    verbose: bool = kwargs.pop("verbose", True)
    progress_message: str = kwargs.pop("progress_message", "Processing please wait!")
    unit: str = kwargs.pop("unit", "chunk")
    void: bool = kwargs.pop("void", False)

    ncores = max(1, ncores_kw or CORES)

    Executor = ThreadPoolExecutor if use_thread else ProcessPoolExecutor

    desc = (progress_message or "Processing.. wait!") + ": "
    start = time.perf_counter()
    total_chunks = kwargs.get('n_chunks', 10)
    chunked = chunker(jobs, n_chunks=total_chunks)
    resume = kwargs.pop('resume', False)
    db_session = kwargs.get('db_session', False)

    from pathlib import Path

    def get_key(db, value):
        try:
            from sqlalchemy import create_engine, text, inspect

            engine = create_engine(f"sqlite:///{db}") if isinstance(db, (Path, str)) else db

            with engine.connect() as conn:
                if "completed" not in inspect(conn).get_table_names():
                    return None

                row = conn.execute(
                    text('SELECT 1 FROM completed WHERE "ID" = :v LIMIT 1'),
                    {"v": value},
                ).fetchone()

                return value if row else None
        except Exception:
            return None

    def write_key(key, db):
        from apsimNGpy.core_utils.database_utils import write_df_to_sql
        out = pd.DataFrame([{f"ID": int(key)}])
        out['ID'] = out['ID'].astype(int)
        write_df_to_sql(out, db_or_con=db, table_name="completed", if_exists='append', chunk_size=None, index=False)
        return db

    from apsimNGpy.core_utils.database_utils import drop_table

    def clear_db(db):
        print("Clearing")
        drop_table(db=db, table_name="completed")

    with Executor(max_workers=ncores) as pool:
        submitted = 0
        completed = 0

        bar = tqdm(
            total=total_chunks, desc=desc, unit=unit,
            dynamic_ncols=True, miniters=1,
            bar_format=("{desc} {bar} {percentage:3.0f}% "
                        "({n_fmt}/{total} chunks) > completed (elapsed=>{elapsed}, eta=>{remaining}) {postfix}")
        ) if verbose else None
        try:
            data_db = db_session or Path(f'__data__{total_chunks}.db')
            data_db = Path(data_db).with_suffix('.db').resolve()
            for idx, chunk in enumerate(chunked):

                key = get_key(value=idx, db=data_db)
                if key and resume:
                    if bar is not None:
                        bar.update(1)
                    continue
                if bar is not None:
                    bar.update(1)
                futures = [pool.submit(func, i, *args) for i in chunk]
                submitted += 1

                # Collect at least one finished chunk
                for fut in as_completed(futures, timeout=None):

                    result = fut.result()  # propagate exceptions
                    completed += 1
                    elapsed = time.perf_counter() - start
                    if completed and elapsed > 0:
                        avg = elapsed / completed
                        rate = completed / elapsed
                        bar.set_postfix_str(f"({avg:.3f} s/{unit} or {rate:,.3f} {unit}/s)")

                    if not void:
                        # yield results for THIS iterable (kept separate)
                        yield result
                    break  # return to top-up loop
                write_key(idx, data_db)
                if idx + 1 == total_chunks:
                    # tracking completed
                    clear_db(db=data_db)

        finally:
            if bar is not None:
                bar.close()

        if void:
            return None
        return None


def worker(x):
    time.sleep(0.1)


if __name__ == '__main__':
    def work(x, scale=2):
        return x * scale


    def mock_failure(x):
        return False


    def mock_success(x):
        return True


    def mock_none(x):
        return None


    # quick example

    success = list(
        custom_parallel(mock_success, range(100), use_thread=True, ncores=10, void=True, display_failures=True))
    fail = list(
        custom_parallel(mock_failure, range(1000), use_thread=True, ncores=10, void=False, display_failures=True, ))
    fai = list(
        custom_parallel(mock_none, range(1000), use_thread=True, ncores=10, void=True, display_failures=True))

    for i in custom_parallel_chunks(worker, range(10000), use_thread=False, n_chunks=102, void=False, resume=True):
        pass
