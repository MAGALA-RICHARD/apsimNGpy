from apsimNGpy.utililies.utils import collect_runfiles
from apsimNGpy.parallel.process import run_apsimxfiles_in_parallel
pp = r'C:\Users\rmagala\Box\p\my_PEWI\RESEARCH_PROJECT_20210622\chapter 2\YieldEvaluation'
path = collect_runfiles(pp, ["*Maize.apsimx", '*bean.apsimx'])



if __name__ == "__main__":
    run_apsimxfiles_in_parallel(path, ncores=5)