from apsimNGpy.config import configuration, Path
from apsimNGpy.starter.starter import CLR
if configuration.bin_path is not None and Path(configuration.bin_path).exists():
    from apsimNGpy.core.core import CoreModel
    from apsimNGpy.core.apsim import ApsimModel
    from apsimNGpy.core.runner import run_apsim_by_path
    __all__ = ['CoreModel', 'ApsimModel', 'run_apsim_by_path']
    if CLR.file_format_modified:
        from apsimNGpy.core.experiment import ExperimentManager
        __all__ += ['ExperimentManager']
