from apsimNGpy.core import pythonet_config
from apsimNGpy.core.base_data import load_default_simulations
import Models

ADD = Models.Core.ApsimFile.Structure.Add
model = load_default_simulations(crop='maize')


def add_replacements():
    FOLDER = Models.Core.Folder()
    FOLDER.Name = "Replacements"
    # REPLACEMENTS = Models.Core.Replacements()
    PARENT = model.Simulations
    newModel = ADD(FOLDER, PARENT)
    model.run()


add_replacements()
#model.preview_simulation()
core = [i for i in dir(Models.Core)]
