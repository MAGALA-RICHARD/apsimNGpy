from apsimNGpy.core import pythonet_config
from apsimNGpy.core.base_data import load_default_simulations
import Models

from apsimNGpy.settings import logger

ADD = Models.Core.ApsimFile.Structure.Add
FOLDER = Models.Core.Folder()
model = load_default_simulations(crop='maize')
from apsimNGpy.utililies.utils import timer


@timer
def add_replacements(_model):
    FOLDER = Models.Core.Folder()
    "everything is edited in place"
    CROP = 'maize'
    FOLDER.Name = "Replacements"
    PARENT = _model.Simulations
    ADD(FOLDER, PARENT)
    _crop = PARENT.FindInScope[Models.PMF.Plant](CROP)
    if _crop is not None:
        ADD(_crop, FOLDER)
    else:
        logger.error(f"No plants of crop{CROP} found")


def add_replacement_folder(_model):
    PARENT = _model.Simulations
    ADD(FOLDER, PARENT)


def add_model(_model, model_name, where):
    parent = _model.Simulations.FindInScope(where)
    return parent



def remove_model(_model, parent, model_name):
    ...


if __name__ == '__main__':
    # test
    add_replacements(model)

    crop = model.Simulations.FindInScope[Models.PMF.Plant]('Soybean')
    # model.preview_simulation()
