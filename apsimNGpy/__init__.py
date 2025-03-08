import os.path
import sys

sys.path.append(os.path.realpath(".."))

in_modules = []
try:
    from apsimNGpy import core, replacements, manager, core_utils
    from apsimNGpy.core.core import APSIMNG
    from apsimNGpy.core.apsim import ApsimModel

    in_modules.extend(['core', 'replacements', 'manager',
                       'ApsimModel',
                       'core_utils', 'config', 'APSIMNG'])

except Exception as e:

    pass

__all__ = in_modules
