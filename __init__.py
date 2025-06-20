from apsimNGpy.core.config import get_apsim_bin_path, set_apsim_bin_path, auto_detect_apsim_bin_path

__all__ = ['get_apsim_bin_path', 'auto_detect_apsim_bin_path', 'set_apsim_bin_path']
if get_apsim_bin_path():
    # import apsimNgpy objects
    from apsimNGpy.core import core, apsim, base_data
    from apsimNGpy.optimizer import mixed, one_objective, one_obj

    __all__.extend(['core', 'apsim', 'get_apsim_bin_path', 'base_data',
                    'mixed', 'one_objective', 'one_obj,variables'])


# Define the apsimNgpy version
__version__ = '0.39.3.2'

