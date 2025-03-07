import os

from apsimNGpy.manager import weathermanager

from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.core.apsim import ApsimModel as SoilModel
from pathlib import Path
import os

# set the working path
cwd = Path.cwd().home()
os.chdir(cwd)
CROP = "Maize"
# download weather from daymet
# sample lonlat
lonlat = -3.01183333, 42.08333333
weather = weathermanager.get_weather(lonlat, start=1990, end=2020, filename="somewhere.met", source='nasa')
data = load_default_simulations(crop=CROP, simulations_object=True)

# initialise
apsim = SoilModel(data.path)
# Now insert weather file into the model
apsim.replace_met_file(weather_file=weather)
# check if it was successful
print(apsim.show_met_file_in_simulation())
# try running
apsim.run()
# collect the results
res = apsim.results
print(res)
# save your model
apsim.save(file_name='changed_met.apsimx')
# check the saved path
print(apsim.path)
