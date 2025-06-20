import os.path
import sys

sys.path.append(os.path.realpath(".."))

__all__= []
try:
    from apsimNGpy import core, manager, core_utils
    from apsimNGpy.core import core
    from apsimNGpy.core.apsim import ApsimModel

    __all__.extend(['core', 'replacements', 'manager',
                       'ApsimModel',
                       'core_utils', 'config'])

except (ImportError, ModuleNotFoundError) as e: # expected errors if pythonnet fails to get initialized

    pass


