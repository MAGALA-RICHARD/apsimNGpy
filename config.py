import configparser
import os
import warnings
from os.path import (realpath, exists)
import platform
import glob
from pathlib import Path
from functools import lru_cache, cache
from os.path import join, dirname
from settings import CONFIG_PATH, logger, MSG
from functools import lru_cache

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
    """
    This will search through a few suspected locations and give up
    the best idea is to just add the installation path to APSIM PATH. Although it is possible to search the whole computer this
    is computationally intensive, but there is a plan to do so through one single run automatically
    @return: apsim bin installation path where.dll files resides or None if not found
    """
    common_t_all = os.getenv("APSIM")
    if common_t_all:
        return common_t_all
    if platform.system() == 'Windows':
        return search_from_programs() or search_from_users() or ""
    if platform.system() == 'Darwin':
        # we search in applications and home and give up
        pattern = '/Applications/APSIM*.app/Contents/Resources/bin'
        _home = os.path.expanduser('~')
        pattern2 = f"{_home}/APSIM*.app/Contents/Resources/bin"
        return _match_pattern_to_path(pattern) or _match_pattern_to_path(pattern2) or ""

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


@lru_cache(maxsize=None)
def get_apsim_bin_path():
    """We can extract the current path from config.ini or from the automatic search:
       @return str: path to the apsim binaries or empty string which evaluate to a boolean false
    """
    if exists(CONFIG_PATH):
        g_CONFIG = configparser.ConfigParser()
        g_CONFIG.read(CONFIG_PATH)
        return g_CONFIG['Paths']['ApSIM_LOCATION']
    auto = auto_detect_apsim_bin_path()
    if auto:
        # the config.ini has not received a path, yet we try to get it from the computer
        # by the function above and then send it to the config.in using the create_config
        create_config(auto)
        return auto

    else:
        # At this moment we need to stop and fix this error, but no let's provide a debugging message
        # because error will avoid importing the get_apsim_bin_path or set_apsim_bin_path to fix the problem
        logger.debug(MSG)


def set_apsim_bin_path(path):
    """ Send your desired path to the aPSim binary folder to the config.in which is then accessed by the pythonet_config module
    the path should end with bin as the parent directory of the aPSim Model.
    >> Please be careful with adding an uninstalled path, which does not have model.exe file or unix executable.
    It won't work and python with throw an error
    >> example from apsimNGpy.config import Config
    # check the current path
     config = Config.get_apsim_bin_path()
     # set the desired path
     >> Config.set_apsim_bin_path(path = '/path/to/APSIM*/bin')

    Here's a refined version of your note, incorporating your requested phrase for improved clarity:

    **Note: ** Due to caching behaviors in `get_apsim_bin_path`, which is interacting with the configuration file,
    errors may occur after changes—especially if the system attempts to access a path that has been uninstalled. If this
     happens, please rerun the application or restart your IDE to refresh the cached results.
    """
    _path = realpath(path)
    if not _apsim_model_is_installed(_path):
        raise ValueError(f"files might have been uninstalled at this location '{_path}'")
    if _path != get_apsim_bin_path():
        create_config(_path)
        logger.info(f"saved {_path} to '{CONFIG_PATH}'")


class Config:
    """
        The configuration class providing the leeway for the user to change the
       global variables such as aPSim bin locations. it is deprecated
        """

    @classmethod
    def get_aPSim_bin_path(cls):
        warnings.warn(
            f'Deprecation warning: apsimNGpy.config.Config.get_apsim_bin_path for changing apsim binary path is deprecated> '
            f'use:apsimNGpy.config.get_apsim_bin_path ',
            FutureWarning)
        """We can extract the current path from config.ini"""
        return get_apsim_bin_path()

    @classmethod
    def set_aPSim_bin_path(cls, path):
        warnings.warn(
            f'Deprecation warning: apsimNGpy.config.Config.set_apsim_bin_path for changing apsim binary path is deprecated> '
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
