import pythonnet
import sys
import platform
import os
import shutil
from pathlib import Path

def _is_runtime(self):
    rt = pythonnet.get_runtime_info()
    return rt is not None


def _is_excutable_on_path(name):
    """Check whether `name` is on PATH and marked as executable."""
    # from whichcraft import which
    from shutil import which
    return which(name) is not None


def _is_apsimx_installed():
    return os.environ['APSIM'] is not None


def get_apsimx_model_path():
    if _is_apsimx_installed():
        return Path(os.path.realpath(os.environ['APSIM']))
def detect_apsim_installation():
    for rr, dd, ff in os.walk(r"C:\Program Files\APSIM2022.12.7130.0\bin"):
        for d in ff:
            if d.startswith('Model') and d.endswith(".exe"):
                f = os.path.join(rr, d)
                if f is not None:
                    return f