"""
This module offers a procedural alternative other than object-oriented approach provided in api and ApsimModel classes
"""
import os
import uuid
from typing import Union

from apsimNGpy.core import pythonet_config
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.exceptions import NodeNotFoundError

pyth = pythonet_config
# now we can safely import C# libraries
from System.Collections.Generic import *
from System import *
import Models

import json
from os.path import (realpath)
import shutil
from pathlib import Path
from apsimNGpy.core.config import get_apsim_bin_path, apsim_version, load_crop_from_disk
import subprocess
from apsimNGpy.settings import SCRATCH
from dataclasses import dataclass
from typing import Any

from apsimNGpy.core.cs_resources import CastHelper as CastHelpers
from apsimNGpy.core.pythonet_config import get_apsim_file_reader, get_apsim_file_writer
from apsimNGpy.core.pythonet_config import is_file_format_modified

GLOBAL_IS_FILE_MODIFIED = is_file_format_modified()


def to_model_from_string(json_string, fname):
    loader = get_apsim_file_reader()

    return loader[Models.Core.Simulations](json_string, None, True, fileName=fname)


def to_json_string(_model: Models.Core.Simulation):
    """We first determine whether the model is loaded from APSIM>CORE."""

    n_model = getattr(_model, 'Node', _model)
    if hasattr(n_model, 'ToJSONString'):
        return n_model.ToJSONString()

    writer = get_apsim_file_writer()
    if _model:
        return writer(_model)
    raise ValueError(f'failed to convert model:`{_model}` to strings ')


@dataclass
class ModelData:
    """
    This is a meta-data container for the loaded models
    """
    IModel: Models
    path: str
    datastore: Any = None
    DataStore: Any = None
    results: Any = None
    met_path: str = ""
    Node: Any = None
    Simulations: Any = None


def get_model(obj):
    out_model = getattr(obj, 'Model', obj)  # for new versions
    out_model = getattr(out_model, 'NewModel', out_model)  # previous versions
    return out_model


def load_from_dict(dict_data, out):
    str_ = json.dumps(dict_data)
    out = realpath(out)
    return to_model_from_string(str_, out)


version = apsim_version()


def copy_file(source: Union[str, Path], destination: Union[str, Path] = None,
              wd: Union[str, Path] = None) -> Union[str, Path]:
    if not wd:
        wd = SCRATCH

    destine_path = f"{str(destination).replace('.apsimx', version)}" + '.apsimx' if destination else os.path.join(wd,
                                                                                                                  f"temp_{uuid.uuid1()}_{version}.apsimx")
    shutil.copy2(source, destine_path)
    return destine_path


def save_model_to_file(_model, out=None):
    """Save the model

        Parameters
        ----------

            Returns the filename or the specified out name
        """
    # Determine the output path
    _model = get_model(_model)
    final_out_path = out or '_saved_model.apsimx'

    json_string = to_json_string(_model)
    # Serialize the model to JSON string

    # Save the JSON string to the determined output path
    with open(final_out_path, "w", encoding='utf-8') as f:
        f.write(json_string)
    return final_out_path


def covert_to_model(object_to_convert):
    return getattr(object_to_convert, 'NewModel', object_to_convert)


def load_from_path(path2file, method='string'):
    """"

    :param path2file: path to apsimx file
    :param method: str with string, we direct the method to first convert the file
    into a string using json and then use the APSIM in-built method to load the file with file, we read directly from
    the file path. This is slower than the former.
    """

    f_name = realpath(path2file)
    with open(f_name, "r+", encoding='utf-8') as apsimx:
        app_ap = json.load(apsimx)
    string_name = json.dumps(app_ap)

    method = method.lower()

    loader = get_apsim_file_reader(method)

    match method:
        case 'string':
            __model = loader[Models.Core.Simulations](string_name, None, True, fileName=f_name)
            __model = getattr(__model, 'NewModel', __model)

        case 'file':
            __model = loader[Models.Core.Simulations](f_name, None, True)
            __model = getattr(__model, 'NewModel', __model)
        case _:
            raise NotImplementedError('Unsupported method for reading apsim json file')

    new_model = covert_to_model(__model)

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
        {ModelData}: A dataclass container with paths, model object, and metadata.
    """
    if isinstance(model, Path):
        model = str(model)

    out = {}  # Store final output path

    match model:
        case dict():
            output = out_path or f"{uuid.uuid1()}.apsimx"
            out['path'] = output
            Model = load_from_dict(model, output)

        case str():
            if not model.endswith('.apsimx'):
                model = load_crop_from_disk(crop=model, out=None, work_space=wd)
            copy_to = copy_file(model, destination=out_path, wd=wd)
            out['path'] = copy_to
            Model = load_from_path(copy_to, file_load_method)

        case None:
            raise ValueError("Model cannot be None")

        case _:
            raise NotImplementedError(f"Unsupported model type: {type(model)}")

    _Model = get_model(Model)
    node = _Model

    if GLOBAL_IS_FILE_MODIFIED:
        g_model = getattr(_Model, 'Model', _Model)
        out_model = CastHelpers.CastAs[Models.Core.Simulations](g_model)
    else:
        out_model = _Model

    out_path = out.get('path')
    datastore_path = str(Path(out_path).with_suffix('.db')) if out_path else ""

    if hasattr(out_model, "FindChild"):
        DataStore = out_model.FindChild[Models.Storage.DataStore]()
    else:
        DataStore = ''
        datastore_path = ''

    return ModelData(
        IModel=out_model,
        path=out_path,
        datastore=datastore_path,
        DataStore=DataStore,
        results=None,
        met_path=met_file,
        Node=node,
        Simulations=Model
    )


def load_as_dict(file: Models.Core.ApsimFile) -> dict:
    """loads apsimx model from a pathlib"""
    model_simulations = load_from_path(file)
    json_string = Models.Core.ApsimFile.FileFormat.WriteToString(model_simulations)
    return json.loads(json_string)


def recompile(_model, out=None, met_path=None, ):
    """ recompile without saving to disk useful for recombining the same model on the go after updating management scripts

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

    json_string = to_json_string(_model.Simulations)
    if GLOBAL_IS_FILE_MODIFIED:
        model_node = getattr(_model.Simulations, 'Node', _model.Simulations)
        json_string = model_node.ToJSONString()
    Model = to_model_from_string(json_string, fname=_model.path)

    _Model = False

    _Model = get_model(Model)
    if GLOBAL_IS_FILE_MODIFIED:
        out_model = CastHelpers.CastAs[Models.Core.Simulations](_Model)
    else:
        out_model = _Model
    try:
        datastore = str(Path(_model.path).with_suffix('.db'))

        DataStore = out_model.FindChild[Models.Storage.DataStore]()
    except AttributeError:
        datastore = ''
        DataStore = ''

    # need to make ModelData a constant and named outside the script for consistency across scripts
    # ModelData = namedtuple('model_data', ['IModel', 'path', 'datastore', "DataStore", 'results', 'met_path'])
    return ModelData(IModel=out_model,
                     path=final_out_path,
                     datastore=datastore,
                     DataStore=DataStore,
                     results=None,
                     met_path=met_path,
                     Node=_Model,
                     Simulations=Model)


def model_from_string(mod):
    if str(mod).endswith('.apsimx'):
        path2file = mod
    else:
        path2file = load_crop_from_disk(mod, out=os.path.realpath(f'{mod}_testformatx.apsimx'))

    f_name = realpath(path2file)

    with open(f_name, "r+", encoding='utf-8') as apsimx:
        app_ap = json.load(apsimx)
        string_name = json.dumps(app_ap)
        loader = get_apsim_file_reader(method='string')

        mod = loader[Models.Core.Simulations](string_name, None, initInBackground=True)
        mod = getattr(mod, "Model", mod)

        mod = covert_to_model(mod)

        return mod


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
    attributes = set()
    d = dir(obj)
    for i in d:
        if not i.startswith('__'):
            attributes.add(i)
    return attributes


if __name__ == '__main__':
    pat = load_crop_from_disk('Maize')
    load = load_apsim_model('Maize')
    p, model, model2 = load.Node, load.IModel, load.IModel

    getattr(Models.Core.ApsimFile, "FileFormat", None)
    # set_apsim_bin_path(r'/Applications/APSIM2025.2.7670.0.app/Contents/Resources/bin')
    to_json_string(model2)
