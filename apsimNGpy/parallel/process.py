from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
import glob, os, sys
from time import perf_counter
from tqdm import tqdm
from multiprocessing import cpu_count
from os.path import dirname
from os.path import join as opj
from apsimNGpy.utililies.run_utils import run_model, read_simulation
from apsimNGpy.manager.soilmanager import DownloadsurgoSoiltables, OrganizeAPSIMsoil_profile


# _______________________________________________________________
def run_apsimxfiles_in_parallel(iterable_files, ncores=None, use_threads=False):
    """
    Run APSIMX simulation from multiple files in parallel.

    Args:
    - iterable_files (list): A list of APSIMX  files to be run in parallel.
    - ncores (int, optional): The number of CPU cores or threads to use for parallel processing. If not provided, it defaults to 50% of available CPU cores.
    - use_threads (bool, optional): If set to True, the function uses thread pool execution; otherwise, it uses process pool execution. Default is False.

    Returns:
    - returns a generator object containing the path to the datastore or sql databases

    Example:
    ```python
    # Example usage of read_result_in_parallel function

    from apsimNgpy.parallel.process import run_apsimxfiles_in_parallel
    simulation_files = ["file1.apsimx", "file2.apsimx", ...]  # Replace with actual database file names

    # Using processes for parallel execution
    result_generator = run_apsimxfiles_in_parallel(simulation_files, ncores=4, use_threads=False)
    ```

    Notes:
    - This function efficiently reads db file results in parallel.
    - The choice of thread or process execution can be specified with the `use_threads` parameter.
    - By default, the function uses 50% of available CPU cores or threads if `ncores` is not provided.
    - Progress information is displayed during execution.
    - Handle any exceptions that may occur during execution for robust processing.
    """
    # remove duplicates. because duplicates will be susceptible to race conditioning in paralell computing
    files = set(iterable_files)
    if ncores:
        ncore2use = ncores
    else:
        ncore2use = int(cpu_count() * 0.50)
    if not use_threads:
        a = perf_counter()
        with ProcessPoolExecutor(ncore2use) as pool:
            futures = [pool.submit(run_model, i) for i in files]
            progress = tqdm(total=len(futures), position=0, leave=True,
                            bar_format='Running apsimx files: {percentage:3.0f}% completed')
            for future in as_completed(futures):
                yield future.result()
                progress.update(1)
            progress.close()
        print(perf_counter() - a, 'seconds', f'to run {len(files)} files')
    else:
        a = perf_counter()
        with ThreadPoolExecutor(ncore2use) as tpool:
            futures = [tpool.submit(run_model, i) for i in files]
            progress = tqdm(total=len(futures), position=0, leave=True,
                            bar_format='Running apsimx files: {percentage:3.0f}% completed')
            # Iterate over the futures as they complete
            for future in as_completed(futures):
                yield future.result()  # use the generated object in the fucntion below
                progress.update(1)
            progress.close()
        print(perf_counter() - a, 'seconds', f'to run {len(files)} files')


def read_result_in_parallel(iterable_files, ncores=None, use_threads=False, report_name="Report"):
    """

    Read APSIMX simulation databases results from multiple files in parallel.

    Args:
    - iterable_files (list): A list of APSIMX db  files to be read in parallel.
    - ncores (int, optional): The number of CPU cores or threads to use for parallel processing. If not provided, it defaults to 50% of available CPU cores.
    - use_threads (bool, optional): If set to True, the function uses thread pool execution; otherwise, it uses process pool execution. Default is False.
    -  report_name the name of the  report table defaults to "Report" you can use None to return all

    Returns:
    - generator: A generator yielding the simulation data read from each file.

    Example:
    ```python
    # Example usage of read_result_in_parallel function
    from  apsimNgpy.parallel.process import read_result_in_parallel

    simulation_files = ["file1.db", "file2.db", ...]  # Replace with actual database file names

    # Using processes for parallel execution
    result_generator = read_result_in_parallel(simulation_files, ncores=4, use_threads=False)

    # Iterate through the generator to process results
    for data in result_generator:
        print(data)
    it depends on the type of data but pd.concat could be a good option on the returned generator
    ```

    Notes:
    - This function efficiently reads db file results in parallel.
    - The choice of thread or process execution can be specified with the `use_threads` parameter.
    - By default, the function uses 50% of available CPU cores or threads if `ncores` is not provided.
    - Progress information is displayed during execution.
    - Handle any exceptions that may occur during execution for robust processing.
    """

    # remove duplicates. because duplicates will be susceptible to race conditioning in paralell computing
    files = set(iterable_files)
    if ncores:
        ncore2use = ncores
    else:
        ncore2use = int(cpu_count() * 0.50)
    if not use_threads:
        a = perf_counter()
        with ProcessPoolExecutor(ncore2use) as pool:
            futures = [pool.submit(read_simulation, i, report_name) for i in files]
            progress = tqdm(total=len(futures), position=0, leave=True,
                            bar_format='reading file databases: {percentage:3.0f}% completed')
            # Iterate over the futures as they complete
            for future in as_completed(futures):
                data = future.result()
                # retrieve and store it in a generator
                progress.update(1)
                yield data
            progress.close()
        print(perf_counter() - a, 'seconds', f'to read {len(files)} apsimx files databases')
    else:
        a = perf_counter()
        with ThreadPoolExecutor(ncore2use) as tpool:
            futures = [tpool.submit(read_simulation, i, report_name) for i in files]
            progress = tqdm(total=len(futures), position=0, leave=True,
                            bar_format='reading file databases: {percentage:3.0f}% completed')
            # Iterate over the futures as they complete
            for future in as_completed(futures):
                data = future.result()  # retrieve and store it in a generator
                progress.update(1)
                yield data
            progress.close()
        print(perf_counter() - a, 'seconds', f'to read {len(files)} apsimx database files')


def download_soil_tables(iterable, use_threads=False, ncores=None, soil_series=None):
    """

    Downloads soil data from SSURGO (Soil Survey Geographic Database) based on lonlat coordinates.

    Args:
    - iterable (iterable): An iterable containing lonlat coordinates as tuples or lists.
    - use_threads (bool, optional): If True, use thread pool execution. If False, use process pool execution. Default is False.
    - ncores (int, optional): The number of CPU cores or threads to use for parallel processing. If not provided, it defaults to 40% of available CPU cores.
    - soil_series (None, optional): [Insert description if applicable.]

    Returns:
    - a generator: with dictionaries containing calculated soil profiles with the corresponding index positions based on lonlat coordinates.

    Example:
    ```python
    # Example usage of download_soil_tables function
    from your_module import download_soil_tables

    lonlat_coords = [(x1, y1), (x2, y2), ...]  # Replace with actual lonlat coordinates

    # Using threads for parallel processing
    soil_profiles = download_soil_tables(lonlat_coords, use_threads=True, ncores=4)

    # Iterate through the results
    for index, profile in soil_profiles.items():
        process_soil_profile(index, profile)
    ```

    Notes:
    - This function efficiently downloads soil data and returns calculated profiles.
    - The choice of thread or process execution can be specified with the `use_threads` parameter.
    - By default, the function utilizes available CPU cores or threads (40% of total) if `ncores` is not provided.
    - Progress information is displayed during execution.
    - Handle any exceptions that may occur during execution to avoid aborting the whole download

    """

    def _concat(x):
        try:
            cod = iterable[x]
            table = DownloadsurgoSoiltables(cod)
            th = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
            sp = OrganizeAPSIMsoil_profile(table, thickness=20, thickness_values=th).cal_missingFromSurgo()
            return {x: sp}
        except Exception as e:
            print("Exception Type:", type(e), "has occured")
            print(repr(e))

    if not ncores:
        ncores_2use = int(cpu_count() * 0.4)
        print(f"using: {ncores_2use} cpu cores")
    else:
        ncores_2use = ncores
    if not use_threads:
        with ThreadPoolExecutor(max_workers=ncores_2use) as tpool:
            futures = [tpool.submit(_concat, n) for n in range(len(iterable))]
            progress = tqdm(total=len(futures), position=0, leave=True,
                            bar_format='downloading soil_tables...: {percentage:3.0f}% completed')
            for future in as_completed(futures):
                progress.update(1)
                yield future.result()
            progress.close()
    else:
        with ProcessPoolExecutor(max_workers=ncores_2use) as ppool:
            futures = [ppool.submit(_concat, n) for n in range(len(iterable))]
            progress = tqdm(total=len(futures), position=0, leave=True,
                            bar_format='downloading soil_tables..: {percentage:3.0f}% completed')
            for future in as_completed(futures):
                progress.update(1)
                yield future.result()
            progress.close()


def custom_parallel(func, iterable, ncores=6, *arg):
    a = perf_counter()
    with ProcessPoolExecutor(max_workers=ncores) as ppool:
        futures = [ppool.submit(func, *arg) for i in iterable]
        progress = tqdm(total=len(futures), position=0, leave=True,
                        bar_format='Running apsimx files: {percentage:3.0f}% completed')
        # Iterate over the futures as they complete
        for future in as_completed(futures):
            yield future.result()
            progress.update(1)
        progress.close()
    print(perf_counter() - a, 'seconds', f'to run {len(files)} files')
if __name__=='__main__':
    def fn(x):
        return 1*x
    lm = custom_parallel(fn, range(10000))