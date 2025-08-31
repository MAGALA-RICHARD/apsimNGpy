import os
import shutil

from apsimNGpy.parallel.process import custom_parallel
from pathlib import Path
from apsimNGpy.core.apsim import ApsimModel
hd = Path.home()/'scart'
hd.mkdir(parents=True, exist_ok=True)
os.chdir(hd)
# create a worker
def worker(i):
    model = ApsimModel(i, out_path = i)
    model.run()
    model.clean_up(db=True)

if __name__ == '__main__':
   # mock some jobs
    some_jobs  = (ApsimModel('Maize').path for _ in range(10))
   # use custom parallel to run jobs
    jobs= custom_parallel(worker, some_jobs, ncores=3, use_thread=False)
    # finalize jobs
    try:
        for _ in jobs:
            pass
    finally:
        try:
           shutil.rmtree(hd)
        except PermissionError as e:
            pass
