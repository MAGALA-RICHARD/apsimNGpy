from importlib import import_module
from typing import TYPE_CHECKING

_LAZY_IMPORTS = {
    'apsim': ('apsimNGpy.tests.unittests.core.apsim', None),
    'core': ('apsimNGpy.tests.unittests.core.core', None),
    'model_tools': ('apsimNGpy.tests.unittests.core.model_tools', None),
    'model_loader': ('apsimNGpy.tests.unittests.core.model_loader', None),
    'runner': ('apsimNGpy.tests.unittests.core.runner', None),
    'core_edit_model': ('apsimNGpy.tests.unittests.core.core_edit_model', None),
    'senstivitymanager': ('apsimNGpy.tests.unittests.core.senstivitymanager', None),
    'edit_model_by_path': ('apsimNGpy.tests.unittests.core.edit_model_by_path', None),
    'experiment': ('apsimNGpy.tests.unittests.core.experiment', None),
    'starter': ('apsimNGpy.tests.unittests.starter.starter', None),
    'weathermanager': ('apsimNGpy.tests.unittests.manager.weathermanager', None),
    'soilmanager': ('apsimNGpy.tests.unittests.manager.soilmanager', None),
    'laze_import_tests': ('apsimNGpy.tests.unittests.laze_import_tests', None),
    'smp': ('apsimNGpy.tests.unittests.optimizer.smp', None),
    'vars': ('apsimNGpy.tests.unittests.optimizer.vars', None),
    'plot_manager': ('apsimNGpy.tests.unittests.core.plot_manager', None),
    'config': ('apsimNGpy.tests.unittests.core.config', None),
    'cs_resources': ('apsimNGpy.tests.unittests.core.cs_resources', None)

}

if TYPE_CHECKING:
    from apsimNGpy.tests.unittests.core import apsim  # noqa: F401
    from apsimNGpy.tests.unittests.core import model_loader  # noqa: F401
    from apsimNGpy.tests.unittests.core import model_tools  # noqa: F401
    from apsimNGpy.tests.unittests.core import runner  # noqa: F401
    from apsimNGpy.tests.unittests.core import core_edit_model  # noqa: F401
    from apsimNGpy.tests.unittests.core import senstivitymanager  # noqa: F401
    from apsimNGpy.tests.unittests.core import edit_model_by_path  # noqa: F401
    from apsimNGpy.tests.unittests.core import experiment  # noqa: F401
    from apsimNGpy.tests.unittests.starter import starter  # noqa: F401
    from apsimNGpy.tests.unittests.manager import soilmanager, weathermanager  # noqa: F401
    from apsimNGpy.tests.unittests import laze_import_tests  # noqa: F401


def __getattr__(name):
    """
    Dynamically load apsimNGpy.unittests objects on first access.

    Parameters
    ----------
    name : str
        Attribute name requested from the module.

    Returns
    -------
    object
        Imported object or module.

    Raises
    ------
    AttributeError
        If attribute does not exist.
    """

    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_name, attr_name = _LAZY_IMPORTS[name]

    module = import_module(module_name)

    value = module if attr_name is None else getattr(module, attr_name)

    # cache the object so future access is fast
    globals()[name] = value

    return value


__all__ = [*_LAZY_IMPORTS.keys()]
