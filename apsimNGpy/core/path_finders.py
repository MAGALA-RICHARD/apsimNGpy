from os.path import (join, dirname)


def get_config_ini_path():
    # wanted to define it one place
    return join(dirname(dirname(__file__)), 'config.ini')

