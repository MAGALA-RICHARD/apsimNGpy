"""
Interface to APSIM simulation models using Python.NET build on top of Matti Pastell farmingpy framework.
"""
import matplotlib.pyplot as plt
import random, logging, pathlib
import string
from typing import Union
import pythonnet
import os, sys, datetime, shutil, warnings
import numpy as np
import pandas as pd
from os.path import join as opj
import sqlite3
import json

import apsimNGpy.manager.weathermanager as weather
from apsimNGpy.manager.soilmanager import DownloadsurgoSoiltables, OrganizeAPSIMsoil_profile

try:
    if pythonnet.get_runtime_info() is None:
        pythonnet.load("coreclr")
except:
    print("dotnet not found ,trying alternate runtime")
    pythonnet.load()

import clr
from os.path import join as opj

# logs folder
Logs = "Logs"
basedir = os.getcwd()
log_messages = opj(basedir, Logs)
if not os.path.exists(log_messages):
    os.mkdir(log_messages)
datime_now = datetime.datetime.now()
timestamp = datime_now.strftime('%a-%m-%y')
logfile_name = 'log_messages' + str(timestamp) + ".log"
log_paths = opj(log_messages, logfile_name)
# f"log_messages{datetime.now().strftime('%m_%d')}.log"
logging.basicConfig(filename=log_paths, level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

## TODO Need to optimize this for all platforms
def detect_apsim_installation():
    for rr, dd, ff in os.walk("C:/"):
        for d in ff:
            if d.startswith('Model') and d.endswith(".exe"):
                f = os.path.join(rr, d)
                if f is not None:
                    return f


sys.path.append(os.path.dirname(detect_apsim_installation()))

try:
    clr.AddReference("Models")
except:
    print("Looking for APSIM")
    apsim_path = shutil.which("Models")
    if apsim_path is not None:
        apsim_path = os.path.split(os.path.realpath(apsim_path))[0]
        sys.path.append(apsim_path)
    clr.AddReference("Models")

clr.AddReference("System")
from System.Collections.Generic import *
from Models.Core import Simulations
from System import *
from Models.PMF import Cultivar
from Models import Options
from Models.Core.ApsimFile import FileFormat
from Models.Climate import Weather
from Models.Soils import Solute, Water, Chemical
from Models.Soils import Soil, Physical, SoilCrop, Organic
import Models
from Models.PMF import Cultivar
import threading
import time


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


class APSIMNG():
    """Modify and run Apsim next generation simulation models."""

    def __init__(self, model: Union[str, Simulations], copy=True, out_path=None, read_from_string=True):
        """
        Parameters
        ----------

        model
            Path to .apsimx file
        copy, optional
            If `True` a copy of original simulation will be created on init, by default True.
        out_path, optional
            Path of modified simulation, if `None` will be set automatically.
        read_from_string (boolean) if True file will be uploaded to memory through json module most preffered, otherwise we can read from file
        """

        assert os.path.exists(model), "The file does not exists in the specified directory"
        self.results = None
        self.Model = None
        self.datastore = None
        self.out_path = out_path
        self.management_data = {'Nitrogen': [0, 140, 180, 220], \
                                'Depth': [0, 100, 250, 100], \
                                "Rotation": ['CC', 'CB'],
                                "Tillage type": [1, 0],
                                'Cover Crop': [1, 0],
                                'Prairie Strips': [1, 0]}

        if type(model) == str:
            apsimx_file = model
            name, ext = os.path.splitext(apsimx_file)
            if copy:
                if out_path is None:
                    copy_path = f"{name}_copy{ext}"
                else:
                    copy_path = out_path
                try:
                    shutil.copy(apsimx_file, copy_path)
                    pathlib.Path(f"{name}.db").unlink(missing_ok=True)
                    pathlib.Path(f"{name}.db-shm").unlink(missing_ok=True)
                    pathlib.Path(f"{name}.db-wal").unlink(missing_ok=True)
                    self.path = copy_path
                except PermissionError as e:
                    print(repr(e))
            else:
                self.path = apsimx_file

            if read_from_string == True:
                self.load_apsimx_from_string(self.path)
            else:
                self._load_apsimx(self.path)

        elif type(model) == Simulations:
            self.Model = model
            self.datastore = self.Model.FindChild[Models.Storage.DataStore]().FileName
            self._DataStore = self.Model.FindChild[Models.Storage.DataStore]()

        plant = self.Model.FindDescendant[Models.Core.Zone]().Plants[0]
        cultivar = plant.FindChild[Cultivar]()

        try:
            self.cultivar_command = self._cultivar_params(cultivar)
        except:
            pass

    @staticmethod
    def generate_unique_name(base_name, length=6):
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=length))
        unique_name = base_name + '_' + random_suffix
        return unique_name

    @property
    def filename(self):
        self.file_name = os.path.basename(self.path)
        return self.file_name

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
            logger.exception(repr(e))
            raise

    def load_apsimx_from_string(self, path):
        try:
            with open(path, "r+") as apsimx:
                app_ap = json.load(apsimx)
            string_name = json.dumps(app_ap)
            fn = path
            self.Model = Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](string_name, None,
                                                                                                  True, fileName=fn)
        except Exception as e:
            logger.exception(repr(e))  # this error will be logged to the folder logs in the current working directory
            raise
        self.datastore = self.Model.FindChild[Models.Storage.DataStore]().FileName
        self._DataStore = self.Model.FindChild[Models.Storage.DataStore]()

    def _load_apsimx(self, path):
        try:
            assert path.endswith(
                ".apsimx"), "file path is missing apsim extention. did you forget to include .apsimx extension"
            self.Model = FileFormat.ReadFromFile[Models.Core.Simulations](path, None, False)
        except Exception as e:
            logger.exception(repr(e))  # this error will be logged to the folder logs in the current working directory
            print('reading from clone\n----ignore error-----')
            self.Model = self.load_apsimx_from_string(path)
            raise
        self.datastore = self.Model.FindChild[Models.Storage.DataStore]().FileName
        self._DataStore = self.Model.FindChild[Models.Storage.DataStore]()

    def load_external_apsimx(self, path, read_from_string=True):
        # when we load we replace exisiting ones, so fune null it
        self.Model = None
        self.path = path
        try:
            assert path.endswith(
                ".apsimx"), "file path is missing apsim extention. did you forget to include .apsimx extension"
            if read_from_string:
                self.load_apsimx_from_string(path)
            else:
                self.Model = FileFormat.ReadFromFile[Models.Core.Simulations](path, None, False)
        except Exception as e:
            logger.exception(repr(e))  # this error will be logged to the folder logs in the current working directory
            raise
        self.datastore = self.Model.FindChild[Models.Storage.DataStore]().FileName
        self._DataStore = self.Model.FindChild[Models.Storage.DataStore]()

    def _reload_saved_file(self):
        self.save_edited_file(self.path)

    def save_edited_file(self):
        """Save the model

        Parameters
        ----------
        out_path, optional
            Path of output .apsimx file, by default `None`
        """
        if self.out_path is None:
            out_path = self.path
        else:
            out_path = self.out_path
        json = Models.Core.ApsimFile.FileFormat.WriteToString(self.Model)
        with open(out_path, "w") as f:
            f.write(json)

    @timing_decorator
    def run(self, simulations=None, clean=False, multithread=True):
        """Run apsim model in the simulations

        Parameters
        ----------
        simulations (__str_), optional
            List of simulation names to run, if `None` runs all simulations, by default `None`.
        clean (_-boolean_), optional
            If `True` remove existing database for the file before running, deafults to False`
        multithread, optional
            If `True` APSIM uses multiple threads, by default `True`
        """
        if multithread:
            runtype = Models.Core.Run.Runner.RunTypeEnum.MultiThreaded
        else:
            runtype = Models.Core.Run.Runner.RunTypeEnum.SingleThreaded

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
        self.results = self._read_simulation()
        # print(self.results)

    def clone_simulation(self, target, simulation=None):
        """Clone a simulation and add it to Model

        Parameters
        ----------
        target
            target simulation name
        simulation, optional
            Simulation name to be cloned, of None clone the first simulation in model
        """

        sim = self._find_simulation(simulation)

        clone_sim = Models.Core.Apsim.Clone(sim)
        clone_sim.Name = target
        # clone_zone = clone_sim.FindChild[Models.Core.Zone]()
        # clone_zone.Name = target

        self.Model.Children.Add(clone_sim)
        self._reload_saved_file()

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
    def extract_report_names(self, report_name=None):
        ''' returns all data frame the available report tables'''
        with sqlite3.connect(self.datastore) as conn:

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
            return table_list

    def _read_simulation(self, report_name=None):
        ''' returns all data frame the available report tables'''
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
            # else:
            # remove elements 
            # print(f"{dfl} data frames has been returned")

        if report_name:
            return dataframe_dict[report_name]
        else:
            return dataframe_dict

    def _cultivar_params(self, cultivar):
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

    def edit_cultivar(self, CultvarName, commands: tuple, values: tuple):
        """

        :param CultvarName: name of the cultvar e.g laila

        :param command: python tuple of strings.
                  example: ('[Grain].MaximumGrainsPerCob.FixedValue', "[Phenology].GrainFilling.Target.FixedValue ")
        values: corresponding values for each command e.g ( 721, 760)
        :return:
        """
        if not isinstance(CultvarName, str):
            raise ValueError("cultiva name must be a string")
        if len(commands) != len(values):
            raise ValueError("Both values and commands must be equal")
        if commands is None or not isinstance(commands, tuple):
            raise ValueError("commands must be a list")
        if commands is None or not isinstance(commands, tuple):
            raise ValueError("values must be presented as a list")
        cultvar = self._find_cultvar(CultvarName)
        params = self._cultivar_params(cultvar)
        for com, val in zip(commands,
                            values):  # when a command exists it is replaced, this avoids duplicates as dictioanry names do not repeat
            params[com] = val
        commands = [f"{k}={v}" for k, v in params.items()]
        cultvar.set_Command(commands)
        return self

    def get_current_cultvar_name(self, ManagerName):
        # if ParameterName != CultivarName:
        try:
            ap = self.extract_user_input(ManagerName)['CultivarName']
            return ap
        except  KeyError:
            parameterName = 'CultivarName'
            print(f"default parameter name is: {parameterName} please change in it your manager script and try again")

    @staticmethod
    def examine_attributes(object):
        at = dir(object)
        for i in at:
            print(i, "\n")

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

    def copy_apsim_file(self):
        path = os.getcwd()
        file_path = opj(path, self.generate_unique_name("clones")) + ".apsimx"
        shutil.copy(self.path, file_path)

    def make_apsimx_clones(self, number=40):
        self.clones = make_apsimx_clones(self.path, number)
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
            logger.exception(repr(e))
            raise

    def update_management_decissions(self, management, simulations=None, reload=False):
        """Update management, handles one manager at a time

        Parameters
        ----------
        management
        
            Parameter = value dictionary of management paramaters to update. examine_management_info` to see current values. 
            make a dictionary with 'Name' as the for the of  management script
        simulations, optional
            List of simulation names to update, if `None` update all simulations not recommended.
        reload, optional
            _description_ defaults to True
        """

        for sim in self.find_simulations(simulations):

            zone = sim.FindChild[Models.Core.Zone]()
            zn = zone.FindAllChildren[Models.Manager]()

            for action in zone.FindAllChildren[Models.Manager]():
                if action.Name == management["Name"]:
                    values = management
                    for i in range(len(action.Parameters)):
                        param = action.Parameters[i].Key
                        if param in values:
                            action.Parameters[i] = KeyValuePair[String, String](param, f"{values[param]}")
                            # action.RebuildScriptModel() # thoought recompiling problem solved
            if reload:
                self.save_edited_file()
            if self.out_path:
                self._load_apsimx(self.out_path)
            else:
                self._load_apsimx(self.path)
        return self

    def worker(self, management, simulations, reload):
        try:
            self.update_management_decissions(management, simulations=simulations, reload=reload)
        except Exception as e:
            print(f"Failed to process {management}: {e}")

    def Update_management(self, management_list, simulations=None, reload=True):
        import queue
        if simulations is None:
            simulations = self.extract_simulation_name

        # Create a queue for managing items to be processed
        manager_queue = queue.Queue()

        # Put management items into the queue
        for management in management_list:
            manager_queue.put(management)

        # Create and start worker threads
        num_threads = len(management_list)
        threads = []

        for _ in range(num_threads):
            thread = threading.Thread(
                target=self.worker,
                args=(manager_queue.get(), simulations, reload)
            )
            threads.append(thread)
            thread.start()

        # Wait for all worker threads to finish
        for thread in threads:
            thread.join()

        if reload:
            # Perform reload operations here
            self.save_edited_file()
            if self.out_path:
                self._load_apsimx(self.out_path)
            else:
                self._load_apsimx(self.path)

        return self

    # Convert CS KeyValuePair to dictionary
    @timing_decorator
    def update_multiple_management_decissions(self, management_list, simulations=None, reload=False):
        """Update management, handles multiple managers in a loop

        Parameters
        ----------
        management_lists

            Parameter = a list of dictionaries of management paramaters to update. examine_management_info` to see current values.
            make a dictionary with 'Name' as the for the of  management script
        simulations, optional
            List of simulation names to update, if `None` update all simulations not recommended.
        reload, optional
            _description_ defaults to True
        """
        # from apsimx.utils import KeyValuePair
        for sim in self.find_simulations(simulations):
            zone = sim.FindChild[Models.Core.Zone]()

            for action in zone.FindAllChildren[Models.Manager]():

                # action.Children.Remove("Post")
                for management in management_list:
                    if action.Name == management["Name"]:
                        values = management
                        for i in range(len(action.Parameters)):
                            param = action.Parameters[i].Key

                            if param in values:
                                fvalue = f"{values[param]}"
                                action.Parameters[i] = KeyValuePair[String, String](param, fvalue)

                                # action.Parameters[i]= {param:f"{values[param]}"}
                            # action.GetParametersFromScriptModel()

            if reload:
                self.save_edited_file()
            if self.out_path:
                self._load_apsimx(self.out_path)
            else:
                self._load_apsimx(self.path)
        return self

    def wupdate_multiple_management_decisions(self, management_list, simulations=None, reload=False):
        simulations = self.find_simulations(simulations)
        for sim in simulations:
            zone = sim.FindChild[Models.Core.Zone]()
            managers = zone.FindAllChildren[Models.Manager]()

            for action in managers:
                matching_management = next((m for m in management_list if m["Name"] == action.Name), None)
                if matching_management:
                    for i, param in enumerate(list(action.Parameters)):
                        if param.Key in matching_management:
                            fvalue = str(matching_management[param.Key])
                            action.Parameters[i] = KeyValuePair[String, String](param.Key, fvalue)

            if reload:
                self.save_edited_file()

            if self.out_path:
                self._load_apsimx(self.out_path)
            else:
                self._load_apsimx(self.path)

        return self

    def show_file_in_APSIM_GUI(self):
        os.startfile(self.path)

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
            out = {}
            out["simulation"] = sim.Name
            for action in actions:
                if action.Name == manager_name:
                    params = self._kvtodict(action.Parameters)
                    return params

    import datetime
    @staticmethod
    def strip_time(date_string):
        date_object = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        formatted_date_string = date_object.strftime("%Y-%m-%dT%H:%M:%S")
        return formatted_date_string  # Output: 2010-01-01T00:00:00

    def change_simulation_dates(self, start_date=None, end_date=None, simulations=None):
        """Set simulation dates. this is important to run this method befire run the weather repalcement method as 
        the date needs to be alligned int weather

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
        except Exception as e:
            logger.exception(repr(e))  # this error will be logged to the folder logs in the current working directory
            raise

    def show_met_file_in_simulation(self):
        """Show weather file for all simulations"""
        for weather in self.Model.FindAllDescendants[Weather]():
            return weather.FileName

    def change_report_variables(self, report, simulations=None):
        """Set APSIM report

        Parameters
        ----------
        report
            New report string.
        simulations, optional
            List of simulation names to update, if `None` update all simulations
        """
        simulations = self.find_simulations(simulations)
        for sim in simulations:
            r = sim.FindDescendant[Models.Report]()
            r.set_VariableNames(report.strip().splitlines())

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
        report = list(sim.FindAllDescendants[Models.Report]())[1]
        return list(report.get_VariableNames())

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
        -------------------------
        returns an array of the parameter values
        """
        assert isinstance(parameter, str) == True, "Soil parameter name must be a string"
        soil_physical = self.extract_soil_physical(simulation)
        soilp_param = getattr(soil_physical, parameter)
        return list(soilp_param)

    def replace_any_soil_physical(self, parameter, param_values, simulation=None):
        """relaces specified soil physical parameters in the simulation

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

    # Make sure that crop ll is below and above LL15 DUL in all layers
    def _harmonise_soil_water(self, simulation):  # REPLACED _fix_crop_ll
        cropll = self._extract_LL(simulation)
        dul = self._extract_DUL(simulation)
        ll15 = self._extract_LL15(simulation)
        for j in range(len(cropll)):
            if cropll[j] > dul[j]:
                cropll[j] = dul[j] - 0.015

        for j in range(len(cropll)):
            if cropll[j] < ll15[j]:
                cropll[j] = ll15[j]

        self.replace_crop_LL(cropll, simulation)

    def set_swcon(self, swcon, simulations=None):
        """Set soil water conductivity (SWCON) constant for each soil layer.

        Parameters
        ----------
        swcon
            Collection of values, has to be the same length as existing values.
        simulations, optional
            List of simulation names to update, if `None` update all simulations
        """

        for sim in self.find_simulations(simulations):
            wb = sim.FindDescendant[Models.WaterModel.WaterBalance]()
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
        self.path = None
        self.out_path = None
        self.Model = None
        self._DataStore = None
        self.datastore = None
        self.results = None
        self.file_name = None
        return self

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


class ApsimSoil(APSIMNG):
        def __init__(self, model: Union[str, Simulations], copy=False, out_path=None, read_from_string=True,
                     lonlat=None,
                     soil_series='domtcp', thickness=20, bottomdepth=200, thickness_values=None, run_all_soils=False):
            super().__init__(model)
            """get suurgo soil tables and organise it to apsim soil profiles
            --------------------
            parameters
             soil_series (_str_) specifying the soils series default is domcp meaning dorminant soil series, users can specify any other series
             if known.
             lonlat {_lonlat_} of the specified location
             run_all_soils (__boolean_) if True, all soil series in the map units will be analysed if false the soil series will be the one determiend by paramter soil series
             model is a path of apsims file or apsimng object
             """
            self.lonlat = lonlat
            self.Nlayers = bottomdepth / thickness
            self.simulation_names = self.path
            self.soil_series = soil_series
            self.thickness = thickness
            self.out_path = out_path
            self.copy = copy
            self.run_all_soils = run_all_soils
            if not isinstance(thickness_values, np.ndarray):
                self.thickness_values = np.array(thickness_values, dtype=np.float64)  # apsim uses floating digit number
            else:
                self.thickness_values = thickness_values

        def _find_soil_solute(self, solute, simulation=None):
            sim = self._find_simulation(simulation)
            solutes = sim.FindAllDescendants[Models.Soils.Solute]()
            return [s for s in solutes if s.Name == solute][0]

        def _get_initial_chemical_values(self, name, simulation):
            s = self._find_soil_solute(name, simulation)
            return np.array(s.InitialValues)

        def _replace_initial_chemical_values(self, name, values, simulations):
            """_summary_

            Args:
                name (str): of the solutes e.g  NH4
                values (array): _values with equal lengths as the existing other variable
                simulations (str): simulation name in the root folder
            """
            simus = self.find_simulations(simulations)
            for sim in simus:
                solute = self._find_soil_solute(name, sim.Name)
                solute.InitialValues = values

        def show_cropsoil_names(self, simulations):
            for simu in self.find_simulations(simulations):
                pysoil = simu.FindDescendant[Physical]()
                soil_crop = pysoil.FindAllDescendants[SoilCrop]()
                # can be use to target specific crop
                for cropLL in soil_crop:
                    print(cropLL.Name)

        def _replace_cropsoil_names(self, simulations, existing_crop_names, new_cropname):
            for simu in self.find_simulations(simulations):
                pysoil = simu.FindDescendant[Physical]()
                soil_crop = pysoil.FindAllDescendants[SoilCrop]()
                # can be use to target specific crop
                for crops in soil_crop:
                    if crops.Name == existing_crop_names:
                        crops.Name = new_cropname

        def get_initial_no3(self, simulation=None):
            """Get soil initial NO3 content"""
            return self._get_initial_values("NO3", simulation)

        def _get_SSURGO_soil_profile(self, lonlat, run_all_soils=False):
            self.lonlat = None
            self.lonlat = lonlat
            self.dict_of_soils_tables = {}
            if not self.run_all_soils:
                self.soil_tables = DownloadsurgoSoiltables(self.lonlat, select_componentname=self.soil_series)
                for ss in self.soil_tables.componentname.unique():
                    self.dict_of_soils_tables[ss] = self.soil_tables[self.soil_tables['componentname'] == ss]

            if self.run_all_soils:
                self.dict_of_soils_tables = {}
                self.soil_tables = DownloadsurgoSoiltables(self.lonlat)

                self.percent = self.soil_tables.prcent.unique()
                # create a dictionary of soil series
                self.unique_soil_series = self.soil_tables.componentname.unique()

                new_col = []
                for i in range(len(self.soil_tables['chkey'])):
                    xi = str(list(self.soil_tables['chkey'])[i]) + "-" + list(self.soil_tables['componentname'])[i]
                    new_col.append(xi)
                self.soil_tables["ch_comp"] = list(new_col)
                self.grouped = self.soil_tables.groupby('ch_comp')['prcent'].unique().apply(lambda x: x[0])
                self.component_percent_dict = self.grouped.to_dict()
                for ss in self.soil_tables.componentname.unique():
                    self.dict_of_soils_tables[ss] = self.soil_tables[self.soil_tables['componentname'] == ss]
            return self

        @staticmethod
        def get_weather_online(lonlat, start, end):
            wp = weather.daymet_bylocation(lonlat, start=start, end=end)
            wpath = os.path.join(os.getcwd(), wp)
            return wpath

        @property
        def get_unique_soil_series(self):
            """this function collects the unique soil types

            Args:
                lonlat (_tuple_): longitude and latitude of the target location
            """
            try:
                soil_tables = DownloadsurgoSoiltables(self.lonlat)
                pr = soil_tables.prcent.unique()

                grouped = soil_tables.groupby('componentname')[
                    'prcent'].unique()  # .agg(list) #.unique().apply(lambda x: x[0])
                component_percent_dict = grouped.to_dict()
                return component_percent_dict
            except Exception as e:
                raise

        def replace_soils(self, lonlat, simulation_names, verbose=False):
            self.thickness_replace = None
            if isinstance(self.thickness_values, np.ndarray):  # since it is alreaduy converted to an array
                self.thickness_replace = self.thickness_values

            else:
                tv = np.tile(float(self.thickness), int(self.Nlayers))
                self.thickness_replace = tv
            pss = self._get_SSURGO_soil_profile(lonlat)
            for keys in pss.dict_of_soils_tables.keys():
                self.soiltype = keys
                if verbose:
                    print("Padding variabales for:", keys)
                self.soil_profile = OrganizeAPSIMsoil_profile(self.dict_of_soils_tables[keys],
                                                              thickness_values=self.thickness_values,
                                                              thickness=self.thickness)
                missing_properties = self.soil_profile.cal_missingFromSurgo()  # returns a list of physical, organic and cropdf each in a data frame
                physical_calculated = missing_properties[0]
                self.organic_calcualted = missing_properties[1]
                self.cropdf = missing_properties[2]
                # ps = self._get_SSURGO_soil_profile()

                # self.thickness_replace = list(np.full(shape=int(self.Nlayers,), fill_value=self.thickness*10,  dtype=np.float64))
                for simu in self.find_simulations(simulation_names):
                    pysoil = simu.FindDescendant[Physical]()  # meaning physical soil node
                    soil_crop = pysoil.FindChild[SoilCrop]()
                    water = simu.FindDescendant[Water]()  # for the crop water parameters
                    soil_crop.LL = physical_calculated.AirDry
                    pysoil.DUL = physical_calculated.DUL
                    pysoil.SAT = physical_calculated.SAT
                    pysoil.BD = physical_calculated.BD
                    pysoil.KS = physical_calculated.KS
                    pysoil.LL15 = physical_calculated.LL15
                    pysoil.ParticleSizeClay = physical_calculated.ParticleSizeClay
                    pysoil.ParticleSizeSand = physical_calculated.ParticleSizeSand
                    pysoil.ParticleSizeSilt = physical_calculated.ParticleSizeSilt
                    water.InitialValues = physical_calculated.DUL
                    water.Thickness = None
                    water.Thickness = self.thickness_replace
                    pysoil.AirDry = soil_crop.LL
                    pysoil.Thickness = self.thickness_replace
                    # replace the organic soils
                for simu in self.find_simulations(simulation_names):
                    organic = simu.FindDescendant[Organic]()
                    organic.Thickness = self.thickness_replace
                    organic.SoilCNRatio = self.organic_calcualted.SoilCNRatio
                    organic.FBiom = self.organic_calcualted.FBiom
                    organic.FOM = self.organic_calcualted.FOM
                    organic.FInert = self.organic_calcualted.FInert
                    organic.Carbon = self.organic_calcualted.Carbon
                    chemical = simu.FindDescendant[Chemical]()
                    chemical.Thickness = self.thickness_replace
                    # to do fix the crop management may use FindAllDescendants. it worked
                    # XF = np.full(shape=self.Nlayers, fill_value=1,  dtype=np.float64)
                    XF = np.tile(float(1), int(self.Nlayers))

                for simu in self.find_simulations(simulation_names):
                    soil_crop = pysoil.FindAllDescendants[SoilCrop]()
                    # can be use to target specific crop
                    for cropLL in soil_crop:
                        cropLL.LL = pysoil.AirDry
                        cropLL.KL = self.organic_calcualted.cropKL
                        cropLL.XF = XF
                        cropLL.Thickness = self.thickness_replace
                if verbose:
                    print("soil replacement complete")
                # self.run()
            return self
            # print(self.results)

        @timing_decorator
        def replace_downloaded_soils(self, soil_tables, simulation_names):  # unique for my project
            self.thickness_replace = self.thickness_values
            physical_calculated = soil_tables[0]
            self.organic_calcualted = soil_tables[1]
            self.cropdf = soil_tables[2]
            for simu in self.find_simulations(simulation_names):
                pysoil = simu.FindDescendant[Physical]()  # meaning physical soil node
                soil_crop = pysoil.FindChild[SoilCrop]()
                water = simu.FindDescendant[Water]()  # for the crop water parameters
                soil_crop.LL = physical_calculated.AirDry
                pysoil.DUL = physical_calculated.DUL
                pysoil.SAT = physical_calculated.SAT
                pysoil.BD = physical_calculated.BD
                pysoil.KS = physical_calculated.KS
                pysoil.LL15 = physical_calculated.LL15
                pysoil.ParticleSizeClay = physical_calculated.ParticleSizeClay
                pysoil.ParticleSizeSand = physical_calculated.ParticleSizeSand
                pysoil.ParticleSizeSilt = physical_calculated.ParticleSizeSilt
                water.InitialValues = physical_calculated.DUL
                water.Thickness = None
                water.Thickness = self.thickness_replace
                pysoil.AirDry = soil_crop.LL
                pysoil.Thickness = self.thickness_replace
                # print(len(pysoil.Thickness))
                # replace the organic soils
            for simu in self.find_simulations(simulation_names):
                organic = simu.FindDescendant[Organic]()
                organic.Thickness = self.thickness_replace
                organic.SoilCNRatio = self.organic_calcualted.SoilCNRatio
                organic.FBiom = self.organic_calcualted.FBiom
                organic.FOM = self.organic_calcualted.FOM
                organic.FInert = self.organic_calcualted.FInert
                organic.Carbon = self.organic_calcualted.Carbon
                chemical = simu.FindDescendant[Chemical]()
                chemical.Thickness = self.thickness_values
                # to do fix the crop management may use FindAllDescendants. it worked
                # XF = np.full(shape=self.Nlayers, fill_value=1,  dtype=np.float64)
                XF = np.tile(float(1), int(self.Nlayers))

            for simu in self.find_simulations(simulation_names):
                soil_crop = pysoil.FindAllDescendants[SoilCrop]()
                # can be use to target specific crop
                for cropLL in soil_crop:
                    cropLL.LL = pysoil.AirDry
                    cropLL.KL = self.organic_calcualted.cropKL
                    cropLL.XF = XF
                    cropLL.Thickness = self.thickness_replace
            return self

        # print(self.results)
        def relace_initial_carbon(self, values, simulation_names):
            """Replaces initial carbon content of the organic module

            Args:
                values (_list_): liss of initial vlaues with length as the soil profile in the simulation file_
                simulation_names (_str_): Name of the simulation in the APSIM  file
            """
            for simu in self.find_simulations(simulation_names):
                organic = simu.FindDescendant[Organic]()
                organic.Carbon = np.array(values)

        def _change_met_file(self, lonlatmet=None, simulation_names=None):  # to be accessed only in this class
            """_similar to class weather management but just in case we want to change the weather within the subclass
            # uses exisitng start and end years to download the weather data
            """
            if lonlatmet == None:
                self.lonlat = self.lonlat
            else:
                self.lonlat = lonlatmet
            self.simulation_names = simulation_names

            start, end = self.extract_start_end_years()
            wp = weather.daymet_bylocation(self.lonlat, start, end)
            wpath = os.path.join(os.getcwd(), wp)
            wpath = os.path.join(os.getcwd(), wp)
            if self.simulation_names:
                sim_name = list(self.simulation_names)
            else:
                sim_name = self.extract_simulation_name  # because it is a property decorator
            self.replace_met_file(wpath, sim_name)
            return self

        def run_edited_file(self, simulations=None, clean=False, multithread=True):
            """Run simulations in this subclass if we want to clean the database, we need to spawn the path with one process to avoid os access permission eros


            Parameters
            ----------
            simulations, optional
                List of simulation names to run, if `None` runs all simulations, by default `None`.
            clean, optional
                If `True` remove existing database for the file before running, by default `True`
            multithread, optional
                If `True` APSIM uses multiple threads, by default `True`
            """
            runa, runb = Models.Core.Run.Runner.RunTypeEnum.MultiThreaded, Models.Core.Run.Runner.RunTypeEnum.SingleThreaded
            if multithread:
                runspeed = runa
            else:
                runspeed = runb
            self.results = None
            if clean:
                self._DataStore.Dispose()
                pathlib.Path(self._DataStore.FileName).unlink(missing_ok=True)
                self._DataStore.Open()
            if simulations is None:
                runmodel = Models.Core.Run.Runner(self.Model, True, False, False, None, runspeed)
                data_run = runmodel.Run()
            else:
                sims = self.find_simulations(simulations)
                # Runner needs C# list
                cs_sims = List[Models.Core.Simulation]()
                for s in sims:
                    cs_sims.Add(s)
                    runmodel = Models.Core.Run.Runner(cs_sims, True, False, False, None, runspeed)
                    data_run = runmodel.Run()

            if (len(data_run) > 0):
                print(data_run[0].ToString())
            self.results = self._read_simulation()  # still wondering if this should be a static method
            return self.results



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


def load_apsimx(pathstring):
    with open(pathstring, "r+") as apsimx:
        app_ap = json.load(apsimx)
    string_name = json.dumps(app_ap)
    fn = pathstring
    model = Models.Core.ApsimFile.FileFormat.ReadFromString[Models.Core.Simulations](string_name, None, False,
                                                                                     fileName=fn)
    return model
