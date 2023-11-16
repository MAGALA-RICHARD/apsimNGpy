import pythonnet
import os
from pathlib import Path
from functools import cache
import shutil
import json
from os.path import realpath
from dataclasses import dataclass
import sys
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


m1 = ShutilMethod()
m2 = OsMethod()
m3 = NotFound()
_find = [m1, m2, m3]


def get_apsim_path():
    for cla in _find:
        path = cla._find_apsim_path()
        if path:
            return path


apsim_config = {}


def _dumper(obj):
    try:
        return obj.toJSON()
    except:
        return obj.__dict__


apsim_config['APSIM'] = realpath(get_apsim_path())

# this creates a json file with the path
apsim_json = realpath(Path.home().joinpath('apsimNGpy.json'))
obj = json.dumps(apsim_config, default=_dumper, indent=2)
with open(apsim_json, 'w+') as f:
    f.writelines(obj)
import pythonnet
@dataclass()
class LoadPythonnet:
    import pythonnet
    def start_pythonnet(self):
        try:
            if pythonnet.get_runtime_info() is None:
               return pythonnet.load("coreclr")
        except:
            print("dotnet not found ,trying alternate runtime")
            return pythonnet.load()
    def load_apsim_model(self):
        self.start_pythonnet()
        apsim_path = os.environ.get("APSIM")
        if 'bin' not in apsim_path:
            apsim_path = os.path.join(apsim_path, 'bin')
            if not os.path.exists(apsim_path):
                raise ValueError("Please a full path to the binary folder is required or path is invalid")
        print(apsim_path)
        sys.path.append(apsim_path)
        import clr
        sy = clr.AddReference("System")
        lm= clr.AddReference("Models.dll")


py = LoadPythonnet()
py.start_pythonnet()
apsim_path = os.environ.get("APSIM")
tm = os.path.join(apsim_path, 'Models.dll')

py.load_apsim_model()