from apsimNGpy.weather import daymet_bylocation_nocsv
from apsimNGpy.base_data import load_example_files
from apsimNGpy.model.soilmodel import SoilModel
from pathlib import Path
# this will be the path to your user profile. Mine is C:\Users\rmagala. feel free to change
cwd = Path.cwd().home()
# get sample apsimx file
data = load_example_files(cwd)
maize = data.get_maize
# initialise the model
apsim = SoilModel(maize)
# run the model
apsim.run_edited_file()
# collect the results from the model
res = apsim.results
print(res)