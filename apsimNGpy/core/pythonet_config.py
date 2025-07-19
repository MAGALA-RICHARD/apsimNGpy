import os
import sys as system
import clr
from apsimNGpy.core import config
from apsimNGpy.core_utils.cs_utils import start_pythonnet
from pathlib import Path

aPSim_PATH = config.get_apsim_bin_path()

start_pythonnet()


def is_file_format_modified():
    """
    Checks if the APSIM.CORE.dll is present in the bin path
    @return: bool
    """
    path = list(Path(aPSim_PATH).rglob("*APSIM.CORE.dll"))
    if len(path) > 0:
        return True
    return False


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
    start_pythonnet()
    # use get because it does not raise key error. it returns none if not found
    aPSim_path = aPSim_PATH
    if not aPSim_path:
        raise KeyError("APSIM is not loaded in the system environmental variable")
    if 'bin' not in aPSim_path:
        aPSim_path = os.path.join(aPSim_path, 'bin')
    system.path.append(aPSim_path)
    import clr
    start_pythonnet()
    SYSTEM = clr.AddReference("System")
    model_path = os.path.join(aPSim_path, 'Models.dll')
    MMODELSS = clr.AddReference(model_path)
    # apsimNG = clr.AddReference('ApsimNG')

    if is_file_format_modified():
        APSIM = clr.AddReference('APSIM.Core')

    # return lm, sys, pythonnet.get_runtime_info()


load_pythonnet()
# now we can safely import C# libraries

from System.Collections.Generic import *
from Models.Core import Simulation

from Models.Climate import Weather
from Models.Soils import Soil, Physical
import Models

from System import *

Models = Models

def get_apsim_file_reader( method:str='string'):

    if is_file_format_modified() or  not getattr(Models.Core.ApsimFile, "FileFormat", None):
        import APSIM.Core
        base = APSIM.Core.FileFormat
        os.environ['A'] = 'true'
    else:
        base = Models.Core.ApsimFile.FileFormat
    match method:
        case 'string':
            return getattr(base, 'ReadFromString')
        case 'file':
            return getattr(base, 'ReadFromFile')
        case _:
            raise NotImplementedError(f"{method} method is not implemented")

def get_apsim_file_writer():

    if is_file_format_modified() or  not getattr(Models.Core.ApsimFile, "FileFormat", None):
        import APSIM.Core
        base = APSIM.Core.FileFormat
        os.environ['A'] = 'true'
    else:
        base = Models.Core.ApsimFile.FileFormat
    return getattr(base, 'WriteToString')
# Example usage:
if __name__ == '__main__':
    loader = load_pythonnet()
    loaded_models = loader

