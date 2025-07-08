from apsimNGpy.core.config import (
    get_apsim_bin_path,
    set_apsim_bin_path,
    auto_detect_apsim_bin_path
)
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.exceptions import (
    InvalidInputErrors,
    ForgotToRunError,
    EmptyDateFrameError
)
from apsimNGpy.version import version
__version__ = version

__all__ = [
    'InvalidInputErrors',
    'ForgotToRunError',
    'EmptyDateFrameError',
    'get_apsim_bin_path',
    'auto_detect_apsim_bin_path',
    'set_apsim_bin_path',
    'timer',
    '__version__',
    'version'
]

# Conditionally import core modules that rely on APSIM binary being available
if get_apsim_bin_path():

    from apsimNGpy.core import core, apsim, base_data
    from apsimNGpy.core.apsim import ApsimModel

    from apsimNGpy.validation import evaluator, eval_methods
    from apsimNGpy.parallel.process import (
        custom_parallel,
        run_apsimx_files_in_parallel
    )
    from apsimNGpy.core_utils import database_utils
    from apsimNGpy.manager.weathermanager import (
        get_met_from_day_met,
        get_met_nasa_power,
        get_iem_by_station,
        get_weather
    )
    from apsimNGpy.optimizer.single import ContinuousVariable, MixedVariable
    from apsimNGpy.optimizer.moo import MultiObjectiveProblem

    __all__.extend([
        'core',
        'apsim',
        'base_data',
        'ApsimModel',
        'evaluator',
        'eval_methods',
        'custom_parallel',
        'run_apsimx_files_in_parallel',
        'database_utils',
        'get_met_from_day_met',
        'get_met_nasa_power',
        'get_iem_by_station',
        'get_weather',
       "ContinuousVariable",
        "MixedVariable",
        'MultiObjectiveProblem'
    ])
