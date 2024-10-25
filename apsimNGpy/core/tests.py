import glob
import platform
from apsimNGpy.config import Config
if platform.system() == 'Darwin':
    # Define the pattern
    pattern = '/Applications/APSIM*.app/Contents/Resources/bin'

    # Use glob to find matching paths
    matching_paths = glob.glob(pattern)

    # Output the results
    for path in matching_paths:
        print(path)
    if path[0]:
        Config.set_aPSim_bin_path(path)