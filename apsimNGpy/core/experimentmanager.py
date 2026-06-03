from apsimNGpy.core.experiment import CLR
from apsimNGpy.logger import logger
if not CLR.file_format_modified:
    logger.warning(f'module experimentmanager is not supported under this {CLR.apsim_compiled_version}')
else:
    from apsimNGpy.core.experiment import ExperimentManager
    __all__ = ['ExperimentManager']
