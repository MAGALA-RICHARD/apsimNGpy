import glob
import os
import platform
import shutil
from functools import cache
from pathlib import Path

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
@cache
def search_from_programs():
    # if the executable is not found, then most likely even if the bin path exists, apsim is uninstalled
    prog_path = glob.glob(f'{cdrive}/APSIM*/bin/Models.exe')
    if prog_path:
      for path_fpath in prog_path:
            return os.path.dirname(path_fpath)
    else:
            return None
@cache
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
@cache
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
            return  os.getenv("APSIM") or os.getenv("Models") or search_from_programs() or search_from_users()
        if platform.system() == 'Darwin':
            # we search in applications and give up
            pattern = '/Applications/APSIM*.app/Contents/Resources/bin'
            return _match_pattern_to_path(pattern)

        if platform.system() == 'Linux':
            pattern1  = '/usr/local/APSIM*/Contents/Resources/bin'
            pattern2 = '~/.APSIM*/Contents/Resources/bin'
            return _match_pattern_to_path(pattern1) or _match_pattern_to_path(pattern2)

auto_searched = auto_detect_apsim_bin_path()
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





