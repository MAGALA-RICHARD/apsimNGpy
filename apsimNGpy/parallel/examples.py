import os

import pandas as pd

from apsimNGpy.parallel.process import run_apsimxfiles_in_parallel, read_result_in_parallel
from apsimNGpy.utililies.utils import collect_runfiles
from pathlib import Path
hd = Path.home()
os.chdir(hd)
from apsimNGpy.base.base_data import DetectApsimExamples, apsim_example
#We can all .apsim files in this directory
files = collect_runfiles(path2files=hd, pattern=["*.apsimx"])
if __name__ == "__main__":

    run_apsimxfiles_in_parallel(files, ncores=10,use_threads=False)
    # files is an iterable or a generator
    # ncores is the numbe rof process or threads to use and use_threads will determine wthere we use threads or not
    # returns nothing
    # we can now read the results using the .db path as follow
    files_db = collect_runfiles(path2files=hd, pattern=["*.db"])
    dat = read_result_in_parallel(files_db, ncores=10)
    # return a generator object
    df = pd.concat(dat)
    print(df)
    [apsim_example.get_example(i) for i in dir(apsim_example) if "__" not in i]