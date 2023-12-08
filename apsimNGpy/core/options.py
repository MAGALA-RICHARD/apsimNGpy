import os.path as osp
import os
import time
from pathlib import Path
import shutil
from concurrent.futures import ProcessPoolExecutor,as_completed
from tqdm import tqdm


def check_version(apsim_version):
    path = True if osp.exists(apsim_version) and apsim_version.endswith("bin") and 'APSIM'  in apsim_version else None
    print(path)
    if not path:
        raise ValueError("This is not an apsimx model path")

sh = shutil.which('Models')
check_version(r"C:\Program Files\APSIM2023.11.7349.0\bin")
from apsimNGpy.utililies.utils import find_models, timer

from apsimNGpy.core import core
from apsimNGpy.core.base_data import LoadExampleFiles
if __name__ == '__main__':
   lm = LoadExampleFiles()
   pass
    #dy = search_apsimx()

    # print(pm)
