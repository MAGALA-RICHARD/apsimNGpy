"""
Interface to APSIM simulation models using Python.NET
author: Richard Magala
email: magalarich20@gmail.com

"""
import inspect
import random, pathlib
import string
from typing import Union
import os, shutil
import numpy as np
import pandas as pd
from os.path import join as opj
import json
import datetime
import apsimNGpy.manager.weathermanager as weather
from functools import cache
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

import Models
from Models.PMF import Cultivar
from apsimNGpy.core.runner import run_model_externally, collect_csv_by_model_path
from apsimNGpy.core.model_loader import (load_apsim_model, save_model_to_file, recompile)
import ast
from typing import Iterable
from collections.abc import Iterable
from typing import Any
from System.Data import DataView

MultiThreaded = Models.Core.Run.Runner.RunTypeEnum.MultiThreaded
SingleThreaded = Models.Core.Run.Runner.RunTypeEnum.SingleThreaded
ModelRUNNER = Models.Core.Run.Runner

ADD = Models.Core.ApsimFile.Structure.Add
DELETE = Models.Core.ApsimFile.Structure.Delete
MOVE = Models.Core.ApsimFile.Structure.Move
RENAME = Models.Core.ApsimFile.Structure.Rename
REPLACE = Models.Core.ApsimFile.Structure.Replace


def dataview_to_dataframe(_model, reports):
    """
    Convert .NET System.Data.DataView to Pandas DataFrame.
    report (str, list, tuple) of the report to be displayed. these should be in the simulations
    :param apsimng model: CoreModel object or instance
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
    """
    __slots__ = ['model', 'out_path', 'experiment', 'copy', 'base_name', 'others', 'report_names',
                 'factor_names', 'permutation', 'experiment_created', 'set_wd', '_str_model',
                 '_model', 'model_info', 'datastore', 'Simulations', 'Datastore', '_DataStore', 'path',
                 '_met_file', 'ran_ok', 'factors'
                 ]

    def __init__(self, model: os.PathLike = None, out_path: os.PathLike = None, out: os.PathLike = None, set_wd=None,
                 experiment=False, **kwargs):

        self.experiment_created = None
        self.experiment = experiment
        self.permutation = None
        self.factor_names = []
        self.report_names = None
        self.others = kwargs.copy()
        self.set_wd = set_wd
        self.factors = {}
        if kwargs.get('copy'):
            warnings.warn(
                'copy argument is deprecated, it is now mandatory to copy the model in order to conserve the original '
                'model.', UserWarning)

        out_path = out_path if isinstance(out_path, str) or isinstance(out_path, Path) else None
        self.copy = kwargs.get('copy')  # Mandatory to conserve the original file
        # all these can be changed after initialization

        self._str_model = None
        self._model = model
        self.out_path = out_path or out
        # model_info is named tuple safe for parallel simulations as named tuples are immutable
        self.model_info = load_apsim_model(self._model, out_path=self.out_path, met_file=kwargs.get('met_file'),
                                           wd=set_wd)
        self.Simulations = self.model_info.IModel

        self.datastore = self.model_info.datastore
        self.Datastore = self.model_info.DataStore
        self._DataStore = self.model_info.DataStore
        self.path = self.model_info.path
        self._met_file = kwargs.get('met_file')
        self.ran_ok = False
        permutation, base = kwargs.get('permutation', True), kwargs.get('base_name', None)
        if experiment:
            # we create an experiment here immediately if the user wants to dive in right away
            self.create_experiment(permutation=permutation, base_name=base)

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
        reports = self.report_names or "Report"  # 'Report' # is the apsim default name
        if self.ran_ok and reports:
            data_tables = collect_csv_by_model_path(self.path)

            if isinstance(reports, str):
                reports = [reports]
            datas = [pd.read_csv(data_tables[i]) for i in reports if i in data_tables]
            return pd.concat(datas)
        else:
            logging.error("attempting to get results before running the model or providing the report name")

    def run(self, report_name: Union[tuple, list, str] = None,
            simulations: Union[tuple, list] = None,
            clean_up: bool = False,
            verbose=False,
            **kwargs) -> 'CoreModel':
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
            instance of the class CoreModel
        """
        try:
            # we could cut the chase and run apsim faster, but unfortunately some versions are not working properly,
            # so we run the model externally the previous function allowed to run specific simulations in the file,
            # it has been renamed to run_in_python.
            self._DataStore.Dispose()

            # before running
            self.save()  # this compiles any modification to the model, sending it to the disk
            res = run_model_externally(self.model_info.path, verbose=verbose, to_csv=kwargs.get('to_csv', True))
            if clean_up:
                self.clean_up()
            if res.returncode == 0:
                # update run satus
                self.ran_ok = True
                # update report names
                self.report_names = report_name
                # self.results = _read_data(report_name)

        finally:
            # close the datastore
            self._DataStore.Close()
        return self

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

    @timer
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
        ```python
        self.clone_model(Models.Clock, "clock1", Models.Simulation, rename="new_clock",adoptive_parent_type= Models.Core.Simulations, adoptive_parent_name="Simulation")
        ```
        This will create a cloned version of `"clock1"` and place it under `"Simulation"` with the new name `"new_clock"`.

        """
        cloner = Models.Core.Apsim.Clone  # Reference to the APSIM cloning function

        # Ensure the model type is valid before proceeding
        if isinstance(model_type, type(Models.Clock)):
            # Locate the model to be cloned within the simulation scope
            clone_parent = (self.Simulations.FindInScope[model_type](model_name) if model_name
                            else self.Simulations.FindInScope[model_type]())

            # Create a clone of the model
            clone = cloner(clone_parent)

            # Assign a new name to the cloned model
            new_name = rename if rename else f"{clone.Name}_clone"
            clone.Name = new_name
            check_exists = self.Simulations.FindInScope[model_type](new_name)
            if check_exists:
                raise ValueError(
                    f"adding the same model with the same name and type as the previous one is not allowed")

            # Find the adoptive parent where the cloned model should be placed
            parent = (self.Simulations.FindInScope[adoptive_parent_type](adoptive_parent_name) if adoptive_parent_name
                      else self.Simulations.FindInScope[adoptive_parent_type]())

            # Add the cloned model to the new parent
            parent.Children.Add(clone)

            # Save the changes to the simulation structure
            self.save()
        else:
            raise TypeError(f'{model_type} is not supported by clone_model at the moment')

    def find_model(self, model_name: str, model_namespace=None):
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
             >>> from apsimNGpy.core.core import Models  # doctest: +SKIP
             >>> model =core.base_data.load_default_simulations(crop = "Maize")  # doctest: +SKIP
             >>> model.find_model("Weather")  # doctest: +SKIP
             'Models.Climate.Weather'
             >>> model.find_model("Clock")  # doctest: +SKIP
              'Models.Clock'

        """
        if model_namespace is None:
            model_namespace = Models  # Default to Models namespace

        if not hasattr(model_namespace, "__dict__"):
            return None  # Base case: Not a valid namespace

        for attr, value in model_namespace.__dict__.items():
            if attr == model_name and isinstance(value, type(getattr(Models, "Clock", object))):
                return value

            if hasattr(value, "__dict__"):  # Recursively search nested namespaces
                result = self.find_model(model_name, value)
                if result:
                    return result

        return None  # Model not found

    def add_model(self, model_type, adoptive_parent, rename=None,
                  adoptive_parent_name=None, verbose=False, **kwargs):

        """
        Adds a model to the Models Simulations namespace.

        Some models are restricted to specific parent models, meaning they can only be added to compatible models.
        For example, a Clock model cannot be added to a Soil model.

        Args:
            model_type (str or Models object): The type of model to add, e.g., `Models.Clock` or just `"Clock"`.
            rename (str): The new name for the model.

            adoptive_parent (Models object): The target parent where the model will be added or moved

            adoptive_parent_name (Models object, optional): Specifies the parent name for precise location.

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
         @param adoptive_parent:

        """

        replacer = {'Clock': 'change_simulation_dates', 'Weather': 'replace_met_file'}
        sims = self.Simulations
        # find where to add the model
        if  isinstance(adoptive_parent, str) and 'Models.' in adoptive_parent :
            adoptive_parent = eval(adoptive_parent)
        if  isinstance(model_type, str) and 'Models.' in model_type:
            model_type = eval(model_type)
        if adoptive_parent == Models.Core.Simulations:
            parent = self.Simulations
        else:
            if isinstance(adoptive_parent, type(Models.Clock)):

                if not adoptive_parent_name:
                    adoptive_parent_name = adoptive_parent().Name
            parent = sims.FindInScope[adoptive_parent](adoptive_parent_name)

        # parent = _model.Simulations.FindChild(where)

        cla = model_type.__class__
        if inspect.isclass(model_type):
            which = model_type
        elif isinstance(model_type, str):
            which = self.find_model(model_type)
        elif isinstance(cla, type(Models.Clock)):
            which = cla
        else:
            raise ValueError(f'Invalid model type description expected str or {type(Models.Clock)}')
        if which and parent:
            loc = which()
            loc_name = loc.Name if hasattr(loc, 'Name') else None
            if rename and hasattr(loc, 'Name'):
                loc.Name = rename
            if hasattr(loc, 'Name'):
                target_child = parent.FindChild[self.find_model(loc_name)](loc.Name)
                if target_child:
                    # not raising the error still studying the behaviors of adding a child that already exists
                    raise ValueError(
                        f'Child node `{model_type}` already exist at the target parent name`{parent.Name}`')

            ADD(loc, parent)
            # parent.Children.Add(loc)
            if verbose:
                logger.info(f"Added {loc.Name} to {parent.Name}")
            # we need to put the changes into effect
            self.save()
            # if verbose:
            #     logger.info(f'successfully saved to {self.path}')

        else:
            logger.debug(f"Adding {model_type} to {parent.Name} failed, perhaps models was not found")

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
            get_report.set_EventNames = list(set(set_event_names))
        self.save()

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

        if not model_name:
            model_name = model_type().Name
        DELETE(self.Simulations.FindInScope[model_type](model_name))
        self.save()

    def move_model(self, model_type: Models, new_parent_type: Models, model_name: str = None,
                   new_parent_name: str = None, verbose: bool = False):
        """
        Args:

        - model_type (Models): type of model tied to Models Namespace
        - new_parent_type: new model parent (Models)
        - model_name:name of the model e.g., Clock, or Clock2, whatever name that was given to the model
        -  new_parent_name: what is the new parent names =Field2, this fiedl is optional but important if you have nested simulations
        Returns:

          returns instance of apsimNGpy.core.core.apsim.ApsimModel or apsimNGpy.core.core.apsim.CoreModel

        """
        sims = self.Simulations
        if not model_name:
            model_name = model_type().Name
        child_to_move = sims.FindInScope[model_type](model_name)
        if not new_parent_name:
            new_parent_name = new_parent_type().Name

        new_parent = sims.FindInScope[new_parent_type](new_parent_name)

        MOVE(child_to_move, new_parent)
        if verbose:
            logger.info(f"Moved {child_to_move.Name} to {new_parent.Name}")
        self.save()

    def rename_model(self, model_type: Models, old_model_name: str, new_model_name: str):
        """
        give new name to a model in the simulations
        @param model_type: (Models) Models types e.g., Models.Clock
        @param old_model_name: (str) current model name
        @param new_model_name: (str) new model name
        @return: None
        Example;
               >>> from apsimNGpy import core
               >>> from apsimNGpy.core.core import Models
               >>> apsim = core.base_data.load_default_simulations(crop = 'Maize')
               >>> apsim = apsim.rename_model(Models.Clock, 'Clock', 'clock')

        """
        __model = self.Simulations.FindInScope[model_type](old_model_name)
        __model.Name = new_model_name
        self.save()

    @property  #
    def extract_report_names(self) -> dict:
        """ returns all data frames the available report tables
        @return: dict of  table names in alist in the simulation

        """
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

    @timer
    def clone(self, new_file_name):
        """this clones all simulations and returns a path to the néw clone simulations"""
        assert Path(new_file_name).suffix == '.apsimx', 'wrong file extension'
        __simulations__ = Models.Core.Apsim.Clone(self.Simulations)
        save_model_to_file(__simulations__, out=new_file_name)
        return new_file_name

    def edit_cultivar(self, *, CultivarName: str, commands: str, values: Any, **kwargs):
        """
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
        Args:
       - ManagerName: script manager module in the zone

       Returns:
           returns the current cultivar name in the manager script 'ManagerName'
        """

        try:
            ap = self.extract_user_input(ManagerName)['CultivarName']
            return ap
        except  KeyError:
            parameterName = 'CultivarName'
            logger.info(f"cultivar name: is not found")

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
        # reject space in fmt
        if fmt != '.':
            path = path.replace(fmt, ".")

        manager = self.Simulations.FindByPath(path)
        for i in range(len(manager.Value.Parameters)):
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
        self.save()
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
        """Get simulation dates

        Parameters
        ----------
        @param simulations: (str) optional
            List of simulation names to use if `None` get all simulations
        @Returns
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

    def inspect_model(self, model_type: Union[str, Models], fullpath=True):
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

        """
        import Models
        if isinstance(model_type, str):
            l_model = len('Models.')
            attr_model = model_type[l_model:]
            # for security purpose we have to evaluate the string
            if "_" in model_type or not getattr(Models, attr_model, None):
                raise ValueError(f"Invalid model name: {model_type}")
            model_type = eval(model_type, {'Models': Models})
        if isinstance(model_type, type(Models.Clock)):
            obj = self.Simulations.FindAllDescendants[model_type]()
            if obj:
                if fullpath:
                    return [i.FullPath for i in obj]
                else:
                    return [i.Name for i in obj]

            logging.info(f"{model_type.__name__} does not exists")
        logging.error(f"Invalid model type '{model_type}'")

    def configs(self):
        """records activities that have been done on the model including changes to the file

        """
        return {
            # check is model has been ran yet
            'model_has_been_ran': self.ran_ok,
            'experiment': self.experiment,
            'experiment_created': self.experiment_created,
            'reports': self.report_names
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
        # find the solute child in the simulation
        sims = self._find_simulation(simulation)
        solute = {}
        for sim in sims:
            solute[sim.Name] = sim.FindAllDescendants[Models.Soils.Solute]()

        return solute

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

    def extract_any_soil_organic(self, parameter: str, simulation: tuple = None):
        """extracts any specified soil  parameters in the simulation

        Args:
            :param parameter (string, required): string e.g., Carbon, FBiom.
            open APSIMX file in the GUI and examne the phyicals child for clues on the parameter names
            :param simulation (string, optional): Targeted simulation name.
            Defaults to None.
           :param  param_values (array, required): arrays or list of values for the specified parameter to replace

        """

        soil_organic = self.extract_soil_organic(simulation)
        get_organic = {sim:
                           list(getattr(soil_organic[sim], parameter))
                       for sim in (simulation if simulation is not None else self.simulation_names)
                       }

        return get_organic

    # Find a list of simulations by name
    def extract_crop_soil_water(self, parameter: str, crop: str = "Maize", simulation: Union[list, tuple] = None):
        """ deprecated

        Args:
           :param parameter (str): crop soil water parameter names e.g. LL, XF etc
           :param crop (str, optional): crop name. Defaults to "Maize".
            simulation (_str_, optional): _target simulation name . Defaults to None.

        Returns:
            _type_: list[int, float]

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

    def clean_up(self, db=True):
        """
        Clears the file cloned the datastore and associated csv files are not deleted if db is set to False defaults to True.

        Returns:
           >>None: This method does not return a value.
           >> Please proceed with caution, we assume that if you want to clear the model objects, then you don't need them,
           but by making copy compulsory, then, we are clearing the edited files

        """
        try:
            self._DataStore.Close()
            self._DataStore.Dispose()
            Path(self.path).unlink(missing_ok=True)
            Path(self.path.strip('apsimx') + "bak").unlink(missing_ok=True)
            if db:
                Path(self.datastore).unlink(missing_ok=True)
                Path(self.path.strip('apsimx') + "db-wal").unlink(missing_ok=True)
                Path(self.path.strip('apsimx') + "db-shm").unlink(missing_ok=True)
                logger.info('database cleaned successfully')
        except (FileNotFoundError, PermissionError) as e:

            pass

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

    def add_factor(self, specification: str, factor_name: str, **kwargs):
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
        if factor_name is None:
            get_name = specification.split("=")[0].strip()
            # split again by
            factor_name = get_name.split(".")[-1]

        if not self.experiment:
            msg = 'experiment was not defined, it has been created with default settings'
            self.create_experiment(permutation=True)  # create experiment with default parameters of permutation

        # Add individual factors
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
        ADD(_FOLDER, PARENT)
        # assumes that the crop already exists in the simulation
        _crop = PARENT.FindInScope[Models.PMF.Plant](CROP)
        if _crop is not None:
            ADD(_crop, _FOLDER)
        else:
            logger.error(f"No plants of crop{CROP} found")
    def get_model_paths(self) -> list[str]:
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
            for i in model_types:

                ans = self.inspect_model(eval(i))
                if not 'Replacements' in ans and 'Folder' in i:
                    continue
                data.extend(ans)
            del Models, model_types
            return data
        return filter_out()
    def inspect_file(self, **kwargs):
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

        tree = build_tree(self.get_model_paths())

        print_tree_branches(tree)

    @timer
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
        """
        report = Models.Report()
        report.Name = rename

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
        report.set_EventNames = set_event_names
        # Try to find a Zone in scope and attach the report to it
        sims = self.find_simulations(simulation_name)
        for sim in sims:
            zone = sim.FindInScope[Models.Core.Zone]()
            if zone is None:
                raise RuntimeError("No Zone found in the Simulation scope to attach the report table.")

            zone.Children.Add(report)
        # save the results to recompile
        self.save()


if __name__ == '__main__':

    from pathlib import Path
    from time import perf_counter

    # Model = FileFormat.ReadFromFile[Models.Core.Simulations](model, None, False)
    os.chdir(Path.home())
    from apsimNGpy.core.base_data import load_default_simulations

    al = load_default_simulations(crop='maize', simulations_object=False)
    modelm = al

    # model = load_default_simulations('maize')
    model = CoreModel(al)

    for N in [3, 300]:
        # for rn in ['Maize, Soybean, Wheat', 'Maize', 'Soybean, Wheat']:
        a = perf_counter()
        # model.RevertCheckpoint()
        model.update_mgt(management=({"Name": 'Sow using a variable rule', 'Population': N},))
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

        a = perf_counter()
    model.clean_up(db=True)
    import doctest

    # doctest.testmod()
