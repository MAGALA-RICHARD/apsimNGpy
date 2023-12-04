import os

import pandas as pd

from apsimNGpy.parallel.process import run_apsimxfiles_in_parallel, read_result_in_parallel
from apsimNGpy.utililies.utils import collect_runfiles
from pathlib import Path

hd = Path.home()
os.chdir(hd)
from apsimNGpy.core.base_data import LoadExampleFiles
from apsimNGpy.utililies.utils import make_apsimx_clones
# let's duplicate some files

# let's copy two files here
data = LoadExampleFiles(hd)
maize = data.get_maize
nt_maize = data.get_maize_no_till
ap = make_apsimx_clones(maize, 20)
def fnn(x):
    return x
# that is it all these files are now in the directory
files = collect_runfiles(path2files=hd, pattern=["*.apsimx"])# change path as needed

if __name__ == "__main__":
    # copy all examples to our workig directory
    # ex = apsim_example.get_all_examples()
    run_apsimxfiles_in_parallel(ap, ncores=10, use_threads=False)
    # files is an iterable or a generator
    # ncores is the numbe rof process or threads to use and use_threads will determine wthere we use threads or not
    # returns nothing
    rpath = os.path.realpath(hd)
    # we can now read the results using the .db path as follow
    files_db = collect_runfiles(path2files=rpath, pattern=["*.db"])
    dat = read_result_in_parallel(files_db, ncores=2, use_threads=True,report_name='MaizeR')
    # return a generator object
    dl = list(dat)
    #df = pd.concat(dat)
    print(dl)
