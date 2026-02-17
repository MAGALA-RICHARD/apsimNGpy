try:
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
except Exception as ex:
  pass
