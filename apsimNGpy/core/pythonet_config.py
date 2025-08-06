import os
import sys as system
from apsimNGpy.core import config
from apsimNGpy.core.cs_resources import start_pythonnet
from pathlib import Path
from apsimNGpy.exceptions import ApsimBinPathConfigError
from apsimNGpy.core_utils.utils import timer

APSIM_BIN_PATH = config.get_apsim_bin_path()

start_pythonnet()


def is_file_format_modified():
    """
    Checks if the APSIM.CORE.dll is present in the bin path
    @return: bool
    """
    path = list(Path(APSIM_BIN_PATH).rglob("*APSIM.CORE.dll"))
    if len(path) > 0:
        return True
    return False


def load_pythonnet(bin_path=APSIM_BIN_PATH):
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

    if not os.path.isdir(bin_path):
        raise ApsimBinPathConfigError(
            "Bin path configuration error or APSIM is not yet installed, or APSIM was recently uninstalled")

    candidate = os.path.join(bin_path, 'bin')
    if os.path.basename(bin_path).lower() != 'bin' and os.path.isdir(candidate):
        bin_path = candidate

    system.path.append(bin_path)

    import clr
    start_pythonnet()
    clr.AddReference("System")
    # model_path = os.path.join(bin_path, 'Models.dll')
    # clr.AddReference(model_path)
    # apsimNG = clr.AddReference('ApsimNG')
    clr.AddReference("Models")
    if is_file_format_modified():
        clr.AddReference('APSIM.Core')

    # return lm, sys, pythonnet.get_runtime_info()


load_pythonnet()
# now we can safely import C# libraries

from System.Collections.Generic import *
from Models.Core import Simulation

import Models

from System import *

Models = Models



def get_apsim_file_reader(method: str = 'string'):
    if is_file_format_modified() or not getattr(Models.Core.ApsimFile, "FileFormat", None):
        import APSIM.Core
        base = APSIM.Core.FileFormat

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
    if is_file_format_modified() or not getattr(Models.Core.ApsimFile, "FileFormat", None):
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
