"""
This module does not directly import from `apsimNGpy.core` or `apsimNGpy.starter`
to avoid errors when PythonNet is not configured or the APSIM binary path is unset.

Instead, it uses `Apsim` class to lazily load and attach the following objects:

- ApsimModel (apsimNGpy.core.apsim)
- MultiCoreManager (apsimNGpy.core.mult_cores)
- run_apsim_by_path (apsimNGpy.core.runner)
- run_sensitivity (apsimNGpy.sensitivity.sensitivity)
- ConfigProblem (apsimNGpy.sensitivity.sensitivity)
- ExperimentManager (apsimNGpy.core.experiment)
- SensitivityManager (apsimNGpy.core.sensitivitymanager)
"""

from apsimNGpy.config import (set_apsim_bin_path, get_apsim_bin_path,
                              apsim_bin_context, load_crop_from_disk, configuration, start_pythonnet, DLL_DIR,
                              Configuration, locate_model_bin_path, scan_dir_for_bin, auto_detect_apsim_bin_path)
from apsimNGpy.logger import logger
from apsimNGpy.parallel.process import custom_parallel
from apsimNGpy.core_utils.utils import is_scalar, timer
from apsimNGpy.exceptions import ApsimRuntimeError, NodeNotFoundError, TableNotFoundError, CastCompilationError

_AutoBin = object()

_doc_msg = """
            Lazy loader for APSIM components dependent on .NET environment and a valid APSIM bin path.

            Avoids direct imports from `apsimNGpy.core` and `apsimNGpy.starter`
            until PythonNet and the APSIM binary are configured.

            `ApsimRuntime` dynamically exposes:
            ApsimModel, MultiCoreManager, run_apsim_by_path,
            run_sensitivity, ConfigProblem,
            ExperimentManager, SensitivityManager.
            """


# define the run time objects inside a callable class
# that way even if the APSIM bin configuration is not set packages errors do not affect entry point
# this is a refactoring class, I did not want to reconfigure apsim_bin-context
class Apsim(apsim_bin_context):

    def __init__(self, apsim_bin_path=_AutoBin, dotenv_path=None, bin_key=None, disk_cache=None):
        if apsim_bin_path is _AutoBin and dotenv_path is None:
            apsim_bin_path = get_apsim_bin_path()
            # since we are getting from config.ini file, disk_cache should be False too
            disk_cache = False
        # another way round implies that apsim_bin_path will be retrieved on global environment variables
        super().__init__(apsim_bin_path, dotenv_path=dotenv_path, bin_key=bin_key, disk_cache=disk_cache)


# ApsimRuntime.__doc__ = _doc_msg + apsim_bin_context.__doc__

__all__ = [
    'Apsim',
    'start_pythonnet',
    "set_apsim_bin_path",
    "get_apsim_bin_path",
    "apsim_bin_context",
    "load_crop_from_disk",
    "Configuration",
    "locate_model_bin_path",
    "logger",
    "ApsimRuntimeError",
    "NodeNotFoundError",
    "TableNotFoundError",
    "CastCompilationError",
    'auto_detect_apsim_bin_path',
    'scan_dir_for_bin',
    'custom_parallel',
    'timer',
    'is_scalar',
    'configuration',
    'DLL_DIR'
]

# if __name__ == '__main__':
#     with Apsim() as runtime:
#         print(runtime.ExperimentManager)
