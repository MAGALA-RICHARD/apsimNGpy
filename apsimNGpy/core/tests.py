import glob
import os,sys
import platform
from apsimNGpy.config import Config
current_path  = os.path.dirname(os.path.abspath(__file__))

sys.path.append(current_path)
sys.path.append(os.path.dirname(current_path))
from pythonet_config import GetAPSIMPath

# auto detect
loaded = GetAPSIMPath()
loaded.auto_detect()
print(current_path)
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