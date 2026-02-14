from apsimNGpy.config import configuration
if configuration.bin_path is not  None:
    from apsimNGpy.core.core import CoreModel
    from apsimNGpy.core.apsim import ApsimModel
    from apsimNGpy.core.experiment import ExperimentManager

    __all__ = ['CoreModel', 'ApsimModel']