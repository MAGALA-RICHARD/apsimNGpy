"""
This module offers a procedural alternative other than object-oriented approach provided in api and ApsimModel classes
"""
import os
import uuid
from functools import singledispatch
from typing import Union

from apsimNGpy.core import pythonet_config
from apsimNGpy.core_utils.utils import timer

pyth = pythonet_config
# now we can safely import C# libraries
from System.Collections.Generic import *
from System import *
import Models
import json
from os.path import (realpath)
from os import chdir
import shutil
from collections import namedtuple
from pathlib import Path
from apsimNGpy.core.config import get_apsim_bin_path
import subprocess
from apsimNGpy.core_utils.database_utils import read_db_table
from apsimNGpy.settings import SCRATCH


def load_from_dict(dict_data, out):
    str_ = json.dumps(dict_data)
    out = realpath(out)
    return Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](str_, None, True,
                                                                                    fileName=out)


def copy_file(source: Union[str, Path], destination: Union[str, Path] = None,
              wd: Union[str, Path] = None) -> Union[str, Path]:
    if not wd:
        wd = SCRATCH
    destine_path = destination if destination else os.path.join(wd, f"temp_{uuid.uuid1()}.apsimx")
    shutil.copy2(source, destine_path)
    return destine_path


def save_model_to_file(_model, out=None):
    """Save the model

        Parameters
        ----------
        out : str, optional path to save the model to
            reload: bool to load the file using the out path
            :param out: out path
            :param _model:APSIM Models.Core.Simulations object
            returns the filename or the specified out name
        """
    # Determine the output path
    _model = covert_to_model(object_to_convert=_model)
    final_out_path = out or '_saved_model.apsimx'

    # Serialize the model to JSON string
    json_string = Models.Core.ApsimFile.FileFormat.WriteToString(_model)

    # Save the JSON string to the determined output path
    with open(final_out_path, "w", encoding='utf-8') as f:
        f.write(json_string)
    return final_out_path


def covert_to_model(object_to_convert):
    if isinstance(object_to_convert, Models.Core.ApsimFile.ConverterReturnType):
        did_convert = object_to_convert.DidConvert
        # if not did_convert:
        #     raise ValueError('conversion to the newest version failed')
        return object_to_convert.get_NewModel()
    else:
        return object_to_convert


def load_model_from_dict(dict_model, out, met_file):
    """useful for spawning many simulation files"""
    met_file = realpath(met_file)
    in_model = dict_model
    memo = load_from_dict(dict_data=in_model, out=out)
    return memo


def load_from_path(path2file, method='file'):
    """"

    :param path2file: path to apsimx file
    :param method: str  with string, we direct the method to first convert the file
    into a string using json and then use the APSIM in-built method to load the file with file, we read directly from
    the file path. This is slower than the former.
    """

    f_name = realpath(path2file)
    with open(f_name, "r+", encoding='utf-8') as apsimx:
        app_ap = json.load(apsimx)
    string_name = json.dumps(app_ap)
    if method == 'string':
        __model = Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](string_name, None,
                                                                                           True,
                                                                                           fileName=f_name)
        __model = __model.NewModel
    else:
        __model = Models.Core.ApsimFile.FileFormat.ReadFromFile[Models.Core.Simulations](f_name, None, True)

    new_model = covert_to_model(__model)

    return new_model


def load_apsim_model(model=None, out_path=None, file_load_method='string', met_file=None, wd=None, **kwargs):
    """
       >> we are loading apsimx model from file, dict, or in memory.
       >> if model is none, we will return a pre - reloaded one from memory.
       >> if out parameter is none, the new file will have a suffix _copy at the end
       >> if model is none, the name is ngpy_model
       returns a named tuple with an out path, datastore path, and IModel in memory
       """
    out = {}  # stores the path to be attached to model_info object
    Model_data = namedtuple('model_data',
                            ['IModel', 'path', 'datastore', "DataStore", 'results', 'met_path'])

    @singledispatch
    def loader(_model):
        """base loader to handle non implemented data type"""
        # this will raise not implemented error if the _model is not a dict, str, None, Models.Core.Simulation,
        raise NotImplementedError(f"Unsupported type: {type(_model)}")

    @loader.register(dict)
    def _(_model: dict):
        """loads apsimx model from a dictionary"""
        # no need to copy the file
        _out = out_path or f"{uuid.uuid1()}.apsimx"
        out['path'] = _out
        return load_from_dict(_model, _out)

    @loader.register(str)
    def _(_model: str):
        """loads apsimx model from a string path"""
        copy_to = copy_file(_model, destination=out_path, wd=wd)
        out['path'] = copy_to
        return load_from_path(copy_to, file_load_method)

    @loader.register(Path)
    def _(_model: Path):
        """loads apsimx model from a pathlib.Path object"""
        # same as the string one, the difference is that this is a pathlib path object
        copy_to = copy_file(_model, destination=out_path, wd=wd)
        out['path'] = copy_to
        return load_from_path(copy_to, file_load_method)

    Model = loader(model)
    _Model = False
    if isinstance(Model, Models.Core.ApsimFile.ConverterReturnType):
        _Model = Model.get_NewModel()
    else:
        _Model = Model
    datastore = _Model.FindChild[Models.Storage.DataStore]().FileName
    DataStore = _Model.FindChild[Models.Storage.DataStore]()
    return Model_data(IModel=_Model, path=out['path'], datastore=datastore, DataStore=DataStore, results=None,
                      met_path=met_file)


def recompile(_model, out=None, met_path=None, ):
    """ recompile without saving to disk useful for recombiling the same model on the go after updating management scripts

            Parameters
            ----------
            out : str, optional path to save the model to

                :param met_path: path to met file
                :param out: out path name for database reconfiguration
                :param _model:APSIM Models.Core.Simulations object
                returns named tuple with a recompiled model
            """
    # Determine the output path

    final_out_path = out or _model.path

    # Serialize the model to JSON string
    json_string = Models.Core.ApsimFile.FileFormat.WriteToString(_model.Simulations)

    Model = Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](json_string, None,
                                                                                     True,
                                                                                     fileName=str(final_out_path))
    # Model = Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](json_string, None, True,
    #                                                                                  fileName=final_out_path)
    _Model = False
    _Model = covert_to_model(Model)

    datastore = _Model.FindChild[Models.Storage.DataStore]().FileName
    DataStore = _Model.FindChild[Models.Storage.DataStore]()
    # need to make ModelData a constant and named outside the script for consistency across scripts
    ModelData = namedtuple('model_data', ['IModel', 'path', 'datastore', "DataStore", 'results', 'met_path'])
    return ModelData(IModel=_Model, path=final_out_path, datastore=datastore, DataStore=DataStore,
                     results=None,
                     met_path=met_path)


@timer
def run_model_externally(model, table, datastore):
    # Define the APSIM executable path (adjust if needed)
    apsim_exe = Path(get_apsim_bin_path()) / 'Models.exe'

    # Define the APSIMX file path
    apsim_file = model

    # Run APSIM with the specified file
    try:
        result = subprocess.run([apsim_exe, apsim_file])

        print("APSIM Run Successful!")

        df = read_db_table(datastore, table)
        return df
    except subprocess.CalledProcessError as e:
        print("Error running APSIM:")
        print(e.stderr)  # Print APSIM error message if execution fails


if __name__ == '__main__':
    import time
    from pathlib import Path
    from apsimNGpy.core.base_data import load_default_simulations

    tt = Path("test_folder")
    tt.mkdir(parents=True, exist_ok=True)
    os.chdir(tt)
    maze = load_default_simulations('Maize', )
    soy = load_default_simulations('soybean', )

    # maze.initialise_model()
    chdir(Path.home())
    a = time.perf_counter()
    mod = load_from_path(maze.path, method='string')
    b = time.perf_counter()
    print(b - a, 'seconds', 'loading from file')
    aa = time.perf_counter()
    model1 = load_from_path(soy.path, method='string')
    print(time.perf_counter() - aa, 'seconds', 'loading from string')

    sv = save_model_to_file(maze.model_info.IModel)
    from apsimNGpy.core.core import CoreModel
    from apsimNGpy.core.apsim import ApsimModel

    maze.update_mgt(management=({"Name": 'Fertilise at sowing', 'Amount': 10},))
    maze.run(report_name='Report')
    me1 = maze.results['Maize.Total.Wt'].mean()
    maze.update_mgt(management=({"Name": 'Fertilise at sowing', 'Amount': 300},))
    maze.extract_user_input('Fertilise at sowing')
    maze.run(report_name='Report')
    me2 = maze.results['Maize.Total.Wt'].mean()
    print(me2)
    dd = run_model_externally(maze.path, 'report', maze.datastore)
