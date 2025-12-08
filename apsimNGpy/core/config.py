# nothing should be run here we don't want any errors, as it is used to set bin_path, which is critical to the
# application
from __future__ import annotations

import configparser
import dataclasses
import glob
import logging
import os
import platform
import subprocess
import sys
import time
from contextlib import AbstractContextManager
from functools import cache
from os.path import (exists)
from pathlib import Path
from shutil import copy2
from typing import Union, Optional, Any
import psutil
from apsimNGpy.core_utils.utils import timer
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
from apsimNGpy.settings import CONFIG_PATH, create_config, logger
from apsimNGpy.exceptions import ApsimBinPathConfigError
from functools import lru_cache

# Load a default .env if present (optional)
load_dotenv()

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


@lru_cache(maxsize=1)
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


def get_apsim_bin_path():
    """
    Returns the path to the apsim bin folder from either auto-detection or from the path already supplied by the user
    through the apsimNGpy config.ini file in the user home directory.

    This function is silent does not raise any exception but return empty string in all
    cases if bin_path is empty or was not found.


    Example::

      bin_path = get_apsim_bin_path()

    .. seealso::

           :func:`~apsimNGpy.core.config.set_apsim_bin_path`


    """

    def _get_bin():
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
                pass  # we are not interested in raising at this point
        return os.path.realpath(apsim_bin_path) if isinstance(apsim_bin_path, Path) else apsim_bin_path

    return _get_bin()


@dataclasses.dataclass
class Configuration:
    """
  In the future, this module will contain all the constants required by the package.
   Users will be able to override these values if needed by importing this module before running any simulations.

    """
    bin_path: Union[Path, str] = None

    def __post_init__(self):
        """if bin_path is None, this function will normalize to a global one store on the disk"""
        self.bin_path = get_apsim_bin_path() or any_bin_path_from_env() if self.bin_path is None else self.bin_path

    def set_temporal_bin_path(self, temporal_bin_path):
        """
         Set a temporary APSIM-NG binary path for this package/module.

        This updates the module-level resolution of APSIM assemblies to use the
        provided path for the current process/session. It does **not** permanently
        change the global APSIM bin path on disk. Use this when you need to pin a
        workflow to a specific APSIM build for reproducibility.

        Parameters
        ----------
        temporal_bin_path : str | os.PathLike
            Absolute or relative path to the APSIM ``bin`` directory to use
            temporarily (e.g., ``C:/APSIM/2025.09.01/bin``).

            Reference (for the *global* fallback, not changed by this method):
            :func:`get_apsim_bin_path()` typically resolves from configuration or
            environment variables ``APSIM_BIN_PATH``, ``MODELS``, or ``APSIM``.

        Returns
        -------
        None

        Raises
        ------
        FileNotFoundError
            If ``temporal_bin_path`` does not exist.
        NotADirectoryError
            If ``temporal_bin_path`` is not a directory.
        PermissionError
            If the process lacks read/execute permission on the path.
        ValueError
            If the directory does not appear to be a valid APSIM ``bin`` (e.g.,
            required assemblies are missing).

        Notes
        -----
        - Assemblies already loaded after pointing to this path will remain bound
          in memory for the lifetime of the process.
        - To limit the override to a block of code, prefer a context manager that
          restores the prior path on exit.

        Examples
        --------

        .. code-block:: python

            from apsimNGpy.core.config import configuration
            configuration.set_temporal_bin_path(r"C:/APSIM/2025.09.01/bin")
            # proceed with imports/execution; assemblies are resolved from that path


        .. seealso::

           :func:`~apsimNGpy.core.config.get_apsim_bin_path`
           :func:`~apsimNGpy.core.config.set_apsim_bin_path`



    """
        self.bin_path = locate_model_bin_path(temporal_bin_path)

    def release_temporal_bin_path(self):
        """release and set back to the global bin path"""
        self.bin_path = get_apsim_bin_path() or any_bin_path_from_env()


configuration = Configuration()


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
    Validate and write the bin path to the config file, where it is accessed by ``get_apsim_bin_path``.

    Parameters
    ___________
    path : Union[str, Path]
        The provided `path` should point to (or contain) the APSIM `bin` directory that
        includes the required binaries:
          - Windows: Models.dll AND Models.exe
          - macOS/Linux: Models.dll AND Models (unix executable)
        If `path` is a parent directory, the function will search recursively to locate
        a matching `bin` directory. The first match is used.

    raise_errors : bool, default is True
        Whether to raise an error in case of errors. for testing purposes only

    verbose: bool
       whether to print messages to the console or not


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

   .. seealso::

           :func:`~apsimNGpy.core.config.get_apsim_bin_path`

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
    create_config(CONFIG_PATH, os.path.realpath(validated_bin))

    if verbose:
        if current_resolved:
            logger.info(f"APSIM binary path updated from '{current_resolved}' to '{validated_bin}'.")
        else:
            logger.info(f"APSIM binary path set to '{validated_bin}'.")

    return True


@cache
def apsim_version(bin_path=configuration.bin_path, release_number: bool = False, verbose: bool = False):
    """
    Display version information of the APSIM model currently
    in the apsimNGpy config environment. runs externally through subprocess module

    Parameters
    ----------
    bin_path : str, Path,
        default to a global bin path in apsimNGpy environmental variables
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
    try:
        bin_path = Path(locate_model_bin_path(bin_path))
    except TypeError as e:
        raise TypeError(
            f"this error `{e}` has likely occurred because the bin-path `{bin_path}` is invalid or does not exist")

    # Determine executable based on OS
    if platform.system() == "Windows":
        APSIM_EXEC = bin_path / "Models.exe"
    else:  # Linux or macOS
        APSIM_EXEC = bin_path / "Models"

    cmd = [os.path.realpath(APSIM_EXEC), "--version"]
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


_memory_cache: dict[tuple, Any] = {}


def _load_crop_from_disk(crop: str, out: Union[str, Path], bin_path: Union[str, Path], suffix='.apsimx') -> None:
    BIN = bin_path or configuration.bin_path
    crop_path = Path(crop)
    if crop_path.suffix == ".apsimx" in crop or crop_path.suffix=='.met':
        crop, suffix = crop_path.stem, crop_path.suffix
    else:
        suffix = suffix
    if not suffix.startswith('.'):
        raise ValueError(f"Unrecognized suffix '{suffix}'")
    if BIN and os.path.exists(BIN):
        # assumes /Examples dir is in the same parent directory where bins
        EXa = Path(locate_model_bin_path(BIN)).parent / 'Examples'
        # print(f"{EXa}*/{crop}.{suffix}")
        assert EXa.exists(), (
            f"Failed to located example files folder relative to the location of the {BIN}. Make sure "
            f"you entered the correct bin path")
        target_location = glob.glob(f"{os.path.realpath(EXa)}/**/*{crop}{suffix}", recursive=True)  # case-sensitive
        if target_location:
            loaded_path = target_location[0]
        else:
            raise FileNotFoundError(f"Could not find matching .apsimx file path for crop '{crop}'")
        _out_path = Path(out).with_suffix('.apsimx')
        copied_file = copy2(loaded_path, _out_path)
        return copied_file

    raise FileNotFoundError(
        "Could not find root path for APSIM binaries. "
        "Try reinstalling APSIM or use :meth:`set_apsim_bin_path` to set the path to an existing APSIM version."
    )


def load_crop_from_disk(crop: str, out: Union[str, Path], bin_path=None, cache_path=True, suffix ='.apsimx'):
    """
    Load a default APSIM crop simulation file from disk by specifying only the crop name. This fucntion can literally
    load anything that resides under the /Examples directory.

    Locates and copies an `.apsimx` file associated with the specified crop from the APSIM
    /Examples directory into a working directory. It is useful when programmatically running default
    simulations for different crops without manually opening them in GUI.

    Parameters
    ----------
    crop: (str)
        The name of the crop to load (e.g., 'Maize', 'Soybean', 'Barley', 'Mungbean', 'Pinus', 'Eucalyptus').
        The name is case-insensitive and must-match an existing `.apsimx` file in the APSIM Examples folder.

    out: (str, optional)
         A custom output path where the `.apsimx` file should be copied.
         If not provided, a temporary file will be created in the working directory. this is stamped with the APSIM version being used


    bin_path: (str, optional):
       no restriction we can laod from  another bin path
    cache_path: (str, optional):

        keep the path in memory for the next request

    Returns
    ________
        `str`: The path to the copied `.apsimx` file ready for further manipulation or simulation.

    .. caution::

      The method catches the results, so if the file is removed from the disk, there may be issues> If this case
      is anticipated, turn off the cach_path to False.

    Raises
    ________
        ``FileNotFoundError``: If the APSIM binary path cannot be resolved or the crop simulation file does not exist.

    Example::

        >>> load_crop_from_disk("Maize", out ='my_maize_example.apsimx')
        'C:/path/to/temp_uuid_Maize.apsimx'

    """
    keys = f"{crop}{out}-{os.path.realpath(str(bin_path))}-{suffix}",
    if cache_path and keys in _memory_cache:
        return _memory_cache[keys]
    else:
        path = _load_crop_from_disk(crop, out, bin_path, suffix=suffix)
        _memory_cache[keys] = path
        return path


def stamp_name_with_version(file_name):
    """
    Stamp every file name with the version, which allows the user to associate the file name with its appropriate
    version it was created.

    Parameters
    ------------
    file_name: str
          path to the would be.apsimx file.

    Returns
    -------
    str path with the apsim version stamp
    """
    version = apsim_version()
    destination = Path(file_name).resolve()
    dest_path = destination.with_name(
        destination.name.replace(".apsimx", f"{version}.apsimx")
    )
    return dest_path


class apsim_bin_context(AbstractContextManager):
    """
        Temporarily configure the APSIM-NG *bin* path used by ``apsimNGpy`` so imports
        (e.g., ``ApsimModel``) can resolve APSIM .NET assemblies. Restores the previous
        configuration on exit.

        Parameters
        ----------
        apsim_bin_path : str | os.PathLike | None, optional
            Explicit path to the APSIM ``bin`` directory (e.g.,
            ``C:/APSIM/2025.05.1234/bin`` or ``/opt/apsim/2025.05.1234/bin``).
            Used if no valid value is resolved from ``dotenv_path``.
        dotenv_path : str | os.PathLike | None, optional
            Path to a ``.env`` file to load *before* resolution. If provided, the
            manager will read (in order): ``bin_key`` (if non-empty), then
            ``APSIM_BIN_PATH``, then ``APSIM_MODEL_PATH`` from that file.
        bin_key : str, default ''
            Custom environment variable name to read from the loaded ``.env``
            (e.g., ``"APSIM_BIN_PATH_2025"``). Ignored when empty.
        timeout : float, default 0.003
            Small sleep (seconds) after setting the bin path to avoid races with
            immediate imports on some filesystems. Set to 0 to disable.

        Returns
        -------
        None
            The context manager returns ``None``; import within the ``with`` block.

        Raises
        ------
        ValueError
            If no path can be resolved from ``dotenv_path``, ``apsim_bin_path``,
            or the process environment.
        FileNotFoundError
            If the resolved path does not exist.

        Notes
        -----
        - Python.NET assemblies cannot be unloaded from a running process; this
          context only restores path configuration for **future** imports.
        - Do not nest this context across threads; the underlying config is global.

        Examples
        --------
        Use an explicit path::

           with apsim_bin_context(r"C:/APSIM/2025.05.1234/bin"):
             from apsimNGpy.core.apsim import ApsimModel
             model = ApsimModel(...)

        Use a .env file with a custom key::

            from pathlib import Path
            with apsim_bin_context(dotenv_path=Path(".env"), bin_key="APSIM_BIN_PATH"):
                 from apsimNGpy.core.apsim import ApsimModel

       If you have .env files located in the root of your script::

         with apsim_bin_context():
             from apsimNGpy.core.apsim import ApsimModel

        Verify restoration::

            prev = get_apsim_bin_path()
            with apsim_bin_context(r"C:/APSIM/X.Y.Z/bin"):

            assert get_apsim_bin_path() == prev

      added in v0.39.10.20+
        """

    def __init__(
            self,
            apsim_bin_path: str | os.PathLike | None = None,
            dotenv_path: str | os.PathLike | None = None,
            bin_key: str = '',

    ) -> None:
        bin_path: str | None = None

        # If a specific .env path is provided, load it first
        if dotenv_path is not None:
            dp = Path(dotenv_path)
            if dp.exists() and os.path.realpath(dp).endswith('.env'):
                load_dotenv(os.path.realpath(dp.resolve()))
            else:
                if dotenv_path is not None:
                    raise FileNotFoundError(f"dotenv_path does not exist or it is invalid .env file: {dp}")
            # Try env vars from that .env
            bin_path = os.getenv(bin_key) or os.getenv("APSIM_BIN_PATH") or os.getenv("APSIM_MODEL_PATH")

        # If no .env bin found, fall back to explicit arg
        if bin_path is None and apsim_bin_path is not None:
            bin_path = os.path.realpath(Path(apsim_bin_path).resolve())

        # If still none, try already-loaded env (from top-level load_dotenv)
        if bin_path is None:
            bin_path = os.getenv("APSIM_BIN_PATH") or os.getenv("APSIM_MODEL_PATH")

        if not bin_path:
            raise ValueError(
                "APSIM bin path not provided. Pass `apsim_bin_path=` or set "
                "APSIM_BIN_PATH / APSIM_MODEL_PATH via environment/.env."
            )

        # Optional: check the path exists
        p = Path(bin_path)
        if not p.exists():
            raise FileNotFoundError(f"APSIM bin path not found: {p}")

        self.bin_path = os.path.realpath(p)

    def __enter__(self):
        # Save and set
        configuration.set_temporal_bin_path(self.bin_path)
        return None

    def __exit__(self, exc_type, exc, tb):
        # Restore previous paths (even if it was None/empty)
        configuration.release_temporal_bin_path()
        return False  # do not suppress exceptions


if __name__ == "__main__":
    # -------- Example usage --------
    from unittest import TestCase
    import unittest


    class TestConfig(TestCase):
        def setUp(self):
            pass

        def test_no_bin_path(self):
            with self.assertRaises(ValueError):
                dot_ev_path = None
                with apsim_bin_context(dotenv_path=dot_ev_path):
                    pass

        def test_no_dot_ev_path(self):
            with self.assertRaises(FileNotFoundError):
                with apsim_bin_context(dotenv_path="dot_ev_path"):
                    pass

if __name__ == "__main__":
    ap = os.path.realpath('maizeTT.apsimx')
    try:

       maize = load_crop_from_disk('Maize', out= ap)
       print(f'path exists' ) if os.path.exists(ap) else print('file does not exist')
    finally:
        try:
            Path(ap).unlink(missing_ok=True)
            print('path is cleaned up')
        except PermissionError:
            pass
