import configparser
import os
import warnings
from os.path import (realpath, exists)
import platform
import glob
from pathlib import Path
from functools import lru_cache, cache
from os.path import join, dirname
from apsimNGpy.settings import CONFIG_PATH

HOME_DATA = Path.home().joinpath('AppData', 'Local', 'Programs')
cdrive = os.environ.get('PROGRAMFILES')
CONFIG = configparser.ConfigParser()


def _apsim_model_is_installed(_path):
    """
    Checks if the APSIM model is installed by verifying the presence of binaries, especially if they haven't been
    deleted. Sometimes, after uninstallation, the `bin` folder remains, so tracking it may give a false sign that the
    binary path exists due to leftover files. :param _path: path to APSIM model binaries
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
    _path = None
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
        return os.getenv("APSIM") or os.getenv("Models") or search_from_programs() or search_from_users() or ""
    if platform.system() == 'Darwin':
        # we search in applications and give up
        pattern = '/Applications/APSIM*.app/Contents/Resources/bin'
        return _match_pattern_to_path(pattern) or ""

    if platform.system() == 'Linux':
        pattern1 = '/usr/local/APSIM*/Contents/Resources/bin'
        pattern2 = '~/.APSIM*/Contents/Resources/bin'
        return _match_pattern_to_path(pattern1) or _match_pattern_to_path(pattern2) or ""
    else:
        return ""


def create_config(apsim_path=""):
    _CONFIG = configparser.ConfigParser()
    _CONFIG.read(CONFIG_PATH)
    _CONFIG['Paths'] = {'ApSIM_LOCATION': apsim_path}
    with open(CONFIG_PATH, 'w') as configured_file:
        _CONFIG.write(configured_file)


def get_apsim_bin_path():
    """
    Returns the path to the apsim bin folder from either auto detection or from the path already supplied by the user through the apsimNgpyconfig.ini file
    The function is silent does not raise any exception but return empty string in all cases
    :return:
    """
    # if it does not exist we create it and try to load from the auto detected pass
    if not exists(CONFIG_PATH):
        auto_path = auto_detect_apsim_bin_path()
        create_config(apsim_path=auto_path)
        return auto_path
    else:
        """We can extract the current path from apsimNgpyconfig.ini"""
        g_CONFIG = configparser.ConfigParser()
        g_CONFIG.read(CONFIG_PATH)
        return g_CONFIG['Paths']['ApSIM_LOCATION']


def set_apsim_bin_path(path):
    """ Send your desired path to the aPSim binary folder to the config module
    the path should end with bin as the parent directory of the aPSim Model.
    >> Please be careful with adding an uninstalled path, which does not have model.exe file or unix executable.
    It won't work and python with throw an error
    >> example from apsimNGpy.config import Config
    # check the current path
     config = Config.get_apsim_bin_path()
     # set the desired path
     >> Config.set_apsim_bin_path(path = '/path/to/APSIM*/bin')
    """
    _path = realpath(path)
    if not _apsim_model_is_installed(_path):
        raise ValueError(f"files might have been uninstalled at this location '{_path}'")
    if _path != get_apsim_bin_path():
        create_config(_path)
        print(f"saved {_path} to '{CONFIG_PATH}'")


class Config:
    """
        The configuration class providing the leeway for the user to change the
       global variables such as aPSim bin locations. it is deprecated
        """

    @classmethod
    def get_aPSim_bin_path(cls):
        warnings.warn(
            f'apsimNGpy.config.Config.get_apsim_bin_path for changing apsim binary path is deprecated> '
            f'use:apsimNGpy.config.get_apsim_bin_path ',
            FutureWarning)
        """We can extract the current path from config.ini"""
        return get_apsim_bin_path()

    @classmethod
    def set_aPSim_bin_path(cls, path):
        warnings.warn(
            f'apsimNGpy.config.Config.set_apsim_bin_path . class for changing apsim binary path is deprecated> '
            f'use:apsimNGpy.config.set_apsim_bin_path ',
            FutureWarning)

        """ Send your desired path to the aPSim binary folder to the config module
        the path should end with bin as the parent directory of the aPSim Model.exe
        >> Please be careful with adding an uninstalled path, which do not have model.exe file.
        It won't work and python with throw an error
        >> example from apsimNGpy.config import Config
        # check the current path
         config = Config.get_apsim_bin_path()
         # set the desired path
         >> Config.set_apsim_bin_path(path = '/path/to/aPSimbinaryfolder/bin')
        """
        _path = realpath(path)
        return set_apsim_bin_path(_path)
