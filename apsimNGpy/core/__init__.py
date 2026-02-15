from apsimNGpy.config import configuration, Path
if configuration.bin_path is not None and Path(configuration.bin_path).exists():
    from apsimNGpy.core.core import CoreModel
    from apsimNGpy.core.apsim import ApsimModel
    from apsimNGpy.core.experiment import ExperimentManager

    __all__ = ['CoreModel', 'ApsimModel', 'ExperimentManager']