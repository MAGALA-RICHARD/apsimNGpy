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
        The configuration of this aPSimNGpy in general providing the place
        for declaring global variables such as aPSim bin locations.
        """

    config = configparser.ConfigParser()
    config.read(config_path)

    @classmethod
    def get_aPSim_bin_path(cls):
        return cls.config['Paths']['ApSIM_LOCATION']

    @classmethod
    def set_aPSim_bin_path(cls, path):
        _path = realpath(path)
        if _path != cls.get_aPSim_bin_path():
            Is_Model_in_bin_folder = join(_path, 'Models.exe')
            # if not, we raise assertion error
            assert isfile(Is_Model_in_bin_folder), f"aPSim binaries may not be present at this location: {_path}"
            cls.config['Paths']['ApSIM_LOCATION'] = _path
            with open('config.ini', 'w') as config_file:
                cls.config.write(config_file)


if __name__ == '__main__':
    # example windows;
    from pathlib import Path

    Home_aPSim = list(Path.home().joinpath('AppData', 'Local', 'Programs').rglob('*2022.12.7130.0'))[0].joinpath('bin')
    Config.set_aPSim_bin_path(Home_aPSim)
    print(Config.get_aPSim_bin_path())
