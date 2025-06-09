import os

import pandas as pd

from apsimNGpy.parallel.process import run_apsimx_files_in_parallel, _read_result_in_parallel
from apsimNGpy.core_utils.utils import collect_runfiles
from pathlib import Path

hd = Path.home()/'scart'
hd.mkdir(parents=True, exist_ok=True)
os.chdir(hd)
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.core_utils.utils import make_apsimx_clones

# let's duplicate some files

# let's copy two files here
maize= load_default_simulations(crop='maize', simulations_object= False)

ap = make_apsimx_clones(maize, 20)


def fnn(x):

    return x


# that is it all these files are now in the dir_path
files = collect_runfiles(path2files=hd, pattern=["*.apsimx"])  # change path as needed

if __name__ == "__main__":
    # copy all examples to our workig dir_path
    # ex = apsim_example.get_all_examples()
    xp =[i for i in run_apsimx_files_in_parallel(ap, ncores=10, use_threads=False)]
    # files is an iterable or a generator
    # ncores is the number of process or threads to use and use_threads will determine wthere we use threads or not
    # returns nothing
    rpath = os.path.realpath(hd.joinpath('apsimx_cloned'))
    # we can now read the results using the .db path as follow
    files_db = [i for i in collect_runfiles(path2files=rpath, pattern=["*.db"])]
    dat = _read_result_in_parallel(files_db, ncores=2, use_threads=True, report_name='report')
    # return a generator object
    dl = list(dat)
    # df = pd.concat(dat)
    print(dl)
