from __future__ import annotations

import math, os, time
from typing import Any, Callable, Iterable, List, Sequence, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from apsimNGpy.parallel.data_manager import chunker

from tqdm import tqdm

CORES = max(1, os.cpu_count())


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
    Run `func` over a generator of iterables (chunks), submitting ONE job per chunk.
    Yields a list of results per chunk (keeps iterables separate to reduce overhead).

    Control kwargs (popped; remaining kwargs go to `func`):
        use_thread: bool = False
        ncores: int = ceil(0.5 * CPU)
        verbose: bool = True
        progress_message: str = "Processing please wait!"
        unit: str = "chunk"
        void: bool = False        # if True, consume results internally (no yields)
        total_chunks: Optional[int] = None  # for tqdm if known
        max_outstanding: Optional[int] = None  # limit in-flight chunk jobs (default ncores*2)
    """
    use_thread: bool = kwargs.pop("use_thread", False)
    ncores_kw: Optional[int] = kwargs.pop("ncores", None)
    verbose: bool = kwargs.pop("verbose", True)
    progress_message: str = kwargs.pop("progress_message", "Processing please wait!")
    unit: str = kwargs.pop("unit", "chunk")
    void: bool = kwargs.pop("void", False)

    ncores = max(1, ncores_kw or CORES)

    Executor = ThreadPoolExecutor if use_thread else ProcessPoolExecutor

    desc = (progress_message or "Processing please wait!") + ": "
    start = time.perf_counter()
    total_chunks = kwargs.get('n_chunks', 10)
    chunked = chunker(jobs, n_chunks=total_chunks)
    with Executor(max_workers=ncores) as pool:
        submitted = 0
        completed = 0

        bar = tqdm(
            total=total_chunks, desc=desc, unit=unit,
            dynamic_ncols=True, miniters=1,
            bar_format=("{desc} {bar} {percentage:3.0f}% "
                        "({n_fmt}/{total}) >> completed (elapsed=>{elapsed}, eta=>{remaining}) {postfix}")
        ) if verbose else None

        try:

            for chunk in chunked:
                futures = [pool.submit(func, i, *args) for i in chunk]
                submitted += 1

                # Collect at least one finished chunk
                for fut in as_completed(futures, timeout=None):

                    result = fut.result()  # propagate exceptions
                    completed += 1

                    if bar is not None:
                        bar.update(1)
                        elapsed = time.perf_counter() - start
                        if completed and elapsed > 0:
                            avg = elapsed / completed
                            rate = completed / elapsed
                            bar.set_postfix_str(f"({avg:.3f} s/{unit} or {rate:,.3f} {unit}/s)")

                    if not void:
                        # yield results for THIS iterable (kept separate)
                        yield result
                    break  # return to top-up loop


        finally:
            if bar is not None:
                bar.close()

        if void:
            return None
        return None


def work(x, scale=2):
    return x * scale


if __name__ == "__main__":
    for chunk_results in custom_parallel_chunks(
            work,
            (i for i in range(100000)),
            scale=3,  # passed to work()
            use_thread=False,  # processes for CPU-bound
            ncores=8,
            unit="chunk",
            n_chunks=20,

    ):
        # each yield is a list of results for ONE input iterable
        pass
