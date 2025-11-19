from apsimNGpy.core.apsim import ApsimModel
from os.path import realpath
from pathlib import Path
from apsimNGpy.core.config import load_crop_from_disk
Fertilise_at_sowing = '.Simulations.Simulation.Field.Fertilise at sowing'
SurfaceOrganicMatter = '.Simulations.Simulation.Field.SurfaceOrganicMatter'
Clock = ".Simulations.Simulation.Clock"
met_file = realpath(Path('wf.met'))
met_file = load_crop_from_disk('AU_Goondiwindi', out=met_file, suffix= '.met')
Weather = '.Simulations.Simulation.Weather'
Organic = '.Simulations.Simulation.Field.Soil.Organic'


with ApsimModel('Maize') as apsim:
    apsim.inspect_file()
    apsim.edit_model_by_path(Fertilise_at_sowing, Amount = 12)
    apsim.edit_model_by_path(Clock, start_date = '01/01/2020')
    apsim.edit_model_by_path(SurfaceOrganicMatter,InitialCNR=100)
    apsim.edit_model_by_path(Weather, weather_file = realpath(met_file))
    apsim.edit_model_by_path(Organic, Carbon =1.23)
    apsim.inspect_model_parameters_by_path(Organic)
    node= apsim.get_replacements_node()
    # test dict
    apsim.edit_model_by_path(**dict(path=Organic, Carbon=1.2))
    cc=apsim.inspect_model_parameters_by_path(Organic)
    apsim.set_params(dict(path=Organic, Carbon=1.58))

