from multiprocessing import cpu_count
from enum import Enum

class ConstantSettings(Enum):
    
    WGS84 = 'epsg:4326'
    
    CORES = int(cpu_count() * 0.6)
    
    SOIL_THICKNESS = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
    
    CRS = 'EPSG:26915'
