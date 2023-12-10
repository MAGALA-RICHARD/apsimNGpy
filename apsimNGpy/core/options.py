import os.path as osp
import os
import time
from pathlib import Path
from dataclasses import dataclass


def _check_path(apsim_version):
    path = True if osp.exists(apsim_version) and apsim_version.endswith("bin") and 'APSIM' in apsim_version else None

# option for changing apsim model
class Options:
    def __init__(self, path):
        self.__path2_apsim = path

    @property
    def APSIMPATH(self):
        return self.__path2_apsim if _check_path(self.__path2_apsim) else None

