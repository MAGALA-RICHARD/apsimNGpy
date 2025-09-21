from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from multiprocessing import cpu_count
from typing import Iterable
from apsimNGpy.core_utils.database_utils import read_db_table
from apsimNGpy.core_utils.run_utils import run_model
from apsimNGpy.settings import NUM_CORES
from tqdm import tqdm

CPU = int(int(cpu_count()) * 0.5)
CORES = NUM_CORES
import time


def select_type(use_thread: bool, n_cores: int):
    return ThreadPoolExecutor(n_cores) if use_thread else ProcessPoolExecutor(n_cores)


def custom_parallel(func, iterable: Iterable, *args, **kwargs):
    """
    Run a function in parallel using threads or processes.

    *Args:
        ``func`` (callable): The function to ``run`` in parallel.

        ``iterable`` (iterable): An iterable of items that will be ran_ok by the function.

        ``*args``: Additional arguments to pass to the ``func`` function.

    Yields:
        Any: The results of the ``func`` function for each item in the iterable.

   **kwargs
     ``use_thread`` (bool, optional): If True, use threads for parallel execution; if False, use processes. Default is False.

     ``ncores`` (int, optional): The number of threads or processes to use for parallel execution. Default is 50% of cpu
         cores on the machine.

     ``verbose`` (bool): if progress should be printed on the screen, default is True.
         progress_message (str) sentence to display progress such processing weather please wait. defaults to f"Processing multiple jobs via 'func.__name__' please wait!".

     ``void`` (bool, optional): if True, it implies that the we start consuming data internally right away, recomended for methods that operates on objects without returning data,
         such that you dont need to unzip or iterate on such returned data objects.

    ``unit`` to display during progress, it is only cosmetic, for showing the iteration rate, defaults to iteration

    """

    use_thread, cpu_cores = kwargs.get('use_thread', False), kwargs.get('ncores', CORES)
    progress_message = kwargs.get('progress_message', f"Processing please wait!")
    progress_message += ": "
    void = kwargs.get('void', False)
    unit = kwargs.get('unit', 'iteration')
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
            for future in as_completed(futures):
                result = future.result()
                pbar.update(1)  # completed so far: pbar.n
                elapsed = time.perf_counter() - start
                avg_rate = elapsed / pbar.n if elapsed > 0 else 0.0
                sim_rate = pbar.n / elapsed if elapsed > 0 else 0.0
                pbar.set_postfix_str(f"({avg_rate:.4f} s/{unit} or {sim_rate:,.3f} {unit}/s)")

                if not void:
                    yield result
        if void:
            return None
        return None


# _______________________________________________________________
def run_apsimx_files_in_parallel(iterable_files: Iterable, **kwargs):
    """
    Run APSIMX simulation from multiple files in parallel.

    Args:
    ``iterable_files`` (list): A list of APSIMX  files to be run in parallel.

    ``ncores`` (int, optional): The number of CPU cores or threads to use for parallel processing. If not provided, it defaults to 50% of available CPU cores.

    ``use_threads`` (bool, optional): If set to True, the function uses thread pool execution; otherwise, it uses process pool execution. Default is False.

    Returns:
    ``returns`` a generator object containing the path to the datastore or sql databases

    Example:

    # Example usage of read_result_in_parallel function

    >>> from apsimNGpy.parallel.process import run_apsimx_files_in_parallel
    >>> simulation_files = ["file1.apsimx", "file2.apsimx", ...]  # Replace with actual database file names

    # Using processes for parallel execution

    >>> result_generator = run_apsimxfiles_in_parallel(simulation_files, ncores=4, use_threads=False)
    ```

    Notes:
    - This function efficiently reads db file results in parallel.
    - The choice of thread or process execution can be specified with the `use_threads` parameter.
    - By default, the function uses 50% of available CPU cores or threads if `ncores` is not provided.
    - Progress information is displayed during execution.
    - Handle any exceptions that may occur during execution for robust processing.
    """
    # remove duplicates. because duplicates will be susceptible to race conditioning in parallel computing
    Ncores = kwargs.get('ncores')
    if Ncores:
        ncores_2use = Ncores
    else:
        ncores_2use = int(cpu_count() * 0.50)

    return custom_parallel(run_model, iterable_files, ncores=ncores_2use, use_threads=kwargs.get('use_threads'))


def _read_result_in_parallel(iterable_files: Iterable, ncores: int = None, use_threads: bool = False,
                             report_name: str = "Report", **kwargs):
    """

    Read APSIMX simulation databases results from multiple files in parallel.

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


def worker(x):
    time.sleep(0.1)


if __name__ == '__main__':
    # quick example

    lm = custom_parallel(worker, range(100), use_thread=True, ncores=10, void=True)

    ap = [i for i in lm]

    for i in lm:
        pass
