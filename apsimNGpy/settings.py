from multiprocessing import cpu_count
import logging


WGS84 = 'epsg:4326'
NUM_CORES: int = int(cpu_count() * 0.6)
SOIL_THICKNESS = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
CRS = 'EPSG:26915'

# configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(console_level)

console_handler = logging.StreamHandler()
console_handler.setLevel(console_level)

# Create file handler and set level
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(file_level)

# Create formatter and set it for both handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


