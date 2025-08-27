import configparser
import os
import warnings
from os.path import (realpath, exists)
import platform
import glob
from pathlib import Path
from functools import lru_cache, cache
from os.path import join, dirname
import logging
from subprocess import Popen, PIPE

import psutil
import uuid
from shutil import copy2

logger = logging.getLogger(__name__)
from apsimNGpy.settings import CONFIG_PATH, create_config, logger
from functools import lru_cache

HOME_DATA = Path.home().joinpath('AppData', 'Local', 'Programs')
cdrive = os.environ.get('PROGRAMFILES')
CONFIG = configparser.ConfigParser()


@cache
def _apsim_model_is_installed(_path: str):
    """
    This private function checks if the APSIM model is installed by verifying the presence of binaries, especially if they haven't been
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
    """
    for windows-only
    @return: list of available drives on windows pc
    """
    drives = []
    for part in psutil.disk_partitions():
        # This checks if there's a filesystem child, which indicates a mounted and accessible partition
        if part.fstype:
            drives.append(f"{part.device}")
    return drives


@lru_cache(maxsize=3)
def scan_dir_for_bin(path: str):
    """
    Recursively scans directories starting at the given path.
    Stops scanning as soon as a dir_path named 'bin' is encountered and returns its path.
    """
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_dir():
                if entry.name == 'bin' and 'APSIM20' in entry.path:
                    # we don't want to call _apsim_model_is_installed on every dir_path,
                    # so we call it below after the first condition is met
                    if _apsim_model_is_installed(entry.path):
                        # Return the path of the 'bin' dir_path
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
     Additionally, we search the home dir_path, though it is unlikely to be a reliable source.
    """
    if platform.system() == 'Windows':
        return scan_drive_for_bin() or ""
    home_ = os.path.expanduser("~")
    if platform.system() == 'Darwin':
        # we search in a few directories home and applications and give up
        apps = '/Applications'

        return scan_dir_for_bin(apps) or scan_dir_for_bin(home_) or ""

    if platform.system() == 'Linux':
        return scan_dir_for_bin('/usr/local') or scan_dir_for_bin(home_) or ""
    else:
        return ""


@cache
def get_apsim_bin_path():
    """
    Returns the path to the apsim bin folder from either auto-detection or from the path already supplied by the user
    through the apsimNgp config.ini file in the user home dir_path. the location folder is called
    The function is silent does not raise any exception but return empty string in all cases
    :return:

    Example::

      bin_path = get_apsim_bin_path()
    """
    # if it does not exist, we create it and try to load from the auto-detected pass
    g_CONFIG = configparser.ConfigParser()
    g_CONFIG.read(CONFIG_PATH)
    # """We can extract the current path from apsimNGpyconfig.ini"""
    apsim_bin_path = g_CONFIG['Paths']['APSIM_LOCATION']
    if not exists(apsim_bin_path):
        auto_path = auto_detect_apsim_bin_path()
        create_config(CONFIG_PATH, apsim_path=auto_path)
        return auto_path

    return apsim_bin_path


def get_bin_use_history():
    """
    shows the bins that have been used oly those still available on the computer as valid paths are shown.

    @return: list[paths]
    """
    g_CONFIG = configparser.ConfigParser()
    g_CONFIG.read(CONFIG_PATH)
    if g_CONFIG.has_section('PreviousPaths'):
        history = g_CONFIG['PreviousPaths']['BINS']
        his = eval(history)
        # return only those currently existing
        his = [i for i in his if os.path.exists(i)]
        return his
    else:
        logger.info('No bin path have been set to get generate bin use histories')


def set_apsim_bin_path(path, raise_errors=True):
    """ Send your desired path to the aPSim binary folder to the config module
    the path should end with bin as the parent dir_path of the aPSim Model.
    >> Please be careful with adding an uninstalled path, which does not have model.exe file or unix executable.
    It won't work and Python with throw an error

    Example::

         from apsimNGpy.core import config
         # check the current path
         config = config.get_apsim_bin_path()
         # set the desired path
         config.set_apsim_bin_path(path = '/path/to/APSIM*/bin')
    """
    _path = realpath(path)
    if os.path.basename(_path) != 'bin':
        _path = os.path.join(_path, 'bin')  # this will work only if base path is valid
    if not _apsim_model_is_installed(_path):
        if raise_errors:
            raise ValueError(f"files might have been uninstalled at this location '{_path}'")
        else:
            logger.warning(f"Attempted to set an invalid path: {_path}")
            return  # Optionally, you could return False here to indicate failure
    current_path = get_apsim_bin_path()
    if str(_path) != str(current_path):
        create_config(CONFIG_PATH, _path)

        logger.info(f"APSIM binary path successfully updated from '{current_path}' to '{_path}'")

    else:

        logger.warning(f"{_path} is similar to exising APSIM binary at this location: '{current_path}'")


class Config:
    """
    @deprecated since version 0.2

        The configuration class providing the leeway for the user to change the
       global variables such as APSIM bin locations. It is deprecated
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
        the path should end with bin as the parent dir_path of the aPSim Model.exe
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


@cache
def apsim_version(release_number=False, verbose: bool = False):
    """ Display version information of the apsim model currently in the apsimNGpy config environment.

    ``verbose``: (bool) Prints the version information ``instantly``

    Example::

            apsim_version = get_apsim_version()

    """
    bin_path = Path(get_apsim_bin_path())
    # Determine executable based on OS
    if platform.system() == "Windows":

        APSIM_EXEC = bin_path / "Models.exe"
    else:  # Linux or macOS
        APSIM_EXEC = bin_path / "Models"

    cmd = [APSIM_EXEC, '--version']
    if verbose:
        cmd.append("--verbose")
    res = Popen(cmd, stdout=PIPE, stderr=PIPE, text=True)
    res.wait()
    release = res.stdout.readlines()[0].strip()
    if release_number:
        return release.strip('APSIM').strip()
    return release


@cache
def load_crop_from_disk(crop: str, out: str = None, work_space: str = None):
    """
    Load a default APSIM crop simulation file from disk by specifying only the crop name.

    This function locates and copies an `.apsimx` file associated with the specified crop from the APSIM
    Examples directory into a working directory. It is useful when programmatically running default
    simulations for different crops without manually opening them in GUI.

    Args:
        ``crop`` (str): The name of the crop to load (e.g., 'Maize', 'Soybean', 'Barley', 'Mungbean', 'Pinus', 'Eucalyptus').
                    The name is case-insensitive and must match an existing `.apsimx` file in the APSIM Examples folder.

        ``out`` (str, optional): A custom output path where the `.apsimx` file should be copied.
                             If not provided, a temporary file will be created in the working directory. this is stamped with the APSIM version being used

        ``work_space`` (str, optional): The base directory to use when generating a temporary output path.
                                    If not specified, the current working directory is used.
                                    This path may also contain other simulation or residue files.

    Returns:
        ``str``: The path to the copied `.apsimx` file ready for further manipulation or simulation.

    Raises:
        ``FileNotFoundError``: If the APSIM binary path cannot be resolved or the crop simulation file does not exist.

    Example::

        >>> load_crop_from_disk("Maize")
        'C:/path/to/temp_uuid_Maize.apsimx'
    """
    BIN = get_apsim_bin_path()
    _version = apsim_version()
    if ".apsimx" in crop:
        crop, suffix = crop.split(".")
    else:
        suffix = 'apsimx'

    if BIN and os.path.exists(BIN):
        EXa = BIN.replace('bin', 'Examples')
        # print(f"{EXa}*/{crop}.{suffix}")

        target_location = glob.glob(f"{EXa}/**/*{crop}.{suffix}", recursive=True)  # case-sensitive
        if target_location:
            loaded_path = target_location[0]
        else:
            raise FileNotFoundError(f"Could not find matching .apsimx file path for crop '{crop}'")

        __wd = Path(work_space) if work_space else Path.cwd()
        _out_path = out or str(__wd / f"temp_{uuid.uuid1()}_{_version}_{crop}.apsimx")
        copied_file = copy2(loaded_path, _out_path)
        return copied_file

    raise FileNotFoundError(
        "Could not find root path for APSIM binaries. "
        "Try reinstalling APSIM or use set_apsim_bin_path() to set the path to an existing APSIM version."
    )


def stamp_name_with_version(file_name):
    """
    we stamp every file name with the version, which allows the user to open it in the appropriate version it was created
    @param file_name: path to the would be.apsimx file
    @return: path to the stamped file
    """
    version = apsim_version()
    destination = Path(file_name).resolve()
    dest_path = destination.with_name(
        destination.name.replace(".apsimx", f"{version}.apsimx")
    )
    return dest_path


APSIM_VERSION_NO = apsim_version(release_number=True)
BASE_RELEASE_NO = '2025.8.7837.0'
