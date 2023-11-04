import pythonnet
import os
from pathlib import Path
from functools import cache
import shutil

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


