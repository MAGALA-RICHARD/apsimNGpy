import configparser
import configparser
import os
from os.path import (realpath, join, isfile, exists)
import sys

import pythonnet


def start_pythonnet():
    try:
        if pythonnet.get_runtime_info() is None:
            return pythonnet.load("coreclr")
    except Exception as e:
        print("dotnet not found, trying alternate runtime", repr(e))
        return pythonnet.load()


# I believe this file should be generated automatically during any time the module is recalled.
# So, we check if it exists first
# I also noticed you've provided a manual option, but after installation,
# the package paths are usually abstracted.
# Therefore, I am implementing an automatic method to handle this.

CONFIG = configparser.ConfigParser()
config_path = join(os.path.dirname(__file__), 'config.ini')
if not exists(config_path):
    with open(config_path, 'w') as cfp:
        CONFIG.write(cfp)
CONFIG.read(config_path)


def get_apsim_binary_path():
    APSIM_LOC = CONFIG['Paths']['APSIM_LOCATION']
    # strict evaluation
    if not exists(APSIM_LOC) and not APSIM_LOC.endswith('bin') and 'APSIM' not in APSIM_LOC:
        return None
    # JUST ENSURE THAT THE FILE EXISTS 1. AND THEN ENSURE IT HAS THE CONFIG, We should not catch any error HERE.
    # What we do is check if the APSIM PATH IS VALID.
    # one advantage of encapsulating logic in method is you can control when they are called.
    return APSIM_LOC


def change_apsim_bin_path(apsim_binary_path):
    if 'Paths' not in CONFIG:
        CONFIG['Paths'] = {}
    CONFIG['Paths']['APSIM_LOCATION'] = apsim_binary_path
    with open(config_path, 'w') as configfile:
        CONFIG.write(configfile)


def load_python_net():
    """
    This function belongs to the config at the root. It will replace the need for the class
    """
    start_pythonnet()
    # use get because it does not raise key error. it returns none if not found
    APSIM_PATH = get_apsim_binary_path() or os.getenv('APSIM') or os.getenv('Models')
    if 'bin' not in APSIM_PATH:
        APSIM_PATH = os.path.join(APSIM_PATH, 'bin')

    if not os.path.exists(APSIM_PATH):
        raise ValueError("A full path to the binary folder is required or the path is invalid")

    sys.path.append(APSIM_PATH)
    os.environ['APSIM_BIN_LOCATION'] = APSIM_PATH

    import clr
    _sys = clr.AddReference("System")
    _lm = clr.AddReference("Models")


def version():
    """
    get the version of the APSIM model currently installed and available for apsimNGpy to run
    """
    # we split the apsim binary path
    _bin_path = get_apsim_binary_path() or os.getenv('APSIM') or os.getenv('Models')
    # if the path does not end with bin, then the code below will fail miserably so, we check it
    if _bin_path and os.path.exists(_bin_path) and _bin_path.endswith('bin'):
        path, _ = os.path.split(get_apsim_binary_path())
        _complete_version = os.path.basename(path)
        # split the path
        # _splits = _complete_version.split('.')
        # year = int(_splits[0].strip('APSIM'))
        # print(year)
        return _complete_version


load_python_net()
if __name__ == '__main__':
    start_pythonnet()
    change_apsim_bin_path(r'C:\Program Files\APSIM2024.5.7493.0\bin')
    x = get_apsim_binary_path()
    load_python_net()
