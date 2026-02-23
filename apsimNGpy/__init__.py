"""
Do not import any module from apsimNGpy.core.core package or apsimNGpy.starter because these will raise an error if
PythoNet related modules are not yet configured or apsim_bin path not correctly set

"""

from apsimNGpy.config import (set_apsim_bin_path, get_apsim_bin_path,
                              apsim_bin_context, load_crop_from_disk, configuration, start_pythonnet, DLL_DIR,
                              CAST_OBJECT,
                              Configuration, locate_model_bin_path, scan_dir_for_bin, auto_detect_apsim_bin_path)
from apsimNGpy.logger import logger
from apsimNGpy.parallel.process import custom_parallel
from apsimNGpy.core_utils.utils import is_scalar, timer
from apsimNGpy.exceptions import ApsimRuntimeError, NodeNotFoundError, TableNotFoundError, CastCompilationError



__all__ = [
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



