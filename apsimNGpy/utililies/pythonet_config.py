import pythonnet
from shutil import which
import os
from pathlib import Path

def _is_runtime(self):
    rt = pythonnet.get_runtime_info()
    return rt is not None


def _is_excutable_on_path(name):
    """Check whether `name` is on PATH and marked as executable."""
    # from which import which
    return which(name) is not None


def _is_apsimx_installed():
    return os.environ['APSIM'] is not None


def get_apsimx_model_path():
    if _is_apsimx_installed():
        path = Path(os.path.realpath(os.environ['APSIM']))
        return path.joinpath("Models.exe")
