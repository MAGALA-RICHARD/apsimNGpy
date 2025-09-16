# nothing should be run here we don't want any errors, as it is sued to set binaries path, which is critical to the
# application
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
from subprocess import Popen, PIPE, run
import subprocess
from typing import Union, Optional

import psutil
import uuid
from shutil import copy2

logger = logging.getLogger(__name__)
from apsimNGpy.settings import CONFIG_PATH, create_config, logger
from apsimNGpy.exceptions import ApsimBinPathConfigError
from functools import lru_cache

HOME_DATA = Path.home().joinpath('AppData', 'Local', 'Programs')
cdrive = os.environ.get('PROGRAMFILES')
CONFIG = configparser.ConfigParser()


@cache
def _apsim_model_is_installed(_path: str):
    """
    This private function checks if the APSIM model is installed by verifying the presence of binaries, especially if
    they haven't been deleted. Sometimes, after uninstallation, the `bin` folder remains, so tracking it may give a
    false sign that the binary path exists due to leftover files.
    param _path: path to APSIM model binaries
    """
    model_files = False
    path_to_search = Path(_path)
    if platform.system() == 'Windows':
        model_files = list(path_to_search.glob('*Models.exe*'))  # we tend to avoid recursion here for safety
    if platform.system() == 'Darwin' or platform.system() == 'Linux':
        model_files = list(path_to_search.glob('*Models'))
    if model_files:
        return True
    else:
        return False


@lru_cache(maxsize =1)
def locate_model_bin_path(bin_path: Union[str, Path], recursive: bool = True) -> Optional[Path]:
    """
    Search for a directory that contains APSIM binaries.

    A 'match' is any directory containing:
      - On Windows: Models.dll and Models.exe
      - On Mac/Linux: Models.dll and Models

    Returns the first matching directory found (depth-first), or None if not found.
    """
    bin_path = Path(bin_path).resolve()

    if not bin_path.exists() or not bin_path.is_dir():
        raise NotADirectoryError(f"{bin_path} is not a directory")

    # Helper to check if this dir has APSIM binaries
    def has_models(path: Path) -> bool:
        if platform.system() == "Windows":
            return (path / "Models.dll").exists() and (path / "Models.exe").exists()
        else:
            return (path / "Models.dll").exists() and (path / "Models").exists()

    # Check the provided directory
    if has_models(bin_path):
        return bin_path

    # Optionally search subdirectories
    if recursive:
        for root, dirs, _ in os.walk(bin_path):
            for d in dirs:
                subdir = Path(root) / d
                if has_models(subdir):
                    return subdir

    return None


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
    @deprecated: use ``locate_model_bin_path``
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
        pp = locate_model_bin_path(d)
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


def any_bin_path_from_env() -> Path:
    """
    Finalize resolving the real APSIM bin path or raise a clear error.

    APSIM bin path expected in environment variables:keys include:

            APSIM_BIN_PATH / APSIM_PATH / APSIM/ Models
    """
    # 1) Accept None -> try envs
    bin_path = None
    env_candidates = {
        os.getenv("APSIM_BIN_PATH"),
        os.getenv("APSIM_PATH"),
        os.getenv("APSIM"),
        os.getenv('Models')
    }
    for c in env_candidates:
        if c:
            bin_path = Path(c).resolve()
            if bin_path.exists():
                if bin_path.is_file():  # perhaps a models.exe or something executable
                    bin_path = bin_path.parent
                else:
                    bin_path = bin_path
                break

    if bin_path is not None:
        # validate this path again
        try:
            bin_path = locate_model_bin_path(bin_path)
        except NotADirectoryError:
            bin_path = None
    return bin_path


@cache
def auto_detect_apsim_bin_path():
    """ For Windows, we scan all drives. On macOS, we check the Applications folder, while on Linux, we look in `/usr/local`.
     Additionally, we search the home dir_path, though it is unlikely to be a reliable source.
    """
    path_from_env = any_bin_path_from_env()
    if path_from_env is not None:
        return path_from_env
    if platform.system() == 'Windows':
        return scan_drive_for_bin() or ""
    home_ = os.path.expanduser("~")
    if platform.system() == 'Darwin':
        # we search in a few directories home and applications and give up
        apps = '/Applications'

        return locate_model_bin_path(apps) or locate_model_bin_path(home_) or ""

    elif platform.system() == 'Linux':
        return locate_model_bin_path('/usr/local') or scan_dir_for_bin(home_) or ""
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
    if apsim_bin_path:
        # make sure it has the required binaries
        try:
           apsim_bin_path = locate_model_bin_path(apsim_bin_path)
        except (NotADirectoryError, FileNotFoundError, ValueError, ApsimBinPathConfigError) as e:
            pass # we are not interested in raising at this point
    return apsim_bin_path


def get_bin_use_history():
    """
    shows the bins that have been used only those still available on the computer as valid paths are shown.

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
        logger.info('No bin path have been set to  generate bin use histories')


def set_apsim_bin_path(path: Union[str, Path],
                       raise_errors: bool = True,
                       verbose: bool = False) -> bool:
    """
    Validate and persist the APSIM binary folder path.

    The provided `path` should point to (or contain) the APSIM `bin` directory that
    includes the required binaries:

      - Windows: Models.dll AND Models.exe
      - macOS/Linux: Models.dll AND Models (unix executable)

    If `path` is a parent directory, the function will search recursively to locate
    a matching `bin` directory. The first match is used.

    Returns
    -------
    bool
        True if the configuration was updated (or already valid and set to the same
        resolved path), False if validation failed and `raise_errors=False`.

    Raises
    ------
    ValueError
        If no valid APSIM binary directory is found and `raise_errors=True`.

    Examples
    --------
    >>> from apsimNGpy.core import config
    >>> # Check the current path
    >>> current = config.get_apsim_bin_path()
    >>> # Set the desired path (either the bin folder or a parent)
    >>> config.set_apsim_bin_path('/path/to/APSIM/2025/bin', verbose=True)
    """
    # Normalize user input
    candidate = Path(path).resolve()

    # Find a valid APSIM bin directory (allows passing a parent folder)
    validated_bin: Optional[Path] = locate_model_bin_path(candidate, recursive=True)

    if validated_bin is None:
        msg = (f"No valid APSIM binaries found under '{candidate}'. "
               f"Expected files: "
               f"{'Models.dll + Models.exe' if platform.system() == 'Windows' else 'Models.dll + Models (unix executable)'}")
        if raise_errors:
            raise ApsimBinPathConfigError(msg)
        if verbose:
            logger.warning(msg)
        return False

    # Compare with existing config (normalize to resolved Path for a fair comparison)
    try:
        current = get_apsim_bin_path()
    except Exception:
        current = ''
    current_resolved = Path(current).resolve() if current else None

    if current_resolved and current_resolved == validated_bin:
        if verbose:
            logger.info(f"APSIM binary path already set to '{validated_bin}'. No change made.")
        return True  # Path is already correct

    # Persist the validated bin path
    create_config(CONFIG_PATH, str(validated_bin))

    if verbose:
        if current_resolved:
            logger.info(f"APSIM binary path updated from '{current_resolved}' to '{validated_bin}'.")
        else:
            logger.info(f"APSIM binary path set to '{validated_bin}'.")

    return True

@cache
def apsim_version(release_number: bool = False, verbose: bool = False):
    """
    Display version information of the APSIM model currently
    in the apsimNGpy config environment. runs externally through subprocess module

    Parameters
    ----------
    release_number : bool, optional
        If True, return only the numeric release version.
    verbose : bool, optional
        If True, prints detailed version information instantly.

    Example
    -------
    >>> apsim_version()
    'APSIM 2025.8.7844.0'
    >>> apsim_version(release_number=True)
    '2025.8.7844.0'
    """
    bin_path = Path(locate_model_bin_path(get_apsim_bin_path()))

    # Determine executable based on OS
    if platform.system() == "Windows":
        APSIM_EXEC = bin_path / "Models.exe"
    else:  # Linux or macOS
        APSIM_EXEC = bin_path / "Models"

    cmd = [str(APSIM_EXEC), "--version"]
    if verbose:
        cmd.append("--verbose")

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        release = result.stdout.splitlines()[0].strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"APSIM version command failed:\n{e.stderr}")

    if release_number:
        return release.replace("APSIM", "").strip()
    return release


@cache
def load_crop_from_disk(crop: str, out: Union[str, Path]):
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

        >>> load_crop_from_disk("Maize", out ='my_maize_example.apsimx')
        'C:/path/to/temp_uuid_Maize.apsimx'
    """
    BIN = get_apsim_bin_path()

    if ".apsimx" in crop:
        crop, suffix = crop.split(".")
    else:
        suffix = 'apsimx'

    if BIN and os.path.exists(BIN):
        # assumes /Examples dir is in the same parent directory where bins
        EXa = Path(locate_model_bin_path(BIN)).parent/'Examples'
        # print(f"{EXa}*/{crop}.{suffix}")
        assert EXa.exists(), (f"Failed to located example files folder relative to the location of the {BIN}. Make sure "
                              f"you entered the correct bin path")
        target_location = glob.glob(f"{str(EXa)}/**/*{crop}.{suffix}", recursive=True)  # case-sensitive
        if target_location:
            loaded_path = target_location[0]
        else:
            raise FileNotFoundError(f"Could not find matching .apsimx file path for crop '{crop}'")
        _out_path = Path(out).with_suffix('.apsimx')
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


