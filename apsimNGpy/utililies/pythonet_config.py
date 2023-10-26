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

def get_apsimx_model_path():
    if _is_apsimx_installed():
        return Path(os.path.realpath(os.environ['APSIM']))
class Method1:
  def __init__(self):
      pass
  def find_apsim_path(self):
      self.path = get_apsimx_model_path()
      return self.path
class Method2:
  def __init__(self):
      pass
  def find_apsim_path(self):
      path = shutil.which("Models")
      if path is not None:
          return os.path.dirname(path)
