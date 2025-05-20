"""
Interface to APSIM simulation models using Python.NET
author: Richard Magala
email: magalarich20@gmail.com

"""
import copy
import sys
from types import MappingProxyType
import re
import inspect
import random, pathlib
import string
from shutil import which
from typing import Union
import os, shutil
import numpy as np
import pandas as pd
from os.path import join as opj
import json
import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union, Optional, List, Dict
import warnings
from sqlalchemy.testing.plugin.plugin_base import logging

import apsimNGpy.manager.weathermanager as weather
from functools import cache, lru_cache, singledispatch
# prepare for the C# import
from apsimNGpy.core import pythonet_config
import warnings
from apsimNGpy.core_utils.utils import timer

# now we can safely import C# libraries
from System.Collections.Generic import *
from Models.Core import Simulations, ScriptCompiler, Simulation
from System import *
from Models.Core.ApsimFile import FileFormat
from Models.Climate import Weather
from Models.Soils import Soil, Physical, SoilCrop, Organic, Solute, Chemical


from apsimNGpy.core_utils.utils import open_file_in_window
from apsimNGpy.core.config import get_apsim_bin_path, load_crop_from_disk

from apsimNGpy.core._modelhelpers import (get_or_check_model, Models, old_method,
                                          inspect_model_inputs, soil_components,
                                          ModelTools, _eval_model, replace_variable_by_index,
                                          _find_model, find_model)
from Models.PMF import Cultivar
from apsimNGpy.core.runner import run_model_externally, collect_csv_by_model_path
from apsimNGpy.core.model_loader import (load_apsim_model, save_model_to_file, recompile)
import ast
from typing import Iterable
from collections.abc import Iterable
from typing import Any


rec_limit = sys.getrecursionlimit()

CLASS_MODEL = type(Models.Clock)
TYPE2 = type(Models.Clock())
import inspect

from apsimNGpy.settings import *


def _looks_like_path(value: str) -> bool:
    return any(sep in value for sep in (os.sep, '/', '\\')) or value.endswith('.apsimx')


@dataclass(slots=True)
class CoreModel:
    """
    Modify and run APSIM Next Generation (APSIM NG) simulation models.

    This class serves as the entry point for all apsimNGpy simulations and is inherited by the `ApsimModel` class.
    It is designed to be base class for all apsimNGpy models.

    Parameters:
        model (os.PathLike): The file path to the APSIM NG model. This parameter specifies the model file to be used in the simulation.
        out_path (str, optional): The path where the output file should be saved. If not provided, the output will be saved with the same name as the model file in the current dir_path.
        out (str, optional): Alternative path for the output file. If both `out_path` and `out` are specified, `out` takes precedence. Defaults to `None`.
        experiment (bool, optional): Specifies whether to initiate your model as an experiment defaults to false
        bY default, the experiment is created with permutation but permutation can be passed as a kewy word argument to change
    Keyword parameters:
      **`copy` (bool, deprecated)**: Specifies whether to clone the simulation file. This parameter is deprecated because the simulation file is now automatically cloned by default.

    When an APSIM file is loaded, it is automatically copied to ensure a fallback to the original file in case of any issues during operations.

   Starting with version 0.35, accessing default simulations no longer requires the load_default_simulations function from the base_data module.
   Instead, default simulations can now be retrieved directly via the CoreModel attribute or the ApsimModel class by specifying the name of the crop (e.g., "Maize").
   This means the relevant classes can now accept either a file path or a string representing the crop name.


    """
    model: Union[str, Path, dict] = None
    out_path: Optional[Union[str, Path]] = None
    out: Optional[Union[str, Path]] = None
    set_wd: Optional[Union[str, Path]] = None
    experiment: bool = False
    copy: Optional[bool] = field(default=None)

    # Initialized in __post_init__
    base_name: Optional[str] = field(init=False, default=None)
    others: Dict = field(init=False, default_factory=dict)
    report_names: Optional[List[str]] = field(init=False, default=None)
    factor_names: List[str] = field(init=False, default_factory=list)
    permutation: Optional[bool] = field(init=False, default=None)
    experiment_created: Optional[bool] = field(init=False, default=None)
    _str_model: Optional[str] = field(init=False, default=None)
    _model: Union[str, Path, dict] = field(init=False, default=None)
    model_info: Optional[object] = field(init=False, default=None)
    datastore: Optional[object] = field(init=False, default=None)
    Simulations: Optional[object] = field(init=False, default=None)
    Datastore: Optional[object] = field(init=False, default=None)
    _DataStore: Optional[object] = field(init=False, default=None)
    path: Optional[Union[str, Path]] = field(init=False, default=None)
    _met_file: Optional[str] = field(init=False, default=None)
    ran_ok: bool = field(init=False, default=False)
    factors: Dict = field(init=False, default_factory=dict)
    work_space: Optional[Union[str, Path]] = field(init=False, default=None)
    Start: str = field(init=False, default='unknown')
    End: str = field(init=False, default='unknown')

    def __post_init__(self):
        self._model = self.model
        self.others = {}

        if isinstance(self.out_path, (str, Path)):
            self.out_path = self.out_path
        else:
            self.out_path = None

        if self.out is not None:
            self.out_path = self.out  # `out` overrides `out_path` if both are provided

        self.work_space = self.set_wd or SCRATCH

        if hasattr(self, 'copy') and self.copy:
            warnings.warn(
                'copy argument is deprecated, it is now mandatory to copy the model in order to conserve the original model.',
                UserWarning
            )

        self._met_file = self.others.get('met_file')
        self.model_info = load_apsim_model(
            self._model,
            out_path=self.out_path,
            met_file=self._met_file,
            wd=self.work_space
        )

        self.Simulations = self.model_info.IModel
        self.datastore = self.model_info.datastore
        self.Datastore = self.model_info.DataStore
        self._DataStore = self.model_info.DataStore
        self.path = self.model_info.path

        self.permutation = self.others.get('permutation', True)
        self.base_name = self.others.get('base_name', None)

        if self.experiment:
            self.create_experiment(permutation=self.permutation, base_name=self.base_name)

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
        Simulations is the whole json object Simulation is the child with the field zones, crops, soils and managers
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
        """
        Save the simulation models to file
        @param file_name:    The name of the file to save the defaults to none, taking the exising filename
        @return: model object
        """
        _path = file_name or self.path
        self.path = _path
        save_model_to_file(self.Simulations, out=_path)
        # logger.info(f"Saved model to {_path} {os.path.isfile(_path)}")

        model_info = recompile(self)  # load_apsim_model(_path)
        self.restart_model(model_info)

        return self

    def save_edited_file(self, out_path: os.PathLike = None, reload: bool = False) -> Union['CoreModel', None]:
        """ Saves the model to the local drive.

            Notes: - If `out_path` is None, the `save_model_to_file` function extracts the filename from the
            `Model.Core.Simulation` object. - `out_path`, however, is given high priority. Therefore,
            we first evaluate if it is not None before extracting from the file. - This is crucial if you want to
            give the file a new name different from the original one while saving.

            Parameters
            - out_path (str): Desired path for the .apsimx file, by default, None.
            - reload (bool): Whether to load the file using the `out_path` or the model's original file name.

        """
        old_method('save_edited_file', 'save')
        warnings.warn('The `save_edited_file` method is deprecated use save().', DeprecationWarning)
        # Determine the output path
        _out_path = out_path or self.model_info.path
        save_model_to_file(self.Simulations, out=_out_path)
        if reload:
            self.model_info = load_apsim_model(_out_path)

            self.restart_model()
            return self

    @property
    def results(self) -> pd.DataFrame:
        """
    Legacy method for retrieving simulation results.

    This method is implemented as a property to enable lazy loading—results are only loaded into memory when explicitly accessed.
    This design helps optimize memory usage, especially for large simulations.

    It must be called only after invoking `.run()`. If accessed before the simulation is run, it will raise an error.

    Notes:
    - The `.run()` method should be called with a valid report name or a list of report names (i.e., APSIM report table names).
    - If `report_names` is not provided (i.e., `None`), the system will inspect the model and automatically detect all available report components.
      These reports will then be used to collect the data.
    - If multiple report names are used, their corresponding data tables will be concatenated along the rows.

    Returns:
        pd.DataFrame: A DataFrame containing the simulation output.
    """
        _reports = self.report_names or self.inspect_model('Models.Report', fullpath=False)# false returns all names other than fullpath of the models in that type
        # Collect all available data tables
        if self.ran_ok: # if run was not successfull, then the tables are not populated
            data_tables = collect_csv_by_model_path(self.path)

            # Normalize report_names to a list
            if isinstance(_reports, str):
                reports = [_reports]
            elif isinstance(_reports, (tuple,list)):
                reports = _reports
            else:
                raise TypeError("report_names must be a string, tuple of strings or a list of strings.")

            # Check for missing report names
            missing = [r for r in reports if r not in data_tables]
            if missing:
                raise ValueError(
                    f"The following report names were not found: {missing}. "
                    f"Available tables include: {list(data_tables.keys())}"
                )

            datas = [pd.read_csv(data_tables[i]) for i in reports]
            return pd.concat(datas)
        else:
            msg = "Attempting to get results before running the model"
            logging.error(msg)
            raise RuntimeError(msg)



    def read_from_db_names(self, report_names: Union[str, list], **kwargs) -> pd.DataFrame:
        """
        Reads report data from CSV files generated by the simulation.

        Parameters:
        -----------
        report_names : Union[str, list]
            Name or list of names of report tables to read. These should match the
            report model names in the simulation output.

        Returns:
        --------
        pd.DataFrame
            Concatenated DataFrame containing the data from the specified reports.

        Raises:
        -------
        ValueError
            If any of the requested report names are not found in the available tables.
        RuntimeError
            If the simulation has not been run successfully before attempting to read data.
        """
        # Collect all available data tables
        data_tables = collect_csv_by_model_path(self.path)

        # Normalize report_names to a list
        if isinstance(report_names, str):
            reports = [report_names]
        elif isinstance(report_names, list):
            reports = report_names
        else:
            raise TypeError("report_names must be a string or a list of strings.")

        # Check for missing report names
        missing = [r for r in reports if r not in data_tables]
        if missing:
            raise ValueError(
                f"The following report names were not found: {missing}. "
                f"Available tables include: {list(data_tables.keys())}"
            )

        # Check if simulation ran successfully
        if not self.ran_ok:
            logging.error("Attempted to retrieve results before running the model.")
            raise RuntimeError("Attempting to get results before running the model.")

        # Load and concatenate requested report data
        datas = [pd.read_csv(data_tables[r]) for r in reports]
        return pd.concat(datas, ignore_index=True, axis=kwargs.get('axis', 0))

    def run(self, report_name: Union[tuple, list, str] = None,
            simulations: Union[tuple, list] = None,
            clean_up: bool = False,
            verbose: bool = False,
            **kwargs) -> 'CoreModel':
        """
        Run APSIM model simulations.

        Parameters
        ----------
        report_name : Union[tuple, list, str], optional
            Defaults to APSIM default Report Name if not specified.
            - If iterable, all report tables are read and aggregated into one DataFrame.
            - If None, runs without collecting database results.
            - If str, a single DataFrame is returned.

        simulations : Union[tuple, list], optional
            List of simulation names to run. If None, runs all simulations.

        clean_up : bool, optional
            If True, removes existing database before running.

        verbose : bool, optional
            If True, enables verbose output for debugging. The method continues with debugging info anyway if the run was unsuccessful

        kwargs : dict
            Additional keyword arguments, e.g., to_csv=True

        Returns
        -------
        CoreModel
            Instance of the class CoreModel.
       RuntimeError
            Raised if the APSIM run is unsuccessful. Common causes include missing meteorological files,
            mismatched simulation start dates with weather data, or other configuration issues.
             """
        try:
            # Dispose any existing data store handle
            self._DataStore.Dispose()

            # Save model changes to disk (compile before run)
            self.save()

            # Run APSIM externally
            res = run_model_externally(
                self.model_info.path,
                verbose=verbose,
                to_csv=kwargs.get('to_csv', True)
            )

            if clean_up:
                self.clean_up()
            # returncode 0 is a sign that everything ran fine
            if res.returncode == 0:
                self.ran_ok = True
                self.report_names = report_name

            # If the model failed and verbose was off, rerun to diagnose
            if not self.ran_ok and not verbose:
                self.run(verbose=True)
                raise RuntimeError(f'Model failed to run: {res.returncode}. please diagnose and try again')

            return self


        finally:
            ...
            # close the datastore
            self._DataStore.Close()


    @property
    def simulated_results(self) -> pd.DataFrame:
        """

        @return: pandas data frame containing the data
        Example:
         >>> from apsimNGpy.core.base_data import load_default_simulations
         >>> fmodel = load_default_simulations(crop ='Maize', simulations_object=False) # get path only
         >>> model = CoreModel(fmodel)
         >>> mn=model.run() #3 run the model before colelcting the results
         >>> sr = model.simulated_results

        """
        old_method('simulated_results', 'read_from_db_names')
        if self.ran_ok:
            data_tables = collect_csv_by_model_path(self.path)
            # reports = get_db_table_names(self.datastore)
            bag = []
            for tab, path in data_tables.items():
                _df = pd.read_csv(path)
                _df['TableName'] = tab

                bag.append(_df)
            return pd.concat(bag)
        else:
            raise ValueError("you cant load data before running the model please call run() first")


    def clone_model(self, model_type, model_name, adoptive_parent_type, rename=None, adoptive_parent_name=None,

                    in_place=False):
        """
        Clone an existing model and move it to a specified parent within the simulation structure.
        The function modifies the simulation structure by adding the cloned model to the designated parent.

        This function is useful when a model instance needs to be duplicated and repositioned in the APSIM simulation
        hierarchy without manually redefining its structure.

        Parameters:
        ----------
        model_type : Models
            The type of the model to be cloned, e.g., `Models.Simulation` or `Models.Clock`.
        model_name : str
            The unique identification name of the model instance to be cloned, e.g., `"clock1"`.
        adoptive_parent_type : Models
            The type of the new parent model where the cloned model will be placed.
        rename : str, optional
            The new name for the cloned model. If not provided, the clone will be renamed using
            the original name with a `_clone` suffix.
        adoptive_parent_name : str, optional
            The name of the parent model where the cloned model should be moved. If not provided,
            the model will be placed under the default parent of the specified type.
        in_place : bool, optional
            If True, the cloned model remains in the same location but is duplicated. Defaults to False.

        Returns:
        -------
        None


        Example:
        -------
        >>> from apsimNGpy.core.base_data import load_default_simulations
        >>> model  = load_default_simulations('Maize')
        >>> model.clone_model('Models.Clock', "clock1", 'Models.Simulation', rename="new_clock",adoptive_parent_type= 'Models.Core.Simulations', adoptive_parent_name="Simulation")
        ```
        This will create a cloned version of `"clock1"` and place it under `"Simulation"` with the new name `"new_clock"`.

        """
        # Reference to the APSIM cloning function
        model_type = _eval_model(model_type, evaluate_bound=True)
        adoptive_parent_type = _eval_model(adoptive_parent_type, evaluate_bound=False)

        # Locate the model to be cloned within the simulation scope
        clone_parent = (self.Simulations.FindInScope[model_type](model_name) if model_name
                        else self.Simulations.FindInScope[model_type]())

        # Create a clone of the model
        clone = ModelTools.CLONER(clone_parent)

        # Assign a new name to the cloned model
        new_name = rename if rename else f"{clone.Name}_clone"
        clone.Name = new_name
        #check_exists = self.Simulations.FindInScope[model_type](new_name)
        check_exists = get_or_check_model(self.Simulations, model_type, new_name, action ='delete')

        # Find the adoptive parent where the cloned model should be placed
        parent = (self.Simulations.FindInScope[adoptive_parent_type](adoptive_parent_name) if adoptive_parent_name
                  else self.Simulations.FindInScope[adoptive_parent_type]())

        # Add the cloned model to the new parent
        parent.Children.Add(clone)

        # Save the changes to the simulation structure
        self.save()

    @staticmethod
    def find_model(model_name: str, model_namespace=None):
        """
        Find a model from the Models namespace and return its path.

        Args:
            model_name (str): The name of the model to find.
            model_namespace (object, optional): The root namespace (defaults to Models).
            path (str, optional): The accumulated path to the model.

        Returns:
            str: The full path to the model if found, otherwise None.

        Example:
            >>> from apsimNGpy import core  # doctest: +SKIP
             >>> model =core.base_data.load_default_simulations(crop = "Maize")  # doctest: +SKIP
             >>> model.find_model("Weather")  # doctest: +SKIP
             'Models.Climate.Weather'
             >>> model.find_model("Clock")  # doctest: +SKIP
              'Models.Clock'

        """
        return _eval_model(model_name)
    def add_model(self, model_type, adoptive_parent, rename=None,
                  adoptive_parent_name=None, verbose=False, source='Models', source_model_name=None, override=True, **kwargs):

        """
        Adds a model to the Models Simulations namespace.

        Some models are restricted to specific parent models, meaning they can only be added to compatible models.
        For example, a Clock model cannot be added to a Soil model.

        Args:
            :model_type (str or Models object): The type of model to add, e.g., `Models.Clock` or just `"Clock"`. if the APSIM Models namespace is exposed to the current script, then model_type can be Models.Clock without strings quotes
            rename (str): The new name for the model.

            :adoptive_parent (Models object): The target parent where the model will be added or moved e.g `Models.Clock` or Clock as string all are valid

            :adoptive_parent_name (Models object, optional): Specifies the parent name for precise location. e.g Models.Core.Simulation or Simulations all are valid

            :source (Models, str, CoreModel, ApsimModel object): defaults to Models namespace, implying a fresh non modified model.
            The source can be an existing Models or string name to point to one fo the default model example, which we can extract the model 
            
            :override (bool, optional): defaults to `True`. When `True` (recomended) it delete for any model with same name and type at the suggested parent location before adding the new model
            if False and proposed model to be added exists at the parent location, APSIM automatically generates a new name for the newly added model. This is not recommended.
        Returns:
            None: Models are modified in place, so models retains the same reference.

        Note:
            Added models are initially empty. Additional configuration is required to set parameters.
            For example, after adding a Clock module, you must set the start and end dates.

        Example:

         >>> from apsimNGpy import core
         >>> from apsimNGpy.core.core import Models
         >>> model =core.base_data.load_default_simulations(crop = "Maize")
         >>> model.remove_model(Models.Clock) # first delete model
         >>> model.add_model(Models.Clock, adoptive_parent = Models.Core.Simulation, rename = 'Clock_replaced', verbose=False)

         >>> model.add_model(model_type=Models.Core.Simulation, adoptive_parent=Models.Core.Simulations, rename='Iowa')
         >>> model.preview_simulation() # doctest: +SKIP
         >>> model.add_model(Models.Core.Simulation, adoptive_parent='Simulations', rename='soybean_replaced', source='Soybean') # basically adding another simulation from soybean to the maize simulation
         

        """
        import Models
        replacer = {'Clock': 'change_simulation_dates', 'Weather': 'replace_met_file'}
        sims = self.Simulations
        model_type = _eval_model(model_type, evaluate_bound=True)
        adoptive_parent = _eval_model(adoptive_parent, evaluate_bound=False)
        # find where to add the model
        if adoptive_parent == Models.Core.Simulations:
            parent = self.Simulations
        else:
            if not adoptive_parent_name:
                adoptive_parent_name = adoptive_parent().Name
            parent = sims.FindInScope[adoptive_parent](adoptive_parent_name)
        if model_type == Models.Core.Simulations:
            raise ValueError(f"{model_type} can not be a simulations holder did you mean 'Models.Core.Simulation' or 'Simulation'?")
        # parent = _model.Simulations.FindChild(where)

        if source =='Models':
            model_type = model_type
        else:
            # look for the model from source
            if isinstance(source,(str, dict)):
                source_model= load_apsim_model(source)
            elif isinstance(source, CoreModel):
                source_model = source
            else:
                raise ValueError(f"model type {type(source)} is not supported. Please supply a crop name or path to the apsim file or apsimNGpy.core.CoreModel objects")
            model_type = (source_model.IModel.FindInScope[model_type](source_model_name) if source_model_name else
            source_model.IModel.FindInScope[model_type]() )

            if not model_type:
                if not source_model_name:
                    raise ValueError(f"{model_type} can not be found. Did you forget to specify the `source_model_name`")
                else:
                    raise ValueError(f"{model_type} can not be found. Please recheck your input or use inspect_file() to see all the available model types")

            model_type.Name  = rename if rename else model_type.Name
            # target_child = parent.FindInScope[model_type.__class__](model_type.Name)
           # target_child = get_or_check_model(parent, model_type.__class__, model_type.Name, action ='delete')
            if override:
                dilit = get_or_check_model(parent, model_type.__class__, model_type.Name, action='delete')


            ModelTools.ADD(model_type, parent)
            self.save()
            if verbose:
                logger.info(f"Added {loc.Name} to {parent.Name}")
            return self
        if model_type and parent:
            loc = model_type()
            loc_name = loc.Name if hasattr(loc, 'Name') else None
            if rename and hasattr(loc, 'Name'):
                loc.Name = rename
            if hasattr(loc, 'Name'):
                target_child = parent.FindChild[model_type](loc.Name)
                if target_child and override:
                    # not raising the error still studying the behaviors of adding a child that already exists
                    DELETE(target_child)

            ModelTools.ADD(loc, parent)

            if verbose:
                logger.info(f"Added {loc.Name} to {parent.Name}")
            # we need to put the changes into effect
            self.save()
            # if verbose:
            #     logger.info(f'successfully saved to {self.path}')

        else:
            logger.debug(f"Adding {model_type} to {parent.Name} failed, perhaps models was not found")

    def edit_model(self, model_type: str, simulations: Union[str, list], model_name: str, **kwargs):
        """
        Modify various APSIM model components by specifying the model type and name across given simulations.

        Parameters
        ----------
        model_type : str
            Type of the model component to modify (e.g., 'Clock', 'Manager', 'Soils.Physical', etc.).
        simulations : Union[str, list], optional
            A simulation name or list of simulation names in which to search. Defaults to all simulations in the model.
        model_name : str
            Name of the model instance to modify.
        **kwargs : dict
            Additional keyword arguments specific to the model type. These vary by component:

            - Weather:
                - `weather_file` (str): Path to the weather `.met` file.

            - Clock:
                - Date properties such as `Start` and `End` in ISO format (e.g., '2021-01-01').

            - Manager:
                - Variables to update in the Manager script using `update_mgt_by_path`.

            - Soils.Physical / Soils.Chemical / Soils.Organic / Soils.Water:
                - Variables to replace using `replace_soils_values_by_path`.

            - Report:
                - `report_name` (str): Name of the report model (optional depending on structure).
                - `variable_spec` (list[str] or str): Variables to include in the report.
                - `set_event_names` (list[str], optional): Events that trigger the report.

            - Cultivar:
                - `commands` (str): APSIM path to the cultivar parameter to update.
                - `values` (Any): Value to assign.
                - `cultivar_manager` (str): Name of the Manager script managing the cultivar, which must contain the `CultivarName` parameter. Required to propagate updated cultivar values, as APSIM treats cultivars as read-only.

        Raises
        ------
        ValueError
            If the model instance is not found, required kwargs are missing, or `kwargs` is empty.
        NotImplementedError
            If the logic for the specified `model_type` is not implemented.

        Examples
        --------

        >>> model = CoreModel(model='Maize')

        # Edit a cultivar model

        >>> model.edit_model(
        ...     model_type='Cultivar',
        ...     simulations='Simulation',
        ...     commands='[Phenology].Juvenile.Target.FixedValue',
        ...     values=256,
        ...     model_name='B_110',
        ...     cultivar_manager='Sow using a variable rule'
        ... )

        # Edit a soil organic matter module

        >>> model.edit_model(
        ...     model_type='Organic',
        ...     simulations='Simulation',
        ...     model_name='Organic',
        ...     Carbon=1.23
        ... )

        # Edit multiple soil layers

        >>> model.edit_model(
        ...     model_type='Organic',
        ...     simulations='Simulation',
        ...     model_name='Organic',
        ...     Carbon=[1.23, 1.0]
        ... )

        # Edit solute models

        >>> model.edit_model(
        ...     model_type='Solute',
        ...     simulations='Simulation',
        ...     model_name='NH4',
        ...     InitialValues=0.2
        ... )

        >>> model.edit_model(
        ...     model_type='Solute',
        ...     simulations='Simulation',
        ...     model_name='Urea',
        ...     InitialValues=0.002
        ... )

        # Edit a manager script

        >>> model.edit_model(
        ...     model_type='Manager',
        ...     simulations='Simulation',
        ...     model_name='Sow using a variable rule',
        ...     population=8.4
        ... )

        # Edit surface organic matter parameters

        >>> model.edit_model(
        ...     model_type='SurfaceOrganicMatter',
        ...     simulations='Simulation',
        ...     model_name='SurfaceOrganicMatter',
        ...     InitialResidueMass=2500
        ... )

        >>> model.edit_model(
        ...     model_type='SurfaceOrganicMatter',
        ...     simulations='Simulation',
        ...     model_name='SurfaceOrganicMatter',
        ...     InitialCNR=85
        ... )

        # Edit Clock start and end dates

        >>> model.edit_model(
        ...     model_type='Clock',
        ...     simulations='Simulation',
        ...     model_name='Clock',
        ...     Start='2021-01-01',
        ...     End='2021-01-12'
        ... )

        # Edit report variables

        >>> model.edit_model(
        ...     model_type='Report',
        ...     simulations='Simulation',
        ...     model_name='Report',
        ...     variable_spec='[Maize].AboveGround.Wt as abw'
        ... )

        # Multiple report variables

        >>> model.edit_model(
        ...     model_type='Report',
        ...     simulations='Simulation',
        ...     model_name='Report',
        ...     variable_spec=[
        ...         '[Maize].AboveGround.Wt as abw',
        ...         '[Maize].Grain.Total.Wt as grain_weight'
        ...     ]
        ... )
        """

        model_type_class = _eval_model(model_type)


        for sim in self.find_simulations(simulations):
            model_instance = get_or_check_model(sim, model_type_class, model_name, action ='get')

            match type(model_instance):
                case Models.Climate.Weather:
                    met_file = kwargs.get('weather_file')
                    if met_file is None:
                        raise ValueError('Use key word argument "weather_file" to supply the weather data')
                    # To avoid carrying over a silent bug or waiting for the bug to manifest during model run, there is need to raise here
                    if not os.path.exists(met_file):
                        raise FileNotFoundError(f"'{met_file}' rejected because it does not exist on the computer")

                    model_instance.FileName = met_file
                case Models.Clock:
                    validated = dict(End = 'End', Start = 'Start', end = 'End', start = 'Start', end_date ='End', start_date ='Start')

                    for kwa, value in kwargs.items():
                        key = validated.get(kwa, 'unknown') # APSIM uses camelcase
                        if key in ['End', 'Start']:
                            parsed_value = DateTime.Parse(value)
                            setattr(model_instance, key, parsed_value)
                            logger.info(f"Set {key} to {parsed_value}")
                            setattr(self, key, value)
                        else:
                            raise AttributeError(f"no valid Clock attributes were passed. Valid arguments are: '{", ".join(validated.keys())}'")


                case Models.Manager:

                    manager_path = model_instance.FullPath
                    self.update_mgt_by_path(path=manager_path, fmt='.', **kwargs)

                case Models.Soils.Physical | Models.Soils.Chemical | Models.Soils.Organic | Models.Soils.Water | Models.Soils.Solute:

                    self.replace_soils_values_by_path(node_path=model_instance.FullPath, **kwargs)
                case  Models.Surface.SurfaceOrganicMatter:
                    if not kwargs:
                        raise ValueError(f"Missing keyword argument 'kwargs'")
                    selected_parameters = set(kwargs.keys())
                    accepted_attributes = { 'SurfOM',
                                           'InitialCPR', 'InitialResidueMass',
                                           'InitialCNR', 'IncorporatedP',}
                    dif = accepted_attributes - selected_parameters
                    if dif == accepted_attributes:
                        raise AttributeError(f"'{', '.join(selected_parameters)}' are not valid")
                    for param in selected_parameters:
                        if hasattr(model_instance, param):
                            setattr(model_instance, param, kwargs[param])
                            print('success', param)
                        else:
                            raise AttributeError(f"suggested attribute {param} is not an attribute of {model_instance}")

                case Models.Report:

                    set_event_names = kwargs.get('set_event_names')
                    report_name = model_name

                    vs = kwargs.get("variable_spec")
                    if not vs:
                        raise ValueError("Please specify a report name using key word 'variable_spec'")
                    self.add_report_variable(variable_spec=vs, set_event_names=set_event_names, report_name=report_name)

                case Models.PMF.Cultivar:

                    if 'Replacements' not in self.inspect_model('Models.Core.Folder'):
                        for i in self.inspect_model(Models.PMF.Plant, fullpath=False):
                            self.add_crop_replacements(_crop=i)

                    commands = kwargs.get("commands")
                    values = kwargs.get("values")
                    # need to specify back to the cultivar manager script the new cultivar name since APSIM is not allowing editing in place.
                    # this is a temporal fix though
                    # editing in place could work if we were reusing the model in memory of python
                    cultivar_manager_paramter_name= kwargs.get("parameter_name", 'CultivarName')
                    cultivar_manager = kwargs.get("cultivar_manager")
                    # the reason the parameter path is split into command and values to allow passing different values during optimization
                    # Errors should mot pass silently
                    if not cultivar_manager:
                        raise ValueError("Please specify a cultivar manager using key word 'cultivar_manager'")
                    if not commands or values is None:
                        raise ValueError("Both 'commands' and 'values' must be provided for Cultivar")
                    # find replacement
                    rep = get_or_check_model(self.Simulations, Models.Core.Folder, 'Replacements', action ='get')
                    # now get cultivar
                    cultvar = get_or_check_model(rep, Models.PMF.Cultivar, model_name, action ='get')

                    cultvar =ModelTools.CLONER(cultvar) # let's clone
                    params = self._cultivar_params(cultvar)
                    params[commands] = values

                    updated_commands = [f"{k}={v}" for k, v in params.items()]
                    cultvar.set_Command(updated_commands)

                    plant = kwargs.get('plant')
                    CroP_Parent = get_or_check_model(rep, Models.PMF.Plant, plant, action='get')
                    cultvarName =f"edited_cultivar_{model_name}"
                    # mask out the current name such that is not accessed
                    current_name = cultvar.Name
                    cultvar.Name = f"p_{model_name}"

                    get_or_check_model(rep, Models.PMF.Cultivar, cultvarName, action ='delete')# this will delete the model if found before we add

                    cultvar.Name = cultvarName

                    ModelTools.ADD(cultvar, CroP_Parent)
                    extra_args = {cultivar_manager_paramter_name: cultvarName}
                    self.edit_model(Models.Manager, sim.Name, model_name =cultivar_manager,**extra_args)
                    self.save()
                    logger.info(f"edited Cultivar '{model_name}' and saved it as {cultvarName}")

                case _:
                    raise NotImplementedError(f"No edit method implemented for model type {type(model_instance)}")
        self.ran_ok = False
        return self

    def add_report_variable(self, variable_spec: Union[list, str, tuple], report_name: str = None, set_event_names:Union[str,list]=None):
        """
        This adds a report variable to the end of other variables, if you want to change the whole report use change_report

        Parameters
        -------------------

        :param variable_spec: (str, required): list of text commands for the report variables e.g., '[Clock].Today as Date'
        :param report_name: (str, optional): name of the report variable if not specified the first accessed report object will be altered
        :set_event_names (list or str, optional): A list of APSIM events that trigger the recording of variables.
                                                     Defaults to ['[Clock].EndOfYear'] if not provided.
        :Returns:
            returns instance of apsimNGpy.core.core.apsim.ApsimModel or apsimNGpy.core.core.apsim.CoreModel
           raises an erros if a report is not found
        Example:
        >>> from apsimNGpy import core

        >>> model = core.base_data.load_default_simulations()

        >>> model.add_report_variable(variable_spec = '[Clock].Today as Date', report_name = 'Report')
        """
        if isinstance(variable_spec, str):
            variable_spec = [variable_spec]

        if report_name:
            get_report = self.Simulations.FindInScope[Models.Report](report_name)
        else:
            get_report = self.Simulations.FindInScope[Models.Report]()
        get_cur_variables = list(get_report.VariableNames)
        get_cur_variables.extend(variable_spec)
        final_command = "\n".join(get_cur_variables)
        get_report.set_VariableNames(final_command.strip().splitlines())
        if set_event_names:
            if isinstance(set_event_names, str):
                set_event_names = [set_event_names]
            set_event_names = list(set(set_event_names))
            final_command = "\n".join(set_event_names)
            get_report.set_EventNames(final_command.strip().splitlines())

        self.save()

    @property
    def extract_simulation_name(self):
        warnings.warn(
            'extract_simulation_name is deprecated for future versions use simulation_names or get_simulation_names', FutureWarning)
        """logger.info or extract a simulation name from the model

            Returns:
            -------------
                The name of the simulation to remove
                
        """
        # this is a repetition because I want to deprecate it and maintain simulation_name or use get_simulation_name
        return self.simulation_names

    def remove_model(self, model_type: Models, model_name: str = None):
        """
       Removes a model from the APSIM Models.Simulations namespace.

        Parameters
        ----------
        model_type : Models
            The type of the model to remove (e.g., `Models.Clock`). This parameter is required.

        model_name : str, optional
            The name of the specific model instance to remove (e.g., `"Clock"`). If not provided, all models of the
            specified type may be removed.
        @Returns:
           None
        Example:
               >>> from apsimNGpy import core
               >>> from apsimNGpy.core.core import Models

               >>> model = core.base_data.load_default_simulations(crop = 'Maize')
               >>> model.remove_model(Models.Clock) #deletes the clock node
               >>> model.remove_model(Models.Climate.Weather) #deletes the weather node
        """
        model_type = _eval_model(model_type)
        if not model_name:
            model_name = model_type().Name
        to_remove= self.Simulations.FindInScope[model_type](model_name)
        if to_remove:
            DELETE(to_remove)
        self.save()

    def move_model(self, model_type: Models, new_parent_type: Models, model_name: str = None,
                   new_parent_name: str = None, verbose: bool = False, simulations: Union[str, list] = None):
        """
        Args:

        - model_type (Models): type of model tied to Models Namespace
        - new_parent_type: new model parent type (Models)
        - model_name:name of the model e.g., Clock, or Clock2, whatever name that was given to the model
        -  new_parent_name: what is the new parent names =Field2, this field is optional but important if you have nested simulations
        Returns:

          returns instance of apsimNGpy.core.core.apsim.ApsimModel or apsimNGpy.core.core.apsim.CoreModel

        """
        sims = self.Simulations

        model_type = _eval_model(model_type)
        new_parent_type = _eval_model(new_parent_type)
        if model_type == Models.Core.Simulations:
            raise ValueError('Can not move a model of type "Models.Core.Simulations". Did you mean Models.Core.Simulation or Simulation?')
        if not model_name:
            model_name = model_type().Name

        child_to_move = get_or_check_model(sims, model_type, model_name, action='get')#sims.FindInScope[model_type](model_name)
        if not new_parent_name:
            new_parent_name = new_parent_type().Name

        new_parent = get_or_check_model(sims, new_parent_type, new_parent_name, action ='get')

        ModelTools.MOVE(child_to_move, new_parent)
        if verbose:
            logger.info(f"Moved {child_to_move.Name} to {new_parent.Name}")
        self.save()

    def rename_model(self, model_type: Models, old_model_name: str, new_model_name: str, simulations=None):
        """
        give new name to a model in the simulations
        @param model_type: (Models) Models types e.g., Models.Clock
        @param old_model_name: (str) current model name
        @param new_model_name: (str) new model name
        @param simulation: (str, optional) defaults to all simulations
        @return: None
        Example;
               >>> from apsimNGpy import core
               >>> from apsimNGpy.core.core import Models
               >>> apsim = core.base_data.load_default_simulations(crop = 'Maize')
               >>> apsim = apsim.rename_model(Models.Clock, 'Clock', 'clock')

        """
        model_type = _eval_model(model_type)
        def _rename(_sim):
            #__sim = _sim.FindInScope[model_type](old_model_name)
            __sim  = get_or_check_model(self.Simulations, model_type=model_type, model_name=old_model_name, action ='get')
            __sim.Name = new_model_name
        if model_type == Models.Core.Simulations:
            self.Simulations.Name = new_model_name
            return self
        else:
            sims = self.find_simulations(simulations)
            for sim in sims:
                if model_type == Models.Core.Simulation:
                    sim.Name = new_model_name
                    continue
                _rename(sim)

        self.save()

    @property  #
    def extract_report_names(self) -> dict:
        """ returns all data frames the available report tables
        @return: dict of  table names in alist in the simulation

        """
        old_method('extract_report_names', 'inspect_model')
        table_dict = self.get_report(names_only=True)
        return table_dict

    def replicate_file(self, k: int, path: os.PathLike = None, suffix: str = "replica"):
        """
        Replicates a file 'k' times.

        If a path is specified, the copies will be placed in that dir_path with incremented filenames.

        If no path is specified, copies are created in the same dir_path as the original file, also with incremented filenames.

        Parameters:
        - self: The core.api.CoreModel object instance containing 'path' attribute pointing to the file to be replicated.

        - k (int): The number of copies to create.

        - path (str, optional): The dir_path where the replicated files will be saved. Defaults to None, meaning the
        same dir_path as the source file.

        - suffix (str, optional): a suffix to attached with the copies. Defaults to "replicate"


        Returns:
        - A list of paths to the newly created files if get_back_list is True else a generator is returned.
        """
        if path is None:
            file_name = self.path.rsplit('.apsimx', 1)[0]
            return [shutil.copy(self.model_info.path, f"{file_name}_{i}_{suffix}.apsimx") for i in range(k)]

        else:
            b_name = os.path.basename(self.path).rsplit('.apsimx', 1)[0]
            return [shutil.copy(self.model_info.path, os.path.join(path, f"{b_name}_{suffix}_{i}.apsimx")) for i in
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

    def _find_cultivar(self, cultivar_name: str):

        rep = self._find_replacement().FindAllDescendants[Models.PMF.Cultivar]()
        xp = [i for i in rep]
        for cult in xp:
            if cult.Name == cultivar_name:
                return cult
                break
        return rep

    def read_cultivar_params(self, name: str, verbose: bool = None):
        old_method('read_cultivar_params', 'inspect_model_parameters')
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
        rep = self._find_replacement()
        crop_rep = rep.FindAllDescendants[Models.PMF.Plant](Crop)
        for i in crop_rep:
            logger.info(i.Name)
            if i.Name == Crop:
                return i
        return self
    def inspect_model_parameters(self, model_type:Union[Models, str], model_name:str, simulations: Union[str, list] ='all', parameters:Union[list, set, tuple, str] ='all', **kwargs):
        """
        Inspect the input parameters of a specific APSIM model type instance within selected simulations.

        This method consolidates functionality previously spread across `examine_management_info`, `read_cultivar_params`, and other inspectors,
        allowing a unified interface for querying parameters of interest across a wide range of APSIM models.

        Parameters
        ----------
        model_type : str
            The name of the model class to inspect (e.g., 'Clock', 'Manager', 'Physical', 'Chemical', 'Water', 'Solute').
            Shorthand names are accepted (e.g., 'Clock', 'Weather') as well as fully qualified names (e.g., 'Models.Clock', 'Models.Climate.Weather').
        simulations : Union[str, list]
            A single simulation name or a list of simulation names within the APSIM context to inspect.
        model_name : str
            The name of the specific model instance within each simulation. For example, if `model_type='Solute'`,
            `model_name` might be 'NH4', 'Urea', or another solute name.
        parameters : Union[str, set, list, tuple], optional
            A specific parameter or a collection of parameters to inspect. Defaults to `'all'`, in which case all accessible attributes are returned.
            For layered models like Solute, valid parameters include `Depth`, `InitialValues`, `SoluteBD`, `Thickness`, etc.
        **kwargs : dict
            Reserved for future compatibility; currently unused.

        Returns
        -------
        Union[dict, list, pd.DataFrame, Any]
            The format depends on the model type:
            - Weather: file path(s) as string(s)
            - Clock: dictionary with start and end datetime objects (or a single datetime if only one is requested)
            - Manager: dictionary of script parameters
            - Soil-related models: pandas DataFrame of layered values
            - Report: dictionary with `VariableNames` and `EventNames`
            - Cultivar: dictionary of parameter strings

        Raises
        ------
        ValueError
            If the specified model or simulation is not found or arguments are invalid.
        NotImplementedError
            If the model type is unsupported by the current interface.

        Requirements
        ------------
        - APSIM Next Generation Python bindings (`apsimNGpy`)
        - Python 3.10+

        Examples
        --------
        >>> model_instance = CoreModel('Maize')

        # Inspect full soil organic profile

        >>> model_instance.inspect_model_parameters('Organic', simulations='Simulation', model_name='Organic')
           CNR  Carbon      Depth  FBiom  ...         FOM  Nitrogen  SoilCNRatio  Thickness
        0  12.0    1.20      0-150   0.04  ...  347.129032     0.100         12.0      150.0
        1  12.0    0.96    150-300   0.02  ...  270.344362     0.080         12.0      150.0
        2  12.0    0.60    300-600   0.02  ...  163.972144     0.050         12.0      300.0
        3  12.0    0.30    600-900   0.02  ...   99.454133     0.025         12.0      300.0
        4  12.0    0.18   900-1200   0.01  ...   60.321981     0.015         12.0      300.0
        5  12.0    0.12  1200-1500   0.01  ...   36.587131     0.010         12.0      300.0
        6  12.0    0.12  1500-1800   0.01  ...   22.191217     0.010         12.0      300.0
        [7 rows x 9 columns]

        # Inspect chemical soil properties

        >>> model_instance.inspect_model_parameters('Chemical', simulations='Simulation', model_name='Chemical')

        # Inspect one or more specific parameters

        >>> model_instance.inspect_model_parameters('Organic', simulations='Simulation', model_name='Organic', parameters='Carbon')
          Carbon
        0    1.20
        1    0.96
        2    0.60
        3    0.30
        4    0.18
        5    0.12
        6    0.12

        >>> model_instance.inspect_model_parameters('Organic', simulations='Simulation', model_name='Organic', parameters=['Carbon', 'CNR'])
           Carbon   CNR
        0    1.20  12.0
        1    0.96  12.0
        2    0.60  12.0
        3    0.30  12.0
        4    0.18  12.0
        5    0.12  12.0
        6    0.12  12.0

        # Inspect Report module attributes

        >>> model_instance.inspect_model_parameters('Report', simulations='Simulation', model_name='Report')
        {'EventNames': ['[Maize].Harvesting'],
        'VariableNames': ['[Clock].Today',
        '[Maize].Phenology.CurrentStageName',
        '[Maize].AboveGround.Wt',
        '[Maize].AboveGround.N',
        '[Maize].Grain.Total.Wt*10 as Yield',
        '[Maize].Grain.Wt',
        '[Maize].Grain.Size',
        '[Maize].Grain.NumberFunction',
        '[Maize].Grain.Total.Wt',
        '[Maize].Grain.N',
        '[Maize].Total.Wt']}

        >>> model_instance.inspect_model_parameters('Report', simulations='Simulation', model_name='Report', parameters='EventNames')
        {'EventNames': ['[Maize].Harvesting']}

        # Inspect weather file path

        >>> model_instance.inspect_model_parameters('Weather', simulations='Simulation', model_name='Weather')
        '%root%/Examples/WeatherFiles/AU_Dalby.met'

        # Inspect manager script parameters

        >>> model_instance.inspect_model_parameters('Manager',
        ... simulations='Simulation', model_name='Sow using a variable rule')

        >>> model_instance.inspect_model_parameters('Manager',
        ... simulations='Simulation', model_name='Sow using a variable rule',
        ... parameters='Population')

        # Inspect cultivar parameters

        >>> model_instance.inspect_model_parameters('Cultivar',
        ... simulations='Simulation', model_name='B_110') # lists all path specifications for B_110 parameters abd their values
        >>> model_instance.inspect_model_parameters('Cultivar', simulations='Simulation',
        ... model_name='B_110', parameters='[Phenology].Juvenile.Target.FixedValue')
        {'[Phenology].Juvenile.Target.FixedValue': '210'}

        # Inspect surface organic matter module

        >>> model_instance.inspect_model_parameters('Models.Surface.SurfaceOrganicMatter',
        ... simulations='Simulation', model_name='SurfaceOrganicMatter')

        {'NH4': 0.0,
         'InitialResidueMass': 500.0,
         'StandingWt': 0.0,
         'Cover': 0.0,
         'LabileP': 0.0,
         'LyingWt': 0.0,
         'InitialCNR': 100.0,
         'P': 0.0,
         'InitialCPR': 0.0,
         'SurfOM': <System.Collections.Generic.List[SurfOrganicMatterType] object at 0x000001DABDBB58C0>,
         'C': 0.0,
         'N': 0.0,
         'NO3': 0.0}

        >>> model_instance.inspect_model_parameters('Models.Surface.SurfaceOrganicMatter', simulations='Simulation',
        ... model_name='SurfaceOrganicMatter', parameters={'InitialCNR', 'InitialResidueMass'})

        {'InitialCNR': 100.0, 'InitialResidueMass': 500.0}

        # Inspect simulation clock

        >>> model_instance.inspect_model_parameters('Clock', simulations='Simulation', model_name='Clock')

         {'End': datetime.datetime(2000, 12, 31, 0, 0),
         'Start': datetime.datetime(1990, 1, 1, 0, 0)}

        >>> model_instance.inspect_model_parameters('Clock', simulations='Simulation', model_name='Clock', parameters='End')

         datetime.datetime(2000, 12, 31, 0, 0)

        >>> model_instance.inspect_model_parameters('Clock', simulations='Simulation', model_name='Clock', parameters='Start').year

        1990

        # Inspect solute models

        >>> model_instance.inspect_model_parameters('Solute', simulations='Simulation', model_name='Urea')
        >>> model_instance.inspect_model_parameters('Solute', simulations='Simulation', model_name='NH4',
        ... parameters='InitialValues')
        """

        if parameters == 'all':
            parameters = None # non is easy to deal with at the back end but all is intuitive
        if simulations == 'all':
            simulations = self.inspect_model('Simulation', fullpath=False)
            simulations = simulations[0] if len(simulations) == 1 else simulations

        return inspect_model_inputs(self, model_type, simulations, model_name, parameters, **kwargs)


    def edit_cultivar(self, *, CultivarName: str, commands: str, values: Any, **kwargs):
        """
        @deprecated
        Edits the parameters of a given cultivar. we don't need a simulation name for this unless if you are defining it in the
        manager section, if that it is the case, see update_mgt.

        Requires:
           required a replacement for the crops

        Args:

          - CultivarName (str, required): Name of the cultivar (e.g., 'laila').

          - variable_spec (str, required): A strings representing the parameter paths to be edited.
                         Example: ('[Grain].MaximumGrainsPerCob.FixedValue', '[Phenology].GrainFilling.Target.FixedValue')

          - values: values for each command (e.g., (721, 760)).

        Returns: instance of the class CoreModel or ApsimModel

        """
        old_method('edit_cultivar', 'edit_model')
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


    def update_cultivar(self, *, parameters: dict, simulations: Union[list, tuple] = None, clear=False, **kwargs):
        """Update cultivar parameters

        Parameters
        ----------
       - parameters (dict, required) dictionary of cultivar parameters to update.

       - simulations, optional
            List or tuples of simulation names to update if `None` update all simulations.
       - clear (bool, optional)
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
        """
        This will show the current management scripts in the simulation root

        Parameters
        ----------
        simulations, optional
            List or tuple of simulation names to update, if `None` show all simulations. if you are not sure,

            use the property decorator 'extract_simulation_name'

        """
        old_method('examine_management_info', new_method='inspect_model_parameters')
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

    def check_som(self, simulations=None):
        old_method('check_som', new_method='inspect_model_parameters')
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
                raise ValueError("File child structure is not supported at a moment")
        return simus

    def change_som(self, *, simulations: Union[tuple, list] = None, inrm: int = None, icnr: int = None,
                   surface_om_name='SurfaceOrganicMatter', **kwargs):
        """
         Change Surface Organic Matter (SOM) properties in specified simulations.

    Parameters:
        simulations (str ort list): List of simulation names to target (default: None).

        inrm (int): New value for Initial Residue Mass (default: 1250).

        icnr (int): New value for Initial Carbon to Nitrogen Ratio (default: 27).

        surface_om_name (str, optional): name of the surface organic matter child defaults to ='SurfaceOrganicMatter'
    Returns:
        self: The current instance of the class.

        """
        old_method('change_som', new_method='edit_model')
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
                    f"File child structure is not supported at a moment. or {surface_om_name} not found in the file "
                    f"rename your SOM module to"
                    "SurfaceOrganicMatter")
            # mp.Value.InitialResidueMass

            return self

    def convert_to_IModel(self):
        if isinstance(self.Simulations, Models.Core.ApsimFile.ConverterReturnType):
            return self.Simulations.get_NewModel()
        else:
            return self.Simulations

    # experimental
    def recompile_edited_model(self, out_path: os.PathLike):
        """
        Args:
        ______________
        out_path: os.PathLike object this method is called to convert the simulation object from ConverterReturnType to model like object

        return: self

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

    def update_mgt_by_path(self, *, path: str, fmt='.', **kwargs):
        """
        Args:
        _________________
        path: complete node path to the script manager e.g. '.Simulations.Simulation.Field.Sow using a
        variable rule'

        fmt: seperator for formatting the path e.g., ".". Other characters can be used with
        caution, e.g., / and clearly declared in fmt argument.
         For the above path if we want to use the forward slash, it will be '/Simulations/Simulation/Field/Sow using a variable rule', fmt = '/'

        kwargs: Corresponding keyword arguments representing the paramters in the script manager and their values. Values is what you want
        to change to; Example here Population =8.2, values should be entered with their corresponding data types e.g.,
        int, float, bool,str etc.

        return: self

        """
        #old_method('update_mgt_by_path', new_method='edit_model')
        # reject space in fmt
        if fmt != '.':
            path = path.replace(fmt, ".")


        manager = self.Simulations.FindByPath(path)
        stack_manager_depth = range(len(manager.Value.Parameters))
        if kwargs == {}:
            raise ValueError(
                "Please supply parameters and their values as keyword arguments. "
                "These arguments are unique for each script.\n"
                f"In '{path}', the following parameters were found: "
                f"{[manager.Value.Parameters[i].Key for i in stack_manager_depth]}.\n"
                "You need to specify at least one of them."
            )

        for i in stack_manager_depth:
            _param = manager.Value.Parameters[i].Key

            if _param in kwargs:
                manager.Value.Parameters[i] = KeyValuePair[String, String](_param, f"{kwargs[_param]}")
                # remove the successfully processed keys
                kwargs.pop(_param)
        if len(kwargs.keys()) > 0:
            logger.error(f"The following {kwargs} were not found in {path}")
        out_mgt_path = self.path
        self.recompile_edited_model(out_path=out_mgt_path)

        return self
    @timer
    def exchange_model(self, model, model_type:str,model_name=None, target_model_name=None, simulations:str=None):
        old_method('exchange_model', new_method=replace_model_from)
        self.replace_model_from(model, model_type, model_name, target_model_name, simulations)

    def replace_model_from(
            self,
            model,
            model_type: str,
            model_name: str = None,
            target_model_name: str = None,
            simulations: str = None
    ):
        """
        Replace a model e.g., a soil model with another soil model from another APSIM model.
        The method assumes that the model to replace is already loaded in the current model and is is the same class as source model.
        e.g., a soil node to soil node, clock node to clock node, et.c

        Args:
            model: Path to the APSIM model file or a CoreModel instance.
            model_type (str): Class name (as string) of the model to replace (e.g., "Soil").
            model_name (str, optional): Name of the model instance to copy from the source model.
                If not provided, the first match is used.
            target_model_name (str, optional): Specific simulation name to target for replacement.
                Only used when replacing Simulation-level objects.
            simulations (str, optional): Simulation(s) to operate on. If None, applies to all.

        Returns:
            self: To allow method chaining.

        Raises:
            ValueError: If model_type is "Simulations" which is not allowed for replacement.
        """

        # Validate and resolve the model type string into the correct class
        model_type = _eval_model(model_type)

        # Load the source model (if a path is provided instead of a CoreModel instance)
        model2 = load_apsim_model(model) if not isinstance(model, CoreModel) else model

        # Find the target model component in the source model
        get_target_model = (
            model2.IModel.FindInScope[model_type](model_name)
            if model_name
            else model2.IModel.FindInScope[model_type]()
        )

        # Find the simulation(s) within the current model
        sims = self.find_simulations(simulations)

        # Prevent replacing "Simulations" class, likely a user error
        if model_type == Models.Core.Simulations:
            raise ValueError(f"{model_type} is not allowed. Did you mean Models.Core.Simulation?")

        # Loop through each simulation and perform the replacement
        for sim in sims:
            if model_type == Models.Core.Simulation:
                # If replacing entire simulations
                target_model_name = target_model_name or sim.Name

                if sim.Name == target_model_name:
                    # Find parent of the simulation (likely Simulations)
                    parent = sim.get_Parent()
                    parent = sim.FindInScope[parent.__class__]()

                    # Replace: delete existing and add new
                    ModelTools.DELETE(sim)
                    ModelTools.ADD(get_target_model, parent)
                    self.save()

            else:
                # Otherwise, replace components inside each simulation (e.g., Soil, Clock)
                target = sim.FindInScope[model_type]()

                # Find parent container (usually the simulation itself)
                parent = target.get_Parent()
                parent = target.FindInScope[parent.__class__]()

                # Replace: delete existing and add new
                ModelTools.DELETE(target)
                ModelTools.ADD(get_target_model, parent)
                self.save()

        return self

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

        if isinstance(management, dict):  # To provide support for multiple scripts
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
        self.save()
        open_file_in_window(self.path)

    def _kvtodict(self, kv):
        return {kv[i].Key: kv[i].Value for i in range(kv.Count)}

    def compile_scripts(self):
        for sim in self.simulations:
            managers = sim.FindAllDescendants[Models.Manager]()
            for manager in list(managers):
                print(manager.SuccessfullyCompiledLast)


    def extract_user_input(self, manager_name: str):
        """
        Get user_input of a given model manager script.

        Args:
            manager_name (str): name of the Models.Manager script
        returns:  a dictionary of user input with the key as the script parameters and values as the inputs

        Example:
        ____________________

        >>> from apsimNGpy.core.base_data import load_default_simulations
        >>> model = load_default_simulations(crop = 'maize')
        >>> ui = model.extract_user_input(manager_name='Fertilise at sowing')
        >>> print(ui)

        {'Crop': 'Maize', 'FertiliserType': 'NO3N', 'Amount': '160.0'}

        """
        old_method(old_method='extract_user_input', new_method='inspect_model_parameters')
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

        :param: start_date: (str) optional
            Start date as string, by default `None`
        :param end_date: str (str) optional
            End date as string, by default `None`
        :param simulations (str), optional
            List of simulation names to update, if `None` update all simulations
        Note
        ________
        one of the start_date or end_date parameters should at least not be None

        raises assertion error if all dates are None

        @return None
        Example:
        ---------
            >>> from apsimNGpy.core.base_data import load_default_simulations
            >>> model = load_default_simulations(crop='maize')
            >>> model.change_simulation_dates(start_date='2021-01-01', end_date='2021-01-12')
            >>> changed_dates = model.extract_dates #check if it was successful
            >>> print(changed_dates)
               {'Simulation': {'start': datetime.date(2021, 1, 1),
                'end': datetime.date(2021, 1, 12)}}
            @note
            It is possible to target a specific simulation by specifying simulation name for this case the name is Simulations, so, it could appear as follows
             model.change_simulation_dates(start_date='2021-01-01', end_date='2021-01-12', simulation = 'Simulation')

        """
        old_method(old_method='change_simulation_dates', new_method='edit_model')
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


        """Get simulation dates in the model. deprecated
        @deprecated
        Parameters
        ----------
        simulations, optional
            List of simulation names to get, if `None` get all simulations
        Returns
        -------
            Dictionary of simulation names with dates
        # Example

            >>> from apsimNGpy.core.base_data import load_default_simulations
            >>> model = load_default_simulations(crop='maize')
            >>> changed_dates = model.extract_dates
            >>> print(changed_dates)

               {'Simulation': {'start': datetime.date(2021, 1, 1),
                'end': datetime.date(2021, 1, 12)}}
            @note
            It is possible to target a specific simulation by specifying simulation name for this case the name is Simulations,
             so, it could appear as follows
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
        """Get simulation dates. deprecated

        Parameters
        ----------
        @param simulations: (str) optional
            List of simulation names to use if `None` get all simulations
        @Returns
        -------
            Dictionary of simulation names with dates

        """
        old_method(old_method='extract_start_end_years', new_method='edit_model')
        dates = {}
        for sim in self.find_simulations(simulations):
            clock = sim.FindChild[Models.Clock]()
            start = clock.Start
            end = clock.End
        return start.Year, end.Year



    def change_met(self):
        self.replace_met_file(self.met)
        return self

    def replace_met_file(self, *, weather_file: Union[Path, str], simulations=None, **kwargs):
        try:
            """
            Searches the weather child and replaces it with a new one

            Parameters
            ----------
            @param weather_file: Union[Path, str], required):
                Weather file name, path should be relative to simulation or absolute.
                
            @param simulations (str, optional)
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
        :simulation, optional
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
        """
        Extracts soil physical parameters in the simulation

        Args:
            parameter (_string_): string e.g. DUL, SAT
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


    def inspect_model(self, model_type: Union[str, Models], fullpath=True, **kwargs):
        """
        Inspect the model types and returns the model paths or names. usefull if you want to identify the path to the
        model for editing the model.
        :param model_type: (Models) e.g. Models.Clock will return all fullpath or names
        of models in the type Clock -Models.Manager returns information about the manager scripts in simulations. strings are allowed
        to, in the case you may not need to import the global namespace, Models. e.g 'Models.Clock' will still work well.

        -Models.Core.Simulation returns information about the simulation -Models.Climate.Weather returns a list of
        paths or names pertaining to weather models -Models.Core.IPlant  returns a list of paths or names pertaining
        to all crops models available in the simulation :param  fullpath: (bool) return the full path of the model
        relative to the parent simulations node. please note the difference between simulations and simulation.
        :return: list[str]: list of all full paths or names of the model relative to the parent simulations node \n
        Example:

        >>> from apsimNGpy.core import base_data
        >>> from apsimNGpy.core.core import Models

        # load default maize module

        >>> model = base_data.load_default_simulations(crop ='maize')
        >>> model.inspect_model(Models.Manager, fullpath=True)
         [.Simulations.Simulation.Field.Sow using a variable rule', '.Simulations.Simulation.Field.Fertilise at
        sowing', '.Simulations.Simulation.Field.Harvest']

         >>> model.inspect_model(Models.Clock) # gets the path to the Clock models
         ['.Simulations.Simulation.Clock']

         >>> model.inspect_model(Models.Core.IPlant) # gets the path to the crop model
         ['.Simulations.Simulation.Field.Maize']

         >>> model.inspect_model(Models.Core.IPlant, fullpath=False) # gets you the name of the crop Models
         ['Maize']

         >>> model.inspect_model(Models.Fertiliser, fullpath=True)
         ['.Simulations.Simulation.Field.Fertiliser']

         >>> model.inspect_model('Models.Fertiliser', fullpath=False) # strings are allowed to

         The models from Models namespace are abstracted to use strings. all you need is to specify the name or the full path to the model enclosed in a stirng as follows

         >>> model.inspect_model('Clock') # get the path to the clock model
         ['.Simulations.Simulation.Clock']

         >>> model.inspect_model('IPlant')
         ['.Simulations.Simulation.Field.Maize']

         >>> model.inspect_model('Weather') # inspects the weather module
         ['.Simulations.Simulation.Weather']

         >>> model.inspect_model('Cultivar', fullpath=False) # list all available cultivar names
         ['Hycorn_53',  'Pioneer_33M54', 'Pioneer_38H20',  'Pioneer_34K77',  'Pioneer_39V43',  'Atrium', 'Laila', 'GH_5019WX']

        """

        model_type = _eval_model(model_type)
        if model_type == Models.Core.Simulations:
            obj = [self.Simulations]
        else:
            obj = self.Simulations.FindAllDescendants[model_type]()

        if obj:
            fupath  = [i.FullPath for i in obj]
            names = [i.split(".")[-1] for i in fupath]
            if fullpath:
                return fupath
            else:
                return names



    @property
    def configs(self):
        """records activities or modifications to the model including changes to the file

        """
        return {
            # check is model has been ran yet
            'model_has_been_ran': self.ran_ok,
            'experiment': self.experiment,
            'experiment_created': self.experiment_created,
            'reports': self.report_names or self.inspect_model("Report"),
            'simulations': self.Simulations.Name,
            'start_changed': True if self.Start !='unknown' else False,
            'end_changed': True if self.End !='unknown' else False
        }

    def replace_soils_values_by_path(self, node_path: str, indices: list = None, **kwargs):
        """
        set the new values of the specified soil object by path

        unfortunately, it handles one soil child at a time e.g., Physical at a go
        Args:

        node_path (str, required): complete path to the soil child of the Simulations e.g.,Simulations.Simulation.Field.Soil.Organic.
         Use`copy path to node fucntion in the GUI to get the real path of the soil node.

        indices (list, optional): defaults to none but could be the position of the replacement values for arrays

        kwargs (key word arguments): This carries the parameter and the values e.g., BD = 1.23 or BD = [1.23, 1.75]
         if the child is Physical, or Carbon if the child is Organic

         raises raise value error if none of the key word arguments, representing the paramters are specified
         returns:
            - apsimNGpy.core.APSIMNG object and if the path specified does not translate to the child object in
         the simulation

         Example:
              >>> from apsimNGpy.core.base_data import load_default_simulations

              >>> model = load_default_simulations(crop ='Maize', simulations_object=False)# initiate model

              >>> model = CoreModel(model) # replace with your intended file path
              >>> model.replace_soils_values_by_path(node_path='.Simulations.Simulation.Field.Soil.Organic', indices=[0], Carbon =1.3)

              >>> sv= model.get_soil_values_by_path('.Simulations.Simulation.Field.Soil.Organic', 'Carbon')

            output # {'Carbon': [1.3, 0.96, 0.6, 0.3, 0.18, 0.12, 0.12]}


        """
        if not kwargs:
            raise ValueError('No parameters are specified')
        _soil_child = self.Simulations.FindByPath(node_path)
        if _soil_child is None:
            raise ValueError(f"No such child: {node_path} exist in the simulation file {self.path}")
        if not kwargs:
            logger.error('no parameters and values are supplied')
            return self
        for k, v in kwargs.items():
            parameter = k
            if isinstance(v, (int, float)):
                v = [v]
            if indices is None:
                indices = [v.index(i) for i in v]

            param_values_new = list(getattr(_soil_child.Value, parameter))
            _param_new = replace_variable_by_index(param_values_new, v, indices)
            setattr(_soil_child.Value, parameter, _param_new)

    def get_soil_values_by_path(self, node_path, *args):

        var_out = {}
        _soil_child_obj = self.Simulations.FindByPath(node_path)

        if args:
            for arg in args:

                gv = getattr(_soil_child_obj.Value, arg, None)
                if gv:
                    gv = list(gv)
                else:
                    logger.error(f"{arg} is not a valid parameter for child {node_path}")
                var_out[arg] = gv
        return var_out


    def replace_soil_properties_by_path(self, path: str,
                                        param_values: list,
                                        str_fmt=".",
                                        **kwargs):
        # TODO I know there is a better way to implement this, to be duplicated
        warnings.warn(f"replace_soil_properties_by_path is deprecated use self.replace_soils_values_by_path instead",
                      DeprecationWarning)

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
            - The `soil_child` child might be replaced in a non-systematic manner, which is why indices
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

        returns:
        ----------
            Returns the instance of `self` after processing the path and applying the parameter value replacements.

        Example:
        ---------------------

            >>> from apsimNGpy.core.base_data import load_default_simulations
            >>> model = load_default_simulations(crop = 'Maize')
            >>> model.replace_soil_properties_by_path(path = 'None.Soil.Organic.None.None.Carbon', param_values= [1.23])
            
            # if we want to replace carbon at the bottom of the soil profile, we use a negative index  -1
            
           >>>  model.replace_soil_properties_by_path(path = 'None.Soil.Organic.None.[-1].Carbon', param_values= [1.23])   
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

        fpt = {k: (p := CoreModel._try_literal_eval(v)) if (k in expected_nones) else (p := v)
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

        :param param_values: list or tuple: values of the specified soil property name to replace

        :param soil_child: str: sub child of the soil component e.g., organic, physical etc.

        :param simulations: list: list of simulations to where the child is found if
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




    def find_simulations(self, simulations: Union[list, tuple, str] = None):
        simulations_names = simulations
        """Find simulations by name

        Parameters
        ----------
        :param simulations, str, optional
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
           logger.info(f"{simulations_names}: Not found!")
           sim_names = ",".join([i.Name for i in self.simulations])
           raise NameError(f"{simulations_names}: Not found! \n Available simulation(s) names are/is: '{sim_names}'?")
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

    def clean_up(self, db=True, verbose=False):
        """
        Clears the file cloned the datastore and associated csv files are not deleted if db is set to False defaults to True.

        Returns:
           >>None: This method does not return a value.
           >> Please proceed with caution, we assume that if you want to clear the model objects, then you don't need them,
           but by making copy compulsory, then, we are clearing the edited files

        """
        try:
            if hasattr(self, '_DataStore'):
                self._DataStore.Close()
                self._DataStore.Dispose()
            try:
              del self._DataStore
              del self.Datastore
            except AttributeError:
                ...

            Path(self.path).unlink(missing_ok=True)
            Path(self.path.replace('apsimx', "bak")).unlink(missing_ok=True)
            if db:
                Path(self.datastore).unlink(missing_ok=True)
                Path(self.path.replace('apsimx', "db-wal")).unlink(missing_ok=True)
                Path(self.path.replace('apsimx', "db-shm")).unlink(missing_ok=True)
                if verbose:
                  logger.info('database cleaned successfully')
        except (FileNotFoundError, PermissionError) as e:
            from apsimNGpy.core_utils.database_utils import clear_all_tables
            # if deleting has failed
            clear_all_tables(self.datastore) if os.path.exists(self.datastore) else None

            if verbose:
               logger.info(e)
            pass
        finally:
            ModelTools.COLLECT()

        return self

    def create_experiment(self, permutation: bool = True, base_name: str = None, **kwargs):
        """
        Initialize an Experiment instance, adding the necessary models and factors.

        Args:

            **kwargs: Additional parameters for CoreModel.

            :param permutation (bool). If True, the experiment uses a permutation node to run unique combinations of the specified
            factors for the simulation. For example, if planting population and nitrogen fertilizers are provided,
            each combination of planting population level and fertilizer amount is run as an individual treatment.

           :param  base_name (str, optional): The name of the base simulation to be moved into the experiment setup. if not
            provided, it is expected to be Simulation as the default

        """
        if self.experiment_created:
            logger.info('Experiment was already created. If you want to amend experiment, '
                        'use add_model(), remove_model()')
            return self
        self.factor_names = []
        self.permutation = permutation
        # Add core experiment structure

        self.add_model(model_type=Models.Factorial.Experiment, adoptive_parent=Models.Core.Simulations, **kwargs)

        self.add_model(model_type=Models.Factorial.Factors, adoptive_parent=Models.Factorial.Experiment, **kwargs)

        if permutation:
            self.add_model(model_type=Models.Factorial.Permutation, adoptive_parent=Models.Factorial.Factors, **kwargs)

        # Move base simulation under the factorial experiment
        self.move_model(Models.Core.Simulation, Models.Factorial.Experiment, base_name, None)

        self.save()
        # update the experiment status
        self.experiment = True
        self.experiment_created = True

    def add_factor(self, specification: str, factor_name:str=None, **kwargs):
        """
        Adds a factor to the created experiment. Thus, this method only works on factorial experiments

        It could raise a value error if the experiment is not yet created.

        Under some circumstances, experiment will be created automatically as a permutation experiment.

        Parameters:
        ----------

        :specification: *(str), required*

        A specification can be:
                - 1. multiple values or categories e.g., "[Sow using a variable rule].Script.Population =4, 66, 9, 10"
                - 2. Range of values e.g, "[Fertilise at sowing].Script.Amount = 0 to 200 step 20",
        :factor_name: *(str), required*

        - expected to be the user-desired name of the factor being specified e.g., population

        Example:
            >>> from apsimNGpy.core import base_data
            >>> apsim = base_data.load_default_simulations(crop='Maize')
            >>> apsim.create_experiment(permutation=False)
            >>> apsim.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20", factor_name='Nitrogen')
            >>> apsim.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2", factor_name='Population')
            >>> apsim.run() # doctest: +SKIP
        """
        # TODO fix factors either composite or not composite
        if factor_name is None:
            get_name = specification.split("=")[0].strip()
            # split again by
            factor_name = get_name.split(".")[-1]

        if not self.experiment:
            msg = 'experiment was not defined, it has been created with default settings'
            self.create_experiment(permutation=True)  # create experiment with default parameters of permutation
            self.experiment=True

        if 'Script' in specification:
            matches = re.findall(r"\[(.*?)\]", specification)
            if matches:
                _managers = set(self.inspect_model('Models.Manager', fullpath=False))
                ITC = set(matches).intersection(_managers)
                if not ITC:
                    raise ValueError('specification has no linked script in the model')

        #Add individual factors
        if self.permutation:
            parent_factor = Models.Factorial.Permutation
        else:
            parent_factor = Models.Factorial.Factors

        # find if a suggested factor exists
        factor_in = self.Simulations.FindInScope[Models.Factorial.Factor](factor_name)
        if factor_in:

            # if already exists, update the specifications
            factor_in.set_Specification(specification)

        else:
            # if new factor, add it to the Simulations
            self.add_model(model_type=Models.Factorial.Factor, adoptive_parent=parent_factor, rename=factor_name)

            _added = self.Simulations.FindInScope[Models.Factorial.Factor](factor_name)
            # update with specification
            _added.set_Specification(specification)
        self.save()
        self.factor_names.append(factor_name)
        self.factors[factor_name] = specification
        return self # allows method chaining

    def set_continuous_factor(self, factor_path, lower_bound, upper_bound, interval, factor_name=None):
        """
        Wraps around `add_factor` to add a continuous factor, just for clarity

        Args:
            :param factor_path: (str): The path of the factor definition relative to its child node,
                e.g., `"[Fertilise at sowing].Script.Amount"`.
            :param factor_name: (str): The name of the factor.
            :param lower_bound: (int or float): The lower bound of the factor.
            :param upper_bound: (int or float): The upper bound of the factor.
            :param interval: (int or float): The distance between the factor levels.

        Returns:
            ApsimModel or CoreModel: An instance of `apsimNGpy.core.core.apsim.ApsimModel` or `CoreModel`.
        Example:
            >>> from apsimNGpy.core import base_data
            >>> apsim = base_data.load_default_simulations(crop='Maize')
            >>> apsim.create_experiment(permutation=False)
            >>> apsim.set_continuous_factor(factor_path = "[Fertilise at sowing].Script.Amount", lower_bound=100, upper_bound=300, interval=10)

        """
        format_factor = f"{factor_path} = {lower_bound} to {upper_bound} step {interval}"
        self.add_factor(specification=format_factor, factor_name=factor_name)

    def set_categorical_factor(self, factor_path: str, categories: Union[list, tuple], factor_name: str = None):
        """
        wraps around add_factor() to add a continuous factor, just for clarity
         parameters
         __________________________
        :param factor_path: (str, required): path of the factor definition relative to its child node "[Fertilise at sowing].Script.Amount"
        :param factor_name: (str) name of the factor.
        :param categories: (tuple, list, required): multiple values of a factor
        :returns:
          ApsimModel or CoreModel: An instance of `apsimNGpy.core.core.apsim.ApsimModel` or `CoreModel`.
        Example:
            >>> from apsimNGpy.core import base_data
            >>> apsim = base_data.load_default_simulations(crop='Maize')
            >>> apsim.create_experiment(permutation=False)
            >>> apsim.set_continuous_factor(factor_path = "[Fertilise at sowing].Script.Amount", lower_bound=100, upper_bound=300, interval=10)

        """
        format_factor = f"{factor_path} = {','.join(map(str, categories))}"
        self.add_factor(specification=format_factor, factor_name=factor_name)

    def add_crop_replacements(self, _crop: str):
        """
        Adds a replacement folder as a child of the simulations.
        Useful when you intend to edit cultivar **parameters**.

        **Args:**
            - **_crop** (*str*): Name of the crop to be added to the replacement folder.

        **Returns:**
            - *ApsimModel*: An instance of `apsimNGpy.core.core.apsim.ApsimModel` or `CoreModel`.

        **Raises:**
            - *ValueError*: If the specified crop is not found.
        """

        _FOLDER = Models.Core.Folder()
        "everything is edited in place"
        CROP = _crop
        _FOLDER.Name = "Replacements"
        PARENT = self.Simulations
        # parent replacemnt should be added once
        target_parent  = PARENT.FindInScope[Models.Core.Folder]('Replacements')
        if not target_parent:
            ModelTools.ADD(_FOLDER, PARENT)
        # assumes that the crop already exists in the simulation
        _crop = PARENT.FindInScope[Models.PMF.Plant](CROP)
        if _crop is not None:
            ModelTools.ADD(_crop, _FOLDER)
        else:
            logger.error(f"No plants of crop{CROP} found")
        return self
    def get_model_paths(self, cultivar=False) -> list[str]:
        """
        select out a few model types to use for building the APSIM file inspections
        """
        def filter_out():
            import Models
            data = []
            model_types = ['Models.Core.Simulation', 'Models.Soils.Soil', 'Models.PMF.Plant', 'Models.Manager',
                  'Models.Climate.Weather', 'Models.Report', 'Models.Clock', 'Models.Core.Folder',
                  'Models.Soils.Solute',
                  'Models.Soils.Swim3', 'Models.Soils.SoilCrop', 'Models.Soils.Water', 'Models.Summary',
                  'Models.Core.Zone', 'Models.Management.RotationManager',
                  'Models.Soils.CERESSoilTemperature', 'Models.Series', 'Models.Factorial.Experiment',
                  'Models.Factorial.Permutation', 'Models.Irrigation',
                  'Models.Factorial.Factors',
                  'Models.Sobol', 'Models.Operations', 'Models.Morris', 'Models.Fertiliser', 'Models.Core.Events',
                  'Models.Core.VariableComposite',
                  'Models.Soils.Physical', 'Models.Soils.Chemical', 'Models.Soils.Organic']
            if cultivar:
                model_types.append(('Models.PMF.Cultivar'))
            for i in model_types:

                ans = self.inspect_model(eval(i))
                if not 'Replacements' in ans and 'Folder' in i:
                    continue
                data.extend(ans)
            del Models, model_types
            return data
        return filter_out()
    def inspect_file(self, cultivar=False,**kwargs):
        """
        Inspect the file by calling inspect_model() through get_model_paths.
        This method is important in inspecting the whole file and also getting the scripts paths
        """
        if kwargs.get('indent', None) or kwargs.get('display_full_path', None):
            logger.info(f"Inspecting file with key word indent or display_full_path is \ndeprecated, the inspect_file now print "
                        f"the inspection as a tree with names and corresponding model \nfull paths combined")

        def build_tree(paths):
            from collections import defaultdict
            tree = lambda: defaultdict(tree)
            root = tree()
            for path in paths:
                parts = path.strip('.').split('.')
                current = root
                for part in parts:
                    current = current[part]
            return root


        def print_tree_branches(node, prefix="", is_last=True, full_path="", display_full_path=False):
            keys = sorted(node.keys())
            for index, key in enumerate(keys):
                is_last_key = index == (len(keys) - 1)
                branch = "└── " if is_last_key else "├── "
                child_prefix = "    " if is_last_key else "│   "
                current_path = f"{full_path}.{key}" if full_path else key


                print(f"{prefix}{branch}\033[95m{key}\033[0m: .{current_path}")

                # else:
                #     print(f"{prefix}{branch}{key}")

                print_tree_branches(
                    node[key],
                    prefix + child_prefix,
                    is_last=is_last_key,
                    full_path=current_path,
                    display_full_path=display_full_path
                )

        tree = build_tree(self.get_model_paths(cultivar=cultivar))

        print_tree_branches(tree)

    #@timer
    def add_db_table(self, variable_spec: list = None, set_event_names: list = None, rename: str = 'my_table', simulation_name:Union[str, list, tuple]=None):
        """
        Adds a new data base table, which APSIM calls Report (Models.Report) to the Simulation under a Simulation Zone.

        This is different from `add_report_variable` in that it creates a new, named report
        table that collects data based on a given list of variables and events.

        :Args:
            variable_spec (list or str): A list of APSIM variable paths to include in the report table.
                                         If a string is passed, it will be converted to a list.
            set_event_names (list or str, optional): A list of APSIM events that trigger the recording of variables.
                                                     Defaults to ['[Clock].EndOfYear'] if not provided. other examples include '[Clock].StartOfYear', '[Clock].EndOfsimulation',
                                                     '[crop_name].Harvesting' etc.,,
            rename (str): The name of the report table to be added. Defaults to 'my_table'.

            simulation_name (str,tuple, or list, Optional): if specified, the name of the simulation will be searched and will become the parent candidate for the report table.
                            If it is none, all Simulations in the file will be updated with the new db_table

        :Raises:
            ValueError: If no variable_spec is provided.
            RuntimeError: If no Zone is found in the current simulation scope.
        : Example:
               >>> from apsimNGpy import core
               >>> model = core.base_data.load_default_simulations(crop = 'Maize')
               >>> model.add_db_table(variable_spec=['[Clock].Today', '[Soil].Nutrient.TotalC[1]/1000 as SOC1'], rename='report2')
               >>> model.add_db_table(variable_spec=['[Clock].Today', '[Soil].Nutrient.TotalC[1]/1000 as SOC1', '[Maize].Grain.Total.Wt*10 as Yield'], rename='report2', set_event_names=['[Maize].Harvesting','[Clock].EndOfYear' ])
        """
        import Models
        report = Models.Report()
        report.Name = rename
        if rename in self.inspect_model('Models.Report', fullpath=False):
            logging.info(f"{rename} is a database table already ")

        # Default events if not specified
        if not set_event_names:
            set_event_names = ['[Clock].EndOfYear']

        # Ensure variable_spec is a list
        if variable_spec is None:
            raise ValueError("Please specify at least one variable to include in the report table.")
        if isinstance(variable_spec, str):
            variable_spec = [variable_spec]

        # Remove duplicates
        variable_spec = list(set(variable_spec))

        # Ensure event names is a list and remove duplicates
        if isinstance(set_event_names, str):
            set_event_names = [set_event_names]
        set_event_names = list(set(set_event_names))

        # Assign variables and events to the report object
        report.VariableNames = variable_spec

        set_event_names = list(set(set_event_names))
        final_command = "\n".join(set_event_names)
        report.set_EventNames(final_command.strip().splitlines())
        # Try to find a Zone in scope and attach the report to it
        sims = self.find_simulations(simulation_name)
        for sim in sims:
            zone = sim.FindInScope[Models.Core.Zone]()
            if zone is None:
                raise RuntimeError("No Zone found in the Simulation scope to attach the report table.")
            check_repo = sim.FindInScope[Models.Report](rename)
            if check_repo:# because this is intented to create an entirley new db table
               ModelTools.DELETE(check_repo)
            zone.Children.Add(report)
            self.save()

        # save the results to recompile




if __name__ == '__main__':

    from pathlib import Path
    from time import perf_counter

    # Model = FileFormat.ReadFromFile[Models.Core.Simulations](model, None, False)
    os.chdir(Path.home())
    from apsimNGpy.core.base_data import load_default_simulations



    # model = load_default_simulations('maize')
    model = CoreModel(model = 'Maize')


    # for rn in ['Maize, Soybean, Wheat', 'Maize', 'Soybean, Wheat']:
    a = perf_counter()
    # model.RevertCheckpoint()
    model.update_mgt(management=({"Name": 'Sow using a variable rule', 'Population': 10},))
    # model.replace_soil_properties_by_path(path='None.Soil.Organic.None.None.Carbon', param_values=[N])
    # model.replace_any_soil_physical(parameter='BD', param_values=[1.23],)
    # model.save_edited_file(reload=True)
    model.run('Report', verbose=True)
    df = model.results
    ui = model.extract_user_input('Sow using a variable rule')
    print(ui)
    print()
    print(df['Maize.Total.Wt'].mean())
    print(df.describe())
    # logger.info(model.results.mean(numeric_only=True))
    b = perf_counter()
    logger.info(f"{b - a}, 'seconds")
    model.add_db_table(variable_spec=['[Clock].Today', '[Soil].Nutrient.TotalC[1]/1000 as SOC1'], rename='reporterte')
    a = perf_counter()
    #model.clean_up(db=True)
    import doctest
    # clone test
    # for i in range(100):
    #     model.clone_model('Models.Core.Simulation', 'Simulation',
    #                       'Models.Core.Simulations', rename=f"sim_{i}")
    # # doctest.testmod()
