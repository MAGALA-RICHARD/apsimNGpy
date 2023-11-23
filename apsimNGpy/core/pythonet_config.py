import pythonnet
import os
from pathlib import Path
from functools import cache
import shutil
import json
from os.path import realpath
from dataclasses import dataclass
import pythonnet

from apsimNGpy.utililies.utils import timer


def _is_runtime(self):
    rt = pythonnet.get_runtime_info()
    return rt is not None


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


@cache
def _is_apsimx_installed():
    try:
        return os.environ['APSIM'] is not None
    except KeyError:
        return None


@cache
def get_apsimx_model_path():
    """
    Quickly gets the APSIM installation path
    """
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
        """
        Find the APSIM installation path using the os  module.
        if APSIM was installed it is possible the path is added to the os.environ

        Returns:
        - str or False: The APSIM installation path if found, or False if not found.

        """
        path = get_apsimx_model_path()
        return path


class ShutilMethod:
    def __init__(self):
        pass

    @cache
    def _find_apsim_path(self):
        """
        Find the APSIM installation path using the shutil module.

        Returns:
        - path: str or False: The APSIM installation path if found, or False if not found.

        Example:
        ```python
        apsim_finder = ShutilMethod()
        apsim_path = apsim_finder._find_apsim_path()

        if apsim_path:
            print(f"Found APSIM installation at: {apsim_path}")
        else:
            print("APSIM installation not found.")

                """
        path = shutil.which("Models")
        if path:
            return os.path.dirname(path)
        else:
            return False


class NotFound:
    """
        Prompt the user to input the APSIM installation path.

        If the provided path is valid and contains the 'bin' folder, it is considered a successful addition
        to the environment. Otherwise, a ValueError is raised.

        Returns:
        - str: The APSIM installation path.

        Example:
        ```python
        not_found = NotFound()
        apsim_path = not_found._find_apsim_path()
        # User interaction:
        # APSIM not found in the system environment variable, please add apsim path
        # Browse your computer and add the path for APSIM installation: <user_input>
        # <printed path>
        # Congratulations you have successfully added APSIM binary folder path to your environ
        ```

        Raises:
        - ValueError: If the entered path is invalid or doesn't contain the 'bin' folder.
        """

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


@cache
def _find_apsim_path():
    """
    # returns a list of classes above, one uses shutil, and one os.environ and notfound allows the user to enter the
    # path directly
    """
    return [ShutilMethod(), OsMethod(), NotFound()]


def get_apsim_path():
    for cla in _find_apsim_path():
        path = cla._find_apsim_path()  # the method _find_apsim_path is polymorphic that mean it allows us to run it on every class once
        if path:
            return path


apsim_config = {}


def _dumper(obj):
    try:
        return obj.toJSON()
    except:
        return obj.__dict__


apsim_config['APSIM'] = realpath(get_apsim_path())

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
        # use get becuase it does not raise key error. it returns none if not found
        apsim_path = os.environ.get("APSIM")
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
# Example usage:
if __name__ == '__main__':
    loader = LoadPythonnet()

    loaded_models = loader()
    import Models
    import System

    ap = get_apsim_path()

