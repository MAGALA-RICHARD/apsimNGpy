import configparser
import os
import warnings
from os.path import (realpath, join, isfile, exists)
from apsimNGpy.core.path_finders import search_from_programs, search_from_users, _apsim_model_is_installed, auto_searched

config_path = realpath('config.ini')
CONFIG = configparser.ConfigParser()
CONFIG.read(config_path)
if not exists(config_path):
    CONFIG = configparser.ConfigParser()
    put_default_path  = auto_searched or " "
    CONFIG['Paths'] = {'ApSIM_LOCATION': put_default_path}
    with open(config_path, 'w') as configured_file:
        CONFIG.write(configured_file)


def get_aPSim_bin_path():
        """We can extract the current path from config.ini"""
        return CONFIG['Paths']['ApSIM_LOCATION']


def set_aPSim_bin_path(path):
    from pathlib import Path
    """ Send your desired path to the aPSim binary folder to the config module
    the path should end with bin as the parent directory of the aPSim Model.exe
    >> Please be careful with adding an uninstalled path, which do not have model.exe file.
    It won't work and python with throw an error
    >> example from apsimNGpy.config import Config
    # check the current path
     config = Config.get_aPSim_bin_path()
     # set the desired path
     >> Config.set_aPSim_bin_path(path = '/path/to/aPSimbinaryfolder/bin')
    """
    _path = realpath(path)
    path_to_search = Path(_path)
    model_files = list(path_to_search.glob('*Models.*'))
    # we also dont want to send a path does not work
    if not path_to_search.is_dir() or not path_to_search.exists():
        raise FileNotFoundError(f"{path} is not a directory or does not exists")

    if _path != get_aPSim_bin_path():
        # if not, we raise assertion error because there is no point to
        # send a non-working path to the pythonnet config module
        # at this point the user may need to change to another path
        if not model_files:
            raise ValueError(f"aPSim binaries may not be present at this location: {_path}")
        CONFIG['Paths']['ApSIM_LOCATION'] = _path
        with open('config.ini', 'w') as config_file:
            CONFIG.write(config_file)



class Config:
    """
        The configuration class providing the leeway for the user to change the
       global variables such as aPSim bin locations. it is deprecated
        """

    @classmethod
    def get_aPSim_bin_path(cls):
        warnings.warn(f'apsimNGpy.config.Config.get_aPSim_bin_path for changing apsim binary path is deprecated> use:apsimNGpy.config.get_aPSim_bin_path ', FutureWarning)
        """We can extract the current path from config.ini"""
        return get_aPSim_bin_path()

    @classmethod
    def set_aPSim_bin_path(cls, path):
        warnings.warn(f'apsimNGpy.config.Config.set_aPSim_bin_path . class for changing apsim binary path is deprecated> use:apsimNGpy.config.set_aPSim_bin_path ', FutureWarning)

        from pathlib import Path
        """ Send your desired path to the aPSim binary folder to the config module
        the path should end with bin as the parent directory of the aPSim Model.exe
        >> Please be careful with adding an uninstalled path, which do not have model.exe file.
        It won't work and python with throw an error
        >> example from apsimNGpy.config import Config
        # check the current path
         config = Config.get_aPSim_bin_path()
         # set the desired path
         >> Config.set_aPSim_bin_path(path = '/path/to/aPSimbinaryfolder/bin')
        """
        _path = realpath(path)
        return set_aPSim_bin_path(_path)


if __name__ == '__main__':
    # example windows;
    from pathlib import Path

    ax = auto_searched

    Config.set_aPSim_bin_path(ax)

    # # This is an example if apsim is installed at the user's directory'
    # Home_aPSim = list(Path.home().joinpath('AppData', 'Local', 'Programs').rglob('*2022.12.7130.0'))[0].joinpath('bin')
    # Config.set_aPSim_bin_path(Home_aPSim)
    # print(Config.get_aPSim_bin_path())
