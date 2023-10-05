from os.path import dirname, realpath
import sys
class Config:
    """
    for declaring global variables.
    """

    # the root directory where the apimNGpy package is located at
    root = dirname(realpath(__file__))

    warnings = {
        "no_compilation": True
    }

    # whether a warning should be printed if compiled modules are not available
    compilation = True

# returns the directory to be used for imports
def get_apsimngpy():
    return dirname(Config.root)
# add to path
def add_apsimngpy_topath():
    path = get_apsimngpy()
    print(path)
    sys.path.extend([path])

