from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.settings import logger
from apsimNGpy.core.inspector import Inspector
CROP = 'Maize'
# load the default model

scriptName = 'Sow using a variable rule'
model = load_default_simulations(crop = CROP)
# first, we will start off by inspecting the manager scripts in the simulations
scripts = model.get_manager_ids(verbose=True) # this gets full path to each manager scripts

# inspect one of the script here
params = model.get_manager_parameters(full_path='.Simulations.Simulation.Field.Sow using a variable rule',
                                      verbose=True)

# we need to update population, RainDays in this scrip manager with path '.Simulations.Simulation.Field.Sow using a variable rule'
model.update_mgt_by_path(path ='.Simulations.Simulation.Field.Sow using a variable rule', fmt='.',
                         Population =6.75, RainDays=10 ) #notice any arguement after must match the parameters spelling and the cases
# inspect again
model.get_manager_parameters(full_path='.Simulations.Simulation.Field.Sow using a variable rule', verbose=True)



