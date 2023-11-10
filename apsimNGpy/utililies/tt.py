from apsimNGpy.utililies.utils import collect_runfiles
from apsimNGpy.parallel.process import run_apsimxfiles_in_parallel
from settings import DEFAULT_PATH

path = collect_runfiles(DEFAULT_PATH, ["*Maize.apsimx", '*bean.apsimx'])


if __name__ == "__main__":
    run_apsimxfiles_in_parallel(path, ncores=5)