import configparser
from os.path import (realpath, join, isfile, exists)

config_path = realpath('config.ini')

if not exists(config_path):
    config = configparser.ConfigParser()
    config['Paths'] = {'ApSIM_LOCATION': ''}
    with open(config_path, 'w') as configfile:
        config.write(configfile)


class Config:
    """
        The configuration module providing the leeway for the user to change the
       global variables such as aPSim bin locations.
        """

    config = configparser.ConfigParser()
    config.read(config_path)

    @classmethod
    def get_aPSim_bin_path(cls):
        """We can extract the current path from config.ini"""
        return cls.config['Paths']['ApSIM_LOCATION']

    @classmethod
    def set_aPSim_bin_path(cls, path):
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
        if _path != cls.get_aPSim_bin_path():
            Is_Model_in_bin_folder = join(_path, 'Models.exe')
            # if not, we raise assertion error because there is no point to
            # send a non-working path to the pythonnet config module
            # at this point the user may need to change to another path
            assert isfile(Is_Model_in_bin_folder), f"aPSim binaries may not be present at this location: {_path}"
            cls.config['Paths']['ApSIM_LOCATION'] = _path
            with open('config.ini', 'w') as config_file:
                cls.config.write(config_file)


if __name__ == '__main__':
    # example windows;
    from pathlib import Path

    # This is an example if apsim is installed at the user's directory'
    Home_aPSim = list(Path.home().joinpath('AppData', 'Local', 'Programs').rglob('*2022.12.7130.0'))[0].joinpath('bin')
    Config.set_aPSim_bin_path(Home_aPSim)
    print(Config.get_aPSim_bin_path())
