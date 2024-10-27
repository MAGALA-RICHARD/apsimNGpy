import configparser
import os
import warnings
from os.path import (realpath, join, isfile, exists, dirname)

from apsimNGpy.core.path_finders import  _apsim_model_is_installed, auto_detect_apsim_bin_path

config_path =join(dirname(__file__), 'config.ini')
from apsimNGpy import CONFIG_PATH as config_path
CONFIG = configparser.ConfigParser()
CONFIG.read(config_path)

def __create_config(apsim_path = ""):
    CONFIG = configparser.ConfigParser()
    put_default_path  = apsim_path
    CONFIG['Paths'] = {'ApSIM_LOCATION': put_default_path}
    with open(config_path, 'w') as configured_file:
        CONFIG.write(configured_file)

def get_aPSim_bin_path():
    """We can extract the current path from config.ini"""
    CONFIG = configparser.ConfigParser()
    CONFIG.read(config_path)
    return CONFIG['Paths']['ApSIM_LOCATION']

if not exists(config_path):
    auto_searched = auto_detect_apsim_bin_path()
    __create_config(apsim_path=auto_searched)

if not get_aPSim_bin_path():
    auto_searched = auto_detect_apsim_bin_path()
    __create_config(apsim_path=auto_searched)

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
    if not _apsim_model_is_installed(_path):
        raise ValueError(f"files might have been uninstalled at this location{_path}")
    if _path != get_aPSim_bin_path():
        # if not, we raise assertion error because there is no point to
        # send a non-working path to the pythonnet config module
        # at this point the user may need to change to another path
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
    print(get_aPSim_bin_path(), 'after removing .config')
    from pathlib import Path
    print (get_aPSim_bin_path())



    # # This is an example if apsim is installed at the user's directory'
    # Home_aPSim = list(Path.home().joinpath('AppData', 'Local', 'Programs').rglob('*2022.12.7130.0'))[0].joinpath('bin')
    # Config.set_aPSim_bin_path(Home_aPSim)
    # print(Config.get_aPSim_bin_path())
