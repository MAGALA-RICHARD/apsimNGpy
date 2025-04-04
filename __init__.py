from apsimNGpy.core.config import get_apsim_bin_path, set_apsim_bin_path, auto_detect_apsim_bin_path
__all__ = ['get_apsim_bin_path', 'auto_detect_apsim_bin_path', 'set_apsim_bin_path']
if get_apsim_bin_path():
    from apsimNGpy.core import core, apsim, structure, base_data

    __all__.extend(['core', 'apsim', 'get_apsim_bin_path', 'base_data', 'structure'])
