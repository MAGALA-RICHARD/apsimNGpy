
from config import get_apsim_bin_path, set_apsim_bin_path

configured = get_apsim_bin_path()

in_modules =  ['get_apsim_bin_path',  'set_apsim_bin_path', 'auto_detect_apsim_bin_path']

try:
    from apsimNGpy import core, replacements, manager, utililies
    from apsimNGpy.core.core import APSIMNG
    from apsimNGpy.core.apsim import ApsimModel

    in_modules.extend(['core', 'replacements', 'manager',
                       'ApsimModel',
                       'utililies', 'config', 'APSIMNG'])

except Exception as e:

    pass

__all__ = in_modules
