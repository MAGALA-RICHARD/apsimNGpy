from concurrent.futures import ProcessPoolExecutor, as_completed,  ThreadPoolExecutor
import glob, os, sys
from time import perf_counter
from apsimNGpy.utililies.run_utils import run_model
from apsimNGpy.utililies import readmodel
#collect_runfiles
#_______________________________________________________________

path2 = r'D:\wd\nf\EXPERIMENT\T\CW\Weather_APSIM_Files'
path  = collect_runfiles(path2, pattern = "*_2py.apsimx")

print(path)
sys.exit(1)
if __name__ == '__main__':
        
        a= perf_counter()
        with ProcessPoolExecutor(18) as pool:
               ap= pool.map(run_model, path)
        print(perf_counter()-a, 'seconds',  f'to run {len(path)}')

u