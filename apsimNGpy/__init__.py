from apsimNGpy import config

import logging
if not config.get_apsim_bin_path:
    logging.info('Failed to find APSIM binary path please add APSIM binary path before you proceed')
in_modules = []
try:
    from apsimNGpy import core, replacements, manager, utililies
    from apsimNGpy.core.core import APSIMNG
    from apsimNGpy.core.apsim import ApsimModel

    in_modules= ['core', 'replacements', 'manager',
               'ApsimModel',
               'utililies', 'config','APSIMNG']
except Exception as e:
    # It's good practice to log the exception
    pass

__all__ = [*in_modules, 'config']