import configparser
from multiprocessing import cpu_count
import logging
import os

BASE_DIR = os.path.dirname(__file__)
# no need to lof this path in the package directory,as it absolute path always seems abstract
# so we send to the user home directory
# IN THAT CASE NO NEED TO IMPORT IT
CONFIG_PATH = os.path.expanduser('~/apsimNGpy_config.ini')
WGS84 = 'epsg:4326'
NUM_CORES: int = int(cpu_count() * 0.6)
SOIL_THICKNESS: list = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
CRS: str = 'EPSG:26915'
MSG  = """
ERROR: APSIM Path Not Found

It seems that the APSIM path is either not installed or not added to your environment variables.

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
   After installing APSIM, make sure to add the installation path to your environment variables. You can do this by using the following Python command:

   ```python
   from apsimNGpy.config import set_apsim_bin_path
   set_apsim_bin_path('~/your/path/to/bin')
"""
# configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler and set level
# am also sending this to the user, because logs maybe removed with removal of the package
log_file = os.path.expanduser('apsimNGpy_sim.log')
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


