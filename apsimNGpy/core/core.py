"""
Interface to APSIM simulation models using Python.NET
author: Richard Magala
email: magalarich20@gmail.com

"""
from functools import singledispatch
import matplotlib.pyplot as plt
import random, logging, pathlib
import string
from typing import Union
import os, sys, datetime, shutil
import numpy as np
import pandas as pd
from os.path import join as opj
import sqlite3
import json
from pathlib import Path
import threading
import time
import datetime
import apsimNGpy.manager.weathermanager as weather
from functools import cache
# prepare for the C# import
from apsimNGpy.core.pythonet_config import LoadPythonnet
from apsimNGpy.utililies.database_utils import read_db_table, get_db_table_names
import warnings
from apsimNGpy.utililies.utils import timer
# py_config = LoadPythonnet()()  # double brackets avoids calling it twice

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
from apsimNGpy.core.model_loader import (load_apx_model, save_model_to_file, recompile)
from apsimNGpy.utililies.utils import timer
from apsimNGpy.core.runner import run_model


# from settings import * This file is not ready and i wanted to do some test


class APSIMNG:
    """Modify and run APSIM next generation simulation models."""

    def __init__(self, model=None, out_path=None, out=None, **kwargs):

        self.others = kwargs.copy()
        if kwargs.get('copy'):
            warnings.warn(
                'copy argument is deprecated, it is now mandatory to copy the model in order to conserve the original '
                'model.')
        """
            Parameters
            ----------
            model : str or Simulations
                Path to .apsimx file or a Simulations object.
            copy : bool, optional
                If True, a copy of the original simulation will be created on init to conserve the original file, by default True.
            out_path : str, optional
                Path of the modified simulation; if None, it will be set automatically.
            read_from_string : bool, optional
                If True, file is uploaded to memory through json module (preferred); otherwise, we read from file.
            """
        out_path = out_path if isinstance(out_path, str) or isinstance(out_path, Path) else None
        self.copy = kwargs.get('copy')  # Mandatory to conserve the original file
        # all these can be changed after initialization
        self.results = None
        self._str_model = None
        self._model = model
        self.out_path = out_path or out
        # model_info is named tuple safe for parallel simulations as named tuples are immutable
        self.model_info = load_apx_model(self._model, out=self.out_path, met_file=kwargs.get('met_file'))
        self.Simulations = self.model_info.IModel
        self.datastore = self.model_info.datastore
        self.Datastore = self.model_info.DataStore
        self._DataStore = self.model_info.DataStore
        self.path = self.model_info.path
        self._met_file = kwargs.get('met_file')
        if self._met_file is not None:
            self.replace_met_file(self._met_file)

    def run_simulations(self, results=None, reports=None, clean_up=False):
        """
        Run the simulation. here we are using the self.model_info named tuple from model loader
        :results : bool, optional if True, we return the results of the simulation
           else we just run, and the user can retrieve he results from the database using the data store path
        reports: str, array like for returning the reports
        clean_up : bool deletes the file on disk, by default False
        returns results if results is True else None
        """
        resu = run_model(self.model_info, results=results, clean_up=clean_up)

        if reports:
            return [resu[repo] for repo in reports] if isinstance(reports, (list, tuple, set)) else resu[reports]
        else:
            return resu

    @property
    def simulation_object(self):
        """
        # A simulation_object in this context is:
        # A path to apsimx file, a str or pathlib Path object
        # A dictionary (apsimx json file converted to a dictionary using the json module)
        # apsimx simulation object already in memory
        """
        return self._model

    @simulation_object.setter
    def simulation_object(self, value):
        """
        Set the model if you don't want to initialize again
        :param value:
        # A value in this context is:
        # A path to apsimx file, a str or pathlib Path object
        # A dictionary (apsimx json file converted to a dictionary using the json module)
        # apsimx simulation object already in memory


        """
        self._model = value

    def clear_links(self):
        self.Simulations.ClearLinks()
        return self

    def ClearSimulationReferences(self):
        self.Simulations.ClearSimulationReferences()
        return self

    @staticmethod
    def _remove_related_files(_name):
        """Remove related database files."""
        for suffix in ["", "-shm", "-wal"]:
            db_file = pathlib.Path(f"{_name}.db{suffix}")
            db_file.unlink(missing_ok=True)

    @staticmethod
    def generate_unique_name(base_name, length=6):
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=length))
        unique_name = base_name + '_' + random_suffix
        return unique_name

    # searches the simulations from APSIM models.core object
    @property
    def simulations(self):
        """
        Retrieve simulation nodes in the APSIMx `Model.Core.Simulations` object.

        We search all Models.Core.Simulation in the scope of Model.Core.Simulations. Please note the difference
        Simulations is the whole json object Simulation is the node with the field zones, crops, soils and managers
        any structure of apsimx file any structure can be handled
        """
        # fixed
        # we can actually specify the simulation name in the bracket
        return list(self.Simulations.FindAllInScope[Models.Core.Simulation]())

    @property
    def simulation_names(self):
        return [s.Name for s in self.simulations]

    @property
    def str_model(self):
        return json.dumps(self._str_model)

    @str_model.setter
    def str_model(self, value: dict):
        self._str_model = json.dumps(value)

    def initialise_model(self):
        simulationList = self.Simulations.FindAllDescendants[Simulation]()
        for models in self.Simulations.FindAllDescendants():
            try:
                models.OnCreated()
            except Exception as e:
                print(e)
            finally:
                for simulation in simulationList:
                    simulation.IsInitialising = False
        return self

    def _reload_saved_file(self):
        self.save_edited_file(self.path)
        return self

    def restart_model(self, model_info=None):
        """
         :param model_info: A named tuple object returned by `load_apx_model` from the `model_loader` module.

        Notes:
        - This parameter is crucial whenever we need to reinitialize the model, especially after updating management practices or editing the file.
        - In some cases, this method is executed automatically.
        - If `model_info` is not specified, the simulation will be reinitialized from `self`.

        This function is called by `save_edited_file` and `update_mgt`.

        :return: self
        """

        if model_info:
            self.model_info = model_info
        self.Simulations = self.model_info.IModel
        self.datastore = self.model_info.datastore
        self.Datastore = self.model_info.DataStore
        self._DataStore = self.model_info.DataStore
        self.path = self.model_info.path
        return self

    def save_edited_file(self, out_path=None, reload=False):
        """ Saves the model to the local drive.

            Notes: - If `out_path` is None, the `save_model_to_file` function extracts the filename from the
            `Model.Core.Simulation` object. - `out_path`, however, is given high priority. Therefore,
            we first evaluate if it is not None before extracting from the file. - This is crucial if you want to
            give the file a new name different from the original one while saving.

            Parameters
            - out_path (str): Desired path for the .apsimx file, by default, None.
            - reload (bool): Whether to load the file using the `out_path` or the model's original file name.

        """
        # Determine the output path
        _out_path = out_path or self.model_info.path
        save_model_to_file(self.Simulations, out=_out_path)
        if reload:
            self.model_info = load_apx_model(_out_path)
            self.restart_model()
            return self

    def run(self, report_name=None, simulations=None, clean=False, multithread=True):
        """Run apsim model in the simulations

        Parameters
        ----------
        report_name: str. defaults to APSIM defaults Report Name and if not specified or Report Name not in the simulation tables, the simulator will
            execute the model and save the outcomes in a database file, accessible through alternative retrieval methods.

        simulations (__str_), optional
            List of simulation names to run, if `None` runs all simulations, by default `None`.

        clean (_-boolean_), optional
            If `True` remove an existing database for the file before running, deafults to False`

        multithread
            If `True` APSIM uses multiple threads, by default `True`
        """
        try:
            if multithread:
                runtype = Models.Core.Run.Runner.RunTypeEnum.MultiThreaded
            else:
                runtype = Models.Core.Run.Runner.RunTypeEnum.SingleThreaded
            # open the datastore

            self._DataStore.Open()
            # Clear old data before running
            self.results = None
            if clean:
                self._DataStore.Dispose()
                pathlib.Path(self._DataStore.FileName).unlink(missing_ok=True)

            if simulations is None:
                runmodel = Models.Core.Run.Runner(self.Simulations, True, False, False, None, runtype)
                e = runmodel.Run()
            else:
                sims = self.find_simulations(simulations)
                # Runner needs C# list
                cs_sims = List[Models.Core.Simulation]()
                for s in sims:
                    cs_sims.Add(s)
                    runmodel = Models.Core.Run.Runner(cs_sims, True, False, False, None, runtype)
                    e = runmodel.Run()

            if len(e) > 0:
                print(e[0].ToString())
            if report_name is None:
                report_name = get_db_table_names(self.datastore)
                # issues with decoding '_Units' we remove it
                if '_Units' in report_name: report_name.remove('_Units')
                warnings.warn('No tables were specified, retrieved tables includes:: {}'.format(report_name))
            if isinstance(report_name, (tuple, list)):
                self.results = [read_db_table(self.datastore, report_name=rep) for rep in report_name]
            else:
                self.results = read_db_table(self.datastore, report_name=report_name)
        finally:
            # close the datastore
            self._DataStore.Close()
        return self

    def clone_simulation(self, target, simulation=None):
        """Clone a simulation and add it to Model

        Parameters
        ----------
        target
             simulation name
        simulation, optional
            Simulation name to be cloned, of None clone the first simulation in model
        """

        sims = self._find_simulation(simulation)
        for sim in sims:
            clone_sim = Models.Core.Apsim.Clone(sim)
            clone_sim.Name = target
            # clone_zone = clone_sim.FindChild[Models.Core.Zone]()
            # clone_zone.Name = target

            # self.Simulations.Children.Clear(clone_sim.Name)
            self.Simulations.Children.Add(clone_sim)
        self._reload_saved_file()
        return self

    def remove_simulation(self, simulation):
        """Remove a simulation from the model

            Parameters
            ----------
            simulation
                The name of the simulation to remove
        """

        sim = self._find_simulation(simulation)
        self.Simulations.Children.Remove(sim)
        self.save_edited_file()

    @property
    def extract_simulation_name(self):
        warnings.warn(
            'extract_simulation_name is deprecated for future versions use simulation_names or get_simulation_names')
        """print or extract a simulation name from the model

            Parameters
            ----------
            simulation
                The name of the simulation to remove
        """
        # this is a repetition because I want to deprecate it and maintain simulation_name or use get_simulation_name
        return self.simulation_names

    def clone_zone(self, target, zone, simulation=None):
        """Clone a zone and add it to Model

            Parameters
            ----------
            target
                 simulation name
            zone
                Name of the zone to clone
            simulation, optional
                Simulation name to be cloned, of None clone the first simulation in model
        """

        sim = self._find_simulation(simulation)
        zone = sim.FindChild[Models.Core.Zone](zone)
        clone_zone = Models.Core.Apsim.Clone(zone)
        clone_zone.Name = target
        sim.Children.Add(clone_zone)
        self.save_edited_file(reload=True)
        return self

    def find_zones(self, simulation):
        """Find zones from a simulation

            Parameters
            ----------
            simulation
                 name

            Returns
            -------
                list of zones as APSIM Models.Core.Zone objects
        """

        sim = self._find_simulation(simulation)
        zones = sim.FindAllDescendants[Models.Core.Zone]()
        return list(zones)

    @property  #
    def extract_report_names(self):
        ''' returns all data frame the available report tables'''
        table_list = get_db_table_names(self.datastore)
        rm = ['_InitialConditions', '_Messages', '_Checkpoints', '_Units']
        return [im for im in table_list if im not in rm]

    # perhaps a good a example of how to edit cultvar
    def adjust_rue(self, csr, cultivar_name='B_110', base_csr=2):  # Iowa only
        CSR = csr ** np.log(1 / csr) * base_csr,
        command = '[Leaf].Photosynthesis.RUE.FixedValue',
        self.edit_cultivar(cultivar_name, commands=command, values=CSR)
        return self

    def replicate_file(self, k, path=None, tag="replica"):
        """
        Replicates a file 'k' times.

        If a path is specified, the copies will be placed in that directory with incremented filenames.
        If no path is specified, copies are created in the same directory as the original file, also with incremented filenames.

        Parameters:
        - self: The core.api.APSIMNG object instance containing 'path' attribute pointing to the file to be replicated.
        - k (int): The number of copies to create.
        - path (str, optional): The directory where the replicated files will be saved. Defaults to None, meaning the same directory as the source file.
        - tag (str, optional): a tag to attached with the copies. Defaults to "replicate"


        Returns:
        - A list of paths to the newly created files if get_back_list is True else a generator is returned.
        """
        if path is None:
            file_name = self.path.rsplit('.apsimx', 1)[0]
            return [shutil.copy(self.model_info.path, f"{file_name}_{tag}_{i}_.apsimx") for i in range(k)]

        else:
            b_name = os.path.basename(self.path).rsplit('.apsimx', 1)[0]
            return [shutil.copy(self.model_info.path, os.path.join(path, f"{b_name}_{tag}_{i}.apsimx")) for i in
                    range(k)]

    def _cultivar_params(self, cultivar):
        """
         returns all params in a cultivar
        """

        cmd = cultivar.Command
        params = {}
        for c in cmd:
            if c:
                p, v = c.split("=")
                params[p.strip()] = v.strip()
        return params

    def _find_replacement(self):
        rep = self.Simulations.FindChild[Models.Core.Folder]()
        return rep

    def _find_cultvar(self, CultvarName):

        rep = self._find_replacement().FindAllDescendants[Models.PMF.Cultivar]()
        xp = [i for i in rep]
        for cult in xp:
            if cult.Name == CultvarName:
                return cult
                break
        return rep

    def read_cultvar_params(self, name, verbose=None):
        cultvar = self._find_cultvar(name)
        c_param = self._cultivar_params(cultvar)
        if verbose:
            for i in c_param:
                print(f"{i} : {c_param[i]} \n")
        return c_param

    def get_crop_replacement(self, Crop):
        """
        :param Crop: crop to get the replacement
        :return: System.Collections.Generic.IEnumerable APSIM plant object
        """
        replace_attrib = Crop + '_Replacement'
        rep = self._find_replacement()
        crop_rep = rep.FindAllDescendants[Models.PMF.Plant](Crop)
        for i in crop_rep:
            print(i.Name)
            if i.Name == Crop:
                return i
        return self

    def edit_cultivar(self, CultivarName, commands: tuple, values: tuple):
        """
        Edits the parameters of a given cultivar.

        :param CultivarName: Name of the cultivar (e.g., 'laila').
        :param commands: A tuple of strings representing the parameter paths to be edited.
                         Example: ('[Grain].MaximumGrainsPerCob.FixedValue', '[Phenology].GrainFilling.Target.FixedValue')
        :param values: A tuple containing the corresponding values for each command (e.g., (721, 760)).
        :return: None
        """
        if not isinstance(CultivarName, str):
            raise ValueError("Cultivar name must be a string")
        if not (isinstance(commands, (tuple, list)) and isinstance(values, (tuple, list))):
            raise ValueError("Commands and values must be presented as a tuple or a list")
        if len(commands) != len(values):
            raise ValueError("The length of values and commands must be equal")

        cultvar = self._find_cultvar(CultivarName)
        if cultvar is None:
            raise ValueError(f"Cultivar '{CultivarName}' not found")

        params = self._cultivar_params(cultvar)
        for command, value in zip(commands, values):
            params[command] = value  # Update or add the command with its new value

        # Prepare the command strings for setting the updated parameters
        updated_commands = [f"{k}={v}" for k, v in params.items()]
        cultvar.set_Command(updated_commands)

        return self

    def get_current_cultvar_name(self, ManagerName):
        try:
            ap = self.extract_user_input(ManagerName)['CultivarName']
            return ap
        except  KeyError:
            parameterName = 'CultivarName'
            print(f"cultivar name: is not found")

    # summarise results by any statistical element
    @staticmethod
    def get_result_stat(df, column, statistic):

        # Define a dictionary mapping statistic names to corresponding functions
        stat_functions = {
            'mean': lambda x: x.mean(),
            'max': lambda x: x.max(),
            'median': lambda x: x.median(),
            'min': lambda x: x.min(),
            'std': lambda x: x.std(),
            'first': lambda x: x.iloc[0],
            'last': lambda x: x.iloc[-1],
            'diff': lambda x: x.iloc[-1] - x.iloc[0]
        }

        # Get the desired statistic function from the dictionary
        func = stat_functions.get(statistic)

        if func is None:
            raise ValueError(
                "Invalid statistic. Supported statistics are 'mean', 'max', 'median', 'std', 'first', and 'last'.")

        # Calculate the desired statistic for the specified column
        result = func(df[column])

        return result

    @staticmethod
    def generate_unique_name(base_name, length=6):
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=length))
        unique_name = base_name + '_' + random_suffix
        return unique_name

    # clone apsimx file by generating unquie name
    def copy_apsim_file(self):
        path = os.getcwd()
        file_path = opj(path, self.generate_unique_name("clones")) + ".apsimx"
        shutil.copy(self.path, file_path)

    def summarize_output_variable(self, var_name, table_name='Report'):
        data = self.results[table_name]

        dic = {}
        index = ['stat']
        for i in ['mean', 'max', 'min', 'first', 'last', 'std', 'diff']:
            varname = f"{var_name}_" + i
            dic[varname] = APSIMNG.get_result_stat(data, var_name, i)
        output_variable_statistics = pd.DataFrame(dic, index=index)
        return output_variable_statistics

    @timer
    def collect_data_for_specific_crop(self, crop, rotation, variable, report_name, statistic):
        assert isinstance(crop, str), "crop name must be a string"
        assert isinstance(rotation, str), "Rotation name must tbe a string"
        if crop in rotation:
            df = self.results[report_name]
            result = self.get_result_stat(df, column=variable, statistic=statistic)
            return result

    @staticmethod
    def collect_specific_report(results, report_names, var_names, stat):
        """_summary_

        Args:
            results (_dict_): diction of apsim results table generated by run method
            report_names (_str_): _report name_
            var_names (_list_): _description_
            Statistic (_list_): how to summary the data supported versions are mean, median, last ,start standard deviation
            statistics and var names should be the order ['yield', 'carbon'] and ['mean', 'diff'], where mean for yield and diff for carbon, respectively
        """
        varnames = var_names
        stat = stat
        data = results[report_names]
        return data

    def update_cultivar(self, parameters, simulations=None, clear=False):
        """Update cultivar parameters

        Parameters
        ----------
        parameters
            Parameter = value dictionary of cultivar paramaters to update.
        simulations, optional
            List of simulation names to update, if `None` update all simulations.
        clear, optional
            If `True` remove all existing parameters, by default `False`.
        """
        for sim in self.find_simulations(simulations):
            zone = sim.FindChild[Models.Core.Zone]()
            cultivar = zone.Plants[0].FindChild[Models.PMF.Cultivar]()
            if clear:
                params = parameters
            else:
                params = self._cultivar_params(cultivar)
                params.update(parameters)
            cultivar.Command = [f"{k}={v}" for k, v in params.items()]

            self.cultivar_command = params

    def examine_management_info(self, simulations=None):
        """this will show the current management scripts in the simulation root

        Parameters
        ----------
        simulations, optional
            List of simulation names to update, if `None` show all simulations. if you are not sure,

            use the property decorator 'extract_simulation_name'
        """
        try:
            for sim in self.find_simulations(simulations):
                zone = sim.FindChild[Models.Core.Zone]()
                print("Zone:", zone.Name)
                for action in zone.FindAllChildren[Models.Manager]():
                    print("\t", action.Name, ":")
                    for param in action.Parameters:
                        print("\t\t", param.Key, ":", param.Value)
        except Exception as e:
            print(repr(e))
            raise Exception(repr(e))

    @cache
    def return_zone(self, simulations=None):
        self.find_simulations(simulations)

    def check_som(self, simulations=None):
        for sim in self.find_simulations(simulations):
            zone = sim.FindChild[Models.Core.Zone]()

            som1 = zone.FindChild('SurfaceOrganicMatter')

            field = zone.Name
            sname = sim.Name

            som_path = f'{zone.FullPath}.SurfaceOrganicMatter'
            if som_path:
                som = zone.FindByPath(som_path)
            if som:
                return som.Value.InitialResidueMass, som.Value.InitialCNR
            else:
                raise Exception("File node structure is not supported at a moment")

    def change_som(self, simulations=None, inrm: int = 1250, icnr: int = 27):
        """
         Change Surface Organic Matter (SOM) properties in specified simulations.

    Parameters:
        simulations (str ort list): List of simulation names to target (default: None).
        inrm (int): New value for Initial Residue Mass (default: 1250).
        icnr (int): New value for Initial Carbon to Nitrogen Ratio (default: 27).

    Returns:
        self: The current instance of the class.
        """
        som = None
        for sim in self.find_simulations(simulations):
            zone = sim.FindChild[Models.Core.Zone]()
            som1 = zone.FindChild('SurfaceOrganicMatter')
            field = zone.Name
            sname = sim.Name

            som_path = f'{zone.FullPath}.SurfaceOrganicMatter'
            if som_path:
                som = zone.FindByPath(som_path)
            if som:
                som.Value.InitialResidueMass = inrm
                som.Value.InitialCNR = icnr
            else:
                raise NotImplementedError(
                    "File node structure is not supported at a moment. please rename your SOM module to "
                    "SurfaceOrganicMatter")
            # mp.Value.InitialResidueMass

            return self

    @property
    def FindAllReferencedFiles(self):
        return self.Simulations.FindAllReferencedFiles()

    def RevertCheckpoint(self):
        self.Simulations = self.Simulations.RevertCheckpoint('new_model')
        return self

    def update_management_decissions(self, management, simulations=None, out=None):
        """Update management, handles multiple managers in a loop

        Parameters
        ----------
        management: a list of dictionaries of management paramaters or a dictionary with keyvarlue pairs of parameters and associated values, respectivelyto update. examine_management_info` to see current values.
        make a dictionary with 'Name' as the for the of  management script
        simulations, optional
            List of simulation names to update, if `None` update all simulations not recommended.
        reload, optional
            _description_ defaults to True
            out: bool, optional specifies the new filename
        """
        if not isinstance(management, list):
            management = [management]
        # from apsimx.utils import KeyValuePair
        for sim in self.find_simulations(simulations):
            zone = sim.FindChild[Models.Core.Zone]()
            atn = []
            for action in zone.FindAllChildren[Models.Manager]():
                for managementt in management:
                    if action.Name == managementt["Name"]:
                        values = managementt
                        for i in range(len(action.Parameters)):
                            param = action.Parameters[i].Key

                            if param in values:
                                fvalue = f"{values[param]}"
                                action.Parameters[i] = KeyValuePair[String, String](param, fvalue)

                                # action.Parameters[i]= {param:f"{values[param]}"}
        # self.examine_management_info()                # action.GetParametersFromScriptModel()
        self.path = out or self.out_path
        self.save_edited_file(outpath=self.path)
        self.load_apsimx_model()

    # experimental
    def update_manager(self, **kwargs):
        """
        updates a single management script by kew word arguments. it is thread safe to call this during multiple processing
        kwargs can be the key value pairs of the parameters of the management script, if Name if the script is not specified, updates will not be successfull
        """
        manager = self.Simulations.FindAllInScope[Models.Manager](kwargs['Name'])
        manager_scripts = [i for i in manager]
        for single in manager_scripts:
            for i in range(len(single.Parameters)):
                kvp = single.Parameters[i]
                if kvp.Key in kwargs.keys():
                    updated_kvp = KeyValuePair[str, str](kvp.Key, kwargs[kvp.Key])
                    single.Parameters[i] = updated_kvp
            # Serialize the model to JSON string

        _json_string = Models.Core.ApsimFile.FileFormat.WriteToString(self.Simulations)
        fileName = kwargs.get('out_path') or self.model_info.path
        self.Simulations = Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](_json_string,
                                                                                                    None, True,
                                                                                                    fileName=fileName)
        return self

    def update_mgt(self, management, simulations=None, out=None):
        """Update management, handles one manager at a time

        Parameters
        ----------
        management

            Parameter = value dictionary of management parameters to update. examine_management_info` to see current 
            values. make a dictionary with 'Name' as the for the of management script simulations, optional List of 
            simulation names to update, if `None` update all simulations not recommended. 
            :param out (str or pathlike ): to harmonize a database path after editing note: No need to reload any
             more that should be called with save_edited_file method, 
            we just don't want to make a lot of evaluations while running batch files
            
        """
        if not isinstance(management, list):
            management = [management]

        for sim in self.find_simulations(simulations):
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
        out_mgt_path = out or self.out_path or self.model_info.path
        self.restart_model(model_info=recompile(self.Simulations, out=out_mgt_path))
        return self

    # immediately open the file in GUI
    def show_file_in_APSIM_GUI(self):
        os.startfile(self.path)

    def _kvtodict(self, kv):
        return {kv[i].Key: kv[i].Value for i in range(kv.Count)}

    def extract_user_input(self, manager_name):
        """Get user_input of a given model manager script
        returns;  a dictionary
        """

        for sim in self.simulations:
            actions = sim.FindAllDescendants[Models.Manager]()
            out = {"simulation": sim.Name}
            for action in actions:
                if action.Name == manager_name:
                    params = self._kvtodict(action.Parameters)
                    return params

    @staticmethod
    def strip_time(date_string):
        date_object = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        formatted_date_string = date_object.strftime("%Y-%m-%dT%H:%M:%S")
        return formatted_date_string  # Output: 2010-01-01T00:00:00

    def change_simulation_dates(self, start_date=None, end_date=None, simulations=None):
        """Set simulation dates. this is important to run this method before run the weather replacement method as
        the date needs to be alligned into weather

        Parameters
        -----------------------------------
        start_date, optional
            Start date as string, by default `None`
        end_date, optional
            End date as string, by default `None`
        simulations, optional
            List of simulation names to update, if `None` update all simulations
        """
        for sim in self.find_simulations(simulations):
            clock = sim.FindChild[Models.Clock]()

            if start_date is not None:
                dateString1 = start_date
                self.start = DateTime.Parse(dateString1)
                clock.Start = self.start

            if end_date is not None:
                dateString2 = end_date
                self.end = DateTime.Parse(dateString2)
                clock.End = self.end

    @property
    def extract_dates(self, simulations=None):
        """Get simulation dates in the model

        Parameters
        ----------
        simulations, optional
            List of simulation names to get, if `None` get all simulations
        Returns
        -------
            Dictionary of simulation names with dates
        """
        dates = {}
        for sim in self.find_simulations(simulations):
            clock = sim.FindChild[Models.Clock]()
            st = clock.Start
            et = clock.End
            dates[sim.Name] = {}
            dates[sim.Name]["start"] = datetime.date(st.Year, st.Month, st.Day)
            dates[sim.Name]["end"] = datetime.date(et.Year, et.Month, et.Day)
        return dates

    def extract_start_end_years(self, simulations=None):
        """Get simulation dates

        Parameters
        ----------
        simulations, optional
            List of simulation names to get, if `None` get all simulations
        Returns
        -------
            Dictionary of simulation names with dates
        """
        dates = {}
        for sim in self.find_simulations(simulations):
            clock = sim.FindChild[Models.Clock]()
            start = clock.Start
            end = clock.End
        return start.Year, end.Year

    @property
    def met(self):
        return self._met

    @met.setter
    def met(self, value):
        self._met = value

    def change_met(self):
        self.replace_met_file(self.met)
        return self

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

    def show_met_file_in_simulation(self):
        """Show weather file for all simulations"""
        for weather in self.Simulations.FindAllDescendants[Weather]():
            return weather.FileName

    def change_report(self, command: str, report_name='Report', simulations=None, set_DayAfterLastOutput=None):
        """
            Set APSIM report variables for specified simulations.

        This function allows you to set the variable names for an APSIM report
        in one or more simulations.

        Parameters
        ----------
        command : str
            The new report string that contains variable names.
        report_name : str
            The name of the APSIM report to update defaults to Report.
        simulations : list of str, optional
            A list of simulation names to update. If `None`, the function will
            update the report for all simulations.

        Returns
        -------
        None
        """
        simulations = self.find_simulations(simulations)
        for sim in simulations:
            i_enum = sim.FindAllDescendants[Models.Report](report_name)
            for rep in i_enum:
                rep.set_VariableNames(command.strip().splitlines())
                if set_DayAfterLastOutput:
                    rep.set_DayAfterLastOutput = set_DayAfterLastOutput
        return rep

    def get_report(self, simulation=None):
        """Get current report string

        Parameters
        ----------
        simulation, optional
            Simulation name, if `None` use the first simulation.
        Returns
        -------
            List of report lines.
        """
        sim = self._find_simulation(simulation)
        for si in sim:
            report = (si.FindAllDescendants[Models.Report]())
            print(list(report))

    def extract_soil_physical(self, simulation=None):
        """Find physical soil

        Parameters
        ----------
        simulation, optional
            Simulation name, if `None` use the first simulation.
        Returns
        -------
            APSIM Models.Soils.Physical object
        """
        for simu in self._find_simulation(simulation):
            soil_object = simu.FindDescendant[Soil]()
            physical_soil = soil_object.FindDescendant[Physical]()
            return physical_soil

    def extract_any_soil_physical(self, parameter, simulation=None):
        """extracts soil physical parameters in the simulation

        Args:
            parameter (_string_): string e.g DUL, SAT
            simulation (string, optional): Targeted simulation name. Defaults to None.
        ---------------------------------------------------------------------------
        returns an array of the parameter values
        """
        assert isinstance(parameter, str) == True, "Soil parameter name must be a string"
        soil_physical = self.extract_soil_physical(simulation)
        soilp_param = getattr(soil_physical, parameter)
        return list(soilp_param)

    def replace_any_soil_physical(self, parameter: str, param_values, simulation: str = None):
        """relaces specified soil physical parameters in the simulation

        ______________________________________________________
        Args:
            parameter (_string_, required): string e.g DUL, SAT. open APSIMX file in the GUI and examne the phyicals node for clues on the parameter names
            simulation (string, optional): Targeted simulation name. Defaults to None.
            param_values (array, required): arrays or list of values for the specified parameter to replace
        """
        assert len(param_values) == len(
            self.extract_any_soil_physical(parameter, simulation)), 'lengths are not equal please try again'
        soil_physical = self.extract_soil_physical(simulation)
        setattr(soil_physical, parameter, param_values)

    # find organic paramters
    def extract_soil_organic(self, simulation=None):
        """Find physical soil

        Parameters
        ----------
        simulation, optional
            Simulation name, if `None` use the first simulation.
        Returns
        -------
            APSIM Models.Soils.Physical object
        """
        for simu in self.find_simulations(simulation):
            soil_object = simu.FindDescendant[Soil]()
            organic_soil = soil_object.FindDescendant[Organic]()
            return organic_soil

    def _extract_solute(self, simulation=None):
        # find the solute node in the simulation
        sim = self._find_simulation(simulation)
        solutes = sim.FindAllDescendants[Models.Soils.Solute]()
        return solutes

    def extract_any_solute(self, parameter: str, simulation=None):
        """
        Parameters
        ____________________________________
        parameter: parameter name e.g NO3
        simulation, optional
            Simulation name, if `None` use the first simulation.
        returns
        ___________________
        the solute array or list
        """
        solutes = self._extract_solute(simulation)
        sol = getattr(solutes, parameter)
        return list(sol)

    def replace_any_solute(self, parameter: str, values: list, simulation=None):
        """# replaces with new solute

        Parameters
        ____________________________________
        parameter: paramter name e.g NO3
        values: new values as a list to replace the old ones
        simulation, optional
            Simulation name, if `None` use the first simulation.
        """
        solutes = self._extract_solute(simulation)
        setattr(solutes, parameter, values)

    def extract_any_soil_organic(self, parameter, simulation=None):
        """extracts any specified soil  parameters in the simulation

        Args:
            parameter (_string_, required): string e.g Carbon, FBiom. open APSIMX file in the GUI and examne the phyicals node for clues on the parameter names
            simulation (string, optional): Targeted simulation name. Defaults to None.
            param_values (array, required): arrays or list of values for the specified parameter to replace
        """
        assert isinstance(parameter, str) == True, "Soil parameter name must be a string"
        soil_organic = self.extract_soil_organic(simulation)
        get_organic = getattr(soil_organic, parameter)
        return list(get_organic)

    def replace_any_soil_organic(self, parameter, param_values, simulation=None):
        """replaces any specified soil  parameters in the simulation

        Args:
            parameter (_string_, required): string e.g Carbon, FBiom. open APSIMX file in the GUI and examne the phyicals node for clues on the parameter names
            simulation (string, optional): Targeted simulation name. Defaults to None.
            param_values (array, required): arrays or list of values for the specified parameter to replace
        """
        assert len(param_values) == len(
            self.extract_any_soil_organic(parameter, simulation)), 'lengths are not equal please try again'
        soil_organic = self.extract_soil_organic(simulation)
        setattr(soil_organic, parameter, param_values)

    # Find a list of simulations by name
    def extract_crop_soil_water(self, parameter, crop="Maize", simulation=None):
        """_summary_

        Args:
            parameter (_str_): crop soil water parameter names e.g. LL, XF etc
            crop (str, optional): crop name. Defaults to "Maize".
            simulation (_str_, optional): _target simulation name . Defaults to None.

        Returns:
            _type_: _description_
        """
        assert isinstance(parameter, str), 'Parameter name should be a string'
        assert isinstance(crop, str), "Crop name should be a string"
        for simu in self.find_simulations(simulation):
            soil_object = simu.FindDescendant[Soil]()
            soil_crop = soil_object.FindAllDescendants[SoilCrop]()
            # can be use to target specific crop
            for crops in soil_crop:
                crop_soil = crop + "Soil"
                if crops.Name == crop_soil:
                    param_values = getattr(crops, parameter)
                    return list(param_values)

    def replace_crop_soil_water(self, parameter, param_values, crop="Maize", simulation=None):
        """_summary_

        Args:
            parameter (_str_): crop soil water parameter names e.g. LL, XF etc
            crop (str, optional): crop name. Defaults to "Maize".
            simulation (_str_, optional): _target simulation name . Defaults to None.
             param_values (_list_ required) values of LL of istance list or 1-D arrays

        Returns:
            doesn't return anything it mutates the specified value in the soil simulation object
        """
        assert len(param_values) == len(self.extract_crop_soil_water(parameter, crop, simulation))
        assert isinstance(parameter, str), 'Parameter name should be a string'
        assert isinstance(crop, str), "Crop name should be a string"
        for simu in self.find_simulations(simulation):
            soil_object = simu.FindDescendant[Soil]()
            soil_crop = soil_object.FindAllDescendants[SoilCrop]()
            # can be use to target specific crop
            for crops in soil_crop:
                crop_soil = crop + "Soil"
                if crops.Name == crop_soil:
                    setattr(crops, parameter, param_values)
                    break

    def find_simulations(self, simulations=None):
        """Find simulations by name

        Parameters
        ----------
        simulations, optional
            List of simulation names to find, if `None` return all simulations
        Returns
        -------
            list of APSIM Models.Core.Simulation objects
        """

        if simulations is None:
            return self.simulations
        if type(simulations) == str:
            simulations = [simulations]
        sims = []
        for s in self.simulations:
            if s.Name in simulations:
                sims.append(s)
        if len(sims) == 0:
            print("Not found!")
        else:
            return sims

    # Find a single simulation by name
    def _find_simulation(self, simulation=None):
        if simulation is None:
            return self.simulations  # removed [0]
        sim = None
        for s in self.simulations:
            if s.Name == simulation:
                sim = s
                break
        if sim is None:
            print("Not found!")
        else:
            return sim

    @staticmethod
    def adjustSatDul(sat_, dul_):
        for enum, (s, d) in enumerate(zip(sat_, dul_)):
            # first check if they are equal
            # if d is greater than s, then by what value?, we need this value to add it to 0.02
            #  to be certain all the time that dul is less than s we subtract the summed value
            if d >= s:

                diff = d - s
                if diff == 0:
                    dul_[enum] = d - 0.02
                else:
                    dul_[enum] = d - (diff + 0.02)

            else:
                dul_[enum] = d
        return dul_

    def set_swcon(self, swcon, simulations=None, thickness_values=None):
        """Set soil water conductivity (SWCON) constant for each soil layer.

        Parameters
        ----------
        swcon
            Collection of values, has to be the same length as existing values.
        simulations, optional
            List of simulation names to update, if `None` update all simulations
            :param thickness_values: the soil profile thickness values
        """
        for sim in self.find_simulations(simulations):
            wb = sim.FindDescendant[Models.WaterModel.WaterBalance]()
            assert len(wb.Thickness) == len(
                thickness_values), "trying to set different thickness values to the existing ones"
            wb.SWCON = swcon

    def get_swcon(self, simulation=None):
        """Get soil water conductivity (SWCON) constant for each soil layer.

        Parameters
        ----------
        simulation, optional
            Simulation name.
        Returns
        -------
            Array of SWCON values
        """
        sim = self._find_simulation(simulation)
        wb = sim.FindDescendant[Models.WaterModel.WaterBalance]()
        return np.array(wb.SWCON)

    def plot_objectives(self, x, *args, **kwargs):
        """

        :param x: x variable to go on the x- axis
        :param args: y variables to plotted against the x variable, e.g 'Maize yield'
        :param kwargs: key word argument specifying the report name e.g report = "Annual"
        :return: graph
        """
        assert self.results, "Please run the apsim simulation first"
        assert len(kwargs) == 1, "Please provide atleast one report table"
        assert isinstance(x, str), 'x variable must be a string'
        report_name = [p for p in kwargs.values()][0]
        report_table = self.results[report_name]
        for y in args:
            assert y in report_table.columns, f"Column '{y}' must be in the data frame."
        x_variable = report_table[x]
        for obj, y in enumerate(args):
            y_variable = report_table[y]
            print(len(y))

            plt.figure(figsize=(7, 5))
            plt.plot(x_variable, y_variable)
            plt.title(f"{x} vs {y} plot")
            plt.xlabel(f"{x}")  # Add x-axis label
            plt.ylabel(f"{y}")
            plt.show()

    def extract_soil_profile(self, simulation=None):
        """Get soil definition as dataframe

        Parameters
        ----------
        simulation, optional
            Simulation name.
        Returns
        -------
            Dataframe with soil definition
        """
        sat = self.get_sat(simulation)
        dul = self.get_dul(simulation)
        ll15 = self.get_ll15(simulation)
        cll = self.get_crop_ll(simulation)
        psoil = self.find_physical_soil(simulation)
        depth = psoil.Depth
        return pd.DataFrame({"Depth": depth, "LL15": ll15, "DUL": dul, "SAT": sat, "Crop LL": cll,
                             "Bulk density": self.get_bd(simulation),
                             "SWCON": self.get_swcon(simulation),
                             "Initial NO3": self.get_initial_no3(simulation),
                             "Initial NH4": self.get_initial_nh4(simulation)})

    def _find_solute(self, solute, simulation=None):
        sim = self._find_simulation(simulation)
        solutes = sim.FindAllDescendants[Models.Soils.Solute]()
        return [s for s in solutes if s.Name == solute][0]

    def clear_db(self):
        """
        Clears the attributes of the object and optionally deletes associated files.

        If the `copy` attribute is set to True, this method will also attempt to delete
        files at `self.path` and `self.datastore`. This is a destructive operation and
        should be used with caution.

        Returns:
           >>None: This method does not return a value.
           >> Please proceed with caution, we assume that if you want to clear the model objects, then you don't need them
           but by making copy compulsory, then, we are clearing the edited files
        """
        self._DataStore.Close()
        Path(self.path).unlink(missing_ok=True)
        Path(self.path.strip('apsimx') + "db-wal").unlink(missing_ok=True)
        Path(self.path.strip('apsimx') + "bak").unlink(missing_ok=True)
        self._DataStore.Dispose()
        Path(self.datastore).unlink(missing_ok=True)

        return self

    def clear(self):
        """
        Clears the attributes of the object and optionally deletes associated files.

        If the `copy` attribute is set to True, this method will also attempt to delete
        files at `self.path` and `self.datastore`. This is a destructive operation and
        should be used with caution.

        Returns:
           >>None: This method does not return a value. 
           >> Please proceed with caution, we assume that if you want to clear the model objects, then you don't need them
           but by making copy compulsory, then, we are clearing the edited files
        """
        Path(self.path.strip('apsimx') + "db-shm").unlink(missing_ok=True)
        Path(self.path).unlink(missing_ok=True)
        Path(self.path.strip('apsimx') + "db-wal").unlink(missing_ok=True)
        Path(self.path.strip('apsimx') + "bak").unlink(missing_ok=True)
        Path(self.datastore).unlink(missing_ok=True)
        self.Simulations = None
        self._DataStore = None

    def replace_soil_organic(self, organic_name, simulation_name=None):
        """replace the organic module comprising Carbon , FBIOm, FInert/ C/N

        Args:
            organic_name (_str_): _description_
            simulation (_str_, optional): _description_. Defaults to None.
        """
        # sim = self._find_simulation(simulation_name)
        # organic = sim.FindAllDescendants[Models.Soils.Organic]()
        # if organic.name  = organic_name:
        #     organic.

    def _get_initial_values(self, name, simulation):
        s = self._find_solute(name, simulation)
        return np.array(s.InitialValues)

    def _set_initial_solute_values(self, name, values, simulations):
        sims = self.find_simulations(simulations)
        for sim in sims:
            s = self._find_solute(name, sim.Name)
            s.InitialValues = values

    def set_initial_nh4(self, values, simulations=None):
        """Set soil initial NH4 content

        Parameters
        ----------
        values
            Collection of values, has to be the same length as existing values.
        simulations, optional
            List of simulation names to update, if `None` update all simulations
        """

        self._set_initial_values("NH4", values, simulations)

    def get_initial_urea(self, simulation=None):
        """Get soil initial urea content"""
        return self._get_initial_values("Urea", simulation)

    def set_initial_urea(self, values, simulations=None):
        """Set soil initial urea content

        Parameters
        ----------
        values
            Collection of values, has to be the same length as existing values.
        simulations, optional
            List of simulation names to update, if `None` update all simulations
        """
        self._set_initial_values("Urea", values, simulations)
        # inherit properties from the ancestors apsimng object


# ap = dat.GetDataUsingSql("SELECT * FROM [MaizeR]")
class ApsiMet(APSIMNG):
    def __init__(self, model: Union[str, Simulations], copy=True, out_path=None, lonlat=None, simulation_names=None):
        super().__init__(model, copy, out_path)
        self.lonlat = lonlat
        self.simulation_names = simulation_names

    def insertweather_file(self):
        start, end = self.extract_start_end_years()
        wp = weather.daymet_bylocation(self.lonlat, start=start, end=end)
        wp = os.path.join(os.getcwd(), wp)
        if self.simulation_names:
            sim_name = list(self.simulation_names)
        else:
            sim_name = self.extract_simulation_name  # because it is a property decorator
        self.replace_met_file(wp, sim_name)


if __name__ == '__main__':

    # test
    from pathlib import Path
    from time import perf_counter

    # Model = FileFormat.ReadFromFile[Models.Core.Simulations](model, None, False)
    os.chdir(Path.home())
    from apsimNGpy.core.base_data import LoadExampleFiles

    al = LoadExampleFiles(Path.cwd())
    modelm = al.get_maize

    model = APSIMNG(model=None, out_path='me.apsimx')
    for _ in range(1):

        for rn in ['Maize, Soybean, Wheat', 'Maize', 'Soybean, Wheat']:
            a = perf_counter()
            # model.RevertCheckpoint()

            model.update_manager(Name="Simple Rotation", Crops=rn)

            b = perf_counter()

            print(b - a, 'seconds')
            model.run('Carbon')
            print(model.results.mean(numeric_only=True))
        model.clear_links()
        a = perf_counter()

        res = model.run_simulations(reports="MaizeR", clean_up=False, results=True)
        b = perf_counter()
        print(b - a, 'seconds')
        mod = model.Simulations
        # xp = mod.FindAllInScope[Models.Manager]('Simple Rotation')
        # a = [i for i in xp]
        # for p in a:
        #  for i in range(len(p.Parameters)):
        #      kvp =p.Parameters[i]
        #      if kvp.Key == "Crops":
        #          updated_kvp = KeyValuePair[str, str](kvp.Key, "UpdatedValue")
        #          p.Parameters[i] = updated_kvp
        #      print(p.Parameters[i])
