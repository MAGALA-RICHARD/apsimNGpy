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


def remove_model(_model, model_name):
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


model.run()

df = dataview_to_dataframe(model, reports='Report')
#df2 =read_db_table(model.datastore, 'Report')
model.clean_up()
print(df)
path = r"D:\My_BOX\Box\PhD thesis\CHAPTER FOUR\source_files\split_single_test.apsimx"


test_model  = ApsimModel(path)