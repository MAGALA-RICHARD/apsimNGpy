import os

from apsimNGpy.base.base_data import LoadExampleFiles
from apsimNGpy.model.soilmodel import SoilModel
from pathlib import Path
pwd = Path.home()
os.chdir(pwd)
data = LoadExampleFiles(pwd)
soil = SoilModel(data.get_maize)

sc = {"Name": 'PostharvestillageMaize', 'Fraction': 0.1}
pm = soil.update_multiple_management_decissions([sc], simulations=soil.extract_simulation_name, reload=True)
mi = soil.examine_management_info()