import os
import sys as system
import pythonnet
from apsimNGpy.core import config
aPSim_PATH = config.get_apsim_bin_path()

def start_pythonnet():
    try:
        if pythonnet.get_runtime_info() is None:
            return pythonnet.load("coreclr")
    except:
        print("dotnet not found, trying alternate runtime")
        return pythonnet.load()


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

    MMODELSS = clr.AddReference("Models")
    apsimNG = clr.AddReference('ApsimNG')

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


# Example usage:
if __name__ == '__main__':
    loader = load_pythonnet()
    loaded_models = loader
    # try importing the C# models and see if the process is successful
