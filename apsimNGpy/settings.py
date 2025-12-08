import configparser
from multiprocessing import cpu_count
import logging
import os
from pathlib import Path
from shutil import rmtree

VERSION = '0.3.9.4'


class MissingType:
    def __bool__(self):
        return False

    def __repr__(self):
        return "<UserOptionMissing>"


MissingOption = MissingType()


def create_config(config_path, apsim_path=""):
    _CONFIG = configparser.ConfigParser()
    _CONFIG.read(config_path)
    _CONFIG['Paths'] = {'APSIM_LOCATION': apsim_path}
    with open(config_path, 'w') as configured_file:
        _CONFIG.write(configured_file)


def create_bin_paths_used(config_path, apsim_path=""):
    BINS = []
    _CONFIG = configparser.ConfigParser()
    _CONFIG.read(config_path)
    if _CONFIG.has_section('PreviousPaths'):
        pp = _CONFIG['PreviousPaths']
        prev = pp.get('BINS', "[]")
        binS = set(eval(prev))
        BINS = [i for i in binS if os.path.exists(i)]
        BINS = list(dict.fromkeys(BINS))
    if os.path.exists(config_path) and os.path.realpath(apsim_path) not in BINS:
        BINS.append(os.path.realpath(apsim_path))
    _CONFIG['PreviousPaths'] = dict(BINS=str(BINS))

    return _CONFIG


def config_internal(key: str, value: str) -> None:
    """Stores the apsim version and many others to be used by the app"""
    ci = configparser.ConfigParser()
    ci.read('./configs.ini')
    ci[key] = {key: value}
    with open('./configs.ini', 'w') as configured_file:
        ci.write(configured_file)


META_Dir = Path.home().joinpath('APSIMNGpy_meta_data')  # the path that will store config.ini and any logs for the user
META_Dir.mkdir(parents=True, exist_ok=True)
CONFIG_path = META_Dir.joinpath('apsimNGpy_config.ini')
CONFIG_PATH = os.path.realpath(CONFIG_path)
BASE_DIR = os.path.dirname(__file__)

if not CONFIG_path.exists():
    # let try and check if a path exists on a path and send it to the config.ini file
    apsim_bin_path = os.getenv('APSIM') or ''  # None file will not serialize
    create_config(CONFIG_PATH, apsim_bin_path)

WGS84 = 'epsg:4326'
NUM_CORES: int = int(cpu_count() * 0.6)
SOIL_THICKNESS: list = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
CRS: str = 'EPSG:26915'
MSG = """
ERROR: APSIM Path Not Found

It seems that the APSIM path is either not installed or not added to your environment _variables.

Please follow these steps to resolve the issue:

1. **Install APSIM**:  
   - If you haven't installed APSIM yet, you can download it here:  
     [APSIM Registration Page](https://registration.apsim.info/)
   - Follow the installation guidelines here:  
     [APSIM Installation Guide](https://apsimnextgeneration.netlify.app/install/)

2. **Access APSIM Tutorials**:  
   - For getting started with APSIM, check out the user tutorials:  
     [APSIM User Tutorials](https://apsimnextgeneration.netlify.app/user_tutorials/)

3. **Set APSIM Bin Path**:  
   After installing APSIM, make sure to add the installation path to your environment _variables. You can do this by using the following Python command:

   ```python
   from apsimNGpy.config import set_apsim_bin_path
   set_apsim_bin_path('~/your/path/to/bin')
"""
# configure the logger
# logger = logging.getLogger(__name__)

log_file = os.path.expanduser('~/apsimNGpy_sim.log')


def setup_logger(name: str = None, level: int = logging.INFO) -> logging.Logger:
    if name is None:
        name = log_file

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler()

        # Enhanced formatter showing file, line, function
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s'
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    return logger


logger = setup_logger()

APSIM_LOCATION = os.environ.get('APSIM_LOCATION')

SCRATCH = os.environ.get('WS', Path(os.getcwd()) / 'scratch')
# need to clean up periodically if can
try:
    SCRATCH.mkdir(parents=True, exist_ok=True)
except PermissionError:
    SCRATCH = Path.cwd()

config_internal('version', f"{VERSION}")
