"""
This module offers a procedural alternative other than object-oriented approach provided in api and ApsimModel classes
"""
from apsimNGpy.core.pythonet_config import LoadPythonnet
# now we can safely import C# libraries
from System.Collections.Generic import *
from Models.Core import Simulations, ScriptCompiler, Simulation
from System import *
from Models.Core.ApsimFile import FileFormat
from Models.Climate import Weather
from Models.Soils import Soil, Physical, SoilCrop, Organic
import Models
from Models.PMF import Cultivar
from apsimNGpy.core.apsim_file import XFile as load_model
import json
from os.path import (join, dirname, realpath, isfile)
from os import chdir
from pathlib import Path
import shutil
from collections import namedtuple


def load_from_dict(dict_data, out):
    str_ = json.dumps(dict_data)
    out = realpath(out)
    return Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](str_, None, True,
                                                                                    fileName=out)


def load_model_from_dict(dict_model, out, met_file):
    """useful for spawning many simulation files"""
    met_file = realpath(met_file)
    in_model = dict_model or load_model
    memo = load_from_dict(dict_data=in_model, out=out)
    return memo


def load_from_path(path2file):
    f_name = realpath(path2file)
    with open(path2file, "r+", encoding='utf-8') as apsimx:
        app_ap = json.load(apsimx)
    string_name = json.dumps(app_ap)

    return Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](string_name, None,
                                                                                    True,
                                                                                    fileName=f_name)


from functools import singledispatch


def load_apx_model(model=None, out=None, met_file=None):
    """
       >> we are loading apsimx model from file, dict, or in memory.
       >> if model is none, we will return a pre - reloaded one from memory.
       >> if out parameter is none, the new file will have a suffix _copy at the end
       >> if model is none, the name is ngpy_model
       returns a named tuple with an out path, datastore path, and IModel in memory
       """
    # name according to the order of preference
    out2 = f"{Path(model).parent}/{Path(model).stem}_copy.apsimx" if model is not None else None
    out1 = realpath(out) if out is not None else None
    out3 = realpath('ngpy_model.apsimx')
    _out = out1 or out2 or out3
    Model_data = namedtuple('model_data', ['IModel', 'path', 'datastore', "DataStore", 'results', 'met_path'])

    @singledispatch
    def loader(_model):
        # this will raise not implemented error if the _model is not a dict, str, None, Models.Core.Simulation,
        # or apathlib path object
        raise NotImplementedError(f"Unsupported type: {type(_model)}")

    @loader.register(dict)
    def _(_model: dict):
        # no need to copy the file
        assert _out, "out can not be none for dictionary data"
        return load_from_dict(_model, _out)

    @loader.register(str)
    def _(_model: str):
        # we first copy the file before loading it
        shutil.copy(_model, _out)
        return load_from_path(_out)

    @loader.register(Path)
    def _(_model: Path):
        # same as the string one, the difference is that this is a pathlib path object
        shutil.copy(_model, _out)
        return load_from_path(_out)

    @loader.register(type(None))
    def _(_model):
        # whenever the model is none, we return a preloaded dictionary in memory from the package
        return load_from_dict(load_model, out=_out)

    @loader.register(Models.Core.Simulations)
    def _(_model: Models.Core.Simulations):
        # it is already a model.core.Simulation object so we just return it
        return _model

    Model = loader(model)
    if 'NewModel' in dir(Model):
        Model = Model.get_NewModel()
    datastore = Model.FindChild[Models.Storage.DataStore]().FileName
    DataStore = Model.FindChild[Models.Storage.DataStore]()
    named_tuple = Model_data(IModel=Model, path=_out, datastore=datastore, DataStore=DataStore, results=None, met_path=met_file )
    return named_tuple


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

    final_out_path = out or _model.FileName

    # Serialize the model to JSON string
    json_string = Models.Core.ApsimFile.FileFormat.WriteToString(_model)

    # Save the JSON string to the determined output path
    with open(final_out_path, "w", encoding='utf-8') as f:
        f.write(json_string)
    return final_out_path


if __name__ == '__main__':
    import time
    from pathlib import Path

    chdir(Path.home())
    a = time.perf_counter()
    pp = r'D:\ndata/sw.apsimx'
    mod = load_from_path(pp)
    b = time.perf_counter()
    print(b - a, 'seconds')

    aa = time.perf_counter()
    model = load_apx_model(pp)
    print(time.perf_counter() - aa, 'seconds')
    from runner import run_model

    a = time.perf_counter()
    resm = run_model(model, results=True, clean_up=True)
    print(time.perf_counter() - a, 'seconds')
