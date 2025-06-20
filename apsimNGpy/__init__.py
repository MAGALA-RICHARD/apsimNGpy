from apsimNGpy.core.config import get_apsim_bin_path, set_apsim_bin_path, auto_detect_apsim_bin_path
__version__ = '0.39.3.2'

__all__ = ['get_apsim_bin_path', 'auto_detect_apsim_bin_path', 'set_apsim_bin_path', '__version__']

if get_apsim_bin_path():

    # import apsimNgpy objects associated with pythonnet

    from apsimNGpy.core import core, apsim, base_data
    from apsimNGpy.core.apsim import ApsimModel
    from apsimNGpy.optimizer import mixed, one_objective, one_obj
    from apsimNGpy.validation import evaluator, eval_methods
    from apsimNGpy.parallel.process import custom_parallel, run_apsimx_files_in_parallel, _read_result_in_parallel
    from apsimNGpy.core_utils import database_utils
    from apsimNGpy.manager.weathermanager import get_met_from_day_met, get_met_nasa_power, get_iem_by_station, get_weather


    __all__.extend(['core', 'apsim', 'get_apsim_bin_path', 'base_data','ApsimModel',
                    'mixed', 'one_objective', 'one_obj',
                    'evaluator', 'eval_methods',
                        "custom_parallel", 'run_apsimx_files_in_parallel', '_read_result_in_parallel',
                    'database_utils',
                   get_met_from_day_met.__name__, "get_met_nasa_power", "get_iem_by_station", "get_weather"])


# Define the apsimNgpy version
__version__ = '0.39.3.2'

