from concurrent.futures import ProcessPoolExecutor, as_completed,  ThreadPoolExecutor
import glob, os, sys
from time import perf_counter
from apsimNGpy.utililies.run_utils import run_model
from apsimNGpy.utililies import utils
#collect_runfiles
#_______________________________________________________________

path2 = r'D:\wd\nf\EXPERIMENT\T\CW\Weather_APSIM_Files'
path  = utils.collect_runfiles(path2, pattern = "*_2py.apsimx")
print(os.getcwd())
def  run_apsimxfiles_in_parallel(files, ncores, use_threads=False):
    """
    files: lists of apsimx simulation files
    ncores  =no of cores or threads to use (integer)
    use_thread: if true thread pool executor will be used if false processpool excutor will be called (boolean)
    """
    if not use_threads:
        a = perf_counter()
        with ProcessPoolExecutor( ncores) as pool:
               ap= pool.map(run_model, path)
        print(perf_counter() - a, 'seconds', f'to run {len(files)}')
    else:
        a = perf_counter()
        with ThreadPoolExecutor(ncores) as pool:
            ap = pool.map(run_model, path)
        print(perf_counter() - a, 'seconds', f'to run {len(files)}')

