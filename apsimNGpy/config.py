import configparser
import os

config_path = os.path.realpath('config.ini')

if not os.path.exists(config_path):
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
        cls.config['Paths']['ApSIM_LOCATION'] = path
        with open('config.ini', 'w') as configfile:
            cls.config.write(configfile)


if __name__ == '__main__':
    print(Config.get_aPSim_bin_path())
