import warnings

from apsimNGpy import config
from config import get_apsim_bin_path, auto_detect_apsim_bin_path, create_config, set_apsim_bin_path

configured = get_apsim_bin_path() or auto_detect_apsim_bin_path() or ''
if not configured:
    warnings.warn('APSIM installation binary path not detected. Please use apsimNGpy.set_apsim_bin_path method to set '
                  'it', UserWarning)

create_config(apsim_path=configured)

in_modules = ['get_apsim_bin_path', 'set_apsim_bin_path']

try:
    from apsimNGpy import core, replacements, manager, utililies
    from apsimNGpy.core.core import APSIMNG
    from apsimNGpy.core.apsim import ApsimModel

    in_modules = ['core', 'replacements', 'manager',
                  'ApsimModel',
                  'utililies', 'config', 'APSIMNG']
except Exception as e:
    # It's good practice to log the exception
    pass

__all__ = [*in_modules, 'config']
