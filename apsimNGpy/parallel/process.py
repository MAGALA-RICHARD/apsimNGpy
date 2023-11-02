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
def run_apsimxfiles_in_parallel(iterable_files, ncores = None, use_threads=False):
    """
    files: lists of apsimx simulation files
    ncores  =no of cores or threads to use (integer)
    use_thread: if true thread pool executor will be used if false processpool excutor will be called (boolean)
    """
    # remove duplicates. because duplicates will be susceptible to race conditioning in paralell computing
    files = set(iterable_files)
    if ncores:
        ncore2use = ncores
    else:
        ncore2use = int(cpu_count()*0.50)
    if not use_threads:
        a = perf_counter()
        with ProcessPoolExecutor(ncore2use) as pool:
            futures = [pool.submit(run_model, i) for i in files]
            progress = tqdm(total=len(futures), position=0, leave=True,
                            bar_format='Running apsimx files: {percentage:3.0f}% completed')
            for future in as_completed(futures):
                future.result()  # retrieve the result (or use it if needed)
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
                future.result()  # retrieve the result (or use it if needed)
                progress.update(1)
            progress.close()
        print(perf_counter() - a, 'seconds', f'to run {len(files)} files')


def read_result_in_parallel(iterable_files, ncores = None, use_threads=False):
    """
    files: lists of apsimx simulation files
    ncores  =no of cores or threads to use (integer)
    use_thread: if true thread pool executor will be used if false processpool excutor will be called (boolean)
    """
    # remove duplicates. because duplicates will be susceptible to race conditioning in paralell computing
    files = set(iterable_files)
    if ncores:
        ncore2use = ncores
    else:
        ncore2use = int(cpu_count()*0.50)
    if not use_threads:
        a = perf_counter()
        with ProcessPoolExecutor(ncore2use) as pool:
            futures = [pool.submit(read_simulation, i) for i in files]
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
            futures = [tpool.submit(read_simulation, i) for i in files]
            progress = tqdm(total=len(futures), position=0, leave=True,
                            bar_format='reading file databases: {percentage:3.0f}% completed')
            # Iterate over the futures as they complete
            for future in as_completed(futures):
                data = future.result()  # retrieve and store it in a generator
                progress.update(1)
                yield data
            progress.close()
        print(perf_counter() - a, 'seconds', f'to read {len(files)} apsimx database files')


def download_soil_tables(iterable, use_threads=False, ncores =None, soil_series=None):
    """
    iterable: an iterable with lonlat coordnates as tuples or lists
    return: calculated soil profiles with the corresponding index positions as a dictionary
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
        ncores_2use = int(cpu_count()*0.4)
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
