import shutil

import pythonnet
import shutil
import os
from pathlib import Path
from functools import cache


def _is_runtime(self):
    rt = pythonnet.get_runtime_info()
    return rt is not None


import shutil


@cache
def is_executable_on_path(name):
    """
    Check whether `name` is on PATH and marked as executable.

    Args:
        name (str): The name of the executable to check.

    Returns:
        bool: True if `name` is on PATH and executable, False otherwise.
    """
    executable_path = shutil.which(name)
    return executable_path is not None


pm = is_executable_on_path("Models")


@cache
def _is_apsimx_installed():
    try:
        return os.environ['APSIM'] is not None
    except KeyError:
        return None


@cache
def get_apsimx_model_path():
    try:
        pat = os.environ['APSIM']
        if pat:
            return Path(os.path.realpath(pat))
    except KeyError:
        return False


def get_pasimx_path_from_shutil():
    if is_executable_on_path("Models"):
        return os.path.dirname(shutil.which('Models'))


class OsMethod:
    def __init__(self):
        pass

    @cache
    def _find_apsim_path(self):
        path = get_apsimx_model_path()
        return path


class ShutilMethod:
    def __init__(self):
        pass

    @cache
    def _find_apsim_path(self):
        path = shutil.which("Models")
        if path:
            return os.path.dirname(path)
        else:
            return False


class NotFound:
    def __init__(self):
        pass

    @cache
    def _find_apsim_path(self):
        print("APSIM not found in the system environment variable, please add apsim path")
        pat = input(f"Browse your computer and add the path for APSIM installation: ")
        print(pat)
        if os.path.exists(pat) and 'bin' in pat:
            print('Congratulations you have successfully added APSIM binary folder path to your environ')
            return pat
        else:
            raise ValueError(f"entered path: '{pat}' not found")


m1 = ShutilMethod()
m2 = OsMethod()
m3 = NotFound()
_find = [m1, m2, m3]


def get_apsim_path():
    for cla in _find:
        path = cla._find_apsim_path()
        if path:
            return path


