import os

from apsimNGpy.weather import daymet_bylocation_nocsv
from apsimNGpy.weather import daymet_bylocation_nocsv
from apsimNGpy.base_data import load_example_files
from apsimNGpy.model.soilmodel import SoilModel
from pathlib import Path
import os
# set the working path
cwd = Path.cwd().home()
os.chdir(cwd)
# download weather from daymet
# sample lonlat
lonlat  = -93.01183333, 42.08333333
weather  = daymet_bylocation_nocsv(lonlat, start  =1990, end =2020, filename="boone.met")
data =  load_example_files(cwd)
maize = data.get_maize
# initialise
apsim = SoilModel(maize)
# Now insert weather file into the model
apsim.replace_met_file(weather)
# check if it was successful
print(apsim.show_met_file_in_simulation())
