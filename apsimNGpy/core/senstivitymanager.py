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
    This class inherits methods and attributes from: :class:`~apsimNGpy.core.apsim.ApsimModel` to manage APSIM Experiments
    with pure factors or permutations. You first need to initiate the instance of this class and then initialize the
    experiment itself with: :meth:`init_experiment`, which creates a new experiment from the suggested base simulation and ``permutation`` type

    The flow of method for :class:`ExperimentManager` class is shown in the diagram below:


    .. mermaid::

       flowchart LR
           PlotManager["PlotManager"]
           CoreModel["CoreModel"]
           ApsimModel["ApsimModel"]
           ExperimentManager["ExperimentManager"]

           PlotManager --> CoreModel
           CoreModel --> ApsimModel
           ApsimModel --> ExperimentManager

    Class Roles
    ---------------
    - :class:`~apsimNGpy.core.plotmanager.PlotManager` → Produces visual outputs from model results (Not exposed in the API reference)
    - :class:`~apsimNGpy.core.core.CoreModel`  → contains methods for running and manipulating models (Not exposed in the API reference)
    - :class:`~apsimNGpy.core.apsim.ApsimModel` → Extends :class:`~apsimNGpy.core.core.Coremodel` capabilities with more functionalities
    - :class:`~apsimNGpy.core.experimentmanager.ExperimentManager` → Manages and creates a new experiment from the suggested base.

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

        from System.IO import File  # dont remove I don't know why if imported it works magic

        try:

            invoke_csharp_gc()

            self.clean_up(db=True)
            self.is_simulations_closed = True
        except PermissionError:
            print(self.model_info.datastore)

    def setup(self, agg_col_name, method: str = 'Morris',
              table_name: str = 'Report',
              base_simulation: str = None,
              num_paths=None):

        """
            Initializes the sensitivity experiment structure inside the APSIM file.

            Parameters
            _____________
            method: (str)
              either morris or sobol are accepted.
            table_name: (str)
               for collecting the results
            base_simulation: (str)
               The base simulation name to use for the experiment. If None, the base simulation is selected
               from the available simulations.
            num_paths: (int) , optional
               for morris

            Side Effects:
            ____________
                - Replaces any existing ExperimentManager node with a new configuration.
                - Clones the base simulation and adds it under the experiment.
                - Never mind, though all this edits are made on a cloned model.
                - In the presence of replacements, they are moved or retained directly at the simulations node


            Examples::

               from apsimNGpy.core.experimentmanager import ExperimentManager
               # initialize the model
               experiment = ExperimentManager('Maize', out_path = 'my_experiment.apsimx')
               # initialize experiment without permutation crossing of the factors
               experiment.init_experiment(permutation=False)
               # initialize experiment with permutation =True
               experiment.init_experiment(permutation=True)
               # initialize experiment with a preferred base simulation name
               experiment.init_experiment(permutation=False, base_simulation='Simulation')
               # view the simulation tree
               experiment.inspect_file()

            The method :meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.inspect_file` is inherited from the
            :class:`~apsimNGpy.core.apsim.ApsimModel` class , but it is still useful here, for example, you can see
            that we added an experiment Model under Simulations as shown below.

            .. code-block:: None

            .. seealso::

               :meth:`add_factor`


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
            self.sensitivity_node.Name = self.method
            self.sensitivity_node.Children.Clear()
            self.sensitivity_node.TableName = table_name
            self.sensitivity_node.AggregationVariableName = agg_col_name
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
        Initialize an experiment:

        .. code-block:: python


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

    def finalize(self, method: str, aggregation_column_name, base_simulation: str = None, num_path: int = None):
        """"
        Finalizes the experiment setup by re-creating the internal APSIM factor nodes from specs.

        This method is designed as a guard against unintended modifications and ensures that all
        factor definitions are fully resolved and written before saving.

        Side Effects:
            Clears existing children from the parent factor node.
            Re-creates and attaches each factor as a new node.
            Triggers model saving.
         """
        self.setup(agg_col_name=aggregation_column_name,method=method, base_simulation=base_simulation, num_paths=num_path)
        invoke_csharp_gc()


import gc


def create_parameter(path, lower, upper, name):
    param = Models.Sensitivity.Parameter()
    param.Path = path
    param.LowerBound = lower
    param.UpperBound = upper
    param.Name = name
    return param


gc.collect()
if __name__ == '__main__':
    exp = SensitivityManager("Maize", out_path='dtb.apsimx')
    exp.add_sens_factor(name='cnr', path='Field.SurfaceOrganicMatter.InitialCNR', lower_bound=10, upper_bound=120)
    exp.add_sens_factor(name='cn2bare', path='Field.Soil.SoilWater.CN2Bare', lower_bound=70, upper_bound=100)
    exp.finalize(method='Morris', aggregation_column_name='Clock.Today')
    exp.preview_simulation()
    pp = create_parameter(path='Field.SurfaceOrganicMatter.InitialCNR', lower=80, upper=100, name='cnr')

    mor = Models.Morris()

    param_list = List[Models.Sensitivity.Parameter]()
    param_list.Add(pp)

    # assign to Morris

    mor.Parameters = param_list
