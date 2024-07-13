import json
import os
import shutil
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pythonnet
from apsimNGpy.config import (Config)
from apsimNGpy.utililies.utils import (timer, find_models)

HOME_DATA = Path.home().joinpath('AppData', 'Local', 'Programs')
cdrive = os.environ.get('PROGRAMFILES')
WINDOWS_PROGRAMFILES = Path(cdrive) if cdrive else None


class GetAPSIMPath:
    """searches for an apsimx path"""

    def __init__(self, user_path=None):
        self.user_apsim_model = user_path

    @cache
    def _shut(self):
        path = shutil.which("Models")
        return os.path.dirname(path) if path else None

    @cache
    def _search_from_C(self):
        return find_models(WINDOWS_PROGRAMFILES, "Models.exe") if WINDOWS_PROGRAMFILES else None

    @cache
    def __call__(self):
        """
        Find the APSIM installation path using the os  module.
        if APSIM was installed it is possible the path is added to the os.environ

        Returns:
        - str or False: The APSIM installation path if found, or False if not found.

        """
        fromConfig = Config.get_aPSim_bin_path()
        if os.path.exists(fromConfig):
            _config_path = fromConfig
        else:
            _config_path = None
        return _config_path or os.environ.get("APSIM") or os.environ.get(
            "Models") or self._shut() or find_models(HOME_DATA,
                                                     "Models.exe") \
            or self._search_from_C()


aPSim_PATH = GetAPSIMPath()()

aPSim_config = {}


def _dumper(obj):
    try:
        return obj.toJSON()
    except:
        return obj.__dict__


path = '../base/apsimNGpy.json'


# this creates a json file with the path
def write_pathto_file(path):
    path = '../base/apsimNGpy.json'
    apsim_json = os.path.realpath(path)
    obj = json.dumps(aPSim_config, default=_dumper, indent=2)
    with open(apsim_json, 'w+') as f:
        f.writelines(obj)
    return apsim_json


@timer
@cache
def load_path_from_file(json_file_path):
    try:
        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)
        # Now 'data' contains the JSON data as a Python dictionary or list
        print(data)
    except FileNotFoundError:
        print(f"File '{json_file_path}' not found.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


@dataclass
class LoadPythonnet:
    """
    A class for loading Python for .NET (pythonnet) and APSIM models.

    This class provides a callable method for initializing the Python for .NET (pythonnet) runtime and loading APSIM models.

    Attributes:
    ----------
    None
    """

    def __init__(self):

        self._aPSim_Path = GetAPSIMPath()()

    # TODO to be completed
    @property
    def load_path(self):
        """Property getter for APSIM binary path."""
        if not self._aPSim_Path:
            raise KeyError("APSIM is not loaded in the system environmental variable")

        if 'bin' not in self._aPSim_Path:
            aPSim_path = os.path.join(self._aPSim_Path, 'bin')
            self._aPSim_Path = aPSim_path

        if not os.path.exists(aPSim_path):
            raise ValueError("A full path to the binary folder is required or the path is invalid")

        return aPSim_path

    @load_path.setter
    def load_path(self, path):
        """Property setter for APSIM binary path."""
        if not path:
            raise ValueError("The path cannot be empty")

        self._aPSim_Path = path

    def start_pythonnet(self):
        try:
            if pythonnet.get_runtime_info() is None:
                return pythonnet.load("coreclr")
        except:
            print("dotnet not found, trying alternate runtime")
            return pythonnet.load()

    def __call__(self):
        """
        Initialize the Python for .NET (pythonnet) runtime and load APSIM models.

        This method attempts to load the 'coreclr' runtime, and if not found, falls back to an alternate runtime.
        It also sets the APSIM binary path, adds necessary references, and returns a reference to the loaded APSIM models.

        Returns:
        -------
        lm: Reference to the loaded APSIM models

        Raises:
        ------
        KeyError: If APSIM path is not found in the system environmental variable.
        ValueError: If the provided APSIM path is invalid.

        Notes:
        It raises a KeyError if APSIM path is not found. Please edit the system environmental variable on your computer.
        """
        # try:
        #     if pythonnet.get_runtime_info() is None:
        #         pythonnet.load("coreclr")
        # except:
        #     print("dotnet not found, trying alternate runtime")
        #     pythonnet.load()
        self.start_pythonnet()
        # use get because it does not raise key error. it returns none if not found
        apsim_path = aPSim_PATH
        if not apsim_path:
            raise KeyError("APSIM is not loaded in the system environmental variable")

        if 'bin' not in apsim_path:
            apsim_path = os.path.join(apsim_path, 'bin')

        if not os.path.exists(apsim_path):
            raise ValueError("A full path to the binary folder is required or the path is invalid")
        import sys
        sys.path.append(apsim_path)
        import clr
        sys = clr.AddReference("System")
        lm = clr.AddReference("Models")

        # return lm, sys, pythonnet.get_runtime_info()


def add_path(new_path):
    import sys
    if not new_path in sys.path:
        sys.path += [new_path]
        print(f"{new_path} successfully added to the system")
    else:
        print("path is already added to the system")


loader = LoadPythonnet()()

from apsimNGpy.utililies.utils import timer


@timer
def fibonacci_sequence(limit):
    a, b = 0, 1
    count = 0
    while count < limit:
        yield a
        a, b = b, a + b
        count += 1


# Example usage:
if __name__ == '__main__':
    loader = LoadPythonnet()
    loaded_models = loader()
    # try importing the C# models and see if the process is successful

    fib = fibonacci_sequence(20)
    lp = []
    for i in fib:
        lp.append(i)
    print(lp)
    import numpy as np

    RP = np.arange(0.5, 3, 0.5)
