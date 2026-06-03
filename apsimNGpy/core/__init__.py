import contextlib

from apsimNGpy import ApsimModel
from apsimNGpy.core.model_loader import get_node_by_path

with contextlib.suppress(ImportError):
    from apsimNGpy.config import configuration
    from apsimNGpy.starter.starter import CLR

    if configuration.is_bin_path_valid():
        from apsimNGpy.core.core import CoreModel
        from apsimNGpy.core.apsim import ApsimModel
        from apsimNGpy.core.runner import run_apsim_by_path

        __all__ = ['CoreModel', 'ApsimModel', 'run_apsim_by_path']
        if CLR.file_format_modified:
            from apsimNGpy.core.experiment import ExperimentManager

            __all__ += ['ExperimentManager']


