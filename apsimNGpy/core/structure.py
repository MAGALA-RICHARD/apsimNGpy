from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.core.apsim import ApsimModel
import Models
from apsimNGpy.settings import logger

# manipulation methods
ADD = Models.Core.ApsimFile.Structure.Add
DELETE = Models.Core.ApsimFile.Structure.Delete
MOVE = Models.Core.ApsimFile.Structure.Move
RENAME = Models.Core.ApsimFile.Structure.Rename
REPLACE = Models.Core.ApsimFile.Structure.Replace

FOLDER = Models.Core.Folder()
model = load_default_simulations(crop='maize')
from apsimNGpy.core_utils.utils import timer


@timer
def add_crop_replacements(_model, _crop):
    _FOLDER = Models.Core.Folder()
    "everything is edited in place"
    CROP = _crop
    _FOLDER.Name = "Replacements"
    PARENT = _model.Simulations
    ADD(_FOLDER, PARENT)
    _crop = PARENT.FindInScope[Models.PMF.Plant](CROP)
    if _crop is not None:
        ADD(_crop, _FOLDER)
    else:
        logger.error(f"No plants of crop{CROP} found")


def add_replacement_folder(_model):
    PARENT = _model.Simulations
    ADD(FOLDER, PARENT)


def add_model(_model, model_name, where):
    sims = _model.Simulations
    # sims.FindByPath(modelToCheck.Parent.FullPath + "." + newName)
    where = where.capitalize()
    parent = _model.Simulations.FindInScope(where)
    if parent is not None:
        ADD(Models.Core.Clock(), sims)
        logger.info(f"Added {where} to {parent.Name}")
    return parent



def find_model(model_name)-> Models:
    """"
    Find a model from the Models NameSpace
    returns a path to the Models NameSpace
    Example:
        >>> find_model("Weather")
         Models.Climate.Weather
        >>> find_model("Clock")
          Models.Clock


    """
    model =Models
    att = model_name
    if not hasattr(model, "__dict__"):
        return None  # Base case: Not an object with attributes

    mds = model.__dict__

    if att in mds:

      obj = mds[att]
      if isinstance(obj, type(Models.Clock)):# we are looking for models in this type; modules and fields no
         return mds[att]
    # Recursively check nested objects
    for attr, value in mds.items():
        if hasattr(value, "__dict__"):  # Ensure it's an object
            result = extract(value, att)
            if result is not None:
                return result

    return None  # Attribute not found
def add(_model, model_name, where, **kwargs):
    """
    Add a model to the Models Simulations NameSpace. some models are tied to specific models, so they can only be added
    to that models an example, we cant add Clock model to Soil Model
    @param _model: apsimNGpy.core.apsim object
    @param model_name: string name of the model
    @param where: loction along the Models Simulations nodes or children to add the model e.g at Simulation,
    @return: none, model are modified in place, so the modified object has the same reference pointer as the _model
    """
    sims = _model.Simulations
    # find where to add the model
    parent = _model.Simulations.FindInScope(where)
    which = find_model(model_name)
    if which is not None:
        ADD(which(), parent)
        logger.info(f"Added {which().Name} to {parent.Name}")
def remove_model(_model, model_name):
    """
    Remove a model from the Models Simulations NameSpace
    @param _model: apsimNgpy.core.model model object
    @param model_name: name of the model e.g Clock
    @return: None
    """
    imodel = _model.Simulations.Parent.FullPath + model_name
    DELETE(_model.Simulations.FindInScope(model_name))

    ...


import System

DataView = System.Data
if __name__ == '__main__':
    # test
    add_crop_replacements(model, _crop='Maize')
    # sims.FindByPath(modelToCheck.Parent.FullPath + "." + newName)

    crop = model.Simulations.FindInScope[Models.PMF.Plant]('Soybean')


    # model.preview_simulation()
    # DataTable predictedData = dataStore.Reader.GetData(TableName);
    def get_data(_model):
        # _model.run()
        _model._DataStore.Open()
        pred = model._DataStore.Reader.GetData("Report")
        view = DataView(pred)
        # for i  in view:
        #    ...# print(i)
        return view


def process():
    row = get_data(model).get_Rows()
    ar = [i.ItemArray for i in row]
    return ar


import clr
import pandas as pd

# Load .NET assemblies (ensure System.Data.dll is available)
clr.AddReference("System.Data")

from System.Data import DataView


@timer
def dataview_to_dataframe(_model, reports):
    """
    Convert .NET System.Data.DataView to Pandas DataFrame.
    :param dataview: System.Data.DataView object
    :return: Pandas DataFrame
    """
    _model._DataStore.Open()
    pred = model._DataStore.Reader.GetData(reports)
    dataview = DataView(pred)

    # Extract column names
    column_names = [col.ColumnName for col in dataview.Table.Columns]

    # Extract data from rows
    data = []
    for row in dataview:
        data.append([row[col] for col in column_names])  # Extract row values

    # Convert to Pandas DataFrame
    df = pd.DataFrame(data, columns=column_names)

    return df




