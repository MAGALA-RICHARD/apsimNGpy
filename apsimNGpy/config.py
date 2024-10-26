import configparser
import os
import warnings
from os.path import (realpath, join, isfile, exists)

config_path = realpath('config.ini')
CONFIG = configparser.ConfigParser()
CONFIG.read(config_path)
if not exists(config_path):
    CONFIG = configparser.ConfigParser()
    CONFIG['Paths'] = {'ApSIM_LOCATION': ''}
    with open(config_path, 'w') as configfile:
        CONFIG.write(configfile)


def get_aPSim_bin_path():
        """We can extract the current path from config.ini"""
        from_sys = os.getenv('Models') or os.getenv('APSIM')
        return CONFIG['Paths']['ApSIM_LOCATION'] or from_sys or " "


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
    warnings.warn('Config class for changing apsim binary path is deprecated', UserWarning)
    @classmethod
    def get_aPSim_bin_path(cls):
        """We can extract the current path from config.ini"""
        from_sys = os.getenv('Models') or os.getenv('APSIM')
        return cls.config['Paths']['ApSIM_LOCATION'] or from_sys or " "

    @classmethod
    def set_aPSim_bin_path(cls, path):
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

        if _path != cls.get_aPSim_bin_path():
            Is_Model_in_bin_folder = join(_path, 'Models.exe')
            # if not, we raise assertion error because there is no point to
            # send a non-working path to the pythonnet config module
            # at this point the user may need to change to another path
            if not model_files:
                raise ValueError(f"aPSim binaries may not be present at this location: {_path}")
            cls.config['Paths']['ApSIM_LOCATION'] = _path
            with open('config.ini', 'w') as config_file:
                cls.config.write(config_file)


if __name__ == '__main__':
    # example windows;
    from pathlib import Path

    ax = 'C:\\Program Files\\APSIM2024.5.7493.0\\bin'

    Config.set_aPSim_bin_path(ax)

    # # This is an example if apsim is installed at the user's directory'
    # Home_aPSim = list(Path.home().joinpath('AppData', 'Local', 'Programs').rglob('*2022.12.7130.0'))[0].joinpath('bin')
    # Config.set_aPSim_bin_path(Home_aPSim)
    # print(Config.get_aPSim_bin_path())
