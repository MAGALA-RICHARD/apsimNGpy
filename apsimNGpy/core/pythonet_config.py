import glob
import json
import os
import shutil
from dataclasses import dataclass
from functools import cache
from pathlib import Path
import platform
import pythonnet
from apsimNGpy.config import (Config)
from apsimNGpy.utililies.utils import (timer, find_models)

HOME_DATA = Path.home().joinpath('AppData', 'Local', 'Programs')
cdrive = os.environ.get('PROGRAMFILES')
WINDOWS_PROGRAM_FILES = Path(cdrive) if cdrive else None

def _apsim_model_is_installed(_path):
    """
   Checks if the APSIM model is installed by verifying the presence of binaries, especially if they haven't been deleted. Sometimes, after uninstallation, the `bin` folder remains, so tracking it
   may give a false indication that the binary path exists due to leftover files.
   :param _path: path to APSIM model binaries
    """
    model_files = False
    path_to_search = Path(_path)
    if platform.system() == 'Windows':
        model_files = list(path_to_search.glob('*Models.exe*'))
    if platform.system() == 'Darwin':
        model_files = list(path_to_search.glob('*Models.pdb*'))
    if model_files:
        return True
    else:
        return False
def search_from_programs():
    prog_path = glob.glob(f'{cdrive}/APSIM*/bin')
    for path_fpath in prog_path:
        if os.path.isdir(path_fpath) and os.path.exists(path_fpath) and _apsim_model_is_installed(path_fpath):
            return path_fpath
        else:
            return None
def search_from_users():
    home_path = os.path.realpath(Path.home())
    trial_search = glob.glob(f"{home_path}/AppData/Local/Programs/APSIM*/bin")
    _path  = None
    if trial_search:
        for paths in trial_search:
            if os.path.isdir(paths) and os.path.exists(paths):
                _path = Path(paths)
                return _path

    else:
        return None


class GetAPSIMPath:
    """searches for an apsimx path"""

    def __init__(self, user_path=None):
        self.user_apsim_model = user_path
        self.auto_bin_path  = ' '

    @cache
    def _shut(self):
        path = shutil.which("Models")
        return os.path.dirname(path) if path else None

    @cache
    def _search_from_C(self):
        if platform.system() == "Windows":
            return find_models(WINDOWS_PROGRAM_FILES, "Models.exe") if WINDOWS_PROGRAM_FILES else None
        else:
            return None

    def auto_detect(self):
            if platform.system() == 'Windows':
                return  self._shut() or find_models(HOME_DATA,
                                                     "Models.exe") \
            or self._search_from_C() or search_from_users()
            if platform.system() == 'Darwin':
                # we search in applications and give up
                pattern = '/Applications/APSIM*.app/Contents/Resources/bin'

                # Use glob to find matching paths
                matching_paths = glob.glob(pattern)
                for matching_path in matching_paths:
                    if os.path.isdir(matching_path) and _apsim_model_is_installed(matching_path):
                        return matching_path
                    else:
                        return None
            else:
                #TODO to impliment for linnux
                return None

    @cache
    def __call__(self):
        """
        Find the aPSim installation path using the os module.
        If aPSim was installed, it is possible the path is added to the os.environ
        but first we first check is the user has sent their own path, and then we proceed to check to already added path
        Returns:
        - str or False: The aPSim installation path if found, or False if not found.

        """
        fromConfig = Config.get_aPSim_bin_path()
        configured = fromConfig if os.path.exists(fromConfig) else None
        return configured or os.getenv("APSIM") or os.getenv(
            "Models") or self.auto_detect()


aPSim_PATH = GetAPSIMPath()()


def start_pythonnet():
    try:
        if pythonnet.get_runtime_info() is None:
            return pythonnet.load("coreclr")
    except:
        print("dotnet not found, trying alternate runtime")
        return pythonnet.load()


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
        start_pythonnet()
        # use get because it does not raise key error. it returns none if not found
        aPSim_path = aPSim_PATH
        if not aPSim_path:
            raise KeyError("APSIM is not loaded in the system environmental variable")

        if 'bin' not in aPSim_path:
            aPSim_path = os.path.join(aPSim_path, 'bin')

        if not os.path.exists(aPSim_path):
            raise ValueError("A full path to the binary folder is required or the path is invalid")
        import sys
        sys.path.append(aPSim_path)
        import clr
        sys = clr.AddReference("System")
        lm = clr.AddReference("Models")

        # return lm, sys, pythonnet.get_runtime_info()
LoadPythonnet()()

# Example usage:
if __name__ == '__main__':
    loader = LoadPythonnet()
    loaded_models = loader()
    # try importing the C# models and see if the process is successful
