import os
import re
import sys
from pathlib import Path
from apsimNGpy.core.config import configuration

from apsimNGpy.core.apsim import ApsimModel
from collections import OrderedDict

from apsimNGpy.core.model_tools import ModelTools, Models

from apsimNGpy.core.cs_resources import CastHelper
from apsimNGpy.core.pythonet_config import is_file_format_modified
from apsimNGpy.core.run_time_info import APSIM_VERSION_NO, BASE_RELEASE_NO, GITHUB_RELEASE_NO
from apsimNGpy.core.model_loader import to_json_string, recompile, get_node_by_path

from apsimNGpy.core_utils.deco import add_outline
from apsimNGpy.core.runner import invoke_csharp_gc, run_model_externally
from apsimNGpy.core.utils_for_experimnet import create

if is_file_format_modified():
    import APSIM.Core as NodeUtils
    import System

    structure = Models.Core.ApsimFile.Structure
else:
    from apsimNGpy.core.config import apsim_version

    raise ValueError(f"The experiment module is not supported for this type of {apsim_version()} ")

import inspect
from typing import Type, Union
from apsimNGpy.core.version_inspector import is_higher_apsim_version

from System.Collections.Generic import List


class SensitivityManager(ApsimModel):
    """
    This class inherits methods and attributes from: :class:`~apsimNGpy.core.apsim.ApsimModel` to manage APSIM Sensitivity Analysis in apsimNGpy
    You first need to initialize the class, define parameters and build the sensitivity analysis model


    The flow of method for :class:`ExperimentManager` class is shown in the diagram below:


    .. mermaid::

       flowchart LR
           PlotManager["PlotManager"]
           CoreModel["CoreModel"]
           ApsimModel["ApsimModel"]
           SensitivityManager["SensitivityManager"]

           PlotManager --> CoreModel
           CoreModel --> ApsimModel
           ApsimModel --> SensitivityManager

    Class Roles
    ---------------
    - :class:`~apsimNGpy.core.plotmanager.PlotManager` → Produces visual outputs from model results (Not exposed in the API reference)
    - :class:`~apsimNGpy.core.core.CoreModel`  → contains methods for running and manipulating models (Not exposed in the API reference)
    - :class:`~apsimNGpy.core.apsim.ApsimModel` → Extends :class:`~apsimNGpy.core.core.Coremodel` capabilities with more functionalities
    - :class:`~apsimNGpy.core.senstivitymanager.SensitivityManager` → Manages and creates a new sensitivity experiment model from the suggested base.

    """

    def __init__(self, model, out_path=None):
        super().__init__(model=model, out_path=out_path)
        self.method_class = None
        self.sensitivity_node = None
        self.parent_factor = None
        self.experiment_node = None
        self.factorial_node = None
        self.permutation_node = None
        self.factors = OrderedDict()
        self.specs = OrderedDict()
        self.counter = 0
        self.sims = self.simulations
        self.init = False
        self.is_simulations_closed = False
        self.names_list = set()
        self.hash_name_and_path = []
        self.param_collections = List[Models.Sensitivity.Parameter]()
        self.method = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        try:

            invoke_csharp_gc()

            self.clean_up(db=True)
            self.is_simulations_closed = True
        except PermissionError:
            print(self.model_info.datastore)

    def setup(self, agg_col_name: str, method: str = 'Morris',
              table_name: str = 'Report',
              base_simulation: str = None,
              num_paths=None,
              jumps=10,
              intervals=20):

        """
        Initialize the sensitivity analysis experiment structure within the APSIM file.

        Parameters
        ----------
        agg_col_name : str
            Name of the column in the database table used for aggregating values.
        method : str, optional
            Sensitivity method to use. Supported options are ``'morris'`` and ``'sobol'``.
            Default is ``'Morris'``.
        table_name : str, optional
            Name of the table where sensitivity results will be stored.
        base_simulation : str, optional
            Name of the base simulation to use for constructing the experiment. If ``None``,
            the first available simulation is used as the base.
        num_paths : int, optional
            Number of parameter paths for the Morris method. The Morris method generates
            multiple parameter trajectories across the N-dimensional parameter space.
            The number of paths should be sufficiently large to adequately explore the
            parameter space and capture variability in model responses. If ``None``, a
            default value is computed based on the number of decision variables.
       jumps : int, optional
            Applicable only to the Morris method. Determines the number of discrete
            steps (also called “jumps”) each parameter is allowed to move within the
            defined sampling grid. A higher number of jumps increases the number of
            possible perturbation positions for a parameter and therefore results in
            a more detailed exploration of the input space. However, increasing the
            number of jumps also leads to more computational demand because the total
            number of model evaluations scales with jumps × paths × (k + 1), where k
            is the number of parameters. If omitted, a reasonable default based on
            the number of decision variables is used.
        intervals : int, optional
            Applicable only to the Morris method. Specifies the number of levels into
            which the range of each parameter is discretized. The parameter space is
            divided into `intervals` equally spaced points, and the Morris trajectories
            (paths) move across these points to compute elementary effects. A larger
            number of intervals increases the resolution of the sensitivity analysis,
            allowing finer distinction between parameter influences, but also expands
            the computational cost. When not provided, a default value is chosen
            according to recommended Morris design practices.

        Side Effects
        ------------
        - If a Replacements folder is present, it is moved or retained under the
          ``Simulations`` node as appropriate.
        - A new sensitivity experiment (Morris or Sobol) is added under ``Simulations``.

        Examples
        --------
        Create and initialize a sensitivity experiment:

        .. code-block:: python

            from apsimNGpy.core.senstivitymanager import SensitivityManager
            exp = SensitivityManager("Maize", out_path="dtb.apsimx")

        Add sensitivity factors:

        .. code-block:: python

            exp.add_sens_factor(name='cnr',
                                path='Field.SurfaceOrganicMatter.InitialCNR',
                                lower_bound=10,
                                upper_bound=120)

            exp.add_sens_factor(name='cn2bare',
                                path='Field.Soil.SoilWater.CN2Bare',
                                lower_bound=70,
                                upper_bound=100)

            exp.finalize(method='Morris', aggregation_column_name='Clock.Today')
            exp.run()

        You can inspect the updated APSIM file structure using the
        :meth:`~apsimNGpy.core.senstivitymanager.SensitivityManager.inspect_file`
        method, inherited from
        :class:`~apsimNGpy.core.apsim.ApsimModel`. This allows you to verify that a
        sensitivity analysis model has been added under the ``Simulations`` node:

    .. code-block:: python

        exp.inspect_file()



            """
        method = method.lower()
        self.method = method
        methods = {'morris': Models.Morris, 'sobol': Models.Sobol, }
        if method not in methods:
            raise NotImplementedError("Method not supported by this method try any of 'sobol' or 'morris'")
        method_class = methods[method]

        def _get_base_sim():
            if base_simulation:
                for _sim in self.simulations:
                    if _sim.Name == base_simulation:
                        sim = _sim
                        break
                else:
                    raise ValueError(f"No base simulation found for this name {base_simulation}")
            else:
                sim = self.simulations[0]
            return sim

        def refresher():
            from apsimNGpy.core.config import load_crop_from_disk
            replace_ments = ModelTools.find_child(self.Simulations, child_class=Models.Core.Folder,
                                                  child_name='Replacements')

            siM = self.Simulations
            if replace_ments:
                siM.AddChild(replace_ments)
            # create experiment
            _experiments = list(siM.Node.FindAll[method_class]())
            if _experiments:
                raise ValueError('Not supported at the moment, provide a base simulation and build from scratch')
            # add then new experiment Node
            self.method_class = method_class
            self.sensitivity_node = method_class()
            self.sensitivity_node.Name = self.method.capitalize()
            self.sensitivity_node.Children.Clear()
            self.sensitivity_node.TableName = table_name
            self.sensitivity_node.AggregationVariableName = agg_col_name
            if hasattr(self.sensitivity_node, 'Jump'):
                self.sensitivity_node.Jump = jumps
            if hasattr(self.sensitivity_node, 'NumIntervals'):
                self.sensitivity_node.NumIntervals = intervals
            if num_paths is None:
                n_paths = self.default_num_paths()
            else:
                n_paths = num_paths
            self.sensitivity_node.NumPaths = n_paths
            if self.names_list:
                self.sensitivity_node.Parameters = self.param_collections
            else:
                raise ValueError(f"No sensitivity  parameter factors set yet")
            sim = _get_base_sim()
            base_full_path = sim.FullPath
            siM.Children.Add(self.sensitivity_node)
            sim.SetParent(self.sensitivity_node)
            self.sensitivity_node.Children.Add(sim)
            # remove base simulation
            simulation_node = get_node_by_path(siM, node_path=base_full_path)

            siM.RemoveChild(simulation_node.Model)

            datastore = ModelTools.find_child_of_class(siM, Models.Storage.DataStore)
            if datastore:
                datastore = CastHelper.CastAs[Models.Storage.DataStore](datastore)
            datastore.set_FileName(self.datastore)
            self.Simulations = siM
            self.save()

        if is_higher_apsim_version(self.Simulations):
            refresher()

        self.init = True
        # compile

    def add_sens_factor(self, name, path, lower_bound, upper_bound, **kwargs):
        """
        Add a new factor to the experiment from an APSIM-style script specification.

        Parameters
        ----------
        name : str
            A unique name for the factor.
        path : str, optional
            full node path specification
        lower_bound : int, required
            lower limit of the factor
        upper bound : int required
           Upper limit of the factor
        **kwargs
            Optional metadata or configuration (currently unused).

        Raises
        ------
        ValueError
            If a script-based specification references a non-existent or unlinked
            manager script.

        Side Effects
        ------------
        - Inserts the factor into the appropriate parent node (``Permutation`` or ``Factors``).
        - If a factor at the same index already exists, it is safely deleted before inserting
          the new one.

        Notes
        -----
        All methods from :class:`~apsimNGpy.core.apsim.ApsimModel` remain available on this
        class. You can still inspect, run, and visualize results.

        Examples
        --------
        configure factors:

        .. code-block:: python

            exp.add_sens_factor(name='cnr', path='Field.SurfaceOrganicMatter.InitialCNR', lower_bound=10, upper_bound=120)
            exp.add_sens_factor(name='cn2bare', path='Field.Soil.SoilWater.CN2Bare', lower_bound=70, upper_bound=100)


        """

        if name in self.names_list:
            raise ValueError(f"Duplicate factor detected or {name} already exists")
        self.names_list.add(name)
        p_p = self.create_parameter(path=path, lower=lower_bound, upper=upper_bound, name=name)
        self.param_collections.Add(p_p)

    def create_parameter(self, name, path, lower, upper):
        param = Models.Sensitivity.Parameter()
        param.Path = path
        param.Name = name
        param.LowerBound = lower
        param.UpperBound = upper
        return param

    @property
    def n_factors(self):
        """
            Returns:
                int: The total number of active factor specifications currently added to the experiment.
            """
        return len(self.names_list)

    def default_num_paths(self) -> int:
        """
        Compute a reasonable default NumPaths for Morris sensitivity analysis.

        Parameters
        ----------
        k : int
            Number of decision variables.

        Returns
        -------
        int
            Recommended number of Morris paths.
        """
        # base rule
        r = 10 + 2 * self.n_factors

        # cap at 50 (optional but practical for APSIM)
        return min(r, 50)

    def statistics(self):
        tables_to_read = {'sobol': 'SobolStatistics', 'morris': 'MorrisStatistics'}
        from apsimNGpy.core_utils.database_utils import read_db_table, get_db_table_names
        read_table = tables_to_read[self.method]
        tables_in_store = get_db_table_names(self.datastore)
        if read_table not in tables_in_store:
            raise RuntimeError(f"table {read_table} is not available for extraction, perhaps not yet run the sensitivity experiment")
        df = read_db_table(self.datastore, read_table)
        return df

    @property
    def default_jumps(self) -> int:
        return min(self.n_factors + 1, 15)

    @property
    def default_intervals(self) -> int:
        return min(max(6, self.n_factors), 10)

    def build_sense_model(self, method: str, aggregation_column_name, base_simulation: str = None,
                          num_path: int = None,
                          jumps: int = None,
                          intervals: int = None):
        """
        To be released in V0.39.12.21

        Finalize and build the sensitivity analysis experiment inside the APSIM file.

        This method acts as a convenience wrapper around :meth:`setup`, providing a
        simplified interface for constructing the sensitivity experiment. It configures
        the sensitivity method (Morris or Sobol), assigns the aggregation column,
        selects or infers the base simulation, and applies the number of paths for
        Morris analyses. After configuration, the APSIM file is updated and a garbage
        collection call is issued to ensure clean C# object management.

        Parameters
        ----------
        method : str
            Sensitivity analysis method to apply. Supported values are
            ``'morris'`` and ``'sobol'``.
        aggregation_column_name : str
            Name of the column in the data table used to aggregate values during
            sensitivity analysis.
        base_simulation : str, optional
            Name of the base simulation for constructing the experiment. If ``None``,
            the first available simulation in the APSIM file is used.
        num_path : int, optional
            Number of parameter paths for the Morris method. If ``None``, a default is
            computed automatically based on the number of decision variables.
        jumps : int, optional
            Morris method only. Specifies the number of discrete step movements
            (``"jumps"``) allowed along each parameter dimension during the construction
            of a trajectory. Each Morris trajectory begins at a randomly selected point
            in the parameter space and perturbs one parameter at a time by a fixed step
            size ``Δ``. The ``jumps`` value determines how many such perturbations can
            occur within each trajectory.

            Increasing ``jumps`` improves the diversity of sampled elementary effects,
            especially in complex models with non-linear interactions. However, higher
            values also increase computational cost because the total number of model
            evaluations scales approximately as:

            .. math::

                N_{mathrm{sims}} = r , (k + 1)

            where ``r`` is the number of paths and ``k`` is the number of parameters.
            If ``jumps`` is not provided, a recommended default is chosen to balance
            computational efficiency with adequate exploration of the parameter space.
        intervals : int, optional
            Morris method only. Defines the number of discrete levels into which each
            parameter range is partitioned. The Morris method samples parameters on a
            ``p``-level grid, where ``p = intervals``. Each parameter range is divided
            into ``intervals`` equally spaced points, and trajectories move across these
            grid points to compute elementary effects.

            A larger number of intervals increases the resolution of the sampling grid,
            enabling more detailed sensitivity insights and reducing discretization
            error. However, high values also increase computational overhead and may not
            necessarily improve screening quality. When omitted, a reasonable default is
            selected according to standard Morris design guidelines.

        Side Effects
        ------------
        - Modifies the APSIM file by inserting a sensitivity analysis experiment under
          the ``Simulations`` node.
        - Ensures proper .NET resource cleanup via an explicit garbage collection call.

        """

        if jumps is None:
            jumps = self.default_jumps
        if intervals is None:
            intervals = self.default_intervals
        self.setup(agg_col_name=aggregation_column_name, method=method, base_simulation=base_simulation,
                   num_paths=num_path, jumps=jumps, intervals=intervals)
        invoke_csharp_gc()


import gc

gc.collect()
if __name__ == '__main__':
    from apsimNGpy.core_utils.database_utils import get_db_table_names

    exp = SensitivityManager("Maize", out_path='sob.apsimx')
    exp.add_sens_factor(name='cnr', path='Field.SurfaceOrganicMatter.InitialCNR', lower_bound=10, upper_bound=120)
    exp.add_sens_factor(name='cn2bare', path='Field.Soil.SoilWater.CN2Bare', lower_bound=70, upper_bound=100)
    exp.build_sense_model(method='sobol', aggregation_column_name='Clock.Today')
    exp.inspect_file()
    # exp.preview_simulation()
    exp.run(verbose=True)
    print(get_db_table_names(exp.datastore))

    # _____________________________
    # Morris
    # ----------------------------------
    exp = SensitivityManager("Maize", out_path='morris.apsimx')
    exp.add_sens_factor(name='cnr', path='Field.SurfaceOrganicMatter.InitialCNR', lower_bound=10, upper_bound=120)
    exp.add_sens_factor(name='cn2bare', path='Field.Soil.SoilWater.CN2Bare', lower_bound=70, upper_bound=100)
    exp.build_sense_model(method='Morris', aggregation_column_name='Clock.Today')
    exp.inspect_file()
    exp.preview_simulation()

    # mor = Models.Morris()
    #
    # param_list = List[Models.Sensitivity.Parameter]()
    # param_list.Add(pp)
    #
    # # assign to Morris
    #
    # mor.Parameters = param_list
