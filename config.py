import configparser
import os
import warnings
from os.path import (realpath, exists)
import platform
import glob
from pathlib import Path
from functools import lru_cache, cache
from os.path import join, dirname

import psutil

from apsimNGpy.settings import CONFIG_PATH, create_config

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


def list_drives():
    drives = []
    for part in psutil.disk_partitions():
        # This checks if there's a filesystem type, which indicates a mounted and accessible partition
        if part.fstype:
            drives.append(f"{part.device}")
    return drives


@lru_cache(maxsize=3)
def scan_dir_for_bin(path):
    """
    Recursively scans directories starting at the given path.
    Stops scanning as soon as a directory named 'bin' is encountered and returns its path.
    """
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_dir():
                if entry.name == 'bin' and 'APSIM20' in entry.path:
                    # we don't want to call _apsim_model_is_installed on every directory,
                    # so we call it below after the first condition is met
                    if _apsim_model_is_installed(entry.path):
                        # Return the path of the 'bin' directory
                        return entry.path

                else:
                    # Recursively scan other directories
                    try:
                        result = scan_dir_for_bin(entry.path)
                        if result:  # If 'bin' is found in the recursion, stop further scanning
                            return result
                    except (PermissionError, OSError):
                        ...

    return None  # Return None if 'bin' and 'APSIM' is not found


def scan_drive_for_bin():
    """This function uses scan_dir_for_bin to scan all drive directories.
    for Windows only"""
    for d in list_drives():
        pp = scan_dir_for_bin(d)
        if pp:
            return pp


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
    """ For Windows, we scan all drives. On macOS, we check the Applications folder, while on Linux, we look in `/usr/local`.
     Additionally, we search the home directory, though it is unlikely to be a reliable source.
    """
    if platform.system() == 'Windows':
        return  scan_drive_for_bin() or ""
    home_ = os.path.expanduser("~")
    if platform.system() == 'Darwin':
        # we search in a few directories home and applications and give up
        apps = '/Applications'

        return scan_dir_for_bin(apps) or scan_dir_for_bin(home_) or ""

    if platform.system() == 'Linux':
        return scan_dir_for_bin('/usr/local') or scan_dir_for_bin(home_) or ""
    else:
        return ""


def get_apsim_bin_path():
    """
    Returns the path to the apsim bin folder from either auto-detection or from the path already supplied by the user
    through the apsimNgpyconfig.ini file in the user home directory. the location folder is called
    The function is silent does not raise any exception but return empty string in all cases
    :return:
    """
    # if it does not exist, we create it and try to load from the auto-detected pass
    g_CONFIG = configparser.ConfigParser()
    g_CONFIG.read(CONFIG_PATH)
    """We can extract the current path from apsimNGpyconfig.ini"""
    apsim_bin_path = g_CONFIG['Paths']['APSIM_LOCATION']
    if not exists(apsim_bin_path):
        auto_path = auto_detect_apsim_bin_path()
        create_config(CONFIG_PATH, apsim_path=auto_path)
        return auto_path
    return apsim_bin_path


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
        create_config(CONFIG_PATH, _path)
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
