"""
This module offers a procedural alternative other than object-oriented approach provided in api and ApsimModel classes
"""
# TODO this module/file is named badly. the functions here should go to core or base.
# for a start, we can use the functions defined here instead of using the ones in APSIMNG's loader.

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
from os.path import (join, dirname, realpath)
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


def load_apx_model(model=None, out=None):
    """
       >> we are loading apsimx model from file, dict, or in memory.
       >> if model is none, we will return a pre - reloaded one from memory.
       >> if out parameter is none, the new file will have a suffix _copy at the end
       >> if model is none, the name is ngpy_model
       returns a named tuple with an out path, datastore path, and IModel in memory
       """
    # name according to the order of preference
    # TODO this is a nice abstractions, except for the use of the loader, just use
    # it functions perfectly as an api function which means that external functions should never know
    # about the functions defined above which are used by this function to load models.
    # conditionals.
    out2 = f"{Path(model).parent}/{Path(model).stem}_copy.apsimx" if model is not None else None
    out1 = realpath(out) if out is not None else None
    out3 = realpath('ngpy_model.apsimx')
    _out = out1 or out2 or out3
    Model_data = namedtuple('model_data', ['IModel', 'path', 'datastore', "DataStore"])

    @singledispatch
    def loader(_model):
        raise NotImplementedError(f"Unsupported type: {type(_model)}")

    @loader.register(dict)
    def _(_model: dict):
        assert _out, "out can not be none for dictionary data"
        return load_from_dict(_model, _out)

    @loader.register(str)
    def _(_model: str):
        shutil.copy(_model, _out)
        return load_from_path(_out)

    @loader.register(Path)
    def _(_model: Path):
        shutil.copy(_model, _out)
        return load_from_path(_out)

    @loader.register(type(None))
    def _(_model):
        return load_from_dict(load_model, out=_out)

    Model = loader(model)
    if 'NewModel' in dir(Model):
        Model = Model.get_NewModel()
    datastore = Model.FindChild[Models.Storage.DataStore]().FileName
    DataStore = Model.FindChild[Models.Storage.DataStore]()
    named_tuple = Model_data(IModel=Model, path=_out, datastore=datastore, DataStore=DataStore)
    return named_tuple



def save_model_to_file(model, out=None):
    """Save the model

        Parameters
        ----------
        out : str, optional path to save the model to
            reload: bool to load the file using the outpath
            :param model:APSIM  Models.Core.Simulations object
            :param reload:
            returns the filename or the specified out name
        """
    # Determine the output path

    final_out_path = out or model.FileName

    # Serialize the model to JSON string
    json_string = Models.Core.ApsimFile.FileFormat.WriteToString(model)

    # Save the JSON string to the determined output path
    with open(final_out_path, "w", encoding='utf-8') as f:
        f.write(json_string)
    return final_out_path


def find_simulation(model):
    return model.FindAllDescendants[Simulation]()


def _find_simulation(model, simulation_name):
    sim_name = simulation_name
    sims = find_simulation(model)
    for sim in sims:
        if sim.Name == sim_name:
            return sim


def look_up_simulations(model, simulations=None):
    """TODO
        """
    sims = find_simulation(model)
    if simulations is None:
        return sims
    else:
        if type(simulations) == str:
            simulations = [simulations]
        sim_s = []
        for s in sims:
            if s.Name in simulations:
                sim_s.append(s)
        if len(sim_s) == 0:
            print("Not found!")
        else:
            return sim_s


def update_mgt(model, management, reload=True, out=None):
    """Update management, handles one manager at a time

        Parameters
        ----------
        management

            Parameter = value dictionary of management paramaters to update. examine_management_info` to see current values.
            make a dictionary with 'Name' as the for the of  management script
        simulations, optional
            List of simulation names to update, if `None` update all simulations not recommended.
            :param out: to save the file after editing
            :param reload:
        """
    if not isinstance(management, list):
        management = [management]
    sims = find_simulation(model)
    for sim in sims:
        zone = sim.FindChild[Models.Core.Zone]()
        zone_path = zone.FullPath
        for mgt in management:
            action_path = f'{zone_path}.{mgt.get("Name")}'
            fp = zone.FindByPath(action_path)
            values = mgt
            for i in range(len(fp.Value.Parameters)):
                param = fp.Value.Parameters[i].Key
                if param in values.keys():
                    fp.Value.Parameters[i] = KeyValuePair[String, String](param, f"{values[param]}")
    out_mgt_path = out or model.FileName
    save_model_to_file(model=model, out=out_mgt_path)
    if reload:
        return load_from_path(out_mgt_path)

    def replace_met_file(self, weather_file, simulations=None):
        try:
            """searched the weather node and replaces it with a new one

            Parameters
            ----------
            weather_file
                Weather file name, path should be relative to simulation or absolute.
            simulations, optional
                List of simulation names to update, if `None` update all simulations
            """
            assert weather_file.endswith(
                '.met'), "the file entered may not be a met file did you forget to put .met extension?"
            for sim_name in self.find_simulations(simulations):
                weathers = sim_name.FindAllDescendants[Weather]()
                for met in weathers:
                    met.FileName = weather_file
            return self
        except Exception as e:
            print(repr(e))  # this error will be logged to the folder logs in the current working directory
            raise


if __name__ == '__main__':
    import time
    from pathlib import Path

    chdir(Path.home())
    a = time.perf_counter()
    pp = r'D:\ndata/sw.apsimx'
    mod = load_from_path(pp)
    mog = update_mgt(model=mod, management={"Name": 'Simple Rotation', 'Crops': 'Maize, Soybean'}, out=None)
    b = time.perf_counter()
    print(b - a, 'seconds')

    aa = time.perf_counter()
    model = load_apx_model(pp)
    print(time.perf_counter() - aa, 'seconds')
