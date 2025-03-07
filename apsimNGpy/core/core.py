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
from apsimNGpy.core import pythonet_config
from apsimNGpy.utililies.database_utils import read_db_table, get_db_table_names
import warnings
from apsimNGpy.utililies.utils import timer

# now we can safely import C# libraries
from System.Collections.Generic import *
from Models.Core import Simulations, ScriptCompiler, Simulation
from System import *
from Models.Core.ApsimFile import FileFormat
from Models.Climate import Weather
from Models.Soils import Soil, Physical, SoilCrop, Organic, Solute, Chemical

import Models
from Models.PMF import Cultivar
from apsimNGpy.core._runner import run_model_externally
from apsimNGpy.core.model_loader import (load_apsim_model, save_model_to_file, recompile)
from apsimNGpy.utililies.utils import timer
from apsimNGpy.core.runner import run_model
import ast
from typing import Iterable
from collections.abc import Iterable
from typing import Any
from System.Data import DataView

MultiThreaded = Models.Core.Run.Runner.RunTypeEnum.MultiThreaded
SingleThreaded = Models.Core.Run.Runner.RunTypeEnum.SingleThreaded
ModelRUNNER = Models.Core.Run.Runner


def dataview_to_dataframe(_model, reports):
    """
    Convert .NET System.Data.DataView to Pandas DataFrame.
    report (str, list, tuple) of the report to be displayed. these should be in the simulations
    :param apsimng model: APSIMNG object or instance
    :return: Pandas DataFrame
    """
    try:
        _model._DataStore.Open()
        pred = _model._DataStore.Reader.GetData(reports)
        dataview = DataView(pred)
        if dataview.Table:
            # Extract column names
            column_names = [col.ColumnName for col in dataview.Table.Columns]

            # Extract data from rows
            data = []
            for row in dataview:
                data.append([row[col] for col in column_names])  # Extract row values

            # Convert to Pandas DataFrame
            df = pd.DataFrame(data, columns=column_names)
            return df
        else:
            logger.error("No DataView was found")
    finally:
        _model._DataStore.Close()


def select_threads(multithread):
    if multithread:
        return MultiThreaded
    else:
        return SingleThreaded


from apsimNGpy.settings import *  # This file is not ready and i wanted to do some test


def replace_variable_by_index(old_list: list, new_value: list, indices: list):
    for idx, new_val in zip(indices, new_value):
        old_list[idx] = new_val
    return old_list


def soil_components(component):
    _comp = component.lower()
    comps = {'organic': Organic,
             'physical': Physical,
             'soilcrop': SoilCrop,
             'solute': Solute,
             'chemical': Chemical,
             }
    return comps[_comp]


class APSIMNG:
    """
    Modify and run APSIM Next Generation (APSIM NG) simulation models.

    This class serves as the entry point for all apsimNGpy simulations and is inherited by the `ApsimModel` class.
    It is designed to be used when you do not intend to replace soil profiles.

    Parameters:
        model (os.PathLike): The file path to the APSIM NG model. This parameter specifies the model file to be used in the simulation.
        out_path (str, optional): The path where the output file should be saved. If not provided, the output will be saved with the same name as the model file in the current dir_path.
        out (str, optional): Alternative path for the output file. If both `out_path` and `out` are specified, `out` takes precedence. Defaults to `None`.

    Keyword parameters:
        'copy' (bool, deprecated): Specify whether to clone the simulation file. This argument is deprecated as the simulation file is automatically cloned without requiring this parameter.

    Note:
        The 'copy' keyword is no longer necessary and will be ignored in future versions.
    """

    def __init__(self, model: os.PathLike = None, out_path: os.PathLike = None, out: os.PathLike = None, **kwargs):

        self.report_names = None
        self.others = kwargs.copy()
        if kwargs.get('copy'):
            warnings.warn(
                'copy argument is deprecated, it is now mandatory to copy the model in order to conserve the original '
                'model.', UserWarning)
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

        self._str_model = None
        self._model = model
        self.out_path = out_path or out
        # model_info is named tuple safe for parallel simulations as named tuples are immutable
        self.model_info = load_apsim_model(self._model, out=self.out_path, met_file=kwargs.get('met_file'))
        self.Simulations = self.model_info.IModel

        self.datastore = self.model_info.datastore
        self.Datastore = self.model_info.DataStore
        self._DataStore = self.model_info.DataStore
        self.path = self.model_info.path
        self._met_file = kwargs.get('met_file')
        self.processed = False
        # self.init_model() work in progress

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

    def check_model(self):
        if isinstance(self.Simulations, Models.Core.ApsimFile.ConverterReturnType):
            self.Simulations = self.Simulations.get_NewModel()
            self.model_info = self.model_info._replace(IModel=self.Simulations)
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
        self.check_model()
        return list(self.Simulations.FindAllInScope[Models.Core.Simulation]())

    @property
    def simulation_names(self):
        """
        retrieves the name of the simulations in the APSIMx `Model.Core
        @return: list of simulation names
        """
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
                logger.info(e)
            finally:
                for simulation in simulationList:
                    simulation.IsInitialising = False
        return self

    def _reload_saved_file(self):
        self.save_edited_file(self.path)
        return self

    def restart_model(self, model_info=None):
        """
         :param model_info: A named tuple object returned by `load_apsim_model` from the `model_loader` module.

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

    def save(self, file_name=None):
        _path = file_name or self.path

        save_model_to_file(self.Simulations, out=_path)
        model_info = recompile(self)  # load_apsim_model(_path)
        self.restart_model(model_info)

        return self

    def save_edited_file(self, out_path: os.PathLike = None, reload: bool = False) -> Union['APSIMNG', None]:
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
            self.model_info = load_apsim_model(_out_path)

            self.restart_model()
            return self

    def run_in_python(self, report_name: Union[tuple, list, str] = None,
                      simulations: Union[tuple, list] = None,
                      clean: bool = False,
                      multithread: bool = True,
                      **kwargs) -> 'APSIMNG':

        try:
            # open the datastore
            runtype = select_threads(multithread=multithread)
            self.save()
            self._DataStore.Open()
            # Clear old data before running

            self._DataStore.Dispose()
            try:
                Path(self.datastore).unlink(missing_ok=True)
            except PermissionError as pe:
                ...
            sims = self.find_simulations(simulations) if simulations else self.Simulations
            if simulations:
                cs_sims = List[Models.Core.Simulation]()
                for s in sims:
                    cs_sims.Add(s)
                sim = cs_sims
            else:
                sim = sims
            _run_model = ModelRUNNER(sim, True, True, False, runTests=True, runType=runtype)
            e = _run_model.Run()
            if len(e) > 0:
                logging.info(e[0].ToString())
            self.processed = True
            self.report_names = report_name  # to avoid breaking those with old code

            # def _read_data(reports):
            #
            #     if isinstance(reports, str):
            #         return read_db_table(self.datastore, report_name=reports)
            #     elif isinstance(reports, Iterable):
            #         data = []
            #         for rpn in report_name:
            #             df = read_db_table(self.datastore, report_name=rpn)
            #             df['report_name'] = rpn
            #             data.append(df)
            #         out_df = pd.concat(data, ignore_index=True, axis=0)
            #         out_df.reset_index(drop=True, inplace=True)
            #         return out_df
            #
            # if self.processed:
            #     self.results = _read_data(report_name)


        finally:
            # close the datastore
            self._DataStore.Close()
        return self

    @property
    def results(self) -> pd.DataFrame:
        reports = self.report_names or "Report"  # 'Report' # is the apsim default name
        if self.processed and reports:
            if not os.path.exists(self.datastore):
                raise FileNotFoundError(self.datastore, f'{self.datastore} is not found have you recently cleaned up '
                                                        f'the data')

            if isinstance(reports, str):
                reports = [reports]
            datas = [dataview_to_dataframe(self, i) for i in reports]
            return pd.concat(datas)
        else:
            logging.warning("attempting to get results before running the model or providing the report name")

    def run(self, report_name: Union[tuple, list, str] = None,
            simulations: Union[tuple, list] = None,
            clean_up: bool = False,
            multithread: bool = True,
            **kwargs) -> 'APSIMNG':
        """Run apsim model in the simulations

        Parameters
        ----------
         :param report_name: (iterable, str). defaults to APSIM defaults Report Name if not specified,
        --Notes
          if `report_name` is iterable, all tables are read and aggregated not one data frame, returned one pandas data frame
          if `report_name` is nOne we run but do not collect the results from the data base
          if report name is string e.g.,  report a panda data frame is returned

        simulations (__list_), optional
            List of simulation names to run, if `None` runs all simulations, by default `None`.

        :param clean (_-boolean_), optional
            If `True` remove an existing database for the file before running, deafults to False`

        :param multithread: bool
            If `True` APSIM uses multiple threads, by default, `True`
            :param simulations:

        returns
            instance of the class APSIMNG
        """
        try:
            # we could cut the chase and run apsim faster, but unfortunately some versions are not working properly,
            # so we run the model externally the previous function allowed to run specific simulations in the file,
            # it has been renamed to run_in_python.
            self._DataStore.Dispose()

            # before running
            self.save()
            res = run_model_externally(self.model_info.path)
            if clean_up:
                self.clean_up()
            if res.returncode == 0:
                self.processed = True
                self.report_names = report_name
                # self.results = _read_data(report_name)

        finally:
            # close the datastore
            self._DataStore.Close()
        return self

    @property
    def simulated_results(self) -> pd.DataFrame:
        reports = get_db_table_names(self.datastore)
        bag = []
        for rep in reports:
            data = read_db_table(self.datastore, report_name=rep)
            data['report_name'] = rep
            bag.append(data)
        return pd.concat(bag)

    def clone_simulation(self, target: str, simulation: Union[list, tuple] = None):
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

    def remove_simulation(self, simulation: Union[tuple, list]):
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
        """logger.info or extract a simulation name from the model

            Parameters
            ----------
            simulation
                The name of the simulation to remove
        """
        # this is a repetition because I want to deprecate it and maintain simulation_name or use get_simulation_name
        return self.simulation_names

    def clone_zone(self, target: str, zone: str, simulation: Union[tuple, list] = None):
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

        sims = self._find_simulation(simulation)
        for sim in sims:
            zone = sim.FindChild[Models.Core.Zone](zone)
            clone_zone = Models.Core.Apsim.Clone(zone)
            clone_zone.Name = target
            sim.Children.Add(clone_zone)
        self.save_edited_file(reload=True)
        return self

    def find_zones(self, simulation: Union[tuple, list]):
        """Find zones from a simulation

            Parameters
            ----------
            simulation
                 name

            Returns
            -------
                list of zones as APSIM Models.Core.Zone objects
        """

        sims = self._find_simulation(simulation)
        zones = [sim.FindAllDescendants[Models.Core.Zone]() for sim in sims]
        return [*zip(*zones)]

    @property  #
    def extract_report_names(self) -> dict:
        """ returns all data frames the available report tables
        @return: dict of  table names in alist in the simulation"""
        table_dict = self.get_report(names_only=True)
        return table_dict

    def replicate_file(self, k: int, path: os.PathLike = None, tag: str = "replica"):
        """
        Replicates a file 'k' times.

        If a path is specified, the copies will be placed in that dir_path with incremented filenames.
        If no path is specified, copies are created in the same dir_path as the original file, also with incremented filenames.

        Parameters:
        - self: The core.api.APSIMNG object instance containing 'path' attribute pointing to the file to be replicated.
        - k (int): The number of copies to create.
        - path (str, optional): The dir_path where the replicated files will be saved. Defaults to None, meaning the same dir_path as the source file.
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

    def _cultivar_params(self, cultivar: str):
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

    def _find_cultivar(self, cultivar_name: str):

        rep = self._find_replacement().FindAllDescendants[Models.PMF.Cultivar]()
        xp = [i for i in rep]
        for cult in xp:
            if cult.Name == cultivar_name:
                return cult
                break
        return rep

    def read_cultivar_params(self, name: str, verbose: bool = None):
        cultivar = self._find_cultivar(name)
        c_param = self._cultivar_params(cultivar)
        if verbose:
            for i in c_param:
                logger.info(f"{i} : {c_param[i]} \n")
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
            logger.info(i.Name)
            if i.Name == Crop:
                return i
        return self

    def edit_cultivar(self, *, CultivarName: str, commands: str, values: Any, **kwargs):
        """
        Edits the parameters of a given cultivar. we don't need a simulation name for this unless if you are defining it in the
        manager section, if that it is the case, see update_mgt

        :param CultivarName: Name of the cultivar (e.g., 'laila').
        :param commands: A strings representing the parameter paths to be edited.
                         Example: ('[Grain].MaximumGrainsPerCob.FixedValue', '[Phenology].GrainFilling.Target.FixedValue')
        :param values: values for each command (e.g., (721, 760)).
        :return: None
        """
        if not isinstance(CultivarName, str):
            raise ValueError("Cultivar name must be a string")

        cultvar = self._find_cultivar(CultivarName)
        if cultvar is None:
            raise ValueError(f"Cultivar '{CultivarName}' not found")

        params = self._cultivar_params(cultvar)

        params[commands] = values  # Update or add the command with its new value

        # Prepare the command strings for setting the updated parameters
        updated_commands = [f"{k}={v}" for k, v in params.items()]
        cultvar.set_Command(updated_commands)

        return self

    def get_current_cultivar_name(self, ManagerName: str):
        """

        @param ManagerName: script manager module in the zone
        @return: returns the current cultivar name in the manager script 'ManagerName'
        """

        try:
            ap = self.extract_user_input(ManagerName)['CultivarName']
            return ap
        except  KeyError:
            parameterName = 'CultivarName'
            logger.info(f"cultivar name: is not found")

    def copy_apsim_file(self):
        path = os.getcwd()
        file_path = opj(path, self.generate_unique_name("clones")) + ".apsimx"
        shutil.copy(self.path, file_path)

    def update_cultivar(self, *, parameters: dict, simulations: Union[list, tuple] = None, clear=False, **kwargs):
        """Update cultivar parameters

        Parameters
        ----------
        @param:parameters (__dict__) dictionary of cultivar parameters to update.
        @param: simulations, optional
            List or tuples of simulation names to update if `None` update all simulations.
        @param: clear, optional
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

    def examine_management_info(self, simulations: Union[list, tuple] = None):
        """this will show the current management scripts in the simulation root

        Parameters
        ----------
        simulations, optional
            List or tuple of simulation names to update, if `None` show all simulations. if you are not sure,

            use the property decorator 'extract_simulation_name'
        """
        try:
            for sim in self.find_simulations(simulations):
                zone = sim.FindChild[Models.Core.Zone]()
                logger.info("Zone:", zone.Name)
                for action in zone.FindAllChildren[Models.Manager]():
                    logger.info("\t", action.Name, ":")
                    for param in action.Parameters:
                        logger.info("\t\t", param.Key, ":", param.Value)
        except Exception as e:
            logger.info(repr(e))
            raise Exception(repr(e))

    @cache
    def return_zone(self, simulations=None):
        self.find_simulations(simulations)

    def check_som(self, simulations=None):
        simus = {}
        for sim in self.find_simulations(simulations):
            zone = sim.FindChild[Models.Core.Zone]()

            som1 = zone.FindChild('SurfaceOrganicMatter')

            field = zone.Name
            sname = sim.Name

            som_path = f'{zone.FullPath}.SurfaceOrganicMatter'
            if som_path:
                som = zone.FindByPath(som_path)
                if som:
                    simus[sim.Name] = som.Value.InitialResidueMass, som.Value.InitialCNR
            else:
                raise ValueError("File node structure is not supported at a moment")
        return simus

    def change_som(self, *, simulations: Union[tuple, list] = None, inrm: int = None, icnr: int = None,
                   surface_om_name='SurfaceOrganicMatter', **kwargs):
        """
         Change Surface Organic Matter (SOM) properties in specified simulations.

    Parameters:
        simulations (str ort list): List of simulation names to target (default: None).
        inrm (int): New value for Initial Residue Mass (default: 1250).
        icnr (int): New value for Initial Carbon to Nitrogen Ratio (default: 27).
        surface_om_name (str, optional): name of the surface organic matter node defaults to ='SurfaceOrganicMatter'
    Returns:
        self: The current instance of the class.
        """
        som = None
        for sim in self.find_simulations(simulations):
            zone = sim.FindChild[Models.Core.Zone]()
            som1 = zone.FindChild(surface_om_name)
            field = zone.Name
            sname = sim.Name

            som_path = f'{zone.FullPath}.SurfaceOrganicMatter'
            if som_path:
                som = zone.FindByPath(som_path)
            if som:
                if inrm is not None:
                    som.Value.InitialResidueMass = inrm
                if icnr is not None:
                    som.Value.InitialCNR = icnr
            else:
                raise NotImplementedError(
                    f"File node structure is not supported at a moment. or {surface_om_name} not found in the file "
                    f"rename your SOM module to"
                    "SurfaceOrganicMatter")
            # mp.Value.InitialResidueMass

            return self

    @property
    def FindAllReferencedFiles(self):
        return self.Simulations.FindAllReferencedFiles()

    def convert_to_IModel(self):
        if isinstance(self.Simulations, Models.Core.ApsimFile.ConverterReturnType):
            return self.Simulations.get_NewModel()
        else:
            return self.Simulations

    # experimental
    def recompile_edited_model(self, out_path: os.PathLike):
        """

        @param out_path: os.PathLike object this method is called to convert the simulation object from ConverterReturnType to model like object
        @return: self
        """

        try:
            if isinstance(self.Simulations, Models.Core.ApsimFile.Models.Core.ApsimFile.ConverterReturnType):
                self.Simulations = self.Simulations.get_NewModel()
                self.path = out_path or self.path
                self.datastore = self.path.replace("apsimx", 'db')
                self._DataStore = self.Simulations.FindChild[Models.Storage.DataStore]()
        except AttributeError as e:
            pass
        return self

    def update_mgt_by_path(self, *, path: str, param_values: str, fmt='.'):
        # reject space in fmt
        assert fmt.split(), 'white or empty space not supported'
        parameters_guide = ['simulations_name', 'Manager', 'manager_name', 'out_path_name', 'parameter_name']
        parameters = ['simulations', 'Manager', 'Name', 'out']
        args = path.split(fmt)
        if len(args) != len(parameters_guide):
            join_p = ".".join(parameters_guide)
            raise ValueError(f"Invalid path '{path}' expected path should follow {join_p}")
        args = [(p := f"'{arg}'") if " " in arg and fmt != " " and '[' not in arg else arg for arg in args]
        _eval_params = [APSIMNG._try_literal_eval(arg) for arg in args]
        _eval_params[1] = {'Name': _eval_params[2], _eval_params[-1]: param_values},
        parameters[1] = 'management'
        _param_values = dict(zip(parameters, _eval_params))

        return self.update_mgt(**_param_values)

    def init_model(self, *args, **kwargs):
        self.run(init_only=True)

    def update_mgt(self, *, management: Union[dict, tuple], simulations: [list, tuple] = None, out: [Path, str] = None,
                   reload: bool = True,
                   **kwargs):
        """
            Update management settings in the model. This method handles one management parameter at a time.

            Parameters
            ----------
            management : dict or tuple
                A dictionary or tuple of management parameters to update. The dictionary should have 'Name' as the key
                for the management script's name and corresponding values to update. Lists are not allowed as they are mutable
                and may cause issues with parallel processing. If a tuple is provided, it should be in the form (param_name, param_value).

            simulations : list of str, optional
                List of simulation names to update. If `None`, updates all simulations. This is not recommended for large
                numbers of simulations as it may result in a high computational load.

            out : str or pathlike, optional
                Path to save the edited model. If `None`, uses the default output path specified in `self.out_path` or
                `self.model_info.path`. No need to call `save_edited_file` after updating, as this method handles saving.

            Returns
            -------
            self : Editor
                Returns the instance of the `Editor` class for method chaining.

            Notes ----- - Ensure that the `management` parameter is provided in the correct format to avoid errors. -
            This method does not perform validation on the provided `management` dictionary beyond checking for key
            existence. - If the specified management script or parameters do not exist, they will be ignored.
            using a tuple for a specifying management script, paramters is recommended if you are going to pass the function to  a multi-processing class fucntion
        """
        if isinstance(management, dict):  # we want to provide support for multiple scripts
            # note the coma creates a tuple
            management = management,

        for sim in self.find_simulations(simulations):
            zone = sim.FindChild[Models.Core.Zone]()
            zone_path = zone.FullPath
            for mgt in management:

                action_path = f'{zone_path}.{mgt.get("Name")}'
                fp = zone.FindByPath(action_path)
                # before proceeding, we need to check if fp is not None, that is if that script name does not exist
                if fp is not None:
                    values = mgt
                    for i in range(len(fp.Value.Parameters)):
                        param = fp.Value.Parameters[i].Key
                        if param in values.keys():
                            fp.Value.Parameters[i] = KeyValuePair[String, String](param, f"{values[param]}")
        out_mgt_path = out or self.out_path or self.model_info.path
        self.recompile_edited_model(out_path=out_mgt_path)

        return self

    # immediately open the file in GUI
    def preview_simulation(self):
        """
        Preview the simulation file in the apsimNGpy object in the APSIM graphical user interface
        @return: opens the simulation file
        """
        # TODO this need to be connected to the apsim installation path to make
        #  sure that file are opened in their corresponding versions
        filepath = self.path
        import platform
        import subprocess
        if platform.system() == 'Darwin':  # macOS
            subprocess.call(['open', filepath])
        elif platform.system() == 'Windows':  # Windows
            os.startfile(filepath)
        elif platform.system() == 'Linux':  # Linux
            subprocess.call(['xdg-open', filepath])
        else:
            raise OSError('Unsupported operating system')

    def _kvtodict(self, kv):
        return {kv[i].Key: kv[i].Value for i in range(kv.Count)}

    def compile_scripts(self):
        for sim in self.simulations:
            managers = sim.FindAllDescendants[Models.Manager]()
            for manager in list(managers):
                print(manager.SuccessfullyCompiledLast)
                # if not manager.SuccessfullyCompiledLast:
                #     manager.RebuildScriptModel(allowDuplicateClassName=False)

    def extract_user_input(self, manager_name: str):
        """Get user_input of a given model manager script
        returns;  a dictionary of user input with the key as the script parameters and values as the inputs
        Example
        _____________________________________________________
        from apsimNGpy.core.base_data import load_default_simulations
        model = load_default_simulations(crop = 'maize')
        ui = model.extract_user_input(manager_name='Fertilise at sowing')
        print(ui)
        # output
        {'Crop': 'Maize', 'FertiliserType': 'NO3N', 'Amount': '160.0'}
        """
        param_dict = {}
        for sim in self.simulations:
            params = None
            actions = sim.FindAllDescendants[Models.Manager]()
            out = {"simulation": sim.Name}
            for action in actions:
                if action.Name == manager_name:
                    params = self._kvtodict(action.Parameters)
                    # return params

                if params is not None and action.Name == manager_name:
                    param_dict[sim.Name] = params
        return param_dict

    @staticmethod
    def strip_time(date_string):
        date_object = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        formatted_date_string = date_object.strftime("%Y-%m-%dT%H:%M:%S")
        return formatted_date_string  # Output: 2010-01-01T00:00:00

    def change_simulation_dates(self, start_date: str = None, end_date: str = None,
                                simulations: Union[tuple, list] = None):
        """Set simulation dates. this is important to run this method before run the weather replacement method as
        the date needs to be allowed into weather

        Parameters
        -----------------------------------
        start_date, optional
            Start date as string, by default `None`
        end_date, optional
            End date as string, by default `None`
        simulations, optional
            List of simulation names to update, if `None` update all simulations
        @note
        one of the start_date or end_date parameters should at least no be None

        @raise assertion error if all dates are None

        @return None
        # Example:
            from apsimNGpy.core.base_data import load_default_simulations

            model = load_default_simulations(crop='maize')

            model.change_simulation_dates(start_date='2021-01-01', end_date='2021-01-12')
             #check if it was successful
             changed_dates = model.extract_dates
             print(changed_dates)
             # OUTPUT
               {'Simulation': {'start': datetime.date(2021, 1, 1),
                'end': datetime.date(2021, 1, 12)}}
            @note
            It is possible to target a specific simulation by specifying simulation name for this case the name is Simulations, so, it could appear as follows
             model.change_simulation_dates(start_date='2021-01-01', end_date='2021-01-12', simulation = 'Simulation')
        """
        check = start_date or end_date
        assert check is not None, "One of the start_date or end_date parameters should not be None"
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
        # Example
           from apsimNGpy.core.base_data import load_default_simulations

            model = load_default_simulations(crop='maize')
             changed_dates = model.extract_dates
             print(changed_dates)
             # OUTPUT
               {'Simulation': {'start': datetime.date(2021, 1, 1),
                'end': datetime.date(2021, 1, 12)}}
            @note
            It is possible to target a specific simulation by specifying simulation name for this case the name is Simulations, so, it could appear as follows
             model.change_simulation_dates(start_date='2021-01-01', end_date='2021-01-12', simulation = 'Simulation')
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

    def extract_start_end_years(self, simulations: str = None):
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

    def replace_met_file(self, *, weather_file, simulations=None, **kwargs):
        try:
            """searched the weather node and replaces it with a new one

            Parameters
            ----------
            weather_file
                Weather file name, path should be relative to simulation or absolute.
            simulations, optional
                List of simulation names to update, if `None` update all simulations
            """
            # we need to catch file not found errors before it becomes a problem
            if not os.path.isfile(weather_file):
                raise FileNotFoundError(weather_file)
            for sim_name in self.find_simulations(simulations):
                weathers = sim_name.FindAllDescendants[Weather]()
                for met in weathers:
                    met.FileName = os.path.realpath(weather_file)
            return self

        except Exception as e:
            logger.info(repr(e))  # this error will be logged to the folder logs in the current working dir_path
            raise

    def show_met_file_in_simulation(self, simulations: list = None):
        """Show weather file for all simulations"""
        weather_list = {}
        for sim_name in self.find_simulations(simulations):
            weathers = sim_name.FindAllDescendants[Weather]()
            for met in weathers:
                weather_list[sim_name.Name] = met.FileName
        return weather_list

    def change_report(self, *, command: str, report_name='Report', simulations=None, set_DayAfterLastOutput=None,
                      **kwargs):
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

    def get_report(self, simulation=None, names_only=False):
        """Get current report string

        Parameters
        ----------
        simulation, optional
            Simulation name, if `None` use the first simulation.
        Returns
        -------
            List of report lines.
            @param names_only: return the names of the reports as a list if names_only is True
        """
        sim = self.find_simulations(simulation)
        REPORTS = {}
        for si in sim:
            REPORTS[si.Name] = [i.Name for i in (si.FindAllDescendants[Models.Report]())] if names_only else \
                si.FindAllDescendants[Models.Report]()
        return REPORTS

    def extract_soil_physical(self, simulations: [tuple, list] = None):
        """Find physical soil

        Parameters
        ----------
        simulation, optional
            Simulation name, if `None` use the first simulation.
        Returns
        -------
            APSIM Models.Soils.Physical object
        """
        sim_physical = {}
        for nn, simu in enumerate(self._find_simulation(simulations)):
            soil_object = simu.FindDescendant[Soil]()
            physical_soil = soil_object.FindDescendant[Physical]()
            sim_physical[simu.Name] = physical_soil
        return sim_physical

    def extract_any_soil_physical(self, parameter, simulations: [list, tuple] = None):
        """extracts soil physical parameters in the simulation

        Args:
            parameter (_string_): string e.g DUL, SAT
            simulations (string, optional): Targeted simulation name. Defaults to None.
        ---------------------------------------------------------------------------
        returns an array of the parameter values
        """
        assert isinstance(parameter, str) == True, "Soil parameter name must be a string"
        data = {}
        _simulations = simulations if simulations else self.simulation_names
        sop = self.extract_soil_physical(_simulations)
        for sim in _simulations:
            soil_physical = sop[sim]
            soil_p_param = getattr(soil_physical, parameter)
            data[sim] = list(soil_p_param)
        return data

    def replace_any_soil_physical(self, *, parameter: str,
                                  param_values: [tuple, list],
                                  simulations: str = None,
                                  indices=None, **kwargs):
        """replaces specified soil physical parameters in the simulation

        ______________________________________________________ Args: parameter (_string_, required): string e.g. DUL,
        SAT. open APSIMX file in the GUI and examine the physical node for clues on the parameter names simulation (        string, optional): Targeted simulation name. Defaults to None. param_values (array, required): arrays or list
        of values for the specified parameter to replace index (int, optional):
        if indices is None replacement is done with corresponding indices of the param values
        """
        _simulations = simulations if simulations else self.simulation_names
        if indices is None:
            indices = [param_values.index(i) for i in param_values]
        sop = self.extract_soil_physical(_simulations)
        for sim in _simulations:
            soil_physical = sop[sim]
            soil_p_param = list(getattr(soil_physical, parameter))
            param_news = replace_variable_by_index(soil_p_param, param_values, indices)
            setattr(soil_physical, parameter, param_news)

    # find organic paramters
    def extract_soil_organic(self, simulation: tuple = None):
        """Find physical soil

        Parameters
        ----------
        simulation, optional
            Simulation name, if `None` use the first simulation.
        Returns
        -------
            APSIM Models.Soils.Physical object
        """
        soil_organics = {}
        for simu in self.find_simulations(simulation):
            soil_object = simu.FindDescendant[Soil]()
            organic_soil = soil_object.FindDescendant[Organic]()
            soil_organics[simu.Name] = organic_soil
        return soil_organics

    def extract_soil_property_by_path(self, path: str, str_fmt='.', index: list = None):
        """
        path to the soil property should be Simulation.soil_child.parameter_name e.g., = 'Simulation.Organic.Carbon.
        @param: index(list), optional position of the soil property to a return
        @return: list
        """
        list_of_soil_nones = dict(organic=Organic, physical=Physical, Chemical=Chemical)
        parameters = path.split(str_fmt)
        if len(parameters) != 3:
            raise ValueError('path incomplete')
        # find the simulation
        find_simu = self.find_simulations(parameters[0])[0]  # because it returns a list
        soil_child = list_of_soil_nones[parameters[1].lower()]
        soil_object = find_simu.FindDescendant[Soil]().FindDescendant[soil_child]()
        attribute = list(getattr(soil_object, parameters[2]))
        if index is None:
            return attribute
        return [attribute[i] for i in index]

    def _extract_solute(self, simulation=None):
        # find the solute node in the simulation
        sims = self._find_simulation(simulation)
        solute = {}
        for sim in sims:
            solute[sim.Name] = sim.FindAllDescendants[Models.Soils.Solute]()

        return solute

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
        _simulation = simulation if simulation else self.simulation_names
        solutes = self._extract_solute(simulation)
        sol = {k: getattr(v, parameter) for k, v in solutes.items()}
        return sol

    def replace_any_solute(self, *, parameter: str, param_values: list, simulation=None, **kwargs):
        """# replaces with new solute

        Parameters
        ____________________________________
        parameter: parameter name e.g NO3
        param_values: new values as a list to replace the old ones
        simulation, optional
            Simulation name, if `None` use the first simulation.
        """
        solutes = self._extract_solute(simulation)
        setattr(solutes, parameter, param_values)

    def replace_soil_properties_by_path(self, path: str,
                                        param_values: list,
                                        str_fmt=".",
                                        **kwargs):
        # TODO I know there is a better way to implement this
        """
        This function processes a path where each component represents different nodes in a hierarchy,
        with the ability to replace parameter values at various levels.

        :param path:
            A string representing the hierarchical path of nodes in the order:
            'simulations.Soil.soil_child.crop.indices.parameter'. Soil here is a constant

            - The components 'simulations', 'crop', and 'indices' can be `None`.
            - Example of a `None`-inclusive path: 'None.Soil.physical.None.None.BD'
            - If `indices` is a list, it is expected to be wrapped in square brackets.
            - Example when `indices` are not `None`: 'None.Soil.physical.None.[1].BD'
            - if simulations please use square blocks
               Example when `indices` are not `None`: '[maize_simulation].physical.None.[1].BD'

            **Note: **
            - The `soil_child` node might be replaced in a non-systematic manner, which is why indices
              are used to handle this complexity.
            - When a component is `None`, default values are used for that part of the path. See the
              documentation for the `replace_soil_property_values` function for more information on
              default values.

        :param param_values:
            A list of parameter values that will replace the existing values in the specified path.
            For example, `[0.1, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]` could be used to replace values for `NH3`.

        :param str_fmt:
            A string specifying the formatting character used to separate each component in the path.
            Examples include ".", "_", or "/". This defines how the components are joined together to
            form the full path.

        :return:
            Returns the instance of `self` after processing the path and applying the parameter value replacements.

            Example f

            from apsimNGpy.core.base_data import load_default_simulations
            model = load_default_simulations(crop = 'maize')
            model.replace_soil_properties_by_path(path = 'None.Soil.Organic.None.None.Carbon', param_values= [1.23])
            if we want to replace carbon at the bottom of the soil profile, we use a negative index  -1
            model.replace_soil_properties_by_path(path = 'None.Soil.Organic.None.[-1].Carbon', param_values= [1.23])
        """

        function_parameters = ['simulations', 'Soil', 'soil_child', 'crop', 'indices', 'parameter']
        expected_nones = ['simulations', 'crop', 'indices']
        args = path.split(str_fmt)
        if len(args) != len(function_parameters):
            raise TypeError(f"expected order is: {function_parameters}, crop, indices and simulations can be None"
                            f"if replacement is related to soil properties, soil is a constant after the simulation name")
        # bind them to the function paramters
        fpv = dict(zip(function_parameters, args))

        # by all means, we want indices to be evaluated

        fpt = {k: (p := APSIMNG._try_literal_eval(v)) if (k in expected_nones) else (p := v)
               for k, v in fpv.items()}
        # we can now call the method below. First, we update param_values
        fpt['param_values'] = param_values
        return self.replace_soil_property_values(**fpt)

    @staticmethod
    def _try_literal_eval(_string):
        try:
            string_new = ast.literal_eval(_string)
        except ValueError:
            return _string
        return string_new

    def replace_soil_property_values(self, *, parameter: str,
                                     param_values: list,
                                     soil_child: str,
                                     simulations: list = None,
                                     indices: list = None,
                                     crop=None,
                                     **kwargs):
        """
        Replaces values in any soil property array. The soil property array
        :param parameter: str: parameter name e.g., NO3, 'BD'
        :param param_values:list or tuple: values of the specified soil property name to replace
        :param soil_child: str: sub child of the soil component e.g., organic, physical etc.
        :param simulations: list: list of simulations to where the node is found if
        not found, all current simulations will receive the new values, thus defaults to None
        :param indices: list. Positions in the array which will be replaced. Please note that unlike C#, python satrt counting from 0
        :crop (str, optional): string for soil water replacement. Default is None

        """
        if isinstance(param_values, (int, float)):
            param_values = [param_values]
        if indices is None:
            indices = [param_values.index(i) for i in param_values]
        for simu in self.find_simulations(simulations):
            soil_object = simu.FindDescendant[Soil]()
            _soil_child = soil_object.FindDescendant[soil_components(soil_child)]()

            param_values_new = list(getattr(_soil_child, parameter))
            if soil_child == 'soilcrop':
                if crop is None:
                    raise ValueError('Crop not defined')
                crop = crop.capitalize() + "Soil"
                _soil_child = soil_object.FindDescendant[soil_components(soil_child)](crop)
                param_values_new = list(getattr(_soil_child, parameter))
                _param_new = replace_variable_by_index(param_values_new, param_values, indices)
                setattr(_soil_child, parameter, _param_new)
            else:
                _param_new = replace_variable_by_index(param_values_new, param_values, indices)
                setattr(_soil_child, parameter, _param_new)
        return self

    def extract_any_soil_organic(self, parameter: str, simulation: tuple = None):
        """extracts any specified soil  parameters in the simulation

        Args:
            parameter (_string_, required): string e.g Carbon, FBiom. open APSIMX file in the GUI and examne the phyicals node for clues on the parameter names
            simulation (string, optional): Targeted simulation name. Defaults to None.
            param_values (array, required): arrays or list of values for the specified parameter to replace
        """

        soil_organic = self.extract_soil_organic(simulation)
        get_organic = {sim:
                           list(getattr(soil_organic[sim], parameter))
                       for sim in (simulation if simulation is not None else self.simulation_names)
                       }

        return get_organic

    # Find a list of simulations by name
    def extract_crop_soil_water(self, parameter: str, crop: str = "Maize", simulation: Union[list, tuple] = None):
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
            # can be used to target specific crop
            for crops in soil_crop:
                crop_soil = crop + "Soil"
                if crops.Name == crop_soil:
                    param_values = getattr(crops, parameter)
                    return list(param_values)

    def find_simulations(self, simulations: Union[list, tuple, str] = None):
        simulations_names = simulations
        """Find simulations by name

        Parameters
        ----------
        simulations, optional
            List of simulation names to find, if `None` return all simulations
        Returns
        -------
            list of APSIM Models.Core.Simulation objects
        """

        if simulations_names is None:
            return self.simulations
        if isinstance(simulations_names, str):
            simulations_names = {simulations_names}
        elif isinstance(simulations, (list, tuple)):
            simulations_names = set(simulations)
        sims = []
        for s, name in zip(self.simulations, simulations_names):
            if s.Name == name:
                sims.append(s)
        if len(sims) == 0:
            logging.info(f"{simulations_names}: Not found!")
        else:
            return sims

    # Find a single simulation by name
    def _find_simulation(self, simulations: Union[tuple, list] = None):
        if simulations is None:
            return self.simulations

        else:
            return [self.Simulations.FindDescendant(i) for i in simulations if i in self.simulation_names]

    @staticmethod
    def adjustSatDul(sat_: list, dul_: list):
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

    def set_swcon(self, swcon: list, simulations: Union[list, tuple] = None, thickness_values: list = None, **kwargs):
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

    def _find_solute(self, solute: str, simulations: Union[list, tuple] = None):
        # values should be returned tagged by their simulation  names
        solutes = [sim.FindAllDescendants[Models.Soils.Solute](solute) for sim in self._find_simulation(simulations)]
        return solutes

    def clean_up(self):
        """
        Clears the attributes of the object and optionally deletes associated files.

        If the `copy` attribute is set to True, this method will also attempt to delete
        files at `self.path` and `self.datastore`. This is a destructive operation and
        should be used with caution.
        proceed with caution with this method otherwise results may not load
        Returns:
           >>None: This method does not return a value.
           >> Please proceed with caution, we assume that if you want to clear the model objects, then you don't need them,
           but by making copy compulsory, then, we are clearing the edited files
        """
        try:
            self._DataStore.Close()
            Path(self.path).unlink(missing_ok=True)

            Path(self.path.strip('apsimx') + "bak").unlink(missing_ok=True)
            # self._DataStore.Dispose()
            # Path(self.datastore).unlink(missing_ok=True)
        except (FileNotFoundError, PermissionError) as e:
            logger.warning(f"{e} encountered while cleaning data")
            pass

        return self

    def replace_soil_organic(self, *, organic_name, simulation_name=None, **kwargs):
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

    def insert_weather_file(self):
        start, end = self.extract_start_end_years()
        wp = weather.daymet_bylocation(self.lonlat, start=start, end=end)
        wp = os.path.join(os.getcwd(), wp)
        if self.simulation_names:
            sim_name = list(self.simulation_names)
        else:
            sim_name = self.extract_simulation_name  # because it is a property decorator
        self.replace_met_file(wp, sim_name)


if __name__ == '__main__':

    from pathlib import Path
    from time import perf_counter

    # Model = FileFormat.ReadFromFile[Models.Core.Simulations](model, None, False)
    os.chdir(Path.home())
    from apsimNGpy.core.base_data import load_default_simulations

    al = load_default_simulations(crop='maize', simulations_object=False)
    modelm = al

    # model = load_default_simulations('maize')
    model = APSIMNG(al)

    for N in [3, 300]:
        # for rn in ['Maize, Soybean, Wheat', 'Maize', 'Soybean, Wheat']:
        a = perf_counter()
        # model.RevertCheckpoint()
        model.update_mgt(management=({"Name": 'Sow using a variable rule', 'Population': N},))
        # model.replace_soil_properties_by_path(path='None.Soil.Organic.None.None.Carbon', param_values=[N])
        # model.replace_any_soil_physical(parameter='BD', param_values=[1.23],)
        # model.save_edited_file(reload=True)
        model.run('Report')
        df = model.results
        ui = model.extract_user_input('Sow using a variable rule')
        print(ui)
        print()
        print(df['Maize.Total.Wt'].mean())
        print(df.describe())
        # logger.info(model.results.mean(numeric_only=True))
        b = perf_counter()
        logger.info(f"{b - a}, 'seconds")

        a = perf_counter()
    model.clean_up()
