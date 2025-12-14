"""
Interface to APSIM simulation models using Python.NET
author: Richard Magala
email: magalarich20@gmail.com

"""
from __future__ import annotations
import gc
import re
import random
import pathlib
import string
from typing import Union
import shutil
import pandas as pd
import json
import datetime
from dataclasses import field
from typing import List, Dict
import warnings
from sqlalchemy.testing.plugin.plugin_base import logging
from apsimNGpy.core.cs_resources import CastHelper
from apsimNGpy.manager.weathermanager import get_weather
from functools import lru_cache
# prepare for the C# import
from apsimNGpy.core_utils.utils import open_apsimx_file_in_window, evaluate_commands_and_values_types, is_scalar
# now we can safely import C# libraries
from apsimNGpy.core.pythonet_config import *
from apsimNGpy.core_utils.database_utils import read_db_table
from apsimNGpy.core.config import configuration
from apsimNGpy.exceptions import ModelNotFoundError, NodeNotFoundError
from apsimNGpy.core.model_tools import (get_or_check_model, old_method, _edit_in_cultivar,
                                        inspect_model_inputs,
                                        ModelTools, validate_model_obj, replace_variable_by_index)
from apsimNGpy.core.runner import run_model_externally, run_p, invoke_csharp_gc
from apsimNGpy.core.model_loader import (load_apsim_model, save_model_to_file, recompile, get_node_by_path)
import ast
from typing import Any
from apsimNGpy.core.run_time_info import BASE_RELEASE_NO, GITHUB_RELEASE_NO
from apsimNGpy.settings import SCRATCH, logger, MissingOption
from apsimNGpy.core.plotmanager import PlotManager
from apsimNGpy.core.model_tools import find_child
from apsimNGpy.core._cultivar import trace_cultivar
import Models
from apsimNGpy.core.pythonet_config import get_apsim_version as apsim_version
from System import InvalidOperationException, ArgumentOutOfRangeException, Array, Double
from apsimNGpy.core._cultivar import edit_cultivar_by_path
from apsimNGpy.core.version_inspector import is_higher_apsim_version

# constants
IS_NEW_MODEL = is_file_format_modified()


def edit_cultivar(node, cultivar_name, commands):
    def validate_commands(cmds):
        valid = []
        invalid = []
        for command in cmds:
            spc = command.split('=')
            if '=' in command and len(spc) > 1 and spc[-1]:
                valid.append(command.strip())
            else:
                invalid.append(command)
        if invalid:
            raise ValueError(f'{invalid} are not valid cultivar commands')
        return valid

    cultivar = node.FindChild[Models.PMF.Cultivar](cultivar_name, recurse=True)
    if isinstance(commands, str):
        commands = {commands}
    existing = list(cultivar.Command)
    valid_commands = validate_commands(commands)
    update = existing + list(valid_commands)
    unique_updated = list(dict.fromkeys(update))
    return unique_updated


def _looks_like_path(value: str) -> bool:
    return any(sep in value for sep in (os.sep, '/', '\\')) or value.endswith('.apsimx')


def compile_script(script_code: str, code_model):
    compiler = Models.Core.ScriptCompiler()
    compiler(script_code, code_model)


class CoreModel(PlotManager):
    """
    Modify and run APSIM Next Generation (APSIM NG) simulation models.

    This class is the main entry point for apsimNGpy simulations and acts
    as the base class for :class:`ApsimModel`. It can load models either
    from disk or from built-in default crop templates (e.g. ``"Maize"``),
    beginning with version 0.35.

    Parameters
    ----------
    model : str | Path | dict
        Path to the APSIM NG model, or a crop-name string referring to
        a default built-in simulation.
    out_path : str | Path, optional
        Destination path for the cloned model file. Defaults to using
        the same directory as the input model.
    experiment : bool, optional
        If ``True``, initialize the model as an experiment.
    set_wd : str | Path, optional
        Working directory for scratch copies and outputs.

    Notes
    -----
    * APSIM files are automatically cloned on load to protect originals.
    * The ``copy`` keyword is deprecated; the system now always makes a
      safe working copy.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
            self,
            model=None,
            out_path=None,
            *,
            experiment=False,
            set_wd=None,
            copy=None,
            **kwargs
    ):
        # User-specified configuration
        self.model = model
        self.out_path = out_path
        self.experiment = experiment
        self.set_wd = set_wd
        self.copy = copy  # deprecated but accepted
        self.others = {}  # additional runtime options
        self.wk_info = {}

        # Runtime APSIM/NET objects (initialized below)
        self.model_info = None
        self.Simulations = None
        self.datastore = None
        self.Datastore = None
        self._DataStore = None
        self.path = None
        self._str_model = None

        # Metadata and experiment configuration
        self.base_name = None
        self.permutation = None
        self.experiment_created = False
        self.factor_names = []
        self.report_names = None
        self._specifications = []
        self._intact_model = []

        # Internal state
        self.ran_ok = False
        self.factors = {}
        self.Start = MissingOption
        self.End = MissingOption
        self.run_method = None

        # Working directories
        self.work_space = self.set_wd or SCRATCH
        self._met_file = None

        # Models namespace handle
        self.Models = Models

        # Perform actual APSIM loading
        self._initialize_model()

    # ------------------------------------------------------------------
    # Internal initialization logic
    # ------------------------------------------------------------------

    def _initialize_model(self):
        """Load model, clone it, initialize datastore and metadata."""
        self._model = self.model
        self._met_file = self.others.get("met_file")

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

        # Experiment settings
        self.permutation = self.others.get("permutation", True)
        self.base_name = self.others.get("base_name")

        if self.experiment:
            self.create_experiment(
                permutation=self.permutation,
                base_name=self.base_name
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.clean_up()
        return None

    def check_model(self):
        if hasattr(Models.Core.ApsimFile, "ConverterReturnType"):

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

        We search all-Models.Core.Simulation in the scope of Model.Core.Simulations. Please note the difference
        Simulations is the whole json object Simulation is the child with the field zones, crops, soils and managers.

        Any structure of apsimx file can be handled.

        .. note::

             The simulations are c# referenced objects, and their manipulation maybe for advanced users only.
        """

        # we can actually specify the simulation name in the bracket
        self.check_model()

        if is_higher_apsim_version(self.Simulations):
            return ModelTools.find_all_in_scope(self.Simulations, Models.Core.Simulation)
        return list(self.Simulations.FindAllDescendants[Models.Core.Simulation]())

    @property
    def simulation_names(self):
        """
        @deprecated will be removed in future releases. Please use inspect_model function instead.

        retrieves the name of the simulations in the APSIMx file
        @return: list of simulation names
        """
        return model.inspect_model('Models.Core.Simulation', fullpath=False)

    @property
    def str_model(self):
        return json.dumps(self._str_model)

    @property
    def tables_list(self, ):
        """
        quick property returns available database report tables name
        """
        return self.inspect_model('Models.Report', fullpath=False)

    @property
    def managers_scripts_list(self, ):
        """
        quick property returns available database manager script names
        """
        return self.inspect_model('Models.Manager', fullpath=False)

    @property
    def simulations_list(self):
        """
        quick property for returning a list of available simulation names
        @return:
        """
        return self.inspect_model('Models.Core.Simulation', fullpath=False)

    @str_model.setter
    def str_model(self, value: dict):
        self._str_model = json.dumps(value)

    def restart_model(self, model_info=None):
        """
        Reinitialize the APSIM model instance after edits or management updates.

        Parameters
        ----------
        model_info : collections.NamedTuple, optional
            A named tuple returned by ``load_apsim_model`` from the ``model_loader``
            module. Contains references to the APSIM model, datastore, and file path.
            If not provided, the method reinitializes the model using the existing
            ``self.model_info`` object.

        Notes
        -----
        - This method is essential when the model needs to be **reloaded** after
          modifying management scripts or saving an edited APSIM file.
        - It may be invoked automatically by internal methods such as
          ``save_edited_file``, ``save``, and ``update_mgt``.
        - Reinitializing ensures that all APSIM NG components and datastore
          references are refreshed and consistent with the modified file.

        Returns
        -------
        self : object
            Returns the updated ApsimModel instance.
        """

        # Update model_info only if explicitly passed
        if model_info is not None:
            self.model_info = model_info

        # Use whichever model_info is now active
        info = self.model_info

        self.Simulations = info.IModel
        self.datastore = info.datastore
        self.Datastore = info.DataStore
        self._DataStore = info.DataStore
        self.path = info.path

        return self

    def save(self, file_name: Union[str, Path, None] = None, reload=True):
        """
        Saves the current APSIM NG model (``Simulations``) to disk and refresh runtime state.

        This method writes the model to a file, using a version-aware strategy:

        After writing, the model is recompiled via :func:`recompile(self)` and the
        in-memory instance is refreshed using :meth:`restart_model`, ensuring the
        object graph reflects the just-saved state. This is now only impozed if the user specified `relaod = True`.

        Parameters
        ----------
        file_name : str or pathlib.Path, optional
            Output path for the saved model file. If omitted (``None``), the method
            uses the instance's existing ``path``. The resolved path is also
            written back to instance `path` attribute for consistency if reload is True.

        reload: bool Optional default is True
             resets the reference path to the one provided after serializing to disk. This implies that the instance `path` will be the provided `file_name`

        Returns
        -------
        Self
            The same model/manager instance to support method chaining.

        Raises
        ------
        OSError
            If the file cannot be written due to I/O errors, permissions, or invalid path.
        AttributeError
            If required attributes (e.g., ``self.Simulations``) or methods are missing.
        Exception
            Any exception propagated by :func:`save_model_to_file`, :func:`recompile`,
            or :meth:`restart_model`.

        Side Effects
        ------------
        - Sets ``self.path`` to the resolved output path (string).
        - Writes the model file to disk (overwrites if it exists).
        - If reload is True (default), recompiles the model and restarts the in-memory instance.

        Notes
        -----
        - *Path normalization:* The path is stringified via ``str(file_name)`` just in case it is a pathlib object.

        - *Reload semantics:* Post-save recompilation and restart ensure any code
          generation or cached reflection is refreshed to match the serialized model.

        Examples
        --------
        check the current path before saving the model
            >>> from apsimNGpy.core.apsim import ApsimModel
            >>> from pathlib import Path
            >>> model = ApsimModel("Maize", out_path='saved_maize.apsimx')
            >>> model.path
            scratch\\saved_maize.apsimx

        Save to a new path and continue working with the refreshed instance
            >>> model.save(file_name='out_maize.apsimx', reload=True)
            # check the path
            >>> model.path
            'out_maize.apsimx'
            # possible to run again the refreshed model.
            >>> model.run()

        Save to a new path without refreshing the instance path
          >>> model = ApsimModel("Maize",  out_path='saved_maize.apsimx')
          >>> model.save(file_name='out_maize.apsimx', reload=False)
          # check the current reference path for the model.
           >>> model.path 'scratch\\saved_maize.apsimx'
           # When reload is False, the original referenced path remains as shown above

        As shown above, everything is saved in the scratch folder; if
        the path is not abolutely provided, e.g., a relative path. If the path is not provided as shown below,
        the reference path is the current path for the isntance model.
           >>> model = ApsimModel("Maize",  out_path='saved_maize.apsimx')
           >>> model.path
           'scratch\\saved_maize.apsimx'
           # save the model without providing the path.
           >>> model.save()# uses the default, in this case the defaul path is the existing path
           >>> model.path
           'scratch\\saved_maize.apsimx'

        In the above case, both reload = `False` or `True`, will produce the same reference path for the live
        instance class.

        """

        _path = str(file_name or self.path)

        try:
            _path = str(file_name or self.path)

            if is_higher_apsim_version(self.Simulations):
                # self.Simulations.Write(str(_path))
                save_model_to_file(getattr(self.Simulations, 'Node', self.Simulations), str(_path))
            else:
                sm = getattr(self.Simulations, 'Node', self.Simulations)
                save_model_to_file(sm, out=_path)
            # rest the reference path to the saved filename or path
            if reload:
                model_info = recompile(self)
                self.restart_model(model_info)
                self.path = _path
            return self
        finally:

            pass

    @property
    def results(self) -> pd.DataFrame:
        """
        Legacy method for retrieving simulation results.

        This method is implemented as a ``property`` to enable lazy loading—results are
        only loaded into memory when explicitly accessed. This design helps optimize
        ``memory`` usage, especially for ``large`` simulations.

        It must be called only after invoking ``run()``. If accessed before the simulation
        is run, it will raise an error.

        Notes
        -----
        - The ``run()`` method should be called with a valid ``report name`` or a list of
          report names.
        - If ``report_names`` is not provided (i.e., ``None``), the system will inspect
          the model and automatically detect all available report components. These
          reports will then be used to collect the data.
        - If multiple report names are used, their corresponding data tables will be
          concatenated along the rows.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the simulation output results.

        Examples
        --------
        >>> from apsimNGpy.core.apsim import ApsimModel
        # create an instance of ApsimModel class
        >>> model = ApsimModel("Maize", out_path="my_maize_model.apsimx")
        # run the simulation
        >>> model.run()
        # get the results
        >>> df = model.results
        # do something with the results e.g. get the mean of numeric columns
        >>> df.mean(numeric_only=True)
        Out[12]:
        CheckpointID                     1.000000
        SimulationID                     1.000000
        Maize.AboveGround.Wt          1225.099950
        Maize.AboveGround.N             12.381196
        Yield                         5636.529504
        Maize.Grain.Wt                 563.652950
        Maize.Grain.Size                 0.284941
        Maize.Grain.NumberFunction    1986.770519
        Maize.Grain.Total.Wt           563.652950
        Maize.Grain.N                    7.459296
        Maize.Total.Wt                1340.837427

        If there are more than one database tables or `reports` as called in APSIM,
        results are concatenated along the axis 0, implying along rows.
        The example below mimics this scenario.

        >>> model.add_db_table(
        ...     variable_spec=['[Clock].Today.Year as year',
        ...                    'sum([Soil].Nutrient.TotalC)/1000 from 01-jan to [clock].Today as soc'],
        ...     rename='soc'
        ... )
        # inspect the reports
        >>> model.inspect_model('Models.Report', fullpath=False)
        ['Report', 'soc']
        >>> model.run()
        >>> model.results
            CheckpointID  SimulationID   Zone  ... source_table    year        soc
        0              1             1  Field  ...       Report     NaN        NaN
        1              1             1  Field  ...       Report     NaN        NaN
        2              1             1  Field  ...       Report     NaN        NaN
        3              1             1  Field  ...       Report     NaN        NaN
        4              1             1  Field  ...       Report     NaN        NaN
        5              1             1  Field  ...       Report     NaN        NaN
        6              1             1  Field  ...       Report     NaN        NaN
        7              1             1  Field  ...       Report     NaN        NaN
        8              1             1  Field  ...       Report     NaN        NaN
        9              1             1  Field  ...       Report     NaN        NaN
        10             1             1  Field  ...          soc  1990.0  77.831512
        11             1             1  Field  ...          soc  1991.0  78.501766
        12             1             1  Field  ...          soc  1992.0  78.916339
        13             1             1  Field  ...          soc  1993.0  78.707094
        14             1             1  Field  ...          soc  1994.0  78.191686
        15             1             1  Field  ...          soc  1995.0  78.573085
        16             1             1  Field  ...          soc  1996.0  78.724598
        17             1             1  Field  ...          soc  1997.0  79.043935
        18             1             1  Field  ...          soc  1998.0  78.343111
        19             1             1  Field  ...          soc  1999.0  78.872767
        20             1             1  Field  ...          soc  2000.0  79.916413
        [21 rows x 17 columns]

        By default all the tables are returned and the column ``source_table`` tells us
        the source table for each row. Since ``results`` is a property attribute,
        which does not take in any argument, we can only decide this when calling the
        ``run`` method as shown below.

        >>> model.run(report_name='soc')
        >>> model.results
            CheckpointID  SimulationID   Zone    year        soc source_table
        0              1             1  Field  1990.0  77.831512          soc
        1              1             1  Field  1991.0  78.501766          soc
        2              1             1  Field  1992.0  78.916339          soc
        3              1             1  Field  1993.0  78.707094          soc
        4              1             1  Field  1994.0  78.191686          soc
        5              1             1  Field  1995.0  78.573085          soc
        6              1             1  Field  1996.0  78.724598          soc
        7              1             1  Field  1997.0  79.043935          soc
        8              1             1  Field  1998.0  78.343111          soc
        9              1             1  Field  1999.0  78.872767          soc
        10             1             1  Field  2000.0  79.916413          soc

        The above example has dataset only from one database table specified at run time.

        .. seealso::

           Related API: :meth:`get_simulated_output`.
        """

        # _____________ Collect all available data tables _____________________
        _reports = self.report_names or self.inspect_model('Models.Report',
                                                           fullpath=False)  # false returns all names other than fullpath of the models in that type
        db_path = Path(self.path).with_suffix('.db')
        if self.ran_ok:
            return self._get_results(_reports, db_path, axis=0)
        else:

            logger.info(f"{self} not yet executed. Please call `run()`")

    def _get_results(self, _reports, _db_path, axis=0):
        from collections.abc import Iterable
        # Normalize report_names to a list
        if isinstance(_reports, str):
            reports = [_reports]
        elif isinstance(_reports, Iterable):  # if iterable, back off
            reports = _reports
        else:
            raise TypeError(f"report_names must be an iterable of strings, not {type(_reports)}.")
        if _reports:
            if self.ran_ok:
                # lazy generator (adds a column with the report name)
                if axis == 0:
                    data = (read_db_table(_db_path, rep).assign(source_table=rep) for rep in reports)
                else:
                    data = (read_db_table(_db_path, rep) for rep in reports)

                return pd.concat(data, axis=axis)
            else:
                logger.info('attempting to access results without calling bound method: `run()`')
                raise RuntimeError(f"attempting to access results without executingg the model. Please call `run()`")

    def get_simulated_output(self, report_names: Union[str, list], axis=0, **kwargs) -> pd.DataFrame:
        """
        Reads report data from CSV files generated by the simulation. More Advanced table-merging arguments will be introduced soon.

        Parameters:
        -----------
        report_names: (str, iterable)
            Name or list names of report tables to read. These should match the
            report names in the simulation output.

        axis: int, Optional. Default to 0
            concatenation axis numbers for multiple reports or database tables. if axis is 0, source_table column is populated to show source of the data for each row

        Returns:
        --------
        ``pd.DataFrame``
            Concatenated DataFrame containing the data from the specified reports.

        Raises:
        -------
        ValueError
            If any of the requested report names are not found in the available tables.

        RuntimeError
            If the simulation has not been ``run`` successfully before attempting to read data.
        Examples
        --------
        >>> from apsimNGpy.core.apsim import ApsimModel
        >>> model = ApsimModel(model='Maize')  # replace with your path to the apsim template model
        >>> model.run()  # if we are going to use get_simulated_output, no need to provide the report name in ``run()`` method
        >>> df = model.get_simulated_output(report_names="Report")
            SimulationName  SimulationID  CheckpointID  ...  Maize.Total.Wt     Yield   Zone
        0       Simulation             1             1  ...        1728.427  8469.616  Field
        1       Simulation             1             1  ...         920.854  4668.505  Field
        2       Simulation             1             1  ...         204.118   555.047  Field
        3       Simulation             1             1  ...         869.180  3504.000  Field
        4       Simulation             1             1  ...        1665.475  7820.075  Field
        5       Simulation             1             1  ...        2124.740  8823.517  Field
        6       Simulation             1             1  ...        1235.469  3587.101  Field
        7       Simulation             1             1  ...         951.808  2939.152  Field
        8       Simulation             1             1  ...        1986.968  8379.435  Field
        9       Simulation             1             1  ...        1689.966  7370.301  Field
        [10 rows x 16 columns]

        This method also handles more than one reports as shown below.

        >>> model.add_db_table(
        ...     variable_spec=[
        ...         '[Clock].Today.Year as year',
        ...         'sum([Soil].Nutrient.TotalC)/1000 from 01-jan to [clock].Today as soc'
        ...     ],
        ...     rename='soc'
        ... )
        # inspect the reports
        >>> model.inspect_model('Models.Report', fullpath=False)
        ['Report', 'soc']
        >>> model.run()
        >>> model.get_simulated_output(["soc", "Report"], axis=0)
            CheckpointID  SimulationID  ...  Maize.Grain.N  Maize.Total.Wt
        0              1             1  ...            NaN             NaN
        1              1             1  ...            NaN             NaN
        2              1             1  ...            NaN             NaN
        3              1             1  ...            NaN             NaN
        4              1             1  ...            NaN             NaN
        5              1             1  ...            NaN             NaN
        6              1             1  ...            NaN             NaN
        7              1             1  ...            NaN             NaN
        8              1             1  ...            NaN             NaN
        9              1             1  ...            NaN             NaN
        10             1             1  ...            NaN             NaN
        11             1             1  ...      11.178291     1728.427114
        12             1             1  ...       6.226327      922.393712
        13             1             1  ...       0.752357      204.108770
        14             1             1  ...       4.886844      869.242545
        15             1             1  ...      10.463854     1665.483701
        16             1             1  ...      11.253916     2124.739830
        17             1             1  ...       5.044417     1261.674967
        18             1             1  ...       3.955080      951.303260
        19             1             1  ...      11.080878     1987.106980
        20             1             1  ...       9.751001     1693.893386
        [21 rows x 17 columns]

        >>> model.get_simulated_output(['soc', 'Report'], axis=1)
            CheckpointID  SimulationID  ...  Maize.Grain.N  Maize.Total.Wt
        0              1             1  ...      11.178291     1728.427114
        1              1             1  ...       6.226327      922.393712
        2              1             1  ...       0.752357      204.108770
        3              1             1  ...       4.886844      869.242545
        4              1             1  ...      10.463854     1665.483701
        5              1             1  ...      11.253916     2124.739830
        6              1             1  ...       5.044417     1261.674967
        7              1             1  ...       3.955080      951.303260
        8              1             1  ...      11.080878     1987.106980
        9              1             1  ...       9.751001     1693.893386
        10             1             1  ...            NaN             NaN
        [11 rows x 19 columns]

        .. seealso::

           Related API: :attr:`results`.
        """
        db_path = Path(self.path).with_suffix('.db')
        _reports = report_names
        if self.ran_ok:
            return self._get_results(_reports, db_path, axis=axis)
        else:
            logger.info('Model not ran use other means to read data if that is the goal')

    def run(self, report_name: Union[tuple, list, str] = None,
            simulations: Union[tuple, list] = None,
            clean_up: bool = True,
            verbose: bool = False,
            timeout: int = 800,
            cpu_count: int = -1,
            **kwargs) -> 'CoreModel':
        """
        Run APSIM model simulations to write the results either to SQLite database or csv file. Does not collect the
         simulated output into memory. Please see related APIs: :attr:`results` and :meth:`get_simulated_output`.

        Parameters
        ----------
        report_name: Union[tuple, list, str], optional
            Defaults to APSIM default Report Name if not specified.
            - If iterable, all report tables are read and aggregated into one DataFrame.

        simulations: Union[tuple, list], optional
            List of simulation names to run. If None, runs all simulations.

        clean_up: bool, optional
            If True, removes the existing database before running.

        verbose: bool, optional
            If True, enables verbose output for debugging. The method continues with debugging info anyway if the run was unsuccessful

        timeout: int, default is 800 seconds
              Enforces a timeout and returns a CompletedProcess-like object.
        cpu_count: int, Optional default is -1, referring to all threads
            This parameter is useful when the number of simulations are more than 1, below that performance differences are minimal
            added in 0.39.11.21+

        kwargs: **dict
            Additional keyword arguments, e.g., to_csv=True, use this flag to correct results from
            a csv file directly stored at the location of the running apsimx file.

        Warning:
        --------------
        In my experience with Models.exe, CSV outputs are not always overwritten; after edits, stale results can persist. Proceed with caution.


        Returns
        -------
            Instance of the respective model class e.g.,  ApsimModel, ExperimentManager.
       ``RuntimeError``
            Raised if the ``APSIM`` run is unsuccessful. Common causes include ``missing meteorological files``,
            mismatched simulation ``start`` dates with ``weather`` data, or other ``configuration issues``.

       Example:

       Instantiate an ``apsimNGpy.core.apsim.ApsimModel`` object and run::

              from apsimNGpy.core.apsim import ApsimModel
              model = ApsimModel(model= 'Maize')# replace with your path to the apsim template model
              model.run(report_name = "Report")
              # check if the run was successful
              model.ran_ok
              'True'

       .. note::

          Updates the ``ran_ok`` flag to ``True`` if no error was encountered.

       .. seealso::

           Related APIs: :attr:`results` and :meth:`get_simulated_output`.
             """

        def dispose_db():
            try:
                self._DataStore.Dispose()
                self.Datastore.Close()
            except AttributeError:
                pass
            except InvalidOperationException:
                pass

        try:

            self.save()
            if clean_up:
                try:
                    dispose_db()
                except PermissionError:
                    pass
                except ArgumentOutOfRangeException:
                    pass

            # Run APSIM externally
            res = run_model_externally(
                # we run using the copied file

                self.path,
                verbose=verbose,
                to_csv=kwargs.get('to_csv', False),
                timeout=timeout,
                cpu_count=cpu_count,
            )

            if res.returncode == 0:
                self.ran_ok = True
                self.report_names = report_name
                self.run_method = run_model_externally

            # If the model failed and verbose was off, rerun to diagnose
            if not self.ran_ok and not verbose:
                logger.info('run time errors occurred')

            return self

        finally:
            ...

    def rename_model(self, model_type, *, old_name, new_name):
        """
            Renames a model within the APSIM simulation tree.

            This method searches for a model of the specified type and current name,
            then updates its name to the new one provided. After renaming, it saves
            the updated simulation file to enforce the changes.

            Parameters
            ----------
            model_type : str
                The type of the model to rename (e.g., "Manager", "Clock", etc.).
            old_name : str
                The current name of the model to be renamed.
            new_name : str
                The new name to assign to the model.

            Returns
            -------
            self : object
                Returns the modified object to allow for method chaining.

            Raises
            ------
            ValueError
                If the model of the specified type and name is not found.

           .. tip::

                This method uses ``get_or_check_model`` with action='get' to locate the model,
                and then updates the model's `Name` attribute. The model is serialized using the `save()`
                immediately after to apply and enfoce the change.

            Examples
            ---------
               >>> from apsimNGpy.core.apsim import ApsimModel
               >>> model = ApsimModel(model = 'Maize', out_path='my_maize.apsimx')
               >>> model.rename_model(model_type="Models.Core.Simulation", old_name ='Simulation', new_name='my_simulation')
               # check if it has been successfully renamed
               >>> model.inspect_model(model_type='Models.Core.Simulation', fullpath = False)
                ['my_simulation']
               # The alternative is to use model.inspect_file to see your changes
               >>> model.inspect_file()

         .. code-block:: none

           └── Models.Core.Simulations: .Simulations
                ├── Models.Storage.DataStore: .Simulations.DataStore
                ├── Models.Core.Folder: .Simulations.Replacements
                │   └── Models.PMF.Plant: .Simulations.Replacements.Maize
                │       └── Models.Core.Folder: .Simulations.Replacements.Maize.CultivarFolder
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Atrium
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.CG4141
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Dekalb_XL82
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.GH_5009
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.GH_5019WX
                │           ├── Models.Core.Folder: .Simulations.Replacements.Maize.CultivarFolder.Generic
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_100
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_103
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_105
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_108
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_110
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_112
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_115
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_120
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_130
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_80
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_90
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_95
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_100
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_103
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_105
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_108
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_110
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_112
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_115
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_120
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_130
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_80
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_90
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_95
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.HY_110
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.LY_110
                │           │   └── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.P1197
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Hycorn_40
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Hycorn_53
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Katumani
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Laila
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Makueni
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Melkassa
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.NSCM_41
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Pioneer_3153
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Pioneer_33M54
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Pioneer_34K77
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Pioneer_38H20
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Pioneer_39G12
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Pioneer_39V43
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.malawi_local
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.mh12
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.mh16
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.mh17
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.mh18
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.mh19
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.r201
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.r215
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.sc401
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.sc501
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.sc601
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.sc623
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.sc625
                │           └── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.sr52
                └── Models.Core.Simulation: .Simulations.Simulation
                    ├── Models.Clock: .Simulations.Simulation.Clock
                    ├── Models.Core.Zone: .Simulations.Simulation.Field
                    │   ├── Models.Manager: .Simulations.Simulation.Field.Fertilise at sowing
                    │   ├── Models.Fertiliser: .Simulations.Simulation.Field.Fertiliser
                    │   ├── Models.Manager: .Simulations.Simulation.Field.Harvest
                    │   ├── Models.PMF.Plant: .Simulations.Simulation.Field.Maize
                    │   │   └── Models.Core.Folder: .Simulations.Simulation.Field.Maize.CultivarFolder
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Atrium
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.CG4141
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.GH_5009
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.GH_5019WX
                    │   │       ├── Models.Core.Folder: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_100
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_103
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_105
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_108
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_110
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_112
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_115
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_120
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_130
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_80
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_90
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_95
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_100
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_103
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_105
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_108
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_110
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_112
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_115
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_120
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_130
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_80
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_90
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_95
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.HY_110
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.LY_110
                    │   │       │   └── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.P1197
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Hycorn_40
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Hycorn_53
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Katumani
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Laila
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Makueni
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Melkassa
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.NSCM_41
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_3153
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_33M54
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_34K77
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_38H20
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_39G12
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_39V43
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.malawi_local
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.mh12
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.mh16
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.mh17
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.mh18
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.mh19
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.r201
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.r215
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.sc401
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.sc501
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.sc601
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.sc623
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.sc625
                    │   │       └── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.sr52
                    │   ├── Models.Report: .Simulations.Simulation.Field.Report
                    │   ├── Models.Soils.Soil: .Simulations.Simulation.Field.Soil
                    │   │   ├── Models.Soils.Chemical: .Simulations.Simulation.Field.Soil.Chemical
                    │   │   ├── Models.Soils.Solute: .Simulations.Simulation.Field.Soil.NH4
                    │   │   ├── Models.Soils.Solute: .Simulations.Simulation.Field.Soil.NO3
                    │   │   ├── Models.Soils.Organic: .Simulations.Simulation.Field.Soil.Organic
                    │   │   ├── Models.Soils.Physical: .Simulations.Simulation.Field.Soil.Physical
                    │   │   │   └── Models.Soils.SoilCrop: .Simulations.Simulation.Field.Soil.Physical.MaizeSoil
                    │   │   ├── Models.Soils.Solute: .Simulations.Simulation.Field.Soil.Urea
                    │   │   └── Models.Soils.Water: .Simulations.Simulation.Field.Soil.Water
                    │   ├── Models.Manager: .Simulations.Simulation.Field.Sow using a variable rule
                    │   └── Models.Surface.SurfaceOrganicMatter: .Simulations.Simulation.Field.SurfaceOrganicMatter
                    ├── Models.Graph: .Simulations.Simulation.Graph
                    │   └── Models.Series: .Simulations.Simulation.Graph.Series
                    ├── Models.MicroClimate: .Simulations.Simulation.MicroClimate
                    ├── Models.Soils.Arbitrator.SoilArbitrator: .Simulations.Simulation.SoilArbitrator
                    ├── Models.Summary: .Simulations.Simulation.Summary
                    └── Models.Climate.Weather: .Simulations.Simulation.Weather

         .. seealso::

             Related APIs: :meth:`~apsimNGpy.core.apsim.ApsimModel.add_model`,
             :meth:`~apsimNGpy.core.apsim.ApsimModel.clone_model`, and
             :meth:`~apsimNGpy.core.apsim.ApsimModel.move_model`.

            """
        model_type = validate_model_obj(model_type)
        mtn = get_or_check_model(self.Simulations, model_type=model_type, model_name=old_name, action='get')
        mtn.Name = f"{new_name}"
        self.save()
        return self

    def add_memo(self, memo_text):
        memo = Models.Memo()
        memo.set_Text(memo_text.strip())
        self.Simulations.Children.Add(memo)

    def clone_model(self, model_type, model_name, adoptive_parent_type, rename=None, adoptive_parent_name=None):
        """
        Clone an existing ``model`` and move it to a specified parent within the simulation structure.
        The function modifies the simulation structure by adding the cloned model to the designated parent.

        This function is useful when a model instance needs to be duplicated and repositioned in the `APSIM` simulation
        hierarchy without manually redefining its structure.

        Parameters:
        ----------
        model_type: Models
            The type of the model to be cloned, e.g., `Models.Simulation` or `Models.Clock`.
        model_name: str
            The unique identification name of the model instance to be cloned, e.g., `"clock1"`.
        adoptive_parent_type: Models
            The type of the new parent model where the cloned model will be placed.
        rename: str, optional
            The new name for the cloned model. If not provided, the clone will be renamed using
            the original name with a `_clone` suffix.
        adoptive_parent_name: str, optional
            The name of the parent model where the cloned model should be moved. If not provided,
            the model will be placed under the default parent of the specified type.
        in_place: bool, optional
            If ``True``, the cloned model remains in the same location but is duplicated. Defaults to ``False``.

        Returns:
        -------
        None

        Example:
        -------
         Create a cloned version of `"clock1"` and place it under `"Simulation"` with the new name `"new_clock`:

            >>> from apsimNGpy.core.apsim import ApsimModel
            >>> model = ApsimModel('Maize', out_path='my_maize.apsimx')
            >>> model.clone_model(model_type='Models.Core.Simulation', model_name="Simulation",
            ... rename="Sim2", adoptive_parent_type = 'Models.Core.Simulations',
            ... adoptive_parent_name='Simulations')
            >>> model.inspect_file()
            └── Simulations: .Simulations
                ├── DataStore: .Simulations.DataStore
                ├── Sim2: .Simulations.Sim2
                │   ├── Clock: .Simulations.Sim2.Clock
                │   ├── Field: .Simulations.Sim2.Field
                │   │   ├── Fertilise at sowing: .Simulations.Sim2.Field.Fertilise at sowing
                │   │   ├── Fertiliser: .Simulations.Sim2.Field.Fertiliser
                │   │   ├── Harvest: .Simulations.Sim2.Field.Harvest
                │   │   ├── Maize: .Simulations.Sim2.Field.Maize
                │   │   ├── Report: .Simulations.Sim2.Field.Report
                │   │   ├── Soil: .Simulations.Sim2.Field.Soil
                │   │   │   ├── Chemical: .Simulations.Sim2.Field.Soil.Chemical
                │   │   │   ├── NH4: .Simulations.Sim2.Field.Soil.NH4
                │   │   │   ├── NO3: .Simulations.Sim2.Field.Soil.NO3
                │   │   │   ├── Organic: .Simulations.Sim2.Field.Soil.Organic
                │   │   │   ├── Physical: .Simulations.Sim2.Field.Soil.Physical
                │   │   │   │   └── MaizeSoil: .Simulations.Sim2.Field.Soil.Physical.MaizeSoil
                │   │   │   ├── Urea: .Simulations.Sim2.Field.Soil.Urea
                │   │   │   └── Water: .Simulations.Sim2.Field.Soil.Water
                │   │   ├── Sow using a variable rule: .Simulations.Sim2.Field.Sow using a variable rule
                │   │   ├── SurfaceOrganicMatter: .Simulations.Sim2.Field.SurfaceOrganicMatter
                │   │   └── soc_table: .Simulations.Sim2.Field.soc_table
                │   ├── Graph: .Simulations.Sim2.Graph
                │   │   └── Series: .Simulations.Sim2.Graph.Series
                │   ├── MicroClimate: .Simulations.Sim2.MicroClimate
                │   ├── SoilArbitrator: .Simulations.Sim2.SoilArbitrator
                │   ├── Summary: .Simulations.Sim2.Summary
                │   └── Weather: .Simulations.Sim2.Weather
                └── Simulation: .Simulations.Simulation
                    ├── Clock: .Simulations.Simulation.Clock
                    ├── Field: .Simulations.Simulation.Field
                    │   ├── Fertilise at sowing: .Simulations.Simulation.Field.Fertilise at sowing
                    │   ├── Fertiliser: .Simulations.Simulation.Field.Fertiliser
                    │   ├── Harvest: .Simulations.Simulation.Field.Harvest
                    │   ├── Maize: .Simulations.Simulation.Field.Maize
                    │   ├── Report: .Simulations.Simulation.Field.Report
                    │   ├── Soil: .Simulations.Simulation.Field.Soil
                    │   │   ├── Chemical: .Simulations.Simulation.Field.Soil.Chemical
                    │   │   ├── NH4: .Simulations.Simulation.Field.Soil.NH4
                    │   │   ├── NO3: .Simulations.Simulation.Field.Soil.NO3
                    │   │   ├── Organic: .Simulations.Simulation.Field.Soil.Organic
                    │   │   ├── Physical: .Simulations.Simulation.Field.Soil.Physical
                    │   │   │   └── MaizeSoil: .Simulations.Simulation.Field.Soil.Physical.MaizeSoil
                    │   │   ├── Urea: .Simulations.Simulation.Field.Soil.Urea
                    │   │   └── Water: .Simulations.Simulation.Field.Soil.Water
                    │   ├── Sow using a variable rule: .Simulations.Simulation.Field.Sow using a variable rule
                    │   ├── SurfaceOrganicMatter: .Simulations.Simulation.Field.SurfaceOrganicMatter
                    │   └── soc_table: .Simulations.Simulation.Field.soc_table
                    ├── Graph: .Simulations.Simulation.Graph
                    │   └── Series: .Simulations.Simulation.Graph.Series
                    ├── MicroClimate: .Simulations.Simulation.MicroClimate
                    ├── SoilArbitrator: .Simulations.Simulation.SoilArbitrator
                    ├── Summary: .Simulations.Simulation.Summary
                    └── Weather: .Simulations.Simulation.Weather
        .. seealso::

           Related APIs: :meth:`add_model` and :meth:`move_model`.
        """
        # Reference to the APSIM cloning function
        model_type = validate_model_obj(model_type, evaluate_bound=True)
        adoptive_parent_type = validate_model_obj(adoptive_parent_type, evaluate_bound=False)

        # Locate the model to be cloned within the simulation scope
        if is_higher_apsim_version(self.Simulations):
            clone_parent = (ModelTools.find_child(self.Simulations, model_type, model_name) if model_name
                            else ModelTools.find_child_of_class(self.Simulations, model_type))
        else:
            clone_parent = (self.Simulations.FindDescendant[model_type](model_name) if model_name
                            else self.Simulations.FindDescendant[model_type]())

        # Create a clone of the model
        from APSIM.Core import Node

        clone = Node.Clone(clone_parent.Node)

        # Add the cloned model to the new parent
        model_clone = self.find_model(model_type)
        mod = getattr(clone, "Model", clone)
        clone = CastHelper.CastAs[model_clone](mod)
        # Assign a new name to the cloned model
        new_name = rename if rename else f"{clone.Name}_clone"
        clone.Name = new_name

        # check_exists = self.Simulations.FindInScope[model_class](new_name)
        get_or_check_model(self.Simulations, model_type, new_name, action='delete')
        # Find the adoptive parent where the cloned model should be placed
        if adoptive_parent_type == Models.Core.Simulations or adoptive_parent_type == 'Models.Core.Simulations':
            self.Simulations.Children.Add(clone)
        else:
            parent = ModelTools.find_child(self.Simulations, child_class=adoptive_parent_type,
                                           child_name=adoptive_parent_name)
            # parent = CastHelper.CastAs[adoptive_parent_type](parent)

            parent.Children.Add(clone)

        # Serialize simulation structure
        self.save()

    @staticmethod
    def find_model(model_name: str):
        """
        Find a model from the Models namespace and return its path.

        Parameters:
        -----------
        model_name: (str)
          The name of the model to find.
        model_namespace: (object, optional):
           The root namespace (defaults to Models).
        path: (str, optional)
           The accumulated path to the model.

        Returns:
            str: The full path to the model if found, otherwise None.

        Example:
        --------
             >>> from apsimNGpy import core  # doctest:
             >>> model =core.apsim.ApsimModel(model = "Maize", out_path ='my_maize.apsimx')
             >>> model.find_model("Weather")  # doctest: +SKIP
             'Models.Climate.Weather'
             >>> model.find_model("Clock")  # doctest: +SKIP
             'Models.Clock'

        """
        return validate_model_obj(model_name)

    def add_model(self, model_type, adoptive_parent, rename=None,
                  adoptive_parent_name=None, verbose=False, source='Models', source_model_name=None, override=True,
                  **kwargs):

        """
        Adds a model to the Models Simulations namespace.

        Some models are restricted to specific parent models, meaning they can only be added to compatible models.
        For example, a Clock model cannot be added to a Soil model.

        Parameters:
        -----------
        model_type: (str or Models object)
           The type of model to add, e.g., `Models.Clock` or just `"Clock"`. if the APSIM Models namespace is exposed to the current script, then model_class can be Models.Clock without strings quotes

        rename (str):
          The new name for the model.

        adoptive_parent: (Models object)
            The target parent where the model will be added or moved e.g `Models.Clock` or `Clock` as string all are valid

        adoptive_parent_name: (Models object, optional)
            Specifies the parent name for precise location. e.g., `Models.Core.Simulation` or ``Simulations`` all are valid

        source: Models, str, CoreModel, ApsimModel object: defaults to Models namespace.
           The source can be an existing Models or string name to point to one of the
           default model examples, which we can extract the model from

        override: bool, optional defaults to `True`.
            When `True` (recommended), it deletes
            any model with the same name and type at the suggested parent location before adding the new model
            if ``False`` and proposed model to be added exists at the parent location;
            `APSIM` automatically generates a new name for the newly added model. This is not recommended.
        Returns:
            None:

        `Models` are modified in place, so models retains the same reference.

        .. caution::
            Added models from ``Models namespace`` are initially empty. Additional configuration is required to set parameters.
            For example, after adding a Clock module, you must set the start and end dates.

        Example
        -------------

        >>> from apsimNGpy import core
        >>> from apsimNGpy.core.core import Models
        >>> model = core.apsim.ApsimModel("Maize")
        >>> model.remove_model(Models.Clock)  # first delete the model
        >>> model.add_model(Models.Clock, adoptive_parent=Models.Core.Simulation, rename='Clock_replaced', verbose=False)

        >>> model.add_model(model_class=Models.Core.Simulation, adoptive_parent=Models.Core.Simulations, rename='Iowa')

        >>> model.preview_simulation()  # doctest: +SKIP

        >>> model.add_model(
        ... Models.Core.Simulation,
        ... adoptive_parent='Simulations',
        ... rename='soybean_replaced',
        ... source='Soybean')  # basically adding another simulation from soybean to the maize simulation

        .. seealso::

            Related APIs: :meth:`clone_model` and :meth:`move_model`.
        """
        import Models

        sims = self.Simulations
        model_type = validate_model_obj(model_type, evaluate_bound=True)
        adoptive_parent = validate_model_obj(adoptive_parent, evaluate_bound=False)
        # find where to add the model
        if adoptive_parent == Models.Core.Simulations:
            parent = self.Simulations
        else:
            if not adoptive_parent_name:
                adoptive_parent_name = adoptive_parent().Name

            try:
                parent = sims.FindInScope[adoptive_parent](adoptive_parent_name)
            except:

                parent = sims.FindDescendant[adoptive_parent](adoptive_parent_name)
        if model_type == Models.Core.Simulations:
            raise ValueError(
                f"{model_type} can not be a simulations holder did you mean 'Models.Core.Simulation' or 'Simulation'?")
        # parent = _model.Simulations.FindChild(where)

        if source == 'Models':
            model_type = model_type
        else:
            # look for the model from source
            if isinstance(source, (str, dict)):
                source_model = load_apsim_model(source)
            elif isinstance(source, CoreModel):
                source_model = source
            else:
                raise ValueError(
                    f"model type {type(source)} is not supported. Please supply a crop name or path to the apsim file or apsimNGpy.core.CoreModel objects")
            model_type = (source_model.IModel.FindInScope[model_type](source_model_name) if source_model_name else
                          source_model.IModel.FindInScope[model_type]())

            if not model_type:
                if not source_model_name:
                    raise ValueError(
                        f"{model_type} can not be found. Did you forget to specify the `source_model_name`")
                else:
                    raise ValueError(
                        f"{model_type} can not be found. Please recheck your input or use inspect_file() to see all the available model types")

            model_type.Name = rename if rename else model_type.Name
            # target_child = parent.FindInScope[model_class.__class__](model_class.Name)
            # target_child = get_or_check_model(parent, model_class.__class__, model_class.Name, action ='delete')
            if override:
                get_or_check_model(parent, model_type.__class__, model_type.Name, action='delete')
            model_type = ModelTools.CLONER(model_type)
            ModelTools.ADD(model_type, parent)
            self.save()
            if verbose:
                logger.info(f"Added {model_type.Name} to {parent.Name}")
            return self
        if model_type and parent:
            loc = model_type()
            if rename and hasattr(loc, 'Name'):
                loc.Name = rename
            if hasattr(loc, 'Name'):
                target_child = parent.FindChild[model_type](loc.Name)
                if target_child and override:
                    # not raising the error still studying the behaviors of adding a child that already exists
                    ModelTools.DELETE(target_child)
            # get_or_check_model(parent, model_class.__class__, model_class.Name, action='delete')
            model_to_add = ModelTools.CLONER(loc)
            del loc
            parent = getattr(parent, 'Model', parent)
            ModelTools.ADD(model_to_add, parent)

            if verbose:
                logger.info(f"Added {model_to_add.Name} to {parent.Name}")
            # compile
            return self

        else:
            logger.debug(f"Adding {model_type} to {parent.Name} failed, perhaps models was not found")

    def _refresh_experiment(self):
        mi = load_apsim_model(self.path)
        self.wk_info['SIM'] = mi.Simulations
        self.wk_info['NODE'] = mi.Node

    @staticmethod
    def _set_clock_vars(model_instance, param_values: dict, verbose=False):
        validated = dict(End='End', Start='Start', end='End', start='Start', end_date='End',
                         start_date='Start')

        for kwa, value in param_values.items():
            key = validated.get(kwa, 'unknown')  # APSIM uses camelcase
            if key in ['End', 'Start']:
                parsed_value = DateTime.Parse(value)
                setattr(model_instance, key, parsed_value)
                if verbose:
                    logger.info(f"Set {key} to {parsed_value}")

            else:
                raise AttributeError(
                    f"no valid Clock attributes were passed. Valid arguments are: '{", ".join(validated.keys())}'")

    @staticmethod
    def _set_weather_path(model_instance, param_values: dict, verbose=False):
        met_file = param_values.get('weather_file') or param_values.get('met_file') or param_values.get("FileName")
        if met_file is None:
            raise ValueError('Use key word argument "weather_file" to supply the weather data')
        # To avoid carrying over a silent bug or waiting for the bug to manifest during a model run,
        # there is a need to raise here
        if not os.path.exists(met_file):
            raise FileNotFoundError(f"'{met_file}' rejected because it does not exist on the computer")
        if not os.path.isfile(met_file):
            raise FileNotFoundError(f"'{met_file}' is not a valid file did you forget to add .met at the end?")
        c_wet = model_instance.FileName
        model_instance.FileName = met_file
        if verbose:
            logger.info(f"weather file changed from '{c_wet}' to '{met_file}'")

    def _set_report_vars(self, model_instance, param_values: dict, verbose=False):

        set_event_names = param_values.get('set_event_names')
        report_name = model_instance.Name

        vs = param_values.get("variable_spec")
        if not vs:
            raise ValueError("Please specify a report name using key word 'variable_spec'")
        self.add_report_variable(variable_spec=vs, set_event_names=set_event_names, report_name=report_name)
        if verbose:
            logger.info(f" '{vs}' added to '{report_name}'")

    @staticmethod
    def _set_surface_organic_matter(model_instance, param_values: dict, verbose=False):
        verbose = verbose
        selected_parameters = set(param_values.keys())
        accepted_attributes = {'SurfOM',
                               'InitialCPR', 'InitialResidueMass',
                               'InitialCNR', 'IncorporatedP', }
        dif = selected_parameters - accepted_attributes
        if len(dif) > 0:
            raise AttributeError(f"'{', '.join(dif)}' are not valid attributes for {model_instance.FullPath}")
        for param in selected_parameters:
            if hasattr(model_instance, param):
                setattr(model_instance, param, param_values[param])

            else:
                raise AttributeError(f"suggested attribute {param} is not an attribute of {model_instance}")
        if verbose:
            logger.info(f"successfully set surface organic matter params {param_values}")

    def detect_model_type(self, model_instance: Union[str, Models]):
        """Detects the model type from a given APSIM model instance or path string."""
        if not isinstance(model_instance, str):
            model = model_instance


        else:
            # Otherwise, assume it's a path and try to retrieve the model
            path = model_instance
            try:
                model = self.Simulations.FindByPath(path)
            except AttributeError as e:
                model = get_node_by_path(self.Simulations, path)
            if model is None:
                raise ValueError(f"No model found associated with: {model_instance}")

        model = getattr(model, 'Model', model)
        model_type = model.GetType()
        model = CastHelper.CastAs[model_type](model)
        return model_type

    def edit_model_by_path(self, path: str, **kwargs):
        """
        Edit a model component located by an APSIM path, dispatching to type-specific editors.

        This method resolves a node under `instance.Simulations` using an APSIM path, then
        edits that node by delegating to an editor based on the node’s runtime type.
        It supports common APSIM NG components (e.g., Weather, Manager, Cultivar, Clock,
        Soil subcomponents, Report, SurfaceOrganicMatter). Unsupported types raise
        :class:`NotImplementedError`.


        Parameters
        ----------
        path : str
            APSIM path to a target node under `self.Simulations` (e.g.,
            '.Simulations.Simulations.Weather' or a similar canonical path).

        kwargs
        ------

        Additional keyword arguments specific to the model type. Atleast one key word argument is required. These vary by component:

        Models.Climate.Weather:
            `weather_file` (str): Path to the weather `.met` file.

        Models.Clock:
            Date properties such as `Start` and `End` in ISO format (e.g., '2021-01-01').

        Models.Manager:
            Variables to update in the Manager script using `update_mgt_by_path`.

        Soils.Physical | Soils.Chemical | Soils.Organic | Soils.Water:
            Variables to replace using `replace_soils_values_by_path`.

            Valid `parameters` are shown below;

            +------------------+--------------------------------------------------------------------------------------------------------------------------------------+
            | Soil Model Type  | **Supported key word arguments**                                                                                                     |
            +==================+======================================================================================================================================+
            | Physical         | AirDry, BD, DUL, DULmm, Depth, DepthMidPoints, KS, LL15, LL15mm, PAWC, PAWCmm, SAT, SATmm, SW, SWmm, Thickness, ThicknessCumulative  |
            +------------------+--------------------------------------------------------------------------------------------------------------------------------------+
            | Organic          | CNR, Carbon, Depth, FBiom, FInert, FOM, Nitrogen, SoilCNRatio, Thickness                                                             |
            +------------------+--------------------------------------------------------------------------------------------------------------------------------------+
            | Chemical         | Depth, PH, Thickness                                                                                                                 |
            +------------------+--------------------------------------------------------------------------------------------------------------------------------------+

        Models.Report:
          report_name (str):
             Name of the report model (optional depending on structure).
          variable_spec`   (list[str] or str):
             Variables to include in the report.
          set_event_names` (list[str], optional):
             Events that trigger the report.

        Models.PMF.Cultivar:
            commands (str):
               APSIM path to the cultivar parameter to update.
            values: (Any)
               Value to assign.
            cultivar_manager: (str)
               Name of the Manager script managing the cultivar, which must contain the `CultivarName` parameter. Required to propagate updated cultivar values, as APSIM treats cultivars as read-only.

        .. warning::

            ValueError
                If the model instance is not found, required kwargs are missing, or `kwargs` is empty.
            NotImplementedError
                If the logic for the specified `model_class` is not implemented.
        Examples
        --------
        Edit a Manager script parameter::

            model.edit_model_by_path(
                ".Simulations.Simulation.Field.Sow using a variable rule",
                verbose=True,
                Population=10)

        Point a Weather component to a new `.met` file::

            model.edit_model_by_path(
                path=".Simulations.Simulation.Weather",
                FileName="data/weather/Ames_2020.met")

        Change Clock dates::

            model.edit_model_by_path(
                ".Simulations.Simulation.Clock",
                StartDate="2020-01-01",
                EndDate="2020-12-31")

        Update soil water properties at a specific path::

            model.edit_model_by_path(
                ".Simulations.Simulation.Field.Soil.Physical",
                LL15="[0.26, 0.18, 0.10, 0.12]")

        Apply cultivar edits::

            model.edit_model_by_path(
                ".Simulations.Simulation.Field.Maize.CultivarFolder.mh18",
                sowed=True,
                **{"Phenology.EmergencePhase.Photo-period": "Short"} )

        .. seealso::

           Related API: :meth:`edit_model`.
        """
        simulations = kwargs.get('simulations', None) or kwargs.get('simulation', None)
        default = kwargs.setdefault('verbose', False)
        verbose = kwargs.get('verbose')
        for p in {'simulation', 'simulations', 'verbose'}:
            kwargs.pop(p, None)
        try:
            v_obj = self.Simulations.FindByPath(path)
        except AttributeError as e:
            v_obj = get_node_by_path(self.Simulations, path)
        if v_obj is None:
            raise ValueError(f"Could not find model instance associated with path `{path}`")
        try:
            values = v_obj.Value
        except AttributeError:
            values = v_obj.Model
            for model_class in {Models.Manager, Models.Climate.Weather,
                                Models.PMF.Cultivar, Models.Clock, Models.Report,
                                Models.Surface.SurfaceOrganicMatter,
                                Models.Soils.Physical, Models.Soils.Chemical, Models.Soils.Organic, Models.Soils.Water,
                                Models.Soils.Solute, Models.WaterModel.WaterBalance,
                                }:
                cast_model = CastHelper.CastAs[model_class](values)

                if cast_model is not None:
                    values = cast_model
                    break

            else:
                raise ValueError(
                    f"Could not find model instance associated with `{path}\n or {path} is not supported by this method")

        match type(values):
            case Models.WaterModel.WaterBalance:
                self.edit_model(Models.WaterModel.WaterBalance, model_name=values.Name, **kwargs)

            case Models.Climate.Weather:
                self._set_weather_path(values, param_values=kwargs, verbose=verbose)
                ...
            case Models.Manager:
                kas = set(kwargs.keys())
                kav = {values.Parameters[i].Key for i in range(len(values.Parameters))}
                dif = kas - kav
                if len(dif) > 0:
                    raise ValueError(f"{kas - kav} is not a valid parameter for {path}")
                # Manager scripts have extra attribute parameters
                if hasattr(values, 'Parameters'):
                    values = values.Parameters
                    for i in range(len(values)):
                        param = values[i].Key
                        if param in kas:
                            param_value = kwargs[param]
                            values[i] = KeyValuePair[String, String](param, f"{param_value}")

                ...
            case Models.PMF.Cultivar:

                # Ensure crop replacements exist under Replacements
                if 'Replacements' not in self.inspect_model('Models.Core.Folder'):
                    for crop_name in self.inspect_model(Models.PMF.Plant, fullpath=False):
                        self.add_crop_replacements(_crop=crop_name)

                kwargs['plant'] = trace_cultivar(self.Simulations, values.Name).get(values.Name)
                commands = kwargs.get('commands')
                if isinstance(commands, dict):
                    commands, pa_values = commands.items()  # no need to extract values
                else:

                    pa_values = kwargs.get('values')
                edit_cultivar_by_path(self, path=path, commands=commands,
                                      values=pa_values, manager_param=kwargs.get('manager_param'),
                                      manager_path=kwargs.get('manager_path'),
                                      sowed=kwargs.get('sowed'), rename=kwargs.get('rename'))
                _edit_in_cultivar(self, model_name=values.Name, simulations=simulations, param_values=kwargs,
                                  verbose=verbose, by_path=True)
                ...
            case Models.Clock:
                self._set_clock_vars(values, param_values=kwargs)
            case Models.Soils.Physical | Models.Soils.Chemical | Models.Soils.Organic | Models.Soils.Water | Models.Soils.Solute:
                self.replace_soils_values_by_path(node_path=path, **kwargs)
            case Models.Report:
                self._set_report_vars(values, param_values=kwargs, verbose=verbose)
            case Models.Surface.SurfaceOrganicMatter:
                if kwargs == {}:
                    raise ValueError(f"Please supply at least one parameter: value \n '{', '.join({'SurfOM',
                                                                                                   'InitialCPR', 'InitialResidueMass',
                                                                                                   'InitialCNR', 'IncorporatedP', })}' for {path}")
                self._set_surface_organic_matter(values, param_values=kwargs, verbose=verbose)
            case _:
                raise NotImplementedError(f"No edit method implemented for model type {type(values)}")

        return self

    def add_base_replacements(self):
        """
        Add base replacements with all available models of type Plants and then start from there to add more
        @return: self
        """

        if not self.get_replacements_node():
            folder = Models.Core.Folder()
            folder.Name = 'Replacements'
            self.Simulations.Children.Add(folder)
            self.save()
        available_crops = self.inspect_model(Models.PMF.Plant, fullpath=False)
        rep = self.get_replacements_node()
        existing = {
            child.Name
            for child in rep.Children
            if isinstance(child, Models.PMF.Plant)
        }
        for crop in available_crops:
            if crop not in existing:
                crop_model = Models.PMF.Plant()
                crop_model.Name = crop
                crop_model.ResourceName = crop
                rep.Children.Add(crop_model)

        self.save()
        return self

    def edit_model(self, model_type: str, model_name: str,
                   simulations: Union[str, list] = 'all', exclude=None,
                   verbose=False, **kwargs):
        """
        Modify various APSIM model components by specifying the model type and name across given simulations.

        .. tip::

           Editing APSIM models in **apsimNGpy** does *not* require placing the
           target model inside a *Replacements* folder or node. However, when
           modifying **cultivar parameters**, it can be helpful to include a
           Replacements folder containing the relevant plant definition hosting
           that cultivar. In many cases, apsimNGpy will handle this automatically.

        Selective Editing
        -----------------
        Selective editing allows you to apply modifications only to certain
        simulations. This is *not* possible when the same model instance is shared
        through a common Replacements folder. For reliable selective editing,
        each simulation should ideally reference a uniquely named model.
        However, even when model names are not unique, apsimNGpy still enables
        targeted editing through two mechanisms:

        1. **Exclusion strategy**
           You can explicitly *exclude* simulations to which the edits should
           **not** be applied.

        2. **Specification strategy**
           You can explicitly *specify* which simulations should have their
           models edited or replaced with new parameters.


        Parameters
        ----------
        model_type: str, required
            Type of the model component to modify (e.g., 'Clock', 'Manager', 'Soils.Physical', etc.).

        simulations: Union[str, list], optional
            A simulation name or list of simulation names in which to search. Defaults to all simulations in the model.

        model_name: str, required
            Name of the model instance to modify.
        verbose: bool, optional
            print the status of the editing activities
        exclude: Union[str, None, Iterable[str]], optional,default is None
            Added in 'V0.39.10.20'+. It is used to specify which simulation should be skipped during the editing process, in case there are more than simulations

        kwargs
        ------

        Additional keyword arguments specific to the model type. Atleast one key word argument is required. These vary by component:

        Models.Climate.Weather:
            `weather_file` (str): Path to the weather `.met` file.

        Models.Clock:
            Date properties such as `Start` and `End` in ISO format (e.g., '2021-01-01').

        Models.Manager:
            Variables to update in the Manager script using `update_mgt_by_path`.

        Soils.Physical | Soils.Chemical | Soils.Organic | Soils.Water:
            Variables to replace using `replace_soils_values_by_path`.

            Valid `parameters` are shown below;

            +------------------+--------------------------------------------------------------------------------------------------------------------------------------+
            | Soil Model Type  | **Supported key word arguments**                                                                                                     |
            +==================+======================================================================================================================================+
            | Physical         | AirDry, BD, DUL, DULmm, Depth, DepthMidPoints, KS, LL15, LL15mm, PAWC, PAWCmm, SAT, SATmm, SW, SWmm, Thickness, ThicknessCumulative  |
            +------------------+--------------------------------------------------------------------------------------------------------------------------------------+
            | Organic          | CNR, Carbon, Depth, FBiom, FInert, FOM, Nitrogen, SoilCNRatio, Thickness                                                             |
            +------------------+--------------------------------------------------------------------------------------------------------------------------------------+
            | Chemical         | Depth, PH, Thickness                                                                                                                 |
            +------------------+--------------------------------------------------------------------------------------------------------------------------------------+

        Models.Report:
          report_name (str):
             Name of the report model (optional depending on structure).
          variable_spec`   (list[str] or str):
             Variables to include in the report.
          set_event_names` (list[str], optional):
             Events that trigger the report.

        Models.PMF.Cultivar:
            commands (str):
               APSIM path to the cultivar parameter to update.
            values: (Any)
               Value to assign.
            cultivar_manager: (str)
               Name of the Manager script managing the cultivar, which must contain the `CultivarName` parameter. Required to propagate updated cultivar values, as APSIM treats cultivars as read-only.

        .. warning::

            ValueError
                If the model instance is not found, required kwargs are missing, or `kwargs` is empty.
            NotImplementedError
                If the logic for the specified `model_class` is not implemented.

        Examples::

            from apsimNGpy.core.apsim import ApsimModel
            model = ApsimModel(model='Maize')

        Example of how to edit a cultivar model::

            model.edit_model(model_type='Cultivar',
                 simulations='Simulation',
                 commands='[Phenology].Juvenile.Target.FixedValue',
                 values=256,
                 model_name='B_110',
                 new_cultivar_name='B_110_edited',
                 cultivar_manager='Sow using a variable rule')

        Edit a soil organic matter module::

            model.edit_model(
                 model_type='Organic',
                 simulations='Simulation',
                 model_name='Organic',
                 Carbon=1.23)

        Edit multiple soil layers::

            model.edit_model(
                 model_type='Organic',
                 simulations='Simulation',
                 model_name='Organic',
                 Carbon=[1.23, 1.0])

        Example of how to edit solute models::

           model.edit_model(
                 model_type='Solute',
                 simulations='Simulation',
                 model_name='NH4',
                 InitialValues=0.2)
           model.edit_model(
                model_class='Solute',
                simulations='Simulation',
                model_name='Urea',
                InitialValues=0.002)

        Edit a manager script::

           model.edit_model(
                model_type='Manager',
                simulations='Simulation',
                model_name='Sow using a variable rule',
                population=8.4)

        Edit surface organic matter parameters::

            model.edit_model(
                model_type='SurfaceOrganicMatter',
                simulations='Simulation',
                model_name='SurfaceOrganicMatter',
                InitialResidueMass=2500)

            model.edit_model(
                model_type='SurfaceOrganicMatter',
                simulations='Simulation',
                model_name='SurfaceOrganicMatter',
                InitialCNR=85)

        Edit Clock start and end dates::

            model.edit_model(
                model_type='Clock',
                simulations='Simulation',
                model_name='Clock',
                Start='2021-01-01',
                End='2021-01-12')

        Edit report _variables::

            model.edit_model(
                model_type='Report',
                simulations='Simulation',
                model_name='Report',
                variable_spec='[Maize].AboveGround.Wt as abw')

        Multiple report _variables::

            model.edit_model(
                model_type='Report',
                simulations='Simulation',
                model_name='Report',
                variable_spec=[
                '[Maize].AboveGround.Wt as abw',
                '[Maize].Grain.Total.Wt as grain_weight'])
        the best way to edit cultivar with minimal error is to use a dict of commands as follows.

        .. code-block:: python

             params = {
            "[Leaf].Photosynthesis.RUE.FixedValue": 1.8984705340394,
            "[Phenology].GrainFilling.Target.FixedValue": 710,
            "[Grain].MaximumGrainsPerCob.FixedValue": 810,
            "[Phenology].FloweringToGrainFilling.Target.FixedValue": 215,
            "[Phenology].MaturityToHarvestRipe.Target.FixedValue": 100,
            "[Maize].Grain.MaximumPotentialGrainSize.FixedValue": 0.867411373063701,
            "[Grain].MaximumNConc.InitialPhase.InitialNconc.FixedValue": 0.05,
            '[Maize].Root.SpecificRootLength.FixedValue': 135,
            '[Maize].Root.RootFrontVelocity.PotentialRootFrontVelocity.PreFlowering.RootFrontVelocity.FixedValue': 22,
            '[Rachis].DMDemands.Structural.DMDemandFunction.MaximumOrganWt.FixedValue': 36
        }

        model.edit_model_by_path(model_type='Models.PMF.Cultivar, model_name='Dekalb_XL82',
                                         commands=params,
                                         cultivar_manager='Sow using a variable rule,
                                         parameter_name='CultivarName'
                                         )

        .. seealso::

           Related API: :meth:`edit_model_by_path`.

        """
        if isinstance(exclude, str):
            exclude = {exclude}
        elif not exclude:
            exclude = set()
        if simulations == 'all' or simulations is None or simulations == MissingOption:
            simulations = self.inspect_model('Models.Core.Simulation', fullpath=False)
            simulations = [str(i) for i in simulations if i not in exclude]

        model_type_class = validate_model_obj(model_type)
        replace_ments = self.get_replacements_node()
        edit_candidate_objects = self.find_simulations(simulations)
        # TODO add unittest when replacement node is available
        if replace_ments is not None:
            edit_candidate_objects.append(replace_ments)

            # model_instance = get_or_check_model(sim, model_type_class, model_name, action='get', cacheit=cacheit,
            #                                     cache_size=cache_size)

        def edit_object(obj):
            sim = obj
            if is_higher_apsim_version(self.Simulations):
                model_instance = find_child(sim, model_type_class, model_name)
            else:
                model_instance = sim.FindDescendant[model_type_class](model_name)
            model_to_cast = getattr(model_instance, "Model", model_instance)
            model_instance = CastHelper.CastAs[model_type_class](model_to_cast)
            match type(model_instance):
                case Models.WaterModel.WaterBalance:
                    try:
                        ModelTools.edit_instance(model_instance, **kwargs)
                    except AttributeError as ate:
                        accepted_attributes = self.inspect_settable_attributes(Models.WaterModel.WaterBalance)
                        ap = '\n'.join(accepted_attributes)
                        logger.info(f'some of the accepted attributes are {ap}')
                        raise AttributeError(
                            f"{str(ate)}. Allowed {model_instance} attributes are: {ap}"
                        ) from ate

                case Models.Climate.Weather:
                    self._set_weather_path(model_instance, param_values=kwargs, verbose=verbose)
                case Models.Clock:
                    self._set_clock_vars(model_instance, param_values=kwargs, verbose=verbose)

                case Models.Manager:
                    self.update_manager(scope=sim, manager_name=model_name, **kwargs)

                case Models.Soils.Physical | Models.Soils.Chemical | Models.Soils.Organic | Models.Soils.Water | Models.Soils.Solute:
                    try:
                        ModelTools.edit_instance(model_instance, **kwargs)
                    except AttributeError as ate:
                        lp = [attr[len('set_'):] for attr in dir(model_instance) if attr.startswith('set_')]
                        accepted_attributes = '\n'.join(lp)
                        logger.info(f'some of the accepted attributes are {accepted_attributes}')
                        raise AttributeError(
                            f"{str(ate)}. Allowed {model_instance} attributes are: {accepted_attributes}"
                        ) from ate
                    # self.replace_soils_values_by_path(node_path=model_instance.FullPath, **kwargs)
                case Models.Surface.SurfaceOrganicMatter:
                    try:
                        ModelTools.edit_instance(model_instance, **kwargs)
                    except AttributeError as ate:
                        accepted_attributes = self.inspect_settable_attributes(Models.Surface.SurfaceOrganicMatter)
                        accept = "\n".join(accepted_attributes)
                        logger.info(f'some of the accepted attributes are {accept}')
                        raise AttributeError(
                            f"{str(ate)}. Allowed {model_instance} attributes are: {accept}"
                        ) from ate
                    # self._set_surface_organic_matter(model_instance, param_values=kwargs, verbose=verbose)

                case Models.Report:
                    self._set_report_vars(model_instance, param_values=kwargs, verbose=verbose)

                case Models.MicroClimate:
                    try:
                        ModelTools.edit_instance(model_instance, **kwargs)
                    except AttributeError as e:
                        attribs = self.inspect_settable_attributes(model_type=Models.MicroClimate)
                        at = ', '.join(attribs)

                        # Log helpful information BEFORE raising the error
                        logger.error(
                            f"Invalid attribute in MicroClimate model. "
                            f"Allowed attributes include: {at}"
                        )

                        # Re-raise with additional context
                        raise AttributeError(
                            f"{str(e)}. Allowed MicroClimate attributes are: {at}"
                        ) from e

                case Models.PMF.Cultivar:

                    # Ensure crop replacements exist under Replacements
                    if 'Replacements' not in self.inspect_model('Models.Core.Folder', fullpath=False):
                        for crop_name in self.inspect_model(Models.PMF.Plant, fullpath=False):
                            self.add_crop_replacements(_crop=crop_name)

                    _cultivar_names = self.inspect_model('Cultivar', fullpath=False)

                    # Extract input parameters
                    commands = kwargs.get("commands")
                    if isinstance(commands, dict):
                        commands, values = commands.items()
                    else:
                        values = kwargs.get("values")

                    cultivar_manager = kwargs.get("cultivar_manager")
                    new_cultivar_name = kwargs.get("new_cultivar_name", None)
                    cultivar_manager_param = kwargs.get("parameter_name", 'CultivarName')

                    plant_name = (kwargs.get('plant') or
                                  trace_cultivar(self.Simulations, model_name).get(model_name))

                    # Input validation
                    if not new_cultivar_name:
                        new_cultivar_name = f"{model_name}-{plant_name}-edited01"

                    if not cultivar_manager:
                        raise ValueError("Please specify a cultivar manager using 'cultivar_manager=\"your_manager\"'")

                    evaluate_commands_and_values_types(commands=commands, values=values)

                    # Get replacement folder and source cultivar model
                    replacements = get_or_check_model(self.Simulations, Models.Core.Folder, 'Replacements',
                                                      action='get')

                    get_or_check_model(replacements, Models.Core.Folder, 'Replacements',
                                       action='delete')
                    cultivar_fallback = get_or_check_model(self.Simulations, Models.PMF.Cultivar, model_name,
                                                           action='get')
                    cultivar = ModelTools.CLONER(cultivar_fallback)

                    # Update cultivar parameters
                    cultivar_params = self._cultivar_params(cultivar)

                    if isinstance(values, str):
                        cultivar_params[commands] = values.strip()
                    elif isinstance(values, (int, float)):
                        cultivar_params[commands] = values
                    else:
                        for cmd, val in zip(commands, values):
                            cultivar_params[cmd.strip()] = val.strip() if isinstance(val, str) else val

                    # Apply updated commands
                    updated_cmds = [f"{k.strip()}={v}" for k, v in cultivar_params.items()]
                    cultivar = CastHelper.CastAs[Models.PMF.Cultivar](cultivar)
                    cultivar.set_Command(updated_cmds)

                    # Attach cultivar under a plant model
                    try:
                        plant_model = get_or_check_model(replacements, Models.PMF.Plant, plant_name,
                                                         action='get')
                    except ValueError:
                        pl_model = find_child(parent=replacements, child_class=Models.PMF.Plant, child_name='Maize')
                        plant_model = pl_model

                    # Remove existing cultivar with same name
                    get_or_check_model(replacements, Models.PMF.Cultivar, new_cultivar_name, action='delete')

                    # Rename and reattach cultivar
                    cultivar.Name = new_cultivar_name
                    ModelTools.ADD(cultivar, plant_model)

                    # Update cultivar manager script
                    self.edit_model(model_type=Models.Manager, model_name=cultivar_manager, simulations=simulations,
                                    **{cultivar_manager_param: new_cultivar_name})

                    self.save()

                    if verbose:
                        logger.info(f"Edited Cultivar '{model_name}' and saved it as '{new_cultivar_name}'")

                case _:
                    if not model_instance and not replace_ments:
                        raise ValueError(f"{model_name} of class {model_type} was not found or does not exist in the "
                                         f"current simulations")
                    if not replace_ments and not isinstance(model_type, Models.Core.Folder):
                        raise NotImplementedError(f"No edit method implemented for model type {type(model_instance)}")

        for _ in map(edit_object, edit_candidate_objects):
            pass

        self.ran_ok = False
        return self

    @staticmethod
    def inspect_settable_attributes(model_type):
        """
        Inspect and return all settable attributes for a given APSIM model type.

        This method identifies which attributes of a model can be modified by
        the user. APSIM model classes typically expose writable parameters through
        setter methods following the naming convention ``set_<AttributeName>()``.
        This function extracts all such attributes and returns them in a clean,
        user-friendly list.

        Added in v0.39.12.21

        Parameters
        ----------
        model_type : type or str
            The APSIM model class or the registered model name. This value is
            validated and resolved to a concrete APSIM model class via
            :func:`validate_model_obj`.

        Returns
        -------
        list of str
            A list of attribute names that can be set on the specified model.
            These correspond to all public APSIM parameters for which a
            ``set_<AttributeName>`` method exists. The ``set_`` prefix is removed
            for clarity, so the list contains clean parameter names.

        Notes
        -----
        - This method does *not* set or modify any attributes—its purpose is
          diagnostic and introspective.
        - Useful for error reporting, documentation, and informing users which
          parameters are valid inputs for :meth:`edit_model` or related methods.

        Examples
        --------
        .. code-block:: python

            from apsimNGpy.core.apsim import ApsimModel
            sm = ApsimModel('Maize')
            sm.inspect_settable_attributes(model_type='Models.Surface.SurfaceOrganicMatter')

        .. code-block:: none

            ['Canopies', 'Children', 'Enabled', 'InitialCNR', 'InitialCPR', 'InitialResidueMass', 'InitialResidueName', 'InitialResidueType',
             'InitialStandingFraction', 'IsHidden', 'Name', 'Node', 'Parent', 'ReadOnly', 'ResourceName', 'Structure']

        .. code-block:: python

              sm.inspect_settable_attributes(Models.WaterModel.WaterBalance)

        .. code-block:: none

            ['CN2Bare', 'CNCov', 'CNRed', 'CatchmentArea', 'Children', 'Depth', 'DiffusConst', 'DiffusSlope', 'DischargeWidth',
            'Enabled', 'Eo', 'IsHidden', 'KLAT', 'Name', 'Node', 'PSIDul', 'Parent', 'PoreInteractionIndex', 'PotentialInfiltration', 'PrecipitationInterception', 'ReadOnly', 'ResourceName', 'Runon', 'SW', 'SWCON', 'Salb', 'Structure', 'SummerCona', 'SummerDate', 'SummerU', 'Thickness', 'Water', 'WaterTable', 'WinterCona', 'WinterDate', 'WinterU']
        """
        model_type_class = validate_model_obj(model_type)
        mc = model_type_class()
        lp = [attr[len('set_'):] for attr in dir(mc) if attr.startswith('set_')]
        return lp

    def _get_report(self, report_name, parent):
        """just fetches the report from the simulations database """
        if not is_higher_apsim_version(self.Simulations):
            if report_name:
                get_report = ModelTools.find_child(parent, Models.Report, report_name)
                # get_report = self.Simulations.FindDescendant[Models.Report](report_name)
            else:
                get_report = parent.FindDescendant[Models.Report]()
        else:
            if report_name:
                get_report = ModelTools.find_child(parent, Models.Report, report_name)
            else:
                get_report = ModelTools.find_child_of_class(parent, Models.Report)
        get_report = CastHelper.CastAs[Models.Report](get_report)
        return get_report

    def get_replacements_node(self):
        # don't raise when not found, should be decided at the specific use context
        return ModelTools.find_child(self.Simulations, Models.Core.Folder, child_name='Replacements')

    def find_model_in_replacements(self, model_type, model_name):
        """checks whether the model to be edited is in the replacement, there is no point to contnue editing from individual simulations"""
        replacement = self.get_replacements_node()
        if replacement:
            return ModelTools.find_child(replacement, model_type, child_name=model_name)

    def add_report_variable(self, variable_spec: Union[list, str, tuple], report_name: str = None,
                            set_event_names: Union[str, list] = None, simulations=None):
        """
        This adds a report variable to the end of other _variables, if you want to change the whole report use change_report

        Parameters
        -------------------
        variable_spec: str, required.
            list of text commands for the report _variables e.g., '[Clock].Today as Date'
        param report_name: str, optional.
            Name of the report variable if not specified, the first accessed report object will be altered
        set_event_names: list or str, optional.
            A list of APSIM events that trigger the recording of _variables.
            Defaults to ['[Clock].EndOfYear'] if not provided.

        Returns
        _______
        returns instance of apsimNGpy.core.core.apsim.ApsimModel or apsimNGpy.core.core.apsim.CoreModel

        Raise
        ---------
           raises an `ValueError` if a report is not found

        Examples
        -------------
        >>> from apsimNGpy.core.apsim import ApsimModel
        >>> model = ApsimModel('Maize')
        >>> model.add_report_variable(variable_spec = '[Clock].Today as Date', report_name = 'Report')
        # isnepct the report
        >>> model.inspect_model_parameters(model_type='Models.Report', model_name='Report')
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
              '[Maize].Total.Wt',
              '[Clock].Today as Date']}
        The new report variable is appended at the end of the existing ones

        .. seealso::

            Related APIs: :meth:`remove_report_variable` and :meth:`add_db_table`.
        """
        if report_name is None:
            raise ValueError('report or database table is required via `report_name` parameter')
        sims = self.find_simulations(simulations)
        rep = self.get_replacements_node()
        if rep is not None and self.find_model_in_replacements(model_type=Models.Report, model_name=report_name):
            sims = {rep}
        for sim in sims:
            if isinstance(variable_spec, str):
                variable_spec = [variable_spec]
            get_report = self._get_report(report_name, sim)
            get_cur_variables = list(get_report.VariableNames)
            get_cur_variables.extend(variable_spec)
            # remove any duplicate after appending
            de_duped = list(dict.fromkeys(get_cur_variables))
            get_cur_variables = de_duped
            final_command = "\n".join(get_cur_variables)
            get_report.set_VariableNames(final_command.strip().splitlines())
            if set_event_names:
                if isinstance(set_event_names, str):
                    set_event_names = [set_event_names]
                set_event_names = list(set(set_event_names))
                final_command = "\n".join(set_event_names)
                get_report.set_EventNames(final_command.strip().splitlines())

        self.save()

    def remove_report_variable(self,
                               variable_spec: Union[list, tuple, str],
                               report_name: str | None = None):
        """
        Remove one or more variable expressions from an APSIM Report component.

        Parameters
        ----------
        variable_spec : str | list[str] | tuple[str, ...]
            Variable expression(s) to remove, e.g. ``"[Clock].Today"`` or
            ``"[Clock].Today as Date"``. You may pass a single string or a list/tuple.
            Matching is done by exact text **after whitespace normalization**
            (consecutive spaces collapsed), so minor spacing differences are tolerated.
        report_name : str, optional
            Name of the Report component to modify. If ``None``, the default
            resolver (``self._get_report``) is used to locate the target report.

        Returns
        -------
        list[str]
            The updated list of variable expressions remaining in the report
            (in original order, without duplicates).

        Notes
        -----
        - Variables not present are ignored (no error raised).
        - Order is preserved; duplicates are removed.
        - The model is saved at the end of this call.

        Examples
        --------
        >>> model= CoreModel('Maize')
        >>> model.add_report_variable(variable_spec='[Clock].Today as Date', report_name='Report')
        >>> model.inspect_model_parameters('Models.Report', 'Report')['VariableNames']
        ['[Clock].Today',
         '[Maize].Phenology.CurrentStageName',
         '[Maize].AboveGround.Wt',
         '[Maize].AboveGround.N',
         '[Maize].Grain.Total.Wt*10 as Yield',
         '[Maize].Grain.Wt',
         '[Maize].Grain.Size',
         '[Maize].Grain.NumberFunction',
         '[Maize].Grain.Total.Wt',
         '[Maize].Grain.N',
         '[Maize].Total.Wt',
         '[Clock].Today as Date']
        >>> model.remove_report_variable(variable_spec='[Clock].Today as Date', report_name='Report')
        >>> model.inspect_model_parameters('Models.Report', 'Report')['VariableNames']
        ['[Clock].Today',
         '[Maize].Phenology.CurrentStageName',
         '[Maize].AboveGround.Wt',
         '[Maize].AboveGround.N',
         '[Maize].Grain.Total.Wt*10 as Yield',
         '[Maize].Grain.Wt',
         '[Maize].Grain.Size',
         '[Maize].Grain.NumberFunction',
         '[Maize].Grain.Total.Wt',
         '[Maize].Grain.N',
         '[Maize].Total.Wt']

        .. seealso::

            Related APIs: :meth:`add_report_variable` and :meth:`add_db_table`.
        """

        # Normalize input to a list
        if isinstance(variable_spec, str):
            to_remove = [variable_spec]
        else:
            to_remove = list(variable_spec)

        # Whitespace-normalize for comparison
        def _norm(s: str) -> str:
            return " ".join(str(s).split())

        remove_set = {_norm(s) for s in to_remove}

        # Locate report and get current variables
        report = self._get_report(report_name, self.Simulations)
        cur_vars = list(report.VariableNames or [])

        # De-duplicate while preserving order
        cur_vars = list(dict.fromkeys(cur_vars))

        # Keep those not slated for removal (compare on a normalized text)
        kept = [v for v in cur_vars if _norm(v) not in remove_set]

        # Update the report; setter may accept a list directly
        report.set_VariableNames(kept)

        # Persist changes
        self.save()

        return self

    def remove_model(self, model_type: Models, model_name):
        """
       Removes a model from the APSIM Models.Simulations namespace.

        Parameters
        ----------
        model_type: Models
            The type of the model to remove (e.g., `Models.Clock`). This parameter is required.

        model_name: str, optional
            The name of the specific model instance to remove (e.g., `"Clock"`). If not provided, all models of the
            specified type may be removed.

        Returns:

           None

        Example::

               from apsimNGpy import core
               from apsimNGpy.core.core import Models
               model = core.base_data.load_default_simulations(crop = 'Maize')
               model.remove_model(Models.Clock) #deletes the clock node
               model.remove_model(Models.Climate.Weather) #deletes the weather node

        .. seealso::

            Related APIs: :meth:`clone_model` and :meth:`add_model`.
        """
        model_class = validate_model_obj(model_type)
        if not model_name:
            model_name = model_class().Name
        to_remove = ModelTools.find_child(self.Simulations, child_class=model_class, child_name=model_name)
        if to_remove:
            try:
                ModelTools.DELETE(to_remove)
            except AttributeError:
                pass
        self.save()

    def move_model(self, model_type: Models, new_parent_type: Models, model_name: str = None,
                   new_parent_name: str = None, verbose: bool = False, simulations: Union[str, list] = None):
        """
        Args:
        -----

        model_type:  Models
            type of model tied to Models Namespace

        new_parent_type: Models.
            New model parent type (Models)

        model_name: str
             Name of the model e.g., Clock, or Clock2, whatever name that was given to the model

        new_parent_name``:  str
           The new parent names =Field2, this field is optional but important if you have nested simulations

        Returns:
        ---------
          returns instance of apsimNGpy.core.core.apsim.ApsimModel or apsimNGpy.core.core.apsim.CoreModel

        """
        sims = self.Simulations

        model_type = validate_model_obj(model_type)
        new_parent_type = validate_model_obj(new_parent_type)
        if model_type == Models.Core.Simulations:
            raise ValueError(
                'Can not move a model of type "Models.Core.Simulations". Did you mean Models.Core.Simulation or Simulation?')
        if not model_name:
            model_name = model_type().Name

        child_to_move = get_or_check_model(sims, model_type, model_name,
                                           action='get')  # sims.FindInScope[model_class](model_name)
        if not new_parent_name:
            new_parent_name = new_parent_type().Name

        new_parent = get_or_check_model(sims, new_parent_type, new_parent_name, action='get')

        ModelTools.MOVE(child_to_move, new_parent)
        if verbose:
            logger.info(f"Moved {child_to_move.Name} to {new_parent.Name}")
        self.save()

    def _rename_model(self, model_type: Models, old_model_name: str, new_model_name: str, simulations=None):
        """
         give new name to a model in the simulations.

         model_class``: (Models) Models types e.g., Models.Clock.

         old_model_name: (str)
            current model name.

         new_model_name: (str)
             new model name.

         simulation: (str, optional)
              defaults to all simulations.

         returns``: None

        Example::

               from apsimNGpy import core
               from apsimNGpy.core.core import Models
               apsim = core.base_data.load_default_simulations(crop = 'Maize')
               apsim = apsim._rename_model(Models.Clock, 'Clock', 'clock')

        """
        model_type = validate_model_obj(model_type)

        def _rename(_sim):
            # __sim = _sim.FindInScope[model_class](old_model_name)
            __sim = get_or_check_model(self.Simulations, model_type=model_type, model_name=old_model_name, action='get')
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

    def replicate_file(self, k: int, path: os.PathLike = None, suffix: str = "replica"):
        """
        Replicates a file ``k`` times.
        Parameters
        ----------
        path:str default is None
          If specified, the copies will be placed in that dir_path with incremented filenames.
          If no path is specified, copies are created in the same dir_path as the original file, also with incremented filenames.

        k int:
           The number of copies to create.

        - suffix: str, optional
            a suffix to attach with the copies. Default to "replicate"

        Returns:
        -------
        - A  generator(str) is returned.
        """
        if path is None:
            file_name = self.path.rsplit('.apsimx', 1)[0]
            return [shutil.copy(self.model_info.path, f"{file_name}_{i}_{suffix}.apsimx") for i in range(k)]

        else:
            b_name = os.path.basename(self.path).rsplit('.apsimx', 1)[0]
            return (shutil.copy(self.model_info.path, os.path.join(path, f"{b_name}_{suffix}_{i}.apsimx")) for i in
                    range(k))


    def _cultivar_params(self, cultivar):
        """
         returns all params in a cultivar
        """
        cultivar = CastHelper.CastAs[Models.PMF.Cultivar](cultivar)
        cmd = cultivar.Command
        params = {}
        for c in cmd:
            if c:
                p, v = c.split("=")
                params[p.strip()] = v.strip()
        return params

    def _find_replacement(self):
        rep = self.get_replacements_node()
        return rep

    def _find_cultivar(self, cultivar_name: str):
        if APSIM_VERSION_NO > BASE_RELEASE_NO or APSIM_VERSION_NO == GITHUB_RELEASE_NO:
            cultivars = ModelTools.find_all_in_scope(self._find_replacement(), Models.PMF.Cultivar)
        else:

            cultivars = self._find_replacement().FindAllDescendants[Models.PMF.Cultivar]()
        xp = [i for i in cultivars]
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

        rep = self.get_replacements_node()
        if rep:
            crop_rep = ModelTools.find_child(rep, Models.PMF.Plant, Crop)
            for i in crop_rep:
                logger.info(i.Name)
                if i.Name == Crop:
                    return i

        return self

    def inspect_model_parameters(self, model_type: Union[Models, str], model_name: str,
                                 simulations: Union[str, list] = MissingOption,
                                 parameters: Union[list, set, tuple, str] = 'all',
                                 exclude: list | set | tuple | str = None, **kwargs):
        """
        Inspect the input parameters of a specific ``APSIM`` model type instance within selected simulations.

        This method consolidates functionality previously spread across ``examine_management_info``, ``read_cultivar_params``, and other inspectors,
        allowing a unified interface for querying parameters of interest across a wide range of APSIM models.

        Parameters
        ----------
        model_type: str required
            The name of the model class to inspect (e.g., 'Clock', 'Manager', 'Physical', 'Chemical', 'Water', 'Solute').
            Shorthand names are accepted (e.g., 'Clock', 'Weather') as well as fully qualified names (e.g., 'Models.Clock', 'Models.Climate.Weather').

        simulations: Union[str, list]
            A single simulation name or a list of simulation names within the APSIM context to inspect.

        model_name: str
            The name of the specific model instance within each simulation. For example, if `model_class='Solute'`,
            `model_name` might be 'NH4', 'Urea', or another solute name.

        parameters: Union[str, set, list, tuple], optional
            A specific parameter or a collection of parameters to inspect. Defaults to `'all'`, in which case all accessible attributes are returned.
            For layered models like Solute, valid parameters include `Depth`, `InitialValues`, `SoluteBD`, `Thickness`, etc.
        exclude: Union[str, list, tuple], optional
            used to exclude a few simulations and include only the rest of the simulations
            Added in v0.39.10.20+

        kwargs:
            Reserved for future compatibility; currently unused.

        Returns
        ----------
            Union[dict, list, pd.DataFrame, Any]
            The format depends on the model type as shown below:
        Weather:
               file path(s) as string(s)

        Clock:
           dictionary with start and end datetime objects (or a single datetime if only one is requested).

        Manager:
           dictionary of script parameters.

        Soil-related:
            pandas DataFrame of layered values.

        Report:
         A dictionary with `VariableNames` and `EventNames`.

        Cultivar:
        dictionary of parameter strings.

        Raises
        ------
        ``ValueError``
            If the specified model or simulation is not found or arguments are invalid.

        ``NotImplementedError``
            If the model type is unsupported by the current interface.


        Requirements
        --------------
        - APSIM Next Generation Python bindings (`apsimNGpy`)
        - Python 3.10+

        Examples::

           from apsimNGpy.core.apsim import ApsimModel
           model_instance = ApsimModel('Maize')

        Inspect full soil `Organic` profile::

            model_instance.inspect_model_parameters('Organic', simulations='Simulation', model_name='Organic')
               CNR  Carbon      Depth  FBiom  ...         FOM  Nitrogen  SoilCNRatio  Thickness
            0  12.0    1.20      0-150   0.04  ...  347.129032     0.100         12.0      150.0
            1  12.0    0.96    150-300   0.02  ...  270.344362     0.080         12.0      150.0
            2  12.0    0.60    300-600   0.02  ...  163.972144     0.050         12.0      300.0
            3  12.0    0.30    600-900   0.02  ...   99.454133     0.025         12.0      300.0
            4  12.0    0.18   900-1200   0.01  ...   60.321981     0.015         12.0      300.0
            5  12.0    0.12  1200-1500   0.01  ...   36.587131     0.010         12.0      300.0
            6  12.0    0.12  1500-1800   0.01  ...   22.191217     0.010         12.0      300.0
            [7 rows x 9 columns]

        Inspect soil `Physical` profile::

            model_instance.inspect_model_parameters('Physical', simulations='Simulation', model_name='Physical')
                AirDry        BD       DUL  ...        SWmm Thickness  ThicknessCumulative
            0  0.130250  1.010565  0.521000  ...   78.150033     150.0                150.0
            1  0.198689  1.071456  0.496723  ...   74.508522     150.0                300.0
            2  0.280000  1.093939  0.488438  ...  146.531282     300.0                600.0
            3  0.280000  1.158613  0.480297  ...  144.089091     300.0                900.0
            4  0.280000  1.173012  0.471584  ...  141.475079     300.0               1200.0
            5  0.280000  1.162873  0.457071  ...  137.121171     300.0               1500.0
            6  0.280000  1.187495  0.452332  ...  135.699528     300.0               1800.0
            [7 rows x 17 columns]

        Inspect soil `Chemical` profile::

            model_instance.inspect_model_parameters('Chemical', simulations='Simulation', model_name='Chemical')
               Depth   PH  Thickness
            0      0-150  8.0      150.0
            1    150-300  8.0      150.0
            2    300-600  8.0      300.0
            3    600-900  8.0      300.0
            4   900-1200  8.0      300.0
            5  1200-1500  8.0      300.0
            6  1500-1800  8.0      300.0

        Inspect one or more specific parameters::

            model_instance.inspect_model_parameters('Organic', simulations='Simulation', model_name='Organic', parameters='Carbon')
              Carbon
            0    1.20
            1    0.96
            2    0.60
            3    0.30
            4    0.18
            5    0.12
            6    0.12

        Inspect more than one specific properties::

            model_instance.inspect_model_parameters('Organic', simulations='Simulation', model_name='Organic', parameters=['Carbon', 'CNR'])
               Carbon   CNR
            0    1.20  12.0
            1    0.96  12.0
            2    0.60  12.0
            3    0.30  12.0
            4    0.18  12.0
            5    0.12  12.0
            6    0.12  12.0

        Inspect Report module attributes::

             model_instance.inspect_model_parameters('Report', simulations='Simulation', model_name='Report')
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

        Specify only EventNames:

           model_instance.inspect_model_parameters('Report', simulations='Simulation', model_name='Report', parameters='EventNames')
           {'EventNames': ['[Maize].Harvesting']}

        Inspect a weather file path::

             model_instance.inspect_model_parameters('Weather', simulations='Simulation', model_name='Weather')
            '%root%/Examples/WeatherFiles/AU_Dalby.met'

        Inspect manager script parameters::

            model_instance.inspect_model_parameters('Manager',
            simulations='Simulation', model_name='Sow using a variable rule')
            {'Crop': 'Maize',
            'StartDate': '1-nov',
            'EndDate': '10-jan',
            'MinESW': '100.0',
            'MinRain': '25.0',
            'RainDays': '7',
            'CultivarName': 'Dekalb_XL82',
            'SowingDepth': '30.0',
            'RowSpacing': '750.0',
            'Population': '10'}
        Inspect manager script by specifying one or more parameters::

            model_instance.inspect_model_parameters('Manager',
            simulations='Simulation', model_name='Sow using a variable rule',
            parameters='Population')
            {'Population': '10'}

        Inspect cultivar parameters::

            model_instance.inspect_model_parameters('Cultivar',
            simulations='Simulation', model_name='B_110') # lists all path specifications for B_110 parameters abd their values
            model_instance.inspect_model_parameters('Cultivar', simulations='Simulation',
            model_name='B_110', parameters='[Phenology].Juvenile.Target.FixedValue')
            {'[Phenology].Juvenile.Target.FixedValue': '210'}

        Inspect surface organic matter module::

            model_instance.inspect_model_parameters('Models.Surface.SurfaceOrganicMatter',
            simulations='Simulation', model_name='SurfaceOrganicMatter')
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

        Inspect a few parameters as needed::

            model_instance.inspect_model_parameters('Models.Surface.SurfaceOrganicMatter', simulations='Simulation',
            ... model_name='SurfaceOrganicMatter', parameters={'InitialCNR', 'InitialResidueMass'})
            {'InitialCNR': 100.0, 'InitialResidueMass': 500.0}

        Inspect a clock::

             model_instance.inspect_model_parameters('Clock', simulations='Simulation', model_name='Clock')
             {'End': datetime.datetime(2000, 12, 31, 0, 0),
             'Start': datetime.datetime(1990, 1, 1, 0, 0)}

        Inspect a few Clock parameters as needed::

            model_instance.inspect_model_parameters('Clock', simulations='Simulation',
            model_name='Clock', parameters='End')
            datetime.datetime(2000, 12, 31, 0, 0)

        Access specific components of the datetime object e.g., year, month, day, hour, minute::

              model_instance.inspect_model_parameters('Clock', simulations='Simulation',
              model_name='Clock', parameters='Start').year # gets the start year only
              1990

        Inspect solute models::

            model_instance.inspect_model_parameters('Solute', simulations='Simulation', model_name='Urea')
                   Depth  InitialValues  SoluteBD  Thickness
            0      0-150            0.0  1.010565      150.0
            1    150-300            0.0  1.071456      150.0
            2    300-600            0.0  1.093939      300.0
            3    600-900            0.0  1.158613      300.0
            4   900-1200            0.0  1.173012      300.0
            5  1200-1500            0.0  1.162873      300.0
            6  1500-1800            0.0  1.187495      300.0

            model_instance.inspect_model_parameters('Solute', simulations='Simulation', model_name='NH4',
            parameters='InitialValues')
                InitialValues
            0 0.1
            1 0.1
            2 0.1
            3 0.1
            4 0.1
            5 0.1
            6 0.1

        .. seealso::

            Related API: :meth:`inspect_model_parameters_by_path`
        """
        exclude = {exclude} if isinstance(exclude, str) or exclude is None else exclude
        if parameters == 'all':
            parameters = None
        if simulations == MissingOption or simulations is None or simulations == 'all':
            simulations = self.inspect_model(model_type='Models.Core.Simulation', fullpath=False)
            simulations = [str(sim) for sim in simulations if str(sim) not in exclude]
            simulations = simulations[0] if len(simulations) == 1 else simulations

        return inspect_model_inputs(self, model_type=model_type, model_name=model_name, simulations=simulations,
                                    parameters=parameters, **kwargs)

    def inspect_model_parameters_by_path(self, path, *,
                                         parameters: Union[list, set, tuple, str] = None):
        """
        Inspect and extract parameters from a model component specified by its path.

        Parameters:
        -------------
        path: str required
           The path relative to the Models.Core.Simulations Node

        parameters: Union[str, set, list, tuple], optional
            A specific parameter or a collection of parameters to inspect. Defaults to `'all'`, in which case all accessible attributes are returned.
            For layered models like Solute, valid parameters include `Depth`, `InitialValues`, `SoluteBD`, `Thickness`, etc.

        kwargs:
            Reserved for future compatibility; currently unused.

        Returns
        ----------
            Union[dict, list, pd.DataFrame, Any]
            The format depends on the model type as shown below:
        Weather:
               file path(s) as string(s)

        Clock:
           dictionary with start and end datetime objects (or a single datetime if only one is requested).

        Manager:
           dictionary of script parameters.

        Soil-related:
            pandas DataFrame of layered values.

        Report:
         A dictionary with `VariableNames` and `EventNames`.

        Cultivar:
        dictionary of parameter strings.

        Raises
        ------
        ``ValueError``
            If the specified model or simulation is not found or arguments are invalid.

        ``NotImplementedError``
            If the model type is unsupported by the current interface.

        Requirements
        --------------
        - APSIM Next Generation Python bindings (`apsimNGpy`)
        - Python 3.10+

       .. seealso::

            Related API: :meth:`inspect_model_parameters`
            Others: :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_model`, :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_file`
        """
        from apsimNGpy.core.model_tools import extract_value
        try:
            model_by_path = self.Simulations.FindByPath(path)
        except AttributeError as ae:
            model_by_path = get_node_by_path(self.Simulations, path)
        _model_type = self.detect_model_type(path)
        model_by_path = CastHelper.CastAs[_model_type](getattr(model_by_path, "Model", model_by_path))

        mod_obj = model_by_path

        return extract_value(mod_obj, parameters=parameters)

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

        Returns: instance of the class CoreModel or ApsimModel

        Example::

            ('[Grain].MaximumGrainsPerCob.FixedValue', '[Phenology].GrainFilling.Target.FixedValue')

          - values: values for each command (e.g., (721, 760)).



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

    def run2(self, simulations='all', clean=True, verbose=True, multithread=True):
        self.run_method = run_p
        run_p(self.path)
        return self

    def update_cultivar(self, *, parameters: dict, simulations: Union[list, tuple] = None, clear=False, **kwargs):
        """Update cultivar parameters

        Parameters
        ----------
       parameters:  (dict, required)
          dictionary of cultivar parameters to update.

       simulations : str optional
            List or tuples of simulation names to update if `None` update all simulations.

       clear (bool, optional)
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
        ``out_path``: os.PathLike object this method is called to convert the simulation object from ConverterReturnType to model like object

        ``return:`` self

        """

        try:
            if isinstance(self.Simulations, Models.Core.ApsimFile.Models.Core.ApsimFile.ConverterReturnType):
                self.Simulations = self.Simulations.get_NewModel()
                self.path = out_path or self.path
                self.datastore = self.path.replace("apsimx", 'db')
                self._DataStore = self.Simulations.FindChild[Models.Storage.DataStore]()
        except AttributeError:
            pass
        return self

    def update_mgt_by_path(self, *, path: str, fmt='.', **kwargs):
        """
        Parameters
        __________
        path: str
            A complete node path to the script manager e.g. '.Simulations.Simulation.Field.Sow using a variable rule'
        fmt: str
            seperator for formatting the path e.g., ".". Other characters can be used with
            caution, e.g., / and clearly declared in fmt argument. If you want to use the forward slash, it will be '/Simulations/Simulation/Field/Sow using a variable rule', fmt = '/'

        **kwargs:
             Corresponding keyword arguments representing the paramters in the script manager and their values. Values is what you want
             to change to; Example here ``Population`` =8.2, values should be entered with their corresponding data types e.g.,
             int, float, bool,str etc.

        Returns:
        ----------
          Instance of apsimNgpy.core.ApsimModel or apsimNgpy.core.experimentmanager.ExperimentManager

        """
        # old_method('update_mgt_by_path', new_method='edit_model')
        # reject space in fmt
        if fmt != '.':
            path = path.replace(fmt, ".")
        try:
            manager = self.Simulations.FindByPath(path)
        except AttributeError:
            manager = get_node_by_path(self.Simulations, path)

            manager = CastHelper.CastAs[Models.Manager](manager.Model)
        try:
            vp = manager.Value.Parameters
        except AttributeError:

            vp = manager.Parameters
        stack_manager_depth = range(len(vp))

        if kwargs == {}:
            raise ValueError(
                "Please supply parameters and their values as keyword arguments. "
                "These arguments are unique for each script.\n"
                f"In '{path}', the following parameters were found: "
                f"{[vp[i].Key for i in stack_manager_depth]}.\n"
                "You need to specify at least one of them."
            )

        for i in stack_manager_depth:
            _param = vp[i].Key

            if _param in kwargs:
                vp[i] = KeyValuePair[String, String](_param, f"{kwargs[_param]}")
                # remove the successfully processed keys
                kwargs.pop(_param)
        if len(kwargs.keys()) > 0:
            logger.error(f"The following {kwargs} were not found in {path}")
        out_mgt_path = self.path
        self.recompile_edited_model(out_path=out_mgt_path)

        return self

    @property
    def is_recent_version(self):
        return is_higher_apsim_version(self.Simulations)

    def update_manager(self, scope, manager_name, **kwargs):
        if is_higher_apsim_version(self.Simulations):
            manager = ModelTools.find_child(scope, Models.Manager, manager_name)
            manager = CastHelper.CastAs[Models.Manager](manager)
            if not manager:
                raise ModelNotFoundError(f"Models.Manager '{manager_name}' not found")
        else:
            manager = scope.FindDescendant[Models.Manager](manager_name)
        g_parameters = manager.Parameters
        for i in range(len(list(g_parameters))):
            _param = g_parameters[i].Key

            if _param in kwargs:
                manager.Parameters[i] = KeyValuePair[String, String](_param, f"{kwargs[_param]}")
                # remove the successfully processed keys
                kwargs.pop(_param)
        if len(kwargs.keys()) > 0:
            logger.error(f"The following {kwargs} were not found in {manager.FullPath}")

    def exchange_model(self, model, model_type: str, model_name=None, target_model_name=None, simulations: str = None):
        old_method('exchange_model', new_method='replace_model_from')
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
        @deprecated and will be removed
        function has not been maintained for a long time, use it at your own risk

        Replace a model, e.g., a soil model with another soil model from another APSIM model.
        The method assumes that the model to replace is already loaded in the current model and the same class as a source model.
        e.g., a soil node to soil node, clock node to clock node, et.c

        Parameters:
        -----------------
            model: Path to the APSIM model file or a CoreModel instance.

            model_type: (str):
                Class name (as string) of the model to replace (e.g., "Soil").

            model_name: (str, optional)
                Name of the model instance to copy from the source model.
                If not provided, the first match is used.

            target_model_name: (str, optional)
                Specific simulation name to target for replacement.
                Only used when replacing Simulation-level objects.

            simulations (str, optional):
                Simulation(s) to operate on. If None, applies to all.

        Returns:
            self: To allow method chaining.

        Raises:
            ``ValueError``: If ``model_class`` is "Simulations" which is not allowed for replacement.
        """

        # Validate and resolve the model type string into the correct class
        model_type = validate_model_obj(model_type)

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

    def update_mgt(self, *, management: Union[dict, tuple], simulations: [list, tuple] = MissingOption,
                   out: [Path, str] = None,
                   reload: bool = True,
                   **kwargs):
        """
            Update management settings in the model. This method handles one management parameter at a time.

            Parameters
            ----------
            management: dict or tuple
                A dictionary or tuple of management parameters to update. The dictionary should have 'Name' as the key
                for the management script's name and corresponding values to update. Lists are not allowed as they are mutable
                and may cause issues with parallel processing. If a tuple is provided, it should be in the form (param_name, param_value).

            simulations: list of str, optional
                List of simulation names to update. If `None`, updates all simulations. This is not recommended for large
                numbers of simulations as it may result in a high computational load.

            out: str or pathlike, optional
                Path to save the edited model. If `None`, uses the default output path specified in `self.out_path` or
                `self.model_info.path`. No need to call `save_edited_file` after updating, as this method handles saving.

            Returns
            -------
                Returns the instance of the respective model class for method chaining.

            ..note::

                Ensure that the `management` parameter is provided in the correct format to avoid errors. -
                This method does not perform `validation` on the provided `management` dictionary beyond checking for key
                existence. - If the specified management script or parameters do not exist, they will be ignored.

        """

        if isinstance(management, dict):  # To provide support for multiple scripts
            # note the coma creates a tuple
            management = management,

        for sim in self.find_simulations(simulations):
            if is_higher_apsim_version(self.Simulations):
                zone = ModelTools.find_child_of_class(sim, Models.Core.Zone)  # expect one Model.Core.Zone
            else:
                zone = sim.FindChild[Models.Core.Zone]()
            if not zone:
                raise ValueError(f'Models.Core.Zone not found in simulation: {sim.Fullpath}')
            zone_path = zone.FullPath
            for mgt in management:

                action_path = f'{zone_path}.{mgt.get("Name")}'
                try:
                    fp = zone.FindByPath(action_path)

                except AttributeError:

                    fp = get_node_by_path(zone, action_path)
                    fp = CastHelper.CastAs[Models.Manager](fp.Model)

                try:
                    vp = fp.Value.Parameters
                except AttributeError:
                    vp = fp.Parameters
                # before proceeding, we need to check if fp is not None, that is if that script name does not exist
                if fp is not None:
                    values = mgt
                    for i in range(len(vp)):
                        param = vp[i].Key
                        if param in values.keys():
                            vp[i] = KeyValuePair[String, String](param, f"{values[param]}")
                else:
                    raise ValueError(f"invalid manager inputs. Manager not found")
        out_mgt_path = out or self.out_path or self.model_info.path
        self.recompile_edited_model(out_path=out_mgt_path)

        return self

    # immediately open the file in GUI
    def preview_simulation(self, watch=False):
        """
           Open the current simulation in the APSIM Next Gen GUI.

           This first saves the in-memory simulation to ``out_path`` and then launches
           the APSIM Next Gen GUI (via :func:`get_apsim_bin_path`) so you can inspect
           the model tree and make quick edits side by side.

           Parameters
           ----------
           watch : bool, default False
               If True, Python will listen for GUI edits and sync them back into the
               model instance in (near) real time. This feature is experimental.

           Returns
           -------
           None
               This function performs a side effect (opening the GUI) and does not
               return a value.

           Raises
           ------
           FileNotFoundError
               If the file does not exist after ``save()``.
           RuntimeError
               If the APSIM Next Gen executable cannot be located or the GUI fails to start.

           .. tip::

              The file opened in the GUI is a *saved copy* of this Python object.
              Changes made in the GUI are **not** propagated back to the
              :class:`~apsimNGpy.core.apsim.ApsimModel` instance unless you set
              ``watch=True``.
              Otherwise, to continue working in Python with GUI edits, save the file in APSIM
              and re-load it, for example:

              .. code-block:: python

                 ApsimModel("gui_edited_file_path.apsimx")

           Examples
           --------
           **1. Preview only**

           .. code-block:: python

               from apsimNGpy.core.apsim import ApsimModel
               model = ApsimModel("Maize", out_path="test_.apsimx")
               model.preview_simulation()

           .. image:: ../images/gui.png
               :alt: Tree structure of the APSIM model
               :align: center
               :width: 98%
               :name: gui_tree_structure_model

           **2. Preview and edit simultaneously**

           After opening the APSIMX file in the GUI via the watching mode (``watch=True``), you can modify any parameters using GUI interface. The Example given below involved changing parameters such as
           **Plant population (/m²)**, **Cultivar to be sown**, and **Row spacing (mm)**
           in the *Sow using a variable rule* script and finally, checked whether the changes were successful by inspecting the model.

           .. code-block:: python

               model.preview_simulation(watch=True)

           .. image:: ../images/gui_watch_changes.png
               :alt: Tree structure of the APSIM model (watch mode)
               :align: center
               :width: 98%
               :name: gui_tree_structure_model_watch

           **Example console output when** ``watch=True``:

           .. code-block:: none

               2025-10-24 13:05:08,480 - INFO - Watching for GUI edits...
               Save in APSIM to sync back.
               2025-10-24 13:05:08,490 - INFO - Press Ctrl+C in this cell to stop.
               APSIM GUI saved. Syncing model...
               2025-10-24 13:05:24,112 - INFO - Watching terminated successfully.

           .. tip::

               When ``watch=True``, follow the console instructions.
               One critical step is that you **must press** ``Ctrl+C`` to stop watching.

           **Checking if changes were successfully propagated back**

           .. code-block:: python

               model.inspect_model_parameters("Models.Manager", "Sow using a variable rule")

           .. code-block:: none

               {'Crop': '[Maize]',
                'StartDate': '1-nov',
                'EndDate': '10-jan',
                'MinESW': '100',
                'MinRain': '25',
                'RainDays': '7',
                'CultivarName': 'B_95',
                'SowingDepth': '25',
                'RowSpacing': '700',
                'Population': '4'}

           .. tip::

               Depending on your environment, you may need to close the GUI window to continue
               or follow the prompts shown after termination.
           """

        self.save()
        open_apsimx_file_in_window(self.path, bin_path=configuration.bin_path)
        # record current modification time
        if watch:
            import time
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            import time
            # being tested but so far very cool
            class APSIMFileHandler(FileSystemEventHandler):
                def __init__(self, model, path):
                    self.model = model
                    self.path = path
                    self.changed = False

                def on_modified(self, event):
                    """

                       Triggered if the save button is pressed or the model is run

                    """
                    if event.src_path == self.path:
                        logger.info("Changes detected. Syncing model...")
                        mi = load_apsim_model(self.model.path)
                        self.model.restart_model(mi)
                        self.model.path = self.path
                        self.changed = True

                def on_deleted(self, event):
                    class WatchDeletionError(RuntimeError):
                        pass

                    # Ignore directory events
                    if event.is_directory:
                        return

                    deleted = Path(event.src_path).resolve()
                    watched = Path(self.path).resolve()

                    if deleted == watched:
                        logger.error("APSIM file was deleted; stopping live sync.")
                        raise WatchDeletionError("File has been deleted; can't continue watching.")

            handler = APSIMFileHandler(self, self.path)
            observer = Observer()
            observer.schedule(handler, path=os.path.dirname(self.path), recursive=False)
            observer.start()

            logger.info("Watching for GUI edits. Press `Ctrl+C` in this cell to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                if not handler.changed:
                    logger.warning("Watch session is ending, but not changes detected...")

                observer.stop()
            observer.join()
            logger.info('watching terminated successfully')

    @staticmethod
    def strip_time(date_string):
        date_object = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        formatted_date_string = date_object.strftime("%Y-%m-%dT%H:%M:%S")
        return formatted_date_string  # Output: 2010-01-01T00:00:00

    def replace_met_file(self, *, weather_file: Union[Path, str], simulations=MissingOption,
                         exclude: set | str | tuple | list = None, **kwargs):
        """
        .. deprecated:: 0.**x**
           This helper will be removed in a future release. Prefer newer weather
           configuration utilities or set the ``FileName`` property on weather nodes
           directly.

        Replace the ``FileName`` of every :class:`Models.Climate.Weather` node under one
        or more simulations so they point to a new ``.met`` file.

        This method traverses the APSIM NG model tree under each selected simulation and
        updates the weather component(s) in-place. Version-aware traversal is used:

        * If ``APSIM_VERSION_NO > BASE_RELEASE_NO`` **or**
          ``APSIM_VERSION_NO == GITHUB_RELEASE_NO``: use
          :func:`ModelTools.find_all_in_scope` to find
          :class:`Models.Climate.Weather` nodes.
        * Otherwise: fall back to ``sim.FindAllDescendants[Models.Climate.Weather]()``.

        Parameters
        ----------
        weather_file : Union[pathlib.Path, str]
            Path to the ``.met`` file. May be absolute or relative to the current
            working directory. The path must exist at call time; otherwise a
            :class:`FileNotFoundError` is raised.
        simulations : Any, optional
            Simulation selector forwarded to :meth:`find_simulations`. If left as
            ``MissingOption`` (default) (or if your implementation accepts ``None``),
            all simulations yielded by :meth:`find_simulations` are updated.
            Acceptable types depend on your :meth:`find_simulations` contract
            (e.g., iterable of names, single name, or sentinel).
        exclude: (str, tuple, list), optional
           used to eliminate a given simulation from getting updated
           Added in 0.39.10.20+
        **kwargs
            Ignored. Reserved for backward compatibility and future extensions.

        Returns
        -------
        Self
            The current model/manager instance to support method chaining.

        Raises
        ------
        FileNotFoundError
            If ``weather_file`` does not exist.
        Exception
            Any exception raised by :meth:`find_simulations` or underlying APSIM
            traversal utilities is propagated unchanged.

        Side Effects
        ------------
        Mutates the model by setting ``met.FileName = os.path.realpath(weather_file)``
        for each matched :class:`Models.Climate.Weather` node.

        Notes
        -----
        - **No-op safety:** If a simulation has no Weather nodes, that simulation
          is silently skipped.
        - **Path normalization:** The stored path is the canonical real path
          (``os.path.realpath``).
        - **Thread/process safety:** This operation mutates in-memory model state
          and is not inherently thread-safe. Coordinate external synchronization if
          calling concurrently.

        Examples
        --------
        Update all simulations to use a local ``Ames.met``::

            model.replace_met_file(weather_file="data/weather/Ames.met")

        Update only selected simulations::

            model.replace_met_file(
                weather_file=Path("~/wx/Boone.met").expanduser(),
                simulations=("Sim_A", "Sim_B")
            )

        See Also
        --------
        find_simulations : Resolve and yield simulation objects by name/selector.
        ModelTools.find_all_in_scope : Scope-aware traversal utility.
        Models.Climate.Weather : APSIM NG weather component.
        """
        warnings.warn(
            "replace_met_file() is deprecated and will be removed in a future release. "
            "Please, use edit_model or edit_model_by_path or set Weather.FileName directly.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Normalize & validate the input path early
        wf = os.fspath(weather_file)
        if not os.path.isfile(wf):
            raise FileNotFoundError(wf)
        exclude = {exclude} if isinstance(exclude, str) or exclude is None else exclude
        rep = self.get_replacements_node()

        if rep:
            weather_Nodes = ModelTools.find_all_in_scope(rep, Models.Climate.Weather)
            if weather_Nodes:
                for wet in weather_Nodes:
                    wet.Name = os.path.realpath(wf)
                return self  # no point continuing as they will not be used if the weather model is under replacements

        # Traverse simulations and update weather nodes
        simus = self.find_simulations(simulations=simulations)
        sims = (i for i in simus if i.Name not in exclude)
        for sim in sims:
            if is_higher_apsim_version(self.Simulations):
                weathers = ModelTools.find_all_in_scope(sim, Models.Climate.Weather)
            else:
                weathers = sim.FindAllDescendants[Models.Climate.Weather]()
            for met in weathers:
                met.FileName = os.path.realpath(wf)

        return self

    def _resolve_editable_candidate_models(self, simulations, model_type) -> [Models.__class__]:
        """
            Resolve candidate APSIM NG nodes of a given type for downstream edits.

            This helper walks either the entire model tree under ``self.Simulations`` or a
            subset of named simulations and returns a flat list of nodes whose type matches
            ``model_type``. It **does not** mutate the document, nor does it verify per-node
            editability flags (e.g., ``ReadOnly``); callers are expected to perform those checks.

            Parameters
            ----------
            simulations : None | str | Iterable[str]
                Which simulations to search:
                - ``None`` (default): Search **all** simulations under ``self.Simulations``.
                - ``str`` or iterable of names: Search only within the named simulation(s).
                  If a provided name is unknown, ``self.find_simulations`` will raise.
            model_type : str | types
                The APSIM node type to locate. Accepts either:
                - A fully qualified type name string (e.g., ``"Models.Climate.Weather"``), or
                - A concrete .NET/Models type (e.g., ``Models.Climate.Weather``),
                as supported by ``ModelTools.find_all_in_scope(..., child_class=...)``.

            Returns
            -------
            list
                A list of matching model nodes (order corresponds to discovery order).

            Raises
            ------
            ValueError
                If one of the requested simulations exists but contains **no** nodes
                of the requested ``model_type``.
            Exception
                Any exception propagated by ``self.find_simulations`` for unknown
                simulation names.

            Notes
            -----
            - This function only **discovers** candidates; it does not check or enforce
              edit permissions. If you must ensure nodes are editable, filter the result
              (e.g., by ``getattr(node, "ReadOnly", False)``) before applying modifications.
            - When ``simulations`` is ``None``, replacement folders and nested scopes
              reachable from ``self.Simulations`` are included in the search.

            Examples
            --------
            Search all simulations:

            >>> mgr._resolve_editable_candidate_models(
            ...     simulations=None,
            ...     model_type="Models.Climate.Weather"
            ... )
            [<Weather ...>, <Weather ...>, ...]

            Search a subset by name using a concrete type:

            >>> mgr._resolve_editable_candidate_models(
            ...     simulations=("Baseline", "Treatment-A"),
            ...     model_type=Models.Climate.Weather
            ... )
            [<Weather ...>, <Weather ...>]
            """

        weather_models = ModelTools.find_all_in_scope(self.Simulations, child_class=model_type)
        editable_candidates = []
        if simulations is None:
            editable_candidates.extend({i for i in weather_models})
            return editable_candidates
        else:
            editable_candidates = []
            sim_s = self.find_simulations(simulations)  # it raises if the suggested simulation(s) are not found
            for sim in sim_s:
                edita_models = ModelTools.find_all_in_scope(sim, model_type)
                if not edita_models:
                    raise ValueError(
                        f'No model of type {model_type} found at the suggested simulations: {sim.Fullpath}')
                editable_candidates.extend(edita_models)
        return editable_candidates

    def get_weather_from_file(self, weather_file, simulations=None) -> 'self':
        """
            Point targeted APSIM Weather nodes to a local ``.met`` file.

            The function name mirrors the semantics of ``get_weather_from_web`` but sources the weather
            from disk. If the provided path lacks the ``.met`` suffix, it is appended.
            The file **must** exist on disk.

            Parameters
            ----------
            weather_file: str | Path
                Path (absolute or relative) to a `.met` file. If the suffix is missing,
                `.met` is appended. A `FileNotFoundError` is raised if the final path
                does not exist. The path is resolved to an absolute path to avoid ambiguity.
            simulations: None | str | Iterable[str], optional
                Which simulations to update:
                - `None` (default): update *all* Weather nodes found under `Simulations`.
                - `str` or iterable of names: only update Weather nodes within the named
                  simulation(s). A `ValueError` is raised if a requested simulation has
                  no Weather nodes.

            Returns
            -------
            Instance of the model for method chaining

            Raises
            ------
            FileNotFoundError
                If the resolved ``.met`` file does not exist.
            ValueError
                If any requested simulation exists but contains no Weather nodes.

            Side Effects
            ------------
            Sets `w.FileName` for each targeted `Models.Climate.Weather` node to the
            resolved path of `weather_file`. The file is *not* copied; only the path
            inside the APSIM document is changed.

            Notes
            -----
            - APSIM resolves relative paths relative to the ``.apsimx`` file. Using an
              absolute path (the default here) reduces surprises across working directories.
            - Replacement folders that contain Weather nodes are also updated when
              ``simulations`` is ``None`` (i.e., “update everything in scope”).

            Examples
            --------
            Update all Weather nodes:

            .. code-block:: python

                from apsimNGpy.core.apsim import ApsimModel
                model = ApsimModel("Maize")
                model.get_weather_from_file("data/ames_2020.met")

            Update only two simulations (suffix added automatically):

            .. code-block:: python

                 model.get_weather_from_file("data/ames_2020", simulations=("Simulation",))

            .. seealso::

                Related APIs: :meth:`edit_model` and :meth:`edit_model_by_path`.
            """
        weather_file = Path(weather_file).with_suffix('.met').resolve()
        if not weather_file.exists():
            raise FileNotFoundError(f"{weather_file} does not exist")
        for w in self._resolve_editable_candidate_models(model_type='Models.Climate.Weather', simulations=simulations):
            w.FileName = str(weather_file)
        # at

    def get_weather_from_web(self, lonlat: tuple, start: int, end: int, simulations=MissingOption, source='nasa',
                             filename=None):
        """
            Replaces the weather (met) file in the model using weather data fetched from an online source. Internally, calls get_weather_from_file after downloading the weather
           Parameters:
           ---------
            lonlat: tuple
                 A tuple containing the longitude and latitude coordinates.

            start: int
                  Start date for the weather data retrieval.

            end: int
                  End date for the weather data retrieval.

            simulations: str | list[str] default is all or None list of simulations or a singular simulation
                  name, where to place the weather data, defaults to None, implying ``all`` the available simulations

            source: str default is 'nasa'
                 Source of the weather data.

            filename: str default is generated using the base name of the apsimx file in use, and the start and
                    end years Name of the file to save the retrieved data. If None, a default name is generated.

            Returns:
               model object with the corresponding file replaced with the fetched weather data.

           Examples
           ----------
            >>> from apsimNGpy.core.apsim import ApsimModel
            >>> model = ApsimModel(model= "Maize")
            >>> model.get_weather_from_web(lonlat = (-93.885490, 42.060650), start = 1990, end = 2001)

            Changing weather data with non-matching start and end dates in the simulation will lead to RuntimeErrors.
            To avoid this, first check the start and end date before proceeding as follows:

              >>> dt = model.inspect_model_parameters(model_class='Clock', model_name='Clock', simulations='Simulation')
              >>> start, end = dt['Start'].year, dt['End'].year
              # output: 1990, 2000
            """

        # start, end = self.inspect_model_parameters(model_class='Clock', model_name='Clock', start=start, end=end)
        file_name = f"{Path(self._model).stem}_{source}_{start}_{end}.met"

        name = filename or file_name  # if filename is not None, use filename. Otherwise, file_name.
        file = get_weather(lonlat, start=start, end=end, source=source, filename=name)

        self.get_weather_from_file(weather_file=file, simulations=simulations)

        ...

    def change_report(self, *, command: str, report_name='Report', simulations=None, set_DayAfterLastOutput=None,
                      **kwargs):
        """
            Set APSIM report _variables for specified simulations.

        This function allows you to set the variable names for an APSIM report
        in one or more simulations.

        Parameters
        ----------
        command: str
            The new report string that contains variable names.
        report_name: str
            The name of the APSIM report to update defaults to Report.
        simulations: list of str, optional
            A list of simulation names to update. If `None`, the function will
            update the report for all simulations.

        Returns
        -------
        None

        """
        simulations = self.find_simulations(simulations)
        for sim in simulations:
            if is_higher_apsim_version(self.Simulations):
                i_enum = ModelTools.find_all_in_scope(sim, Models.Report)
                i_enum = [i for i in i_enum if i.Name == report_name]
            else:
                i_enum = sim.FindAllDescendants[Models.Report](report_name)
            for rep in i_enum:
                rep.set_VariableNames(command.strip().splitlines())
                if set_DayAfterLastOutput:
                    rep.set_DayAfterLastOutput = set_DayAfterLastOutput
        return rep

    def extract_soil_physical(self, simulations: [tuple, list] = None):
        """Find physical soil

        Parameters
        ----------
        ``simulation``, optional
            Simulation name, if `None` use the first simulation.
        Returns
        -------
            APSIM Models.Soils.Physical object

        """
        sim_physical = {}
        for nn, simu in enumerate(self._find_simulation(simulations)):
            if is_higher_apsim_version(self.Simulations):
                physical_soil = ModelTools.find_child_of_class(simu, Models.Soils.Physical)
            else:
                soil_object = simu.FindDescendant[Models.Soils]()
                physical_soil = soil_object.FindDescendant[Models.Soils.Physical]()
            sim_physical[simu.Name] = physical_soil
        return sim_physical

    def extract_any_soil_physical(self, parameter, simulations: [list, tuple] = MissingOption):
        """
        Extracts soil physical parameters in the simulation

        Args::
            ``parameter`` (_string_): string e.g. DUL, SAT
            ``simulations`` (string, optional): Targeted simulation name. Defaults to None.
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

    def inspect_children_by_path(self, path):
        ch_model = get_node_by_path(self.Simulations, path)
        return [i.Model.FullPath for i in ch_model.Children]

    def inspect_model(self, model_type: Union[str, Models], fullpath=True, **kwargs):
        """
        Inspect the model types and returns the model paths or names.

        When is it needed?
        --------------------
         useful if you want to identify the paths or name of the model for further editing the model e.g., with the ``in edit_model`` method.

        Parameters
        --------------

        model_class : type | str
            The APSIM model type to search for. You may pass either a class (e.g.,
            Models.Clock, Models.Manager) or a string. Strings can be short names
            (e.g., "Clock", "Manager") or fully qualified (e.g., "Models.Core.Simulation",
            "Models.Climate.Weather", "Models.Core.IPlant"). Please see from The list of classes
            or model types from the **Models** Namespace below. Red represents the modules, and this method
             will throw an error if only a module is supplied. The list constitutes the classes or
             model types under each module

            Models:
              - Models.Clock
              - Models.Fertiliser
              - Models.Irrigation
              - Models.Manager
              - Models.Memo
              - Models.MicroClimate
              - Models.Operations
              - Models.Report
              - Models.Summary
            Models.Climate:
              - Models.Climate.Weather
            Models.Core:
              - Models.Core.Folder
              - Models.Core.Simulation
              - Models.Core.Simulations
              - Models.Core.Zone
            Models.Factorial:
              - Models.Factorial.Experiment
              - Models.Factorial.Factors
              - Models.Factorial.Permutation
            Models.PMF:
              - Models.PMF.Cultivar
              - Models.PMF.Plant
            Models.Soils:
              - Models.Soils.Arbitrator.SoilArbitrator
              - Models.Soils.CERESSoilTemperature
              - Models.Soils.Chemical
              - Models.Soils.Nutrients.Nutrient
              - Models.Soils.Organic
              - Models.Soils.Physical
              - Models.Soils.Sample
              - Models.Soils.Soil
              - Models.Soils.SoilCrop
              - Models.Soils.Solute
              - Models.Soils.Water
            Models.Storage:
              - Models.Storage.DataStore
            Models.Surface:
              - Models.Surface.SurfaceOrganicMatter
            Models.WaterModel:
              - Models.WaterModel.WaterBalance

        fullpath : bool, optional (default: False)
            If False, return the model *name* only.
            If True, return the model’s *full path* relative to the Simulations root.

        Returns
        -------
        list[str]
            A list of model names or full paths, depending on `fullpath`.

        Examples::

             from apsimNGpy.core.apsim import ApsimModel
             from apsimNGpy.core.core import Models


        load default ``maize`` module::

             model = ApsimModel('Maize')

        Find the path to all the manager scripts in the simulation::

             model.inspect_model(Models.Manager, fullpath=True)
             [.Simulations.Simulation.Field.Sow using a variable rule', '.Simulations.Simulation.Field.Fertilise at
             sowing', '.Simulations.Simulation.Field.Harvest']

        Inspect the full path of the Clock Model::

             model.inspect_model(Models.Clock) # gets the path to the Clock models
             ['.Simulations.Simulation.Clock']

        Inspect the full path to the crop plants in the simulation::

             model.inspect_model(Models.Core.IPlant) # gets the path to the crop model
             ['.Simulations.Simulation.Field.Maize']

        Or use the full string path as follows::

             model.inspect_model(Models.Core.IPlant, fullpath=False) # gets you the name of the crop Models
             ['Maize']
        Get the full path to the fertilizer model::

             model.inspect_model(Models.Fertiliser, fullpath=True)
             ['.Simulations.Simulation.Field.Fertiliser']

        The models from APSIM Models namespace are abstracted to use strings. All you need is to specify the name or the full path to the model enclosed in a stirng as follows::

             model.inspect_model('Clock') # get the path to the clock model
             ['.Simulations.Simulation.Clock']

        Alternatively, you can do the following::

             model.inspect_model('Models.Clock')
             ['.Simulations.Simulation.Clock']

        Repeat inspection of the plant model while using a ``string``::

             model.inspect_model('IPlant')
             ['.Simulations.Simulation.Field.Maize']

        Inspect using the full model namespace path::

             model.inspect_model('Models.Core.IPlant')

        What about the weather model?::

             model.inspect_model('Weather') # inspects the weather module
             ['.Simulations.Simulation.Weather']

        Alternative::

             # or inspect using full model namespace path
             model.inspect_model('Models.Climate.Weather')
             ['.Simulations.Simulation.Weather']

        Try finding the path to the cultivar model::

             model.inspect_model('Cultivar', fullpath=False) # list all available cultivar names
             ['Hycorn_53', 'Pioneer_33M54', 'Pioneer_38H20','Pioneer_34K77', 'Pioneer_39V43','Atrium', 'Laila', 'GH_5019WX']

        # we can get only the names of the cultivar models using the full string path::

             model.inspect_model('Models.PMF.Cultivar', fullpath = False)
             ['Hycorn_53','Pioneer_33M54', 'Pioneer_38H20','Pioneer_34K77', 'Pioneer_39V43','Atrium', 'Laila', 'GH_5019WX']

        .. tip::

            Models can be inspected either by importing the Models namespace or by using string paths. The most reliable
             approach is to provide the full model path—either as a string or as the ``Models`` object.

            However, remembering full paths can be tedious, so allowing partial model names or references can significantly
             save time during development and exploration.


        .. note::

            - You do not need to import `Models` if you pass a string; both short and
              fully qualified names are supported.
            - “Full path” is the APSIM tree path **relative to the Simulations node**
              (be mindful of the difference between *Simulations* (root) and an individual
              *Simulation*).

        .. seealso::

               Related APIs:
               :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_file`,
               :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_model_parameters`,
               :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_model_parameters_by_path`
        """
        _version = float(self.Simulations.ApsimVersion.replace(".", ''))
        _base_version = float(BASE_RELEASE_NO.replace(".", ''))

        model_type = validate_model_obj(model_type)
        if model_type == Models.Core.Simulations:
            obj = [self.Simulations]

        else:

            if is_higher_apsim_version(self.Simulations):
                obj = ModelTools.find_all_in_scope(self.Simulations, model_type)
            else:
                try:
                    obj = self.Simulations.FindAllDescendants[model_type]()
                except AttributeError:
                    logger.info(f"{_version} is not supported by this method install the appropriate APSIM version")
                    raise

        if obj:
            fpath = [i.FullPath for i in obj]
            names = [i.Name for i in obj]
            if fullpath:
                return fpath
            else:
                return names

    @property
    def configs(self):
        """records activities or modifications to the model including changes to the file

        """
        return {
            # check if model has been ran yet
            'model_has_been_ran': self.ran_ok,
            'experiment': self.experiment,
            'experiment_created': self.experiment_created,
            'reports': self.report_names or self.inspect_model("Report"),
            'simulations': self.Simulations.Name,
            'start_changed': True if self.Start != MissingOption else False,
            'end_changed': True if self.End != MissingOption else False,
            'start_date': self.inspect_model_parameters(model_type='Clock', model_name='Clock',
                                                        simulations=self.simulation_names, parameters='Start'),
            'end_date': self.inspect_model_parameters(model_type='Clock', model_name='Clock',
                                                      simulations=self.simulation_names, parameters='Start')
        }

    def replace_soils_values_by_path(self, node_path: str, indices: list = None, **kwargs):
        """
        set the new values of the specified soil object by path. only layers parameters are supported.

        Unfortunately, it handles one soil child at a time e.g., ``Physical`` at a go

        Parameters:
        -----------

        node_path: (str, required):
           complete path to the soil child of the Simulations e.g.,Simulations.Simulation.Field.Soil.Organic.
           Use`copy path to node function in the GUI to get the real path of the soil node.

        indices: (list, optional)
            defaults to none but could be the position of the replacement values for arrays

        **kwargs: (key word arguments)
            This carries the parameter and the values e.g., BD = 1.23 or BD = [1.23, 1.75]
            if the child is ``Physical``, or ``Carbon`` if the child is ``Organic``

         raises:
         `ValueError if none of the key word arguments, representing the paramters are specified

         returns:
            - Instance of the model object
         Example::

              from apsimNGpy.core.base_data import load_default_simulations
              model = load_default_simulations(crop ='Maize', simulations_object=False) # initiate model.
              model = CoreModel(model) # ``replace`` with your intended file path
              model.replace_soils_values_by_path(node_path='.Simulations.Simulation.Field.Soil.Organic', indices=[0], Carbon =1.3)
              sv= model.get_soil_values_by_path('.Simulations.Simulation.Field.Soil.Organic', 'Carbon')
              output # {'Carbon': [1.3, 0.96, 0.6, 0.3, 0.18, 0.12, 0.12]}


        """
        if not kwargs:
            raise ValueError('No parameters are specified')
        if hasattr(self.Simulations, 'FindByPath'):
            _soil_child = self.Simulations.FindByPath(node_path)
        else:
            _soil_child = get_node_by_path(self.Simulations, node_path)

            soil_child_class_model = getattr(_soil_child, 'Model', _soil_child)
            soil_child_model_class = soil_child_class_model.GetType()

            _soil_child = CastHelper.CastAs[soil_child_model_class](soil_child_class_model)

        if _soil_child is None:
            raise ValueError(f"No such child: {node_path} exist in the simulation file {self.path}")
        if not kwargs:
            logger.error('no parameters and values are supplied')
            return self
        for k, v in kwargs.items():
            parameter = k
            if isinstance(v, (int, float, str)):
                v = [v]
            if indices is None:
                indices = range(len(v))
            val_p = getattr(_soil_child, 'Value', _soil_child)
            param_values_new = list(getattr(val_p, parameter))
            _param_new = replace_variable_by_index(param_values_new, v, indices)
            setattr(val_p, parameter, _param_new)

    def get_soil_values_by_path(self, node_path, *args):

        var_out = {}
        try:
            _soil_child_obj = self.Simulations.FindByPath(node_path)
        except AttributeError:
            _soil_child_obj = get_node_by_path(self.Simulations, node_path)
            soil_class = 'Models.Soils.' + '.'.join(node_path.split('.')[-1:])
            soil_class = validate_model_obj(soil_class)
            _soil_child_obj = CastHelper.CastAs[soil_class](_soil_child_obj.Model)

        if args:
            for arg in args:
                val_p = getattr(_soil_child_obj, 'Value', _soil_child_obj)
                gv = getattr(val_p, arg, None)
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

        warnings.warn("replace_soil_properties_by_path is deprecated use self.replace_soils_values_by_path instead",
                      DeprecationWarning)

        """
        This function processes a path where each component represents different nodes in a hierarchy,
        with the ability to replace parameter values at various levels.

        ``path``:
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

        ``param_values``:
            A list of parameter values that will replace the existing values in the specified path.
            For example, `[0.1, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]` could be used to replace values for `NH3`.

        ``str_fmt``:
            A string specifying the formatting character used to separate each component in the path.
            Examples include ".", "_", or "/". This defines how the components are joined together to
            form the full path.

        ``returns``:
        ----------
            Returns the instance of `self` after processing the path and applying the parameter value replacements.

        Example:
        ---------------------

            >>> from apsimNGpy.core.base_data import load_default_simulations
            >>> model = load_default_simulations(crop = 'Maize')
            >>> model.replace_soil_properties_by_path(path = 'None.Soil.Organic.None.None.Carbon', param_values= [1.23])

            # if we want to replace ``carbon`` at the ``bottom`` of the ``soil profile``, we use a negative index  -1

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
                                     simulations: list = MissingOption,
                                     indices: list = None,
                                     crop=None,
                                     **kwargs):
        """
        Replaces values in any soil property array. The soil property array.

        ``parameter``: str: parameter name e.g., NO3, 'BD'

        ``param_values``: list or tuple: values of the specified soil property name to replace

        ``soil_child``: str: sub child of the soil component e.g., organic, physical etc.

        ``simulations``: list: list of simulations to where the child is found if
          not found, all current simulations will receive the new values, thus defaults to None

        ``indices``: list. Positions in the array which will be replaced. Please note that unlike C#, python satrt counting from 0

        ``crop`` (str, optional): string for soil water replacement. Default is None

        """
        if isinstance(param_values, (int, float)):
            param_values = [param_values]
        if indices is None:
            indices = [param_values.index(i) for i in param_values]
        for simu in self.find_simulations(simulations):
            sub_soil = soil_child.capitalize()
            soil_class = self.find_model(sub_soil)

            if soil_child != 'soilcrop':
                if is_higher_apsim_version(self.Simulations):
                    _soil_child = ModelTools.find_all_in_scope(simu, soil_class)  # requires recussion
                    if not _soil_child:
                        raise ModelNotFoundError(f"model of class {soil_class} not found in {simu.FullPath}")
                    _soil_child = _soil_child[0]
                else:
                    _soil_child = simu.FindDescendant[soil_class]()
                # _soil_child = soil_object.FindDescendant[soil_components(soil_child)]()

                param_values_new = list(getattr(_soil_child, parameter))
                _param_new = replace_variable_by_index(param_values_new, param_values, indices)
                setattr(_soil_child, parameter, _param_new)
            else:

                if crop is None:
                    raise ValueError('Crop not defined')
                crop = crop.capitalize() + "Soil"
                _soil_child = simu.FindDescendant[Models.Soils.SoilCrop](crop)
                param_values_new = list(getattr(_soil_child, parameter))
                _param_new = replace_variable_by_index(param_values_new, param_values, indices)
                setattr(_soil_child, parameter, _param_new)

        return self

    def find_simulations(self, simulations: Union[list, tuple, str, None] = MissingOption):
        simulations_names = simulations
        """Find simulations by name or names in a list

        Parameters
        ----------
        simulations: str, list optional
            List of simulation names to find, if `None` or named 'all' return all simulations. These will be removed in future versions and stick to MissingOption
        Returns:
        ----------
            list of APSIM ``Models.Core.Simulation`` objects
        """

        if simulations == 'all' or simulations == MissingOption or simulations is None:
            return self.simulations
        if isinstance(simulations_names, str):
            simulations_names = {simulations_names}
        elif isinstance(simulations, (list, tuple)):
            simulations_names = set(simulations)
        sims = []
        # available_simulations = {si.Name:si for si in self.simulations}
        for sim in self.simulations:
            sim_name = str(sim.Name)
            if sim_name in simulations_names:
                sims.append(sim)
                simulations_names.remove(sim_name)
        if len(sims) == 0:
            logger.info(f"{simulations_names}: Not found!")
            sim_names = ", ".join([i.Name for i in self.simulations])
            raise NameError(f"{simulations_names}: Not found! \n Available simulation(s) names are/is: '{sim_names}'?")
        else:
            return sims

    # Find a single simulation by name
    def _find_simulation(self, simulations: Union[tuple, list] = MissingOption):
        if simulations is MissingOption:
            return self.simulations

        else:
            return [self.Simulations.FindDescendant(i) for i in simulations if i in self.simulation_names]

    @staticmethod
    @lru_cache(maxsize=80)
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

    def clean_up(self, db=True, verbose=False, csv=True):
        """
        Clears the file cloned the datastore and associated csv files are not deleted if db is set to False defaults to True.

        Returns:
           >>None: This method does not return a value.

        .. caution::

           Please proceed with caution, we assume that if you want to clear the model objects, then you don't need them,
           but by making copy compulsory, then, we are clearing the edited files

        """

        try:
            path = Path(self.path)
            _db = path.with_suffix('.db')
            bak = path.with_suffix('.bak')
            db_wal = path.with_suffix('.db-wal')
            db_shm = path.with_suffix('.db-shm')
            try:
                db_csv = {path.with_suffix(f'.{rep}.csv') for rep in
                          self.inspect_model(Models.Report, fullpath=False)} if csv else set()
            except TypeError:
                db_csv = set()
            clean_candidates = {bak, bak, db_wal, path, db_shm, *db_csv}
            if db:
                clean_candidates.add(_db)
            for candidate in clean_candidates:
                try:
                    _exists = candidate.exists()
                    candidate.unlink(missing_ok=True)

                    if verbose and _exists:
                        if not candidate.exists():
                            logger.info(f'{candidate} cleaned successfully')

                except PermissionError:
                    if verbose:
                        logger.info(f'{candidate} could not be cleaned due to permission error')

        finally:
            ModelTools.COLLECT()

        return self

    def create_experiment(self, permutation: bool = True, base_name: str = None, **kwargs):
        """
         @deprecated and will be removed in future versions for this class.

        Initialize an ``ExperimentManager`` instance, adding the necessary models and factors.

        Args:

            ``kwargs``: Additional parameters for CoreModel.

            ``permutation`` (bool). If True, the experiment uses a permutation node to run unique combinations of the specified
            factors for the simulation. For example, if planting population and nitrogen fertilizers are provided,
            each combination of planting population level and fertilizer amount is run as an individual treatment.

           ``base_name`` (str, optional): The name of the base simulation to be moved into the experiment setup. if not
            provided, it is expected to be Simulation as the default.

        .. warning::

            ``base_name`` is optional but the experiment may not be created if there are more than one base simulations. Therefore, an error is likely.

        """
        if IS_NEW_MODEL:
            from apsimNGpy.core.config import apsim_version
            version = apsim_version()
            logger.warning(
                f'\n create_experiment is deprecated for this apsim version {version} use the `apsimNGpy.core.experiment.ExperimentManager` class instead.')
            return self
        #
        self.refresh_model()
        self.factor_names = []

        self.permutation = permutation
        # Add core experiment structure

        self.add_model(model_type='Models.Factorial.Experiment', adoptive_parent='Models.Core.Simulations',
                       **kwargs)

        self.add_model(model_type=Models.Factorial.Factors, adoptive_parent=Models.Factorial.Experiment,
                       **kwargs)

        if permutation:
            self.add_model(model_type=Models.Factorial.Permutation, adoptive_parent=Models.Factorial.Factors, **kwargs)

        # Move base simulation under the factorial experiment
        self.move_model(Models.Core.Simulation, Models.Factorial.Experiment, base_name, None)

        self.save()
        # update the experiment status
        self.experiment = True
        self.experiment_created = True

    def stop(self):
        storage = self.Simulations.FindDescendant[Models.Storage.DataStore]()
        storage.Writer.Stop()

    def refresh_model(self):
        """
       for methods that will alter the simulation objects and need refreshing the second time we call
       @return: self for method chaining
       """
        if not self._intact_model:
            old_model = ModelTools.CLONER(self.Simulations)
            self._intact_model.append(old_model)
        if self._intact_model:
            self.Simulations = self._intact_model[0]

    def add_factor(self, specification: str, factor_name: str = None, **kwargs):
        """
        Adds a factor to the created experiment. Thus, this method only works on factorial experiments

        It could raise a value error if the experiment is not yet created.

        Under some circumstances, experiment will be created automatically as a permutation experiment.

        Parameters:
        ----------

        specification``: (str), required*
            A specification can be:
                    - 1. multiple values or categories e.g., "[Sow using a variable rule].Script.Population =4, 66, 9, 10"
                    - 2. Range of values e.g, "[Fertilise at sowing].Script.Amount = 0 to 200 step 20",

        factor_name: (str), required
            expected to be the user-desired name of the factor being specified e.g., population

        This method is overwritten in :class:`~apsimNGpy.core.experimentmanager.ExperimentManager` class.

        @deprecated and will be removed in future versions for this class.

        Example::

            from apsimNGpy.core import base_data
            apsim = base_data.load_default_simulations(crop='Maize')
            apsim.create_experiment(permutation=False)
            apsim.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20", factor_name='Nitrogen')
            apsim.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2", factor_name='Population')
            apsim.run() # doctest: +SKIP
        """
        # TODO fix factors either composite or not composite
        if factor_name is None:
            get_name = specification.split("=")[0].strip()
            # split again by
            factor_name = get_name.split(".")[-1]
        original_spec = specification
        if specification not in self._specifications:

            if not self.experiment:
                msg = 'experiment was not defined, it has been created with default settings'
                self.create_experiment(permutation=True)  # create experiment with default parameters of permutation
                self.experiment = True

            if 'Script' in specification:
                matches = re.findall(r"\[(.*?)\]", specification)
                if matches:
                    _managers = set(self.inspect_model('Models.Manager', fullpath=False))
                    ITC = set(matches).intersection(_managers)
                    if not ITC:
                        raise ValueError('specification has no linked script in the model')

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
            self._specifications.append(original_spec)
        return self  # allows method chaining

    def add_fac(self, model_type, parameter, model_name, values, factor_name=None):
        """
        Add a factor to the initiated experiment. This should replace add_factor. which has less abstractionn @param
        model_type: model_class from APSIM Models namespace @param parameter: name of the parameter to fill e.g CNR
        @param model_name: name of the model @param values: values of the parameter, could be an iterable for case of
        categorical variables or a string e.g, '0 to 100 step 10 same as [0, 10, 20, 30, ...].
        @param factor_name: name to identify the factor in question
        @return:
        """
        if not isinstance(values, str) and 'step' not in values:
            values = ','.join(values)
        if isinstance(values, str):
            values = values.strip()
        if model_type in {'Manager', 'Models.Manager', 'manager', Models.Manager}:
            model_in = self.Simulations.FindDescendant[Models.Manager](model_name)
            if not model_in:
                raise ValueError(f'{model_name} of type Models.Manager does not exist in the current simulations')
            specification = f"[{model_name}].Script.{parameter}={values}"
        else:
            specification = f"[{model_name}].{parameter}={values}"
        original_spec = specification
        if factor_name is None:
            factor_name = parameter
        if specification not in self._specifications:
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
            self._specifications.append(original_spec)
        return self  # allows method chaining

    # to be completed

    def set_continuous_factor(self, factor_path, lower_bound, upper_bound, interval, factor_name=None):
        """
        Wraps around `add_factor` to add a continuous factor, just for clarity

        Args:
            ``factor_path``: (str): The path of the factor definition relative to its child node,
                e.g., `"[Fertilise at sowing].Script.Amount"`.

            ``factor_name``: (str): The name of the factor.

            ``lower_bound``: (int or float): The lower bound of the factor.

            ``upper_bound``: (int or float): The upper bound of the factor.

            ``interval``: (int or float): The distance between the factor levels.

        ``Returns``:
            ``ApsimModel`` or ``CoreModel``: An instance of `apsimNGpy.core.core.apsim.ApsimModel` or `CoreModel`.
        Example::

            from apsimNGpy.core import base_data
            apsim = base_data.load_default_simulations(crop='Maize')
            apsim.create_experiment(permutation=False)
            apsim.set_continuous_factor(factor_path = "[Fertilise at sowing].Script.Amount", lower_bound=100, upper_bound=300, interval=10)

        """
        format_factor = f"{factor_path} = {lower_bound} to {upper_bound} step {interval}"
        self.add_factor(specification=format_factor, factor_name=factor_name)

    def set_categorical_factor(self, factor_path: str, categories: Union[list, tuple], factor_name: str = None):
        """
        wraps around ``add_factor()`` to add a continuous factor, just for clarity.

         parameters
         __________________________
        ``factor_path``: (str, required): path of the factor definition relative to its child node "[Fertilise at sowing].Script.Amount"

        ``factor_name``: (str) name of the factor.

        ``categories``: (tuple, list, required): multiple values of a factor

        ``returns``:
          ``ApsimModel`` or ``CoreModel``: An instance of ``apsimNGpy.core.core.apsim.ApsimModel`` or ``CoreModel``.

        Example::

            from apsimNGpy.core import base_data
            apsim = base_data.load_default_simulations(crop='Maize')
            apsim.create_experiment(permutation=False)
            apsim.set_continuous_factor(factor_path = "[Fertilise at sowing].Script.Amount", lower_bound=100, upper_bound=300, interval=10)

        """
        format_factor = f"{factor_path} = {','.join(map(str, categories))}"
        self.add_factor(specification=format_factor, factor_name=factor_name)
        return self

    def add_crop_replacements(self, _crop: str):
        """
        Adds a replacement folder as a child of the simulations.

        Useful when you intend to edit cultivar **parameters**.

        **Args:**
            ``_crop`` (*str*): Name of the crop to be added to the replacement folder.

        ``Returns:``
            - *ApsimModel*: An instance of `apsimNGpy.core.core.apsim.ApsimModel` or `CoreModel`.

        ``Raises:``
            - *ValueError*: If the specified crop is not found.
        """
        if self.get_replacements_node():
            return self

        _FOLDER = Models.Core.Folder()
        #  "everything is edited in place"
        CROP = _crop
        _FOLDER.Name = "Replacements"
        PARENT = self.Simulations
        # parent replacement should be added once
        if is_higher_apsim_version(self.Simulations):
            target_parent = ModelTools.find_child(PARENT, Models.Core.Folder, 'Replacements')
        else:
            target_parent = PARENT.FindDescendant[Models.Core.Folder]('Replacements')
        if not target_parent:
            ModelTools.ADD(_FOLDER, PARENT)
        # assumes that the crop already exists in the simulation
        if is_higher_apsim_version(self.Simulations):
            _crop = ModelTools.find_child(PARENT, Models.PMF.Plant, CROP)
        else:
            _crop = PARENT.FindDescendant[Models.PMF.Plant](CROP)

        if _crop is not None:
            ModelTools.ADD(_crop, _FOLDER)
        else:

            logger.error(f"No plants of crop{CROP} found")
        return self

    def get_model_paths(self, cultivar=False) -> list[str]:
        """
        Select out a few model types to use for building the APSIM file inspections
        """
        self.save()

        def filter_out():
            data = []
            model_classes = {'Models.Core.Simulation', 'Models.Soils.Soil', 'Models.PMF.Plant', 'Models.Manager',
                             'Models.Climate.Weather', 'Models.Report', 'Models.Clock', 'Models.Core.Folder',
                             'Models.Soils.Solute', 'Models.Surface.SurfaceOrganicMatter',
                             'Models.Soils.Swim3', 'Models.Soils.SoilCrop', 'Models.Soils.Water', 'Models.Summary',
                             'Models.Core.Zone', 'Models.Management.RotationManager',
                             'Models.Soils.CERESSoilTemperature', 'Models.Series', 'Models.Factorial.ExperimentManager',
                             'Models.Factorial.Permutation', 'Models.Irrigation',
                             'Models.Factorial.Factors',
                             'Models.Sobol', 'Models.Operations', 'Models.Morris', 'Models.Fertiliser',
                             'Models.Core.Events',
                             'Models.MicroClimate',
                             'Models.Core.VariableComposite',
                             'Models.Zones.RectangularZone',
                             'Models.Soils.Arbitrator.SoilArbitrator',
                             'Models.Summary',
                             'Models.Storage.DataStore',
                             'Models.Graph',
                             'Models.WaterModel.WaterBalance',
                             'Models.Soils.Physical', 'Models.Soils.Chemical', 'Models.Soils.Organic'}
            if cultivar:
                model_classes.add('Models.PMF.Cultivar')
            for i in model_classes:
                try:
                    ans = self.inspect_model(eval(i))
                    if ans is None:
                        continue
                except AttributeError as ae:
                    continue
                if 'Replacements' not in ans and 'Folder' in i:
                    continue
                data.extend(ans)
            del model_classes
            return [i for i in data if i is not None]

        return filter_out()

    def inspect_file(self, *, cultivar=False, console=True, **kwargs):

        """
        Inspects the file by traversing the entire simulation tree, using :meth:`inspect_model` under the hood

        This method is important in inspecting the `whole file` and also getting the `scripts paths`.

        Parameters
        ----------
        cultivar: (bool)
           To include cultivar paths.

        console: (bool)
           Prints to the console if True

        Examples
        -----------
        .. code-block:: python

           from apsimNGpy.core.apsim import ApsimModel
           model = ApsimModel('Maize')
           model.inspect_file(cultivar=False)

        # output

        .. code-block:: none

            └── Models.Core.Simulations: .Simulations
                ├── Models.Storage.DataStore: .Simulations.DataStore
                ├── Models.Core.Folder: .Simulations.Replacements
                │   └── Models.PMF.Plant: .Simulations.Replacements.Maize
                └── Models.Core.Simulation: .Simulations.Simulation
                    ├── Models.Clock: .Simulations.Simulation.Clock
                    ├── Models.Core.Zone: .Simulations.Simulation.Field
                    │   ├── Models.Manager: .Simulations.Simulation.Field.Fertilise at sowing
                    │   ├── Models.Fertiliser: .Simulations.Simulation.Field.Fertiliser
                    │   ├── Models.Manager: .Simulations.Simulation.Field.Harvest
                    │   ├── Models.PMF.Plant: .Simulations.Simulation.Field.Maize
                    │   ├── Models.Report: .Simulations.Simulation.Field.Report
                    │   ├── Models.Soils.Soil: .Simulations.Simulation.Field.Soil
                    │   │   ├── Models.Soils.Chemical: .Simulations.Simulation.Field.Soil.Chemical
                    │   │   ├── Models.Soils.Solute: .Simulations.Simulation.Field.Soil.NH4
                    │   │   ├── Models.Soils.Solute: .Simulations.Simulation.Field.Soil.NO3
                    │   │   ├── Models.Soils.Organic: .Simulations.Simulation.Field.Soil.Organic
                    │   │   ├── Models.Soils.Physical: .Simulations.Simulation.Field.Soil.Physical
                    │   │   │   └── Models.Soils.SoilCrop: .Simulations.Simulation.Field.Soil.Physical.MaizeSoil
                    │   │   ├── Models.Soils.Solute: .Simulations.Simulation.Field.Soil.Urea
                    │   │   └── Models.Soils.Water: .Simulations.Simulation.Field.Soil.Water
                    │   ├── Models.Manager: .Simulations.Simulation.Field.Sow using a variable rule
                    │   └── Models.Surface.SurfaceOrganicMatter: .Simulations.Simulation.Field.SurfaceOrganicMatter
                    ├── Models.Graph: .Simulations.Simulation.Graph
                    │   └── Models.Series: .Simulations.Simulation.Graph.Series
                    ├── Models.MicroClimate: .Simulations.Simulation.MicroClimate
                    ├── Models.Soils.Arbitrator.SoilArbitrator: .Simulations.Simulation.SoilArbitrator
                    ├── Models.Summary: .Simulations.Simulation.Summary
                    └── Models.Climate.Weather: .Simulations.Simulation.Weather

        Turn cultivar paths on as follows:

        .. code-block:: python

          model.inspect_file(cultivar=True)

        # output

        .. code-block:: none

           └── Models.Core.Simulations: .Simulations
                ├── Models.Storage.DataStore: .Simulations.DataStore
                ├── Models.Core.Folder: .Simulations.Replacements
                │   └── Models.PMF.Plant: .Simulations.Replacements.Maize
                │       └── Models.Core.Folder: .Simulations.Replacements.Maize.CultivarFolder
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Atrium
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.CG4141
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Dekalb_XL82
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.GH_5009
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.GH_5019WX
                │           ├── Models.Core.Folder: .Simulations.Replacements.Maize.CultivarFolder.Generic
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_100
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_103
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_105
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_108
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_110
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_112
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_115
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_120
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_130
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_80
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_90
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.A_95
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_100
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_103
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_105
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_108
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_110
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_112
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_115
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_120
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_130
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_80
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_90
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.B_95
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.HY_110
                │           │   ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.LY_110
                │           │   └── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Generic.P1197
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Hycorn_40
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Hycorn_53
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Katumani
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Laila
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Makueni
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Melkassa
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.NSCM_41
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Pioneer_3153
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Pioneer_33M54
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Pioneer_34K77
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Pioneer_38H20
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Pioneer_39G12
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.Pioneer_39V43
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.malawi_local
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.mh12
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.mh16
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.mh17
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.mh18
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.mh19
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.r201
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.r215
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.sc401
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.sc501
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.sc601
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.sc623
                │           ├── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.sc625
                │           └── Models.PMF.Cultivar: .Simulations.Replacements.Maize.CultivarFolder.sr52
                └── Models.Core.Simulation: .Simulations.Simulation
                    ├── Models.Clock: .Simulations.Simulation.Clock
                    ├── Models.Core.Zone: .Simulations.Simulation.Field
                    │   ├── Models.Manager: .Simulations.Simulation.Field.Fertilise at sowing
                    │   ├── Models.Fertiliser: .Simulations.Simulation.Field.Fertiliser
                    │   ├── Models.Manager: .Simulations.Simulation.Field.Harvest
                    │   ├── Models.PMF.Plant: .Simulations.Simulation.Field.Maize
                    │   │   └── Models.Core.Folder: .Simulations.Simulation.Field.Maize.CultivarFolder
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Atrium
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.CG4141
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.GH_5009
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.GH_5019WX
                    │   │       ├── Models.Core.Folder: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_100
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_103
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_105
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_108
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_110
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_112
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_115
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_120
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_130
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_80
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_90
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_95
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_100
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_103
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_105
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_108
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_110
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_112
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_115
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_120
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_130
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_80
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_90
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_95
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.HY_110
                    │   │       │   ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.LY_110
                    │   │       │   └── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Generic.P1197
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Hycorn_40
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Hycorn_53
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Katumani
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Laila
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Makueni
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Melkassa
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.NSCM_41
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_3153
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_33M54
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_34K77
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_38H20
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_39G12
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_39V43
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.malawi_local
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.mh12
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.mh16
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.mh17
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.mh18
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.mh19
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.r201
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.r215
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.sc401
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.sc501
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.sc601
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.sc623
                    │   │       ├── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.sc625
                    │   │       └── Models.PMF.Cultivar: .Simulations.Simulation.Field.Maize.CultivarFolder.sr52
                    │   ├── Models.Report: .Simulations.Simulation.Field.Report
                    │   ├── Models.Soils.Soil: .Simulations.Simulation.Field.Soil
                    │   │   ├── Models.Soils.Chemical: .Simulations.Simulation.Field.Soil.Chemical
                    │   │   ├── Models.Soils.Solute: .Simulations.Simulation.Field.Soil.NH4
                    │   │   ├── Models.Soils.Solute: .Simulations.Simulation.Field.Soil.NO3
                    │   │   ├── Models.Soils.Organic: .Simulations.Simulation.Field.Soil.Organic
                    │   │   ├── Models.Soils.Physical: .Simulations.Simulation.Field.Soil.Physical
                    │   │   │   └── Models.Soils.SoilCrop: .Simulations.Simulation.Field.Soil.Physical.MaizeSoil
                    │   │   ├── Models.Soils.Solute: .Simulations.Simulation.Field.Soil.Urea
                    │   │   └── Models.Soils.Water: .Simulations.Simulation.Field.Soil.Water
                    │   ├── Models.Manager: .Simulations.Simulation.Field.Sow using a variable rule
                    │   └── Models.Surface.SurfaceOrganicMatter: .Simulations.Simulation.Field.SurfaceOrganicMatter
                    ├── Models.Graph: .Simulations.Simulation.Graph
                    │   └── Models.Series: .Simulations.Simulation.Graph.Series
                    ├── Models.MicroClimate: .Simulations.Simulation.MicroClimate
                    ├── Models.Soils.Arbitrator.SoilArbitrator: .Simulations.Simulation.SoilArbitrator
                    ├── Models.Summary: .Simulations.Simulation.Summary
                    └── Models.Climate.Weather: .Simulations.Simulation.Weather


        .. seealso::

            - Related APIs: :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_model`, :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_model_parameters`
            - :ref:`Model inspections <plain_inspect>`

        """
        self.save()  # save before compiling for consistent behaviors
        if kwargs.get('indent', None) or kwargs.get('display_full_path', None):
            logger.info(
                "Inspecting file with key word indent or display_full_path is \ndeprecated, the inspect_file now print "
                "the inspection as a tree with names and corresponding model \nfull paths combined")

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
                try:
                    if not current_path.startswith('.'):
                        node_path = f".{current_path}"
                    else:
                        node_path = current_path
                    _model_type = get_node_by_path(self.Simulations, node_path)
                except NodeNotFoundError as nde:
                    _model_type = ''
                mo_del = getattr(_model_type, 'Model', _model_type)
                mod = CastHelper.CastAs[mo_del.GetType()](mo_del)
                # print(mod)
                print(f"{prefix}{branch}\033[95m{mod}\033[0m: .{current_path}")

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
        if console:

            print_tree_branches(tree)
        else:
            return tree
            # future implementation

    def summarize_numeric(self, data_table: Union[str, tuple, list] = None, columns: list = None,
                          percentiles=(0.25, 0.5, 0.75), round=2) -> pd.DataFrame:
        """
        Summarize numeric columns in a simulated pandas DataFrame. Useful when you want to quickly look at the simulated data

        Parameters:

            -  data_table (list, tuple, str): The names of the data table attached to the simulations. defaults to all data tables.
            -  specific (list) columns to summarize.
            -  percentiles (tuple): Optional percentiles to include in the summary.
            -  round (int): number of decimal places for rounding off.

        Returns:

            pd.DataFrame: A summary DataFrame with statistics for each numeric column.


        """
        from pandas import DataFrame
        if data_table is None:
            fd = self.results
        else:
            fd = self.get_simulated_output(data_table)

        if not isinstance(fd, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")

        get_df = fd.get(columns)
        sel_df = fd.select_dtypes(include='number')
        drop_col = {'SimulationID', 'CheckpointID'}
        numeric_df = DataFrame(get_df) if columns else sel_df
        dp = numeric_df.columns.intersection(drop_col)

        numeric_df = numeric_df.drop(dp, axis=1)
        if numeric_df.empty:
            raise ValueError("No numeric columns found in the DataFrame")

        summary = numeric_df.describe(percentiles=percentiles).T
        summary['missing'] = fd.shape[0] - summary['count']

        return summary.round(round)

    def create_experiment_for_node(self, permutation=True):
        def exp_refresher(mode):
            sim = mode.simulations[0]
            base = ModelTools.CLONER(sim)
            for simx in mode.simulations:  # it does not matter how many experiments exist, we need only one
                ModelTools.DELETE(simx)
            # replace before delete
            mode.simulations[0] = base
            base = mode.simulations[0]
            experiment = Models.Factorial.ExperimentManager()
            factor = Models.Factorial.Factors()
            if permutation:
                factor.AddChild(Models.Factorial.Permutation())
            experiment.AddChild(factor)
            experiment.AddChild(base)
            mode.model_info.Node.AddChild(experiment)

        # delete experiment if exists to allow refreshing if simulation was edited
        experi = self.Simulations.FindInScope[Models.Factorial.ExperimentManager]()
        if experi:
            ModelTools.DELETE(experi)
        exp_refresher(self)
        self.save()
        fp = self.Simulations.FindInScope[Models.Factorial.ExperimentManager]()
        exp_node = get_node_by_path(self.model_info.Node, fp.FullPath)
        self.preview_simulation()
        return exp_node

    # @timer
    def add_db_table(self, variable_spec: list = None, set_event_names: list = None, rename: str = None,
                     simulation_name: Union[str, list, tuple] = MissingOption):
        """
        Adds a new database table, which ``APSIM`` calls ``Report`` (Models.Report) to the ``Simulation`` under a Simulation Zone.

        This is different from ``add_report_variable`` in that it creates a new, named report
        table that collects data based on a given list of _variables and events. actu

        Parameters:
        ----------
        variable_spec: (list or str)
            A list of APSIM variable paths to include in the report table.
            If a string is passed, it will be converted to a list.

        set_event_names: (list or str, optional):
           A list of APSIM events that trigger the recording of _variables.
            Defaults to ['[Clock].EndOfYear'] if not provided. other examples include '[Clock].StartOfYear', '[Clock].EndOfsimulation',
            '[crop_name].Harvesting' etc.

        rename: (str): The name of the report table to be added. Defaults to 'my_table'.

        simulation_name: (str,tuple, or list, Optional)
           if specified, the name of the simulation will be searched and will become the parent candidate for the report table.
           If it is none, all Simulations in the file will be updated with the new db_table

        Raises:
        ______
        ``ValueError``: If no variable_spec is provided.
        ``RuntimeError``: If no Zone is found in the current simulation scope.

        Examples::

               from apsimNGpy.core.apsim import ApsimModel
               model = ApsimModel('Maize')
               model.add_db_table(variable_spec=['[Clock].Today', '[Soil].Nutrient.TotalC[1]/1000 as SOC1'], rename='report2')
               model.add_db_table(variable_spec=['[Clock].Today', '[Soil].Nutrient.TotalC[1]/1000 as SOC1', '[Maize].Grain.Total.Wt*10 as Yield'], rename='report2', set_event_names=['[Maize].Harvesting','[Clock].EndOfYear' ])
       .. seealso::

        Related APIs: :meth:`remove_report_variables` and :meth:`add_report_variables`.
        """
        if not rename:
            raise ValueError(f" please specify rename ")

        report_table = Models.Report()
        report_table.Name = rename
        # Default events if not specified
        if not set_event_names:
            set_event_names = ['[Clock].EndOfYear']
            # Ensure variable_spec is a list
        if variable_spec is None:
            raise ValueError("Please specify at least one variable to include in the report table.")
        if isinstance(variable_spec, str):
            variable_spec = [variable_spec]
            # Remove duplicates
        variable_spec = list(dict.fromkeys(variable_spec))  # preserves the order
        # Ensure event names is a list and remove duplicates
        if isinstance(set_event_names, str):
            set_event_names = [set_event_names]
        set_event_names = list(set(set_event_names))

        # Assign _variables and events to the report object
        report_table.VariableNames = variable_spec

        set_event_names = list(set(set_event_names))
        final_command = "\n".join(set_event_names)
        report_table.set_EventNames(final_command.strip().splitlines())
        # Try to find a Zone in scope and attach the report to it
        if rename in self.inspect_model('Models.Report', fullpath=False):
            logger.info(f"{rename} is a database table already only variable specs and events were updated ")
            self.add_report_variable(variable_spec=variable_spec, report_name=rename, set_event_names=set_event_names)
            self.save()
            return self
        sims = self.find_simulations(simulation_name)

        for sim in sims:
            if is_higher_apsim_version(self.Simulations):
                zone = ModelTools.find_child_of_class(sim, Models.Core.Zone)
            else:
                zone = sim.FindDescendant[Models.Core.Zone]()

            if zone is None:
                raise RuntimeError("No Zone found in the Simulation scope to attach the report table.")
            # check_repo = sim.FindDescendant[Models.Report](rename)
            zone.Children.Add(report_table)
        # save the results to recompile
        self.save()

    @simulations.setter
    def simulations(self, value):
        self._simulations = value


APSIMNG = CoreModel

gc.collect()
if __name__ == '__main__':
    from pathlib import Path
    from time import perf_counter

    # Model = FileFormat.ReadFromFile[Models.Core.Simulations](model, None, False)
    os.chdir(Path.home())

    home = Path.home()

    # model = load_default_simulations('maize')
    with CoreModel(model='Maize') as model:
        a = perf_counter()
        model.run('Report', verbose=True, cpu_count=1)
        b = perf_counter()
        logger.info(f"{b - a}, 'seconds")
        df = model.results
        model.add_db_table(variable_spec=['[Clock].Today.Year as year', '[Soil].Nutrient.TotalC[1]/1000 as SOC1'],
                           rename='soc_table')
        model.inspect_model_parameters('Models.Report', model_name='soc_table')


    def add_model(parent, model_type):
        if callable(model_type):
            model = model_type()
        else:
            model = model_type
        parent.Children.Add(model)


    with CoreModel('Maize') as corep:
        corep.run(verbose=True)
        print('Path exists before exit:', Path(corep.path).exists())
        print('datastore Path exists before exit:', Path(corep.datastore).exists())
        corep.add_base_replacements()
        corep.inspect_file(cultivar=True)
        water = ModelTools.find_child(corep.Simulations, child_class=Models.WaterModel.WaterBalance,
                                      child_name='SoilWater')
        waterb = CastHelper.CastAs[Models.WaterModel.WaterBalance](water)
        corep.edit_model('Models.WaterModel.WaterBalance', 'SoilWater', SWCON=[3, 3, 5, 50, 60], )
        inp = corep.inspect_model_parameters('Models.WaterModel.WaterBalance', 'SoilWater')
        print(inp['SWCON'])
        corep.save()
        corep.edit_model_by_path('.Simulations.Simulation.Field.Soil.SoilWater', SWCON=5, indices=[-1])
        inp = corep.inspect_model_parameters('Models.WaterModel.WaterBalance', 'SoilWater')
        sw = corep.inspect_model_parameters_by_path('.Simulations.Simulation.Field.Soil.SoilWater')
        print(corep.inspect_children_by_path('.Simulations.Simulation.Field.Maize'))
        print(sw['SWCON'])
    print('Path exists after exit:', Path(corep.path).exists())
    print('datastore Path exists after exit:', Path(corep.datastore).exists())
