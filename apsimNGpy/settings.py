from multiprocessing import cpu_count
import logging
import os

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, 'data')

WGS84 = 'epsg:4326'
NUM_CORES: int = int(cpu_count() * 0.6)
SOIL_THICKNESS: list = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
CRS: str = 'EPSG:26915'

# configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler and set level

log_file = 'apsimNGpy_sim.log'
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create file handler and set level
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Create formatter and set it for both handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

APSIM_LOCATION = os.environ.get('APSIM_LOCATION')


