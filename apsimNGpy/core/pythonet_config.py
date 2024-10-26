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
    if platform.system() == 'Darwin' or platform.system() == 'Linux':
        model_files = list(path_to_search.glob('*Models'))
    if model_files:
        return True
    else:
        return False
def search_from_programs():
    # if the executable is not found, then most likely even if the bin path exists, apsim is uninstalled
    prog_path = glob.glob(f'{cdrive}/APSIM*/bin/Models.exe')
    if prog_path:
      for path_fpath in prog_path:
            return os.path.dirname(path_fpath)
    else:
            return None
def search_from_users():
    # if the executable is not found, then most likely even if the bin path exists, apsim is uninstalled
    home_path = os.path.realpath(Path.home())
    trial_search = glob.glob(f"{home_path}/AppData/Local/Programs/APSIM*/bin/Models.exe")
    _path  = None
    if trial_search:
        for paths in trial_search:
            return os.path.dirname(paths)
    else:
        return None
def _match_pattern_to_path(pattern):
    matching_paths = glob.glob(pattern)
    for matching_path in matching_paths:
        if os.path.isdir(matching_path) and _apsim_model_is_installed(matching_path):
            return matching_path
        else:
            return None
@cache
def auto_detect_apsim_bin_path():
        if platform.system() == 'Windows':
            return  shutil.which("Models") or search_from_programs() or search_from_users()
        if platform.system() == 'Darwin':
            # we search in applications and give up
            pattern = '/Applications/APSIM*.app/Contents/Resources/bin'
            return _match_pattern_to_path(pattern)

        if platform.system() == 'Linux':
            pattern1  = '/usr/local/APSIM*/Contents/Resources/bin'
            pattern2 = '~/.APSIM*/Contents/Resources/bin'
            return _match_pattern_to_path(pattern1) or _match_pattern_to_path(pattern2)

auto_searched = auto_detect_apsim_bin_path()
print(auto_searched)
@cache
def collect_apsim_path():
    """searches for an apsimx path
        Find the aPSim installation path using the os module.
        If aPSim was installed, it is possible the path is added to the os.environ
        but first we first check is the user has sent their own path, and then we proceed to check to already added path
        @return: unix or windows path
          --- if found, or False if not found.

        """
    from_config = Config.get_aPSim_bin_path()
    configured = from_config if os.path.exists(from_config) else None
    return configured or auto_searched or os.getenv("APSIM") or os.getenv(
        "Models")


aPSim_PATH = collect_apsim_path()


def start_pythonnet():
    try:
        if pythonnet.get_runtime_info() is None:
            return pythonnet.load("coreclr")
    except:
        print("dotnet not found, trying alternate runtime")
        return pythonnet.load()


@cache
def load_pythonnet():
    """
    A method for loading Python for .NET (pythonnet) and APSIM models.

    This class provides a callable method for initializing the Python for .NET (pythonnet) runtime and loading APSIM models.
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
    Attributes:
    ----------
    None
    """



    _aPSim_Path = collect_apsim_path()

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

    import sys
    sys.path.append(aPSim_path)
    import clr
    sys = clr.AddReference("System")
    lm = clr.AddReference("Models")

        # return lm, sys, pythonnet.get_runtime_info()

load_pythonnet()

# Example usage:
if __name__ == '__main__':
    loader = load_pythonnet()
    loaded_models = loader
    import Models
    # try importing the C# models and see if the process is successful
