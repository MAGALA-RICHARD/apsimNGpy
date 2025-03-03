from apsimNGpy.core import pythonet_config
from apsimNGpy.core.base_data import load_default_simulations
import Models

from apsimNGpy.settings import logger

ADD = Models.Core.ApsimFile.Structure.Add
FOLDER = Models.Core.Folder()
model = load_default_simulations(crop='maize')
from apsimNGpy.utililies.utils import timer


@timer
def add_replacements():
    "everything is edited in place"
    CROP = 'maize'
    FOLDER.Name = "Replacements"
    PARENT = model.Simulations
    ADD(FOLDER, PARENT)
    _crop = PARENT.FindInScope[Models.PMF.Plant](CROP)
    if _crop is not None:
        ADD(_crop, FOLDER)
    else:
        logger.error(f"No plants of crop{CROP} found")


def add_replacement_folder(_model):
    PARENT = _model.Simulations
    ADD(FOLDER, PARENT)


def add_model(parent, model_name):
    ...


def remove_model(parent, model_name):
    ...


if __name__ == '__main__':
    # test
    add_replacements()

    crop = model.Simulations.FindInScope[Models.PMF.Plant]('Soybean')
    # model.preview_simulation()
