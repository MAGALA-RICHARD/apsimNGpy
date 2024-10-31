import configparser
import os
import warnings
from os.path import (realpath, join, isfile, exists, dirname)
import glob
import os
import platform
from functools import cache
from os.path import (join, dirname)
from pathlib import Path
from apsimNGpy.core.path_finders import get_config_ini_path

CONFIG_PATH = get_config_ini_path()
HOME_DATA = Path.home().joinpath('AppData', 'Local', 'Programs')
cdrive = os.environ.get('PROGRAMFILES')


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


def __create_config(apsim_path=""):
    c_config = configparser.ConfigParser()
    put_default_path = apsim_path
    c_config['Paths'] = {'ApSIM_LOCATION': put_default_path}
    with open(CONFIG_PATH, 'w') as configured_file:
        c_config.write(configured_file)


def get_apsim_bin_path():
    """We can extract the current path from config.ini"""
    g_config = configparser.ConfigParser()
    g_config.read(CONFIG_PATH)
    return g_config['Paths']['ApSIM_LOCATION']


if not exists(CONFIG_PATH):
    auto_searched = auto_detect_apsim_bin_path()
    __create_config(apsim_path=auto_searched)

if not get_apsim_bin_path():
    auto_searched = auto_detect_apsim_bin_path()
    __create_config(apsim_path=auto_searched)


def set_apsim_bin_path(path):
    s_config = configparser.ConfigParser()
    s_config.read(CONFIG_PATH)
    from pathlib import Path
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
    path_to_search = Path(_path)
    model_files = list(path_to_search.glob('*Models.*'))
    # we also don't want to send a path does not work
    if not _apsim_model_is_installed(_path):
        raise ValueError(f"files might have been uninstalled at this location{_path}")
    if _path != get_apsim_bin_path():
        # if not, we raise assertion error because there is no point to
        # send a non-working path to the pythonnet config module
        # at this point the user may need to change to another path
        s_config['Paths']['ApSIM_LOCATION'] = _path
        with open('config.ini', 'w') as config_file:
            s_config.write(config_file)


class Config:
    """
        The configuration class providing the leeway for the user to change the
       global variables such as aPSim bin locations. it is deprecated
        """

    @classmethod
    def get_aPSim_bin_path(cls):
        warnings.warn(
            f'apsimNGpy.config.Config.get_apsim_bin_path for changing apsim binary path is deprecated> use:apsimNGpy.config.get_apsim_bin_path ',
            FutureWarning)
        """We can extract the current path from config.ini"""
        return get_apsim_bin_path()

    @classmethod
    def set_aPSim_bin_path(cls, path):
        warnings.warn(
            f'apsimNGpy.config.Config.set_apsim_bin_path . class for changing apsim binary path is deprecated> use:apsimNGpy.config.set_apsim_bin_path ',
            FutureWarning)

        from pathlib import Path
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


if __name__ == '__main__':
    # example windows;
    print(get_apsim_bin_path(), 'after removing .config')
    from pathlib import Path

    print(get_apsim_bin_path())
    set_apsim_bin_path(get_apsim_bin_path())

    # # This is an example if apsim is installed at the user's directory'
    # Home_aPSim = list(Path.home().joinpath('AppData', 'Local', 'Programs').rglob('*2022.12.7130.0'))[0].joinpath('bin')
    # Config.set_apsim_bin_path(Home_aPSim)
    # print(Config.get_apsim_bin_path())
