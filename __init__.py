from os.path import (join, realpath, dirname)
import warnings
from config import get_apsim_bin_path, auto_detect_apsim_bin_path, create_config, set_apsim_bin_path
configured = get_apsim_bin_path() or auto_detect_apsim_bin_path() or ''
if not configured:
    warnings.warn('APSIM installation binary path not detected. Please use apsimNGpy.set_apsim_bin_path method to set '
                  'it', UserWarning)
create_config(apsim_path=configured)

__all__ = ['get_apsim_bin_path', 'set_apsim_bin_path', 'join']