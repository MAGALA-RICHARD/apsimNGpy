"""
This module offers a procedural alternative other than object-oriented approach provided in api and ApsimModel classes
"""
import os
import sys
import uuid
from functools import singledispatch, lru_cache
from typing import Union

from apsimNGpy.core import pythonet_config
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.exceptions import NodeNotFoundError
pyth = pythonet_config
# now we can safely import C# libraries
from System.Collections.Generic import *
from System import *
import Models
import APSIM.Core as NEW_APSIM_CORE
import json
from os.path import (realpath)
from os import chdir
import shutil
from collections import namedtuple
from pathlib import Path
from apsimNGpy.core.config import get_apsim_bin_path, apsim_version, load_crop_from_disk
import subprocess
from apsimNGpy.core_utils.database_utils import read_db_table
from apsimNGpy.settings import SCRATCH
from dataclasses import dataclass
from typing import Any

@dataclass
class ModelData:
    IModel: Models
    path: str
    datastore: Any = None
    DataStore: Any = None
    results: Any = None
    met_path: str = ""
    Node: Any = None
    Simulations: Any = None



def load_from_dict(dict_data, out):
    str_ = json.dumps(dict_data)
    out = realpath(out)
    return Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](str_, None, True,
                                                                                    fileName=out)

version = apsim_version()

def copy_file(source: Union[str, Path], destination: Union[str, Path] = None,
              wd: Union[str, Path] = None) -> Union[str, Path]:
    if not wd:
        wd = SCRATCH

    destine_path = f"{str(destination).replace('.apsimx', version)}" +'.apsimx' if destination else os.path.join(wd, f"temp_{uuid.uuid1()}_{version}.apsimx")
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
    if pythonet_config.is_file_format_modified(Models) is False:
        if isinstance(object_to_convert, Models.Core.ApsimFile.ConverterReturnType):
            return object_to_convert.get_NewModel()
        return object_to_convert
    if pythonet_config.is_file_format_modified(Models):
        d=dir(object_to_convert)

        return object_to_convert


def load_model_from_dict(dict_model, out, met_file):
    """"""
    met_file = realpath(met_file)
    in_model = dict_model
    memo = load_from_dict(dict_data=in_model, out=out)
    return memo


def load_from_path(path2file, method='string'):
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
        if not pythonet_config.is_file_format_modified(Models):
            __model = Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](string_name, None,
                                                                                               True,
                                                                                           fileName=f_name)
            __model = __model.NewModel
        else:

            _model = NEW_APSIM_CORE.FileFormat.ReadFromString[Models.Core.Simulations](string_name, None,
                                                                                               True,
                                                                                            fileName=f_name)
            print(_model, 'be')
            __model = _model.get_Model()
            print(__model, 'af') # output Models.Core.Simulations
            print(__model==_model)


    else:

        try:
            __model = Models.Core.ApsimFile.FileFormat.ReadFromFile[Models.Core.Simulations](f_name, None, True)

        except AttributeError:
            __model = NEW_APSIM_CORE.FileFormat.ReadFromFile[Models.Core.Simulations](f_name, None, True)

    new_model = covert_to_model(__model)
    print(new_model, 'converted ;;')

    return new_model


def load_apsim_model(model=None, out_path=None, file_load_method='string', met_file=None, wd=None, **kwargs):
    """
    Load an APSIMX model from a file path, dictionary, or in-memory object.

    Parameters:
        model (str | dict | Simulation | None): The APSIM model source. Can be a file path, dictionary,
                                                APSIM simulation object, or None.
        out_path (str | Path, optional): The output path to save the working copy of the model.
                                         If None, a new filename will be generated.
        file_load_method (str): How to load the file (e.g., 'string', 'json').
        met_file (str, optional): Path to the associated meteorological file.
        wd (str, optional): Working directory for temporary file operations.
        **kwargs: Additional options (reserved for future use).

    Returns:
        ModelData: A dataclass container with paths, model object, and metadata.
    """

    if isinstance(model, Path):
        model = str(model)

    out = {}  # Stores the final output path used

    @singledispatch
    def loader(_model):
        """Base loader to handle unrecognized types."""
        raise NotImplementedError(f"Unsupported model type: {type(_model)}")

    @loader.register(dict)
    def _load_from_dict(_model: dict):
        """Load APSIMX model from a dictionary."""
        output = out_path or f"{uuid.uuid1()}.apsimx"
        out['path'] = output
        return load_from_dict(_model, output)

    @loader.register(str)
    def _load_from_str(_model: str):
        """Load apsimx model from a string path."""
        if not _model.endswith('.apsimx'):
            _model = load_crop_from_disk(crop=_model, out=None, work_space=wd)
        copy_to = copy_file(_model, destination=out_path, wd=wd)
        out['path'] = copy_to
        return load_from_path(copy_to, file_load_method)

    # Dispatch loader based on model type
    Model = loader(model)

    # If loaded object has get_NewModel, extract the inner model
    if getattr(Model, 'get_NewModel', None):
        _Model = Model.get_NewModel()
    else:
        _Model = Model


    if hasattr(_Model, "FindChild"):
        DataStore = _Model.FindChild[Models.Storage.DataStore]()

        datastore_path = DataStore.FileName

    else:
        DataStore = None
        datastore_path = None

    return ModelData(
        IModel=_Model,
        path=out.get('path'),
        datastore=datastore_path,
        DataStore=DataStore,
        results=None,
        met_path=met_file,
        Node=_Model.Node,
        Simulations=Model
    )


def recompile(_model, out=None, met_path=None, ):
    """ recompile without saving to disk useful for recompiling the same model on the go after updating management scripts

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
    print(_Model == Model)
    try:
        datastore = _Model.FindChild[Models.Storage.DataStore]().FileName
        DataStore = _Model.FindChild[Models.Storage.DataStore]()
    except AttributeError:
        datastore = None
        DataStore = None
    # need to make ModelData a constant and named outside the script for consistency across scripts
    #ModelData = namedtuple('model_data', ['IModel', 'path', 'datastore', "DataStore", 'results', 'met_path'])
    return ModelData(IModel=_Model, path=final_out_path, datastore=datastore, DataStore=DataStore,
                     results=None,
                     met_path=met_path,
                     Node=_Model.Node,
                     Simulations=Model)

def  read_from_string(model):
    if str(model).endswith('.apsimx'):
        path2file = model
    else:
        path2file = load_crop_from_disk(model, out='../testformatx.apsimx')

    f_name = realpath(path2file)

    with open(f_name, "r+", encoding='utf-8') as apsimx:
        app_ap = json.load(apsimx)
        string_name = json.dumps(app_ap)
        from Models.Core import Simulations
        model= NEW_APSIM_CORE.FileFormat.ReadFromString[Simulations](string_name, None, True ).Model
        return model

@timer
def run_model_externally(model):
    # Define the APSIM executable path (adjust if needed)
    apsim_exe = Path(get_apsim_bin_path()) / 'Models.exe'

    # Define the APSIMX file path
    apsim_file = model

    # Run APSIM with the specified file
    try:
        result = subprocess.run([apsim_exe, apsim_file])

        print("APSIM Run Successful!")

        # df = read_db_table(datastore, table)
        # return df
    except subprocess.CalledProcessError as e:
        print("Error running APSIM:")
        print(e.stderr)  # Print APSIM error message if execution fails


# if __name__ == '__main__':
#     import time
#     from pathlib import Path
#     from apsimNGpy.core.base_data import load_default_simulations
#
#     tt = Path("test_folder")
#     tt.mkdir(parents=True, exist_ok=True)
#     os.chdir(tt)
#     maze = load_default_simulations('Maize', )
#     soy = load_default_simulations('soybean', )
#     ap =load_apsim_model('Soybean')
#     # maze.initialise_model()
#     chdir(Path.home())
#     a = time.perf_counter()
#     mod = load_from_path(maze.path, method='string')
#     b = time.perf_counter()
#     print(b - a, 'seconds', 'loading from file')
#     aa = time.perf_counter()
#     model1 = load_from_path(soy.path, method='string')
#     print(time.perf_counter() - aa, 'seconds', 'loading from string')
#
#     sv = save_model_to_file(maze.model_info.IModel)
#     from apsimNGpy.core.core import CoreModel
#     from apsimNGpy.core.apsim import ApsimModel
#
#     maze.update_mgt(management=({"Name": 'Fertilise at sowing', 'Amount': 10},))
#     maze.run(report_name='Report')
#     me1 = maze.results['Maize.Total.Wt'].mean()
#     maze.update_mgt(management=({"Name": 'Fertilise at sowing', 'Amount': 300},))
#     maze.extract_user_input('Fertilise at sowing')
#     maze.run(report_name='Report', verbose=True)
#     me2 = maze.results['Maize.Total.Wt'].mean()
#     print(me2)
#     dd = run_model_externally(maze.path, 'report', maze.datastore)
#
#
#
def get_node_by_name(node, name):
    if hasattr(node, 'Node'):
        node = node.Node
    if hasattr(node, 'Walk'):
        for n in node.Walk():
            if n.Name == name:
                return n
    else:
        raise AttributeError(f"Node supplied has no attribute: Walk")
    raise NodeNotFoundError(f'Node with supplied name: `{name}` was not found')
    #
def get_node_by_path(node, node_path):
    """
    get a node by path
    @param node: node object or APSIM.Core object
    @param node_path: node path
    @return: node object if found. raise NodeNotFoundError
    """
    if hasattr(node, 'Node'):
        node = node.Node
    if hasattr(node, 'Walk'):
        for n in node.Walk():
            if n.get_FullNameAndPath() == node_path:
                return n
    else:
        raise AttributeError(f"Node supplied has no attribute: Walk")
    raise NodeNotFoundError(f'Node with supplied path: `{node_path}` was not found')

def get_node_string(node):
    """

    @param node: node object
    @return: a string name for the node e.g., Models.Clock
    """
    return node.ToString()


def get_attributes(obj):
    d = dir(obj)
    for i in d:
        if not i.startswith('__'):
            print(i)


if __name__ =='__main__':
     load = load_apsim_model('Maize')
     p, model, model2 = load.Node, load.IModel, load.IModel
     for mm in p.Walk():
         mod = mm.get_Model()
         typ = mod.GetType()

         print(mm.get_Model().GetType())
         if mm.Name =='Clock':
             mod = mm.get_Model()
             print(mod.GetType(), 'end')
             mm.get_FullNameAndPath()
             break
     for ws in p.WalkScoped():
        ws
     for pp in p.WalkParents():
         print(pp)
     ch =  list(load.Simulations.GetChildren())
     xc=  ch[0].GetChildren()
     print([i.Name for i in xc])

     dat= read_from_string("Maize")
     odm = load_from_path(load.path).Node.Model
     sim = list(dat.GetChildren())[0]
     chid = list(sim.GetChildren())[0]
     from typing import cast
     from System import DateTime
     from datetime import datetime
     cas = cast(mod, Models.Clock)



