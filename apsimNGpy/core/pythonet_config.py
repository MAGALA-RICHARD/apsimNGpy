import pythonnet
import os
from os.path import dirname
from pathlib import Path
from functools import cache
import shutil
import json
from os.path import realpath
from dataclasses import dataclass
import pythonnet

from apsimNGpy.utililies.utils import timer, find_models

HOME_DATA = Path.home().joinpath('AppData', 'Local', 'Programs')
WINDOWS_PROGRAMFILES = Path(os.environ.get('PROGRAMFILES'))


class Internal_Method:
    """searches for apsimx path"""

    def __init__(self):
        pass

    @cache
    def _shut(self):
        path = shutil.which("Models")
        if path:
            return os.path.dirname(path)
        else:
            return None
    @cache
    def _search_from_C(self):
        return find_models(WINDOWS_PROGRAMFILES, "Models.exe") if WINDOWS_PROGRAMFILES else None

    def _notfound(self):
        print("APSIM not found in the system environment variable, please add apsim path")
        pat = input(f"Browse your computer and add the path for APSIM installation: ")
        print(pat)
        if os.path.exists(pat) and 'bin' in pat:
            print('Congratulations you have successfully added APSIM binary folder path to your environ')
            return pat
        else:
            raise ValueError(f"entered path: '{pat}' not found")

    @cache
    def __call__(self):
        """
        Find the APSIM installation path using the os  module.
        if APSIM was installed it is possible the path is added to the os.environ

        Returns:
        - str or False: The APSIM installation path if found, or False if not found.

        """
        return os.environ.get("APSIM") or os.environ.get("Models") or self._shut() or find_models(HOME_DATA,
                                                                                                 "Models.exe") \
            or self._notfound() or self._search_from_C()


APSIM_PATH = Internal_Method()()

apsim_config = {}


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
    obj = json.dumps(apsim_config, default=_dumper, indent=2)
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
        apsim_path = APSIM_PATH
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
import Models

# Example usage:
if __name__ == '__main__':
    loader = LoadPythonnet()
    print(APSIM_PATH)
    loaded_models = loader()
    import Models
    import System
