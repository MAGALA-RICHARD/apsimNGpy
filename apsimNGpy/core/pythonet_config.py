import glob
import json
import os
import shutil
from dataclasses import dataclass
from functools import cache
from pathlib import Path
import platform
import pythonnet
from apsimNGpy.config import get_aPSim_bin_path
from apsimNGpy.utililies.utils import (timer, find_models)

@cache
def collect_apsim_path():
    """searches for an apsimx path
        Find the aPSim installation path using the os module.
        If aPSim was installed, it is possible the path is added to the os.environ
        but first we first check is the user has sent their own path, and then we proceed to check to already added path
        @return: unix or windows path
          --- if found, or False if not found.

        """
    from_config = get_aPSim_bin_path()
    configured = from_config if os.path.exists(from_config) else None
    return configured


aPSim_PATH = get_aPSim_bin_path()


def start_pythonnet():
    try:
        if pythonnet.get_runtime_info() is None:
            return pythonnet.load("coreclr")
    except:
        print("dotnet not found, trying alternate runtime")
        return pythonnet.load()


@cache
def load_pythonnet():
    """
    A method for loading Python for .NET (pythonnet) and APSIM models.

    This class provides a callable method for initializing the Python for .NET (pythonnet) runtime and loading APSIM models.
    Initialize the Python for .NET (pythonnet) runtime and load APSIM models.

        This method attempts to load the 'coreclr' runtime, and if not found, falls back to an alternate runtime.
        It also sets the APSIM binary path, adds necessary references, and returns a reference to the loaded APSIM models.

        Returns:
        -------
        lm: Reference to the loaded APSIM models

        Raises:
        ------
        KeyError: If APSIM path is not found in the system environmental variable.
        ValueError: If the provided APSIM path is invalid.

        Notes:
        It raises a KeyError if APSIM path is not found. Please edit the system environmental variable on your computer.
    Attributes:
    ----------
    None
    """


    _aPSim_Path = aPSim_PATH

    # try:
    #     if pythonnet.get_runtime_info() is None:
    #         pythonnet.load("coreclr")
    # except:
    #     print("dotnet not found, trying alternate runtime")
    #     pythonnet.load()
    start_pythonnet()
    # use get because it does not raise key error. it returns none if not found
    aPSim_path = aPSim_PATH
    if not aPSim_path:
        raise KeyError("APSIM is not loaded in the system environmental variable")
    if 'bin' not in aPSim_path:
        aPSim_path = os.path.join(aPSim_path, 'bin')

    import sys
    sys.path.append(aPSim_path)
    import clr
    sys = clr.AddReference("System")
    lm = clr.AddReference("Models")

        # return lm, sys, pythonnet.get_runtime_info()

load_pythonnet()

# Example usage:
if __name__ == '__main__':
    loader = load_pythonnet()
    loaded_models = loader
    import Models
    # try importing the C# models and see if the process is successful
