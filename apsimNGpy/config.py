import configparser
from os.path import (realpath, join, isfile, exists)
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


def get_apsim_binary_path():
    config = configparser.ConfigParser()
    from os.path import join
    config_path = join(os.path.dirname(__file__), 'config.ini')
    config.read(config_path)
    APSIM_LOC = config['Paths']['APSIM_LOCATION']
    # JUST ENSURE THAT THE FILE EXISTS 1. AND THEN ENSURE IT HAS THE CONFIG, We should not catch any error HERE.
    # What we do is check if the APSIM PATH IS VALID.
    # one advantage of encapsulating logic in method is you can control when they are called.
    return APSIM_LOC


def load_python_net():
    """
    This function belongs to the config at the root. It will replace the need for the class
    """
    start_pythonnet()
    # use get because it does not raise key error. it returns none if not found
    APSIM_PATH = get_apsim_binary_path()

    if 'bin' not in APSIM_PATH:
        APSIM_PATH = os.path.join(APSIM_PATH, 'bin')

    if not os.path.exists(APSIM_PATH):
        raise ValueError("A full path to the binary folder is required or the path is invalid")

    sys.path.append(APSIM_PATH)

    import clr
    _sys = clr.AddReference("System")
    _lm = clr.AddReference("Models")


