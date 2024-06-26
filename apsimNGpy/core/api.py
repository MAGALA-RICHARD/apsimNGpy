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
from Models.Core import Simulations, ScriptCompiler
from System import *
from Models.Core.ApsimFile import FileFormat
from Models.Climate import Weather
from Models.Soils import Soil, Physical, SoilCrop, Organic
import Models
from Models.PMF import Cultivar
from apsimNGpy.core.apsim_file import XFile as load_model


# from settings import * This file is not ready and i wanted to do some test


# decorator to monitor performance
def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        print(f"{func.__name__} took {elapsed_time:.4f} seconds to execute.")
        return result

    return wrapper


class APSIMNG:
    """Modify and run Apsim next generation simulation models."""

    def __init__(self, model=None, out_path=None, out=None, read_from_string=True, load=True, **kwargs):

        self._DataStore = None
        self._met = None
        self.path = None
        if kwargs.get('copy'):
            warnings.warn(
                'copy argument is deprecated, it is now mandatory to copy the model in order to conserve the original model.')
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
        self.copy = True  # Mandatory to conserve the original file
        self.results = None
        self.Model = None
        self.load = load
        self.datastore = None
        self._str_model = None
        self._model = model if model is not None else load_model
        self.out_path = out

        self.load_apsimx_from_string()

    @property
    def set_model(self):
        return self._model

    @set_model.setter
    def set_model(self, value):
        self._model = value

        # self.Model = self.load_apsimx_from_string()

    def _init_from_file(self, read_from_string: bool):
        """Initialize the object from a file path."""
        apsimx_file = os.path.realpath(self._model)
        self._name, self._ext = os.path.splitext(self._model)

        copy_path = self._copy_file()
        self.path = copy_path

        if read_from_string:
            self.load_apsimx_from_string(self.path)
        else:
            self._load_apsimx(self.path)

    def clear_links(self):
        self.Model.ClearLinks()
        return self

    def ClearSimulationReferences(self):
        self.Model.ClearSimulationReferences()
        return self

    def _copy_file(self) -> str:
        """Copy the apsimx file and remove related database files."""
        if self.out_path is None:
            copy_path = f"{self._name}_copy{self._ext}"
        else:
            copy_path = self.out_path

        try:
            shutil.copy(self._model, copy_path)
            self._remove_related_files(self._name)
        except PermissionError as e:
            print(f"PermissionError: {e}")
            raise

        return copy_path

    @staticmethod
    def _remove_related_files(_name):
        """Remove related database files."""
        for suffix in ["", "-shm", "-wal"]:
            db_file = pathlib.Path(f"{_name}.db{suffix}")
            db_file.unlink(missing_ok=True)

    def _init_from_simulations(self, model: Simulations):
        """Initialize the object from a Simulations object."""
        self.Model = model
        self.datastore = self.Model.FindChild[Models.Storage.DataStore]().FileName
        self._DataStore = self.Model.FindChild[Models.Storage.DataStore]()

    @staticmethod
    def generate_unique_name(base_name, length=6):
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=length))
        unique_name = base_name + '_' + random_suffix
        return unique_name

    @property
    def filename(self):
        self.file_name = os.path.basename(self.path)
        return self.file_name

    # searches the simulations from aspsim models.core object
    @property
    def simulations(self):
        try:
            simus = list(self.Model.FindAllChildren[Models.Core.Simulation]())
            if len(simus) != 0:
                return list(self.Model.FindAllChildren[Models.Core.Simulation]())
            else:
                experiment = self.Model.FindAllChildren[Models.Factorial.Experiment]()

                for i in experiment:
                    simus = list(i.FindAllChildren[Models.Core.Simulation]())

                return (simus)

        except Exception as e:
            print(type(e), "occured")
            raise Exception(type(e))

    @property
    def str_model(self):
        return json.dumps(self._str_model)

    @str_model.setter
    def str_model(self, value: dict):
        self._str_model = json.dumps(value)

    def load_from_memory(self, file_name):
        str_ = self.str_model
        self.Model = Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](str_, None, True,
                                                                                              fileName=file_name)
        self.datastore = self.Model.FindChild[Models.Storage.DataStore]().UpdateFileName()
        self.Model.ClearSimulationReferences()

        return self

    # loads the apsimx file into memory but from string

    def load_apsimx_from_string(self):

        """
        :param _data: data can be a STRING PATH, A DICTIONARY FOR APSIM SIMULATION OBJECT OR A A STING
        :return: Model object
        """
        if isinstance(self._model, str):
            with open(self._model, "r+", encoding='utf-8') as apsimx:
                app_ap = json.load(apsimx)
            string_name = json.dumps(app_ap)
            self.Model = Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](string_name, None,
                                                                                                  True,
                                                                                                  fileName=self._model)

        elif isinstance(self._model, dict):

            str_ = json.dumps(self._model)
            if self.out_path:
                string_nam = self.out_path
                self.path = self.out_path
            else:

                string_nam = os.path.join(os.getcwd(), APSIMNG.generate_unique_name('frm_string') + '.apsimx')
            self.Model = Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](str_, None, True,
                                                                                                  fileName=string_nam)
        # elif _data is None:

        else:
            raise NotImplementedError("Cannot process data of this type")

        try:

            if 'NewModel' in dir(self.Model):
                self.Model = self.Model.get_NewModel()
                # initialize the model just in case
                self.Model.OnCreated()

        except PermissionError as e:
            print('file is being used by another process')
            raise

        self.datastore = self.Model.FindChild[Models.Storage.DataStore]().FileName
        self._DataStore = self.Model.FindChild[Models.Storage.DataStore]()
        # self.version = self.Model.get_ApsimVersion()
        return self

    # loads apsimx file from the computer into memory using its path
    # def _load_apsimx(self, path):
    #     try:
    #         if not os.path.isfile(path):
    #             raise ValueError("file path is missing apsim extention. did you forget to include .apsimx extension")
    #         self.Model = FileFormat.ReadFromFile[Models.Core.Simulations](path, None, False)
    #         if 'NewModel' in dir(self.Model):
    #             self.Model = self.Model.get_NewModel()
    #
    #     except Exception as e:
    #         print(repr(e))  # this error will be logged to the folder logs in the current working directory
    #         print('reading from clone\n----ignore error-----')
    #         self.Model = self.load_apsimx_from_string(path)
    #         raise
    #     self.datastore = self.Model.FindChild[Models.Storage.DataStore]().FileName
    #     self._DataStore = self.Model.FindChild[Models.Storage.DataStore]()
    #     # self.version = self.Model.get_ApsimVersion()

    def load_external_apsimx(self, path, read_from_string=True):
        # when we load we replace exisiting ones, so fune null it
        self.Model = None
        self.path = path
        try:
            assert path.endswith(
                ".apsimx"), "file path is missing APSIM extension. did you forget to include .apsimx extension"
            if read_from_string:
                self.load_apsimx_from_string(path)
            else:
                self.Model = FileFormat.ReadFromFile[Models.Core.Simulations](path, None, False)
                if 'NewModel' in dir(self.Model):
                    self.Model = self.Model.get_NewModel()
        except Exception as e:
            print(repr(e))  # this error will be logged to the folder logs in the current working directory
            raise
        self.datastore = self.Model.FindChild[Models.Storage.DataStore]().FileName
        self._DataStore = self.Model.FindChild[Models.Storage.DataStore]()

    def _reload_saved_file(self):
        self.save_edited_file(self.path)
        return self

    import os

    def save_edited_file(self, outpath=None, reload=False):
        """Save the model

        Parameters
        ----------
        outpath : str, optional
            Path of the output .apsimx file, by default None
            reload: bool to load the file using the outpath
        """
        # Determine the output path
        if outpath:
            # If an outpath is provided, use it and convert to real path
            final_out_path = os.path.realpath(outpath)
        else:
            # If no outpath is provided, check if self.out_path is already set
            if self.out_path is None:
                # If self.out_path is not set, default to self.path
                final_out_path = self.path
            else:
                # Use the existing self.out_path
                final_out_path = self.out_path

        # Serialize the model to JSON string
        json_string = Models.Core.ApsimFile.FileFormat.WriteToString(self.Model)

        # Save the JSON string to the determined output path
        with open(final_out_path, "w", encoding='utf-8') as f:
            f.write(json_string)
        if reload:
            self._model = final_out_path
            self.load_apsimx_from_string(self._model)
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
            If `True` remove existing database for the file before running, deafults to False`

        multithread
            If `True` APSIM uses multiple threads, by default `True`
        """
        if multithread:
            runtype = Models.Core.Run.Runner.RunTypeEnum.MultiThreaded
        else:
            runtype = Models.Core.Run.Runner.RunTypeEnum.SingleThreaded
        # open the datassote
        self._DataStore.Open()
        # Clear old data before running
        self.results = None
        if clean:
            self._DataStore.Dispose()
            pathlib.Path(self._DataStore.FileName).unlink(missing_ok=True)
            self._DataStore.Open()

        if simulations is None:
            runmodel = Models.Core.Run.Runner(self.Model, True, False, False, None, runtype)
            e = runmodel.Run()
        else:
            sims = self.find_simulations(simulations)
            # Runner needs C# list
            cs_sims = List[Models.Core.Simulation]()
            for s in sims:
                cs_sims.Add(s)
                runmodel = Models.Core.Run.Runner(cs_sims, True, False, False, None, runtype)
                e = runmodel.Run()

        if (len(e) > 0):
            print(e[0].ToString())
        if report_name is None:
            report_name = get_db_table_names(self.datastore)
            warnings.warn('No tables were specified, retrieved tables includes:: {}'.format(report_name))
        if isinstance(report_name, (tuple, list)):
            self.results = [read_db_table(self.datastore, report_name=rep) for rep in report_name]
        else:
            self.results = read_db_table(self.datastore, report_name=report_name)
        # close the datastore
        self._DataStore.Close()
        return self
        # print(self.results)

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

            self.Model.Children.Clear(clone_sim.Name)
            self.Model.Children.Add(clone_sim)
        self._reload_saved_file()
        self.extr

    def remove_simulation(self, simulation):
        """Remove a simulation from the model

            Parameters
            ----------
            simulation
                The name of the simulation to remove
        """

        sim = self._find_simulation(simulation)
        self.Model.Children.Remove(sim)
        self.save_edited_file()
        self._load_apsimx(self.path)

    @property
    def extract_simulation_name(self):
        """print or extract a simulation name from the model

            Parameters
            ----------
            simulation
                The name of the simulation to remove
        """
        sim_names = []
        for simu in self.simulations:
            sim_names.append(simu.Name)
            return sim_names

    def clone_zone(self, target, zone, simulation=None):
        """Clone a zone and add it to Model

            Parameters
            ----------
            target
                target simulation name
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
        self.save_edited_file()
        self._load_apsimx(self.path)

    def find_zones(self, simulation):
        """Find zones from a simulation

            Parameters
            ----------
            simulation
                simulation name

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

    @staticmethod
    def read_apsimx_db(datastore, report_name):
        """
        reads an already simulated model data base
         returns all data frame the available report tables"""
        data = read_db_table(datastore, report_name)
        return data

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
            return [shutil.copy(self.path, f"{file_name}_{tag}_{i}_.apsimx") for i in range(k)]

        else:
            b_name = os.path.basename(self.path).rsplit('.apsimx', 1)[0]
            return [shutil.copy(self.path, os.path.join(path, f"{b_name}_{tag}_{i}.apsimx")) for i in range(k)]

    def _read_simulation(self, report_name=None):
        """ returns all data frame the available report tables
        this is slow use read_db_table instead"""
        conn = sqlite3.connect(self.datastore)
        cursor = conn.cursor()

        # reading all table names

        table_names = [a for a in cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]

        table_list = []
        for i in table_names:
            table_list.append(i[0])
            # remove these
        rm = ['_InitialConditions', '_Messages', '_Checkpoints', '_Units']
        for i in rm:
            if i in table_list:
                table_list.remove(i)
                # start selecting tables

        select_template = 'SELECT * FROM {table_list}'

        # create data fram dictionary to keep all the tables
        dataframe_dict = {}

        for tname in table_list:
            query = select_template.format(table_list=tname)
            dataframe_dict[tname] = pd.read_sql(query, conn)
        # close the connection cursor
        conn.close()
        dfl = len(dataframe_dict)
        if len(dataframe_dict) == 0:
            print("the data dictionary is empty. no data has been returned")
            # else:
            # remove elements
            # print(f"{dfl} data frames has been returned")

        if report_name:
            return dataframe_dict[report_name]
        else:
            return dataframe_dict

    @staticmethod
    def _read_external_simulation(datastore, report_name=None):
        ''' returns all data frame the available report tables'''
        conn = sqlite3.connect(datastore)
        cursor = conn.cursor()

        # reading all table names

        table_names = [a for a in cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]

        table_list = []
        for i in table_names:
            table_list.append(i[0])
            # remove these
        rm = ['_InitialConditions', '_Messages', '_Checkpoints', '_Units']
        for i in rm:
            if i in table_list:
                table_list.remove(i)
                # start selecting tables
        select_template = 'SELECT * FROM {table_list}'

        # create data fram dictionary to keep all the tables
        dataframe_dict = {}

        for tname in table_list:
            query = select_template.format(table_list=tname)
            dataframe_dict[tname] = pd.read_sql(query, conn)
        # close the connection cursor
        conn.close()
        dfl = len(dataframe_dict)
        if len(dataframe_dict) == 0:
            print("the data dictionary is empty. no data has been returned")
        if report_name:
            return dataframe_dict[report_name]
        else:
            return dataframe_dict

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
        rep = self.Model.FindChild[Models.Core.Folder]()
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

    def update_manager_parameters(self, **kwargs):
        """updates  the manager module by passing the parameters as keys and their values as values

        >>>> from apsimNGpy.core.apsim import ApsimModel
        >>>> from apsimNGpy.core.base_data. import LoadExampleFiles, Path
        >>>> pp = Path.home()
        # sending to home directory
        >>>>  os.chdir(pp)
        >>>> init = LoadExampleFiles()
        >>>> model = init.maize.get_maize
        >>>> print(model)
        >>>> _model = ApsimModel(file)
        >>>> _model.update_manager_parameters('Name'= Tillage, Fraction =0.75)
        Tillage is the name of the manager script which is displayed in the GUI while fraction is the corresponding parameter name and 0.75 is the new value to update
        """
        mgt_params = {i: J for i, J in kwargs.items()}
        try:
            self.update_mgt(management=mgt_params)
        except AttributeError:
            raise AttributeError(f"error updating the manager: {kwargs.get('Name')} does not exists")
        return self

    def summarize_output_variable(self, var_name, table_name='Report'):
        data = self.results[table_name]

        dic = {}
        index = ['stat']
        for i in ['mean', 'max', 'min', 'first', 'last', 'std', 'diff']:
            varname = f"{var_name}_" + i
            dic[varname] = APSIMNG.get_result_stat(data, var_name, i)
        output_variable_statistics = pd.DataFrame(dic, index=index)
        return output_variable_statistics

    @timing_decorator
    def collect_data_for_specific_crop(self, crop, rotation, variable, report_name, statistic):
        assert isinstance(crop, str), "crop name must be a string"
        assert isinstance(rotation, str), "Rotation name must tbe a string"
        if crop in rotation:
            df = self.results[report_name]
            result = self.get_result_stat(df, column=variable, statistic=statistic)
            return result

    @staticmethod
    def collect_specificreport(results, report_names, var_names, stat):
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

    def save_and_Load(self, out):
        self.save_edited_file(outpath=out)
        self.load_apsimx_from_string(_data=out)
        return self

    @property
    def FindAllReferencedFiles(self):
        return self.Model.FindAllReferencedFiles()

    def RevertCheckpoint(self):
        self.Model = self.Model.RevertCheckpoint('new_model')
        return self

    def update_management_decissions(self, management, simulations=None, reload=True):
        """Update management, handles multiple managers in a loop

        Parameters
        ----------
        management: a list of dictionaries of management paramaters or a dictionary with keyvarlue pairs of parameters and associated values, respectivelyto update. examine_management_info` to see current values.
        make a dictionary with 'Name' as the for the of  management script
        simulations, optional
            List of simulation names to update, if `None` update all simulations not recommended.
        reload, optional
            _description_ defaults to True
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
        if reload:
            self.save_edited_file()
            self.load_apsimx_from_string(self.path)

    # experimental

    def update_mgt(self, management, simulations=None, reload=False):  # use this one it is very fast
        """Update management, handles one manager at a time

        Parameters
        ----------
        management

            Parameter = value dictionary of management paramaters to update. examine_management_info` to see current values.
            make a dictionary with 'Name' as the for the of  management script
        simulations, optional
            List of simulation names to update, if `None` update all simulations not recommended.
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

        # return zone  # for mgt in management:
        #     action_path = f'{zone_path}.{mgt.get("Name")}'
        #     fp = zone.FindByPath(action_path)
        #     values = mgt
        #     for i in range(len(fp.Value.Parameters)):
        #         param = fp.Value.Parameters[i].Key
        #         if param in values.keys():
        #             fp.Value.Parameters[i] = KeyValuePair[String, String](param, f"{values[param]}")
        self.save_edited_file()
        self._model = self.path
        self.load_apsimx_from_string()
        return self

    # immediately open the file in GUI
    def show_file_in_APSIM_GUI(self):
        os.startfile(self.path)

    # dynamically saves the file and relaod into the system. in otherwords it compiles the scripts
    def dynamic_path_handler(self):
        self.save_edited_file()
        if self.out_path:
            self._load_apsimx(self.out_path)
        else:
            self._load_apsimx(self.path)
        return self

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
        for weather in self.Model.FindAllDescendants[Weather]():
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

    ## find the solute node in the simulation
    def _extract_solute(self, simulation=None):
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

    def adjustSatDul(self, sat_, dul_):
        for enum, (s, d) in enumerate(zip(sat_, dul_)):
            # first check if they are equal
            # if d is greater than s, then by what value?, we need this value to add it to 0.02
            #  to be certain all the time that dul is less than s we subtract the summed value
            if d >= s:

                diff = d - s
                if diff == 0:
                    dul_[enum] = d - 0.02
                else:
                    duL[enum] = d - (diff + 0.02)

            else:
                dul_[enum] = d
        return dul

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
        self.Model = None
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

    model = APSIMNG(model=modelm)
    for _ in range(100):
        a = perf_counter()
        # model.RevertCheckpoint()
        model.run("MaizeR")
        b = perf_counter()
        print(b - a, 'seconds')
