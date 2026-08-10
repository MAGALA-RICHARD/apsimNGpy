from __future__ import annotations
import re
import warnings
from collections import OrderedDict
from pathlib import Path
from typing import Union, Iterable
from apsimNGpy.core._experiment_from_file import _create_experiment_from_file, NAME, _pre_experiment_test
from apsimNGpy import NodeNotFoundError
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.model_loader import get_node_by_path, AUTO_PATH
from apsimNGpy.core.model_tools import ModelTools, Models
from apsimNGpy.core.runner import invoke_csharp_gc, run_model_externally
from apsimNGpy.core.version_inspector import is_higher_apsim_version
from apsimNGpy.starter.starter import CLR
from apsimNGpy.logger import logger
from apsimNGpy.core.sim_tools import create_factor_table
from apsimNGpy.core._experiment_from_models import _create_experiment_from_models, EXPERIMENT_NAME, build_experiment
import textwrap

CastHelper = CLR.CastHelper
NodeUtils = CLR.APsimCore
System = CLR.System
apsim_version = CLR.apsim_compiled_version


def create_experiment_from_models(
        model,
        specifications: dict[str, str],
        base_simulation: int | str = 0,
        permutation: bool = True,
        experiment_name: str = EXPERIMENT_NAME,
):
    """
    Create an APSIM factorial experiment from a Models namespace.

    Unlike file-based experiment builders, this function creates the
    experiment directly from an APSIM Models namespace object or an existing
    ``ApsimModel`` instance. Factor definitions are supplied as a dictionary,
    preventing duplicate factor names.

    **model** : str | pathlib.Path | ApsimModel
        Path to an APSIM model file or an existing ``ApsimModel`` instance.

    **specifications** : dict[str, str]
        Mapping of unique factor names to APSIM factor specifications. Each
        specification identifies the parameter path and the values to test.

        For example::

            {
                "fertiliser_type":
                    "[Fertilise at sowing].Script.FertiliserType=DAP,NO3N",
                "amount":
                    "[Fertilise at sowing].Script.Amount=0,300",
            }

    **base_simulation** : int | str, default=0
        Index or name of the simulation used as the experiment template.

    **permutation** : bool, default=True
        Whether to generate every possible combination of the supplied factor
        levels. When ``False``, factors are not combined as a full factorial
        permutation.

    **experiment_name** : str, default=EXPERIMENT_NAME
        Name assigned to the generated APSIM experiment.

    Returns
    -------
    ApsimModel
        APSIM model containing the newly created factorial experiment. The
        returned object can be run, inspected, or modified like any other
        ``ApsimModel`` instance.

    Examples
    --------
    Create a factorial experiment with fertiliser type and application rate:

    .. code-block:: python

        experiment = create_experiment_from_models(
            model="Maize.apsimx",
            specifications={
                "fertiliser_type": (
                    "[Fertilise at sowing].Script."
                    "FertiliserType=DAP,NO3N"
                ),
                "amount": (
                    "[Fertilise at sowing].Script.Amount=0,300"
                ),
            },
            base_simulation=0,
            permutation=True,
            experiment_name="FertiliserExperiment",
        )

    Run the experiment and retrieve its results:

    .. code-block:: python

        experiment.run()
        results = experiment.results

        print(results.head())

    .. versionadded:: 1.5.7
    """
    return _create_experiment_from_models(model=model, specifications=specifications,
                                          experiment_name=experiment_name,
                                          permutation=permutation, base_simulation=base_simulation)


def create_experiment_from_file(
        model,
        experiment_from_file,
        name_column,
        sheet=None,
        base_simulation=0,
        experiment_name=NAME,
):
    """
    Create an APSIM factorial experiment from a CSV or Excel factor file (Functional style).

    This function is the public interface for creating an APSIM
    ``FactorFromFile`` experiment. It delegates the implementation to
    :func:`_create_experiment_from_file`.

    Each row in the factor file represents one factorial treatment. Column
    names should correspond to valid APSIM property paths, while
    ``name_column`` identifies the column used to name each generated
    simulation.

    Parameters
    ----------
    model : str, pathlib.Path, or ApsimModel
        APSIM model file or an existing ``ApsimModel`` instance.

    experiment_from_file : str or pathlib.Path
        Path to the CSV or Excel file containing the factorial treatments.

    name_column : str
        Name of the column used to identify and name each generated
        simulation.

    sheet : str, optional
        Excel worksheet name. This is required when ``factor_file_name`` is
        not a CSV file and ignored for CSV files.

    base_simulation : int or str, default=0
        Index or name of the simulation to use as the experiment template.

    experiment_name : str, default=NAME
        Name assigned to the generated APSIM experiment.

    Returns
    -------
    ApsimModel
        The APSIM model root containing the newly created factorial
        experiment. Note this instance has all the methods and attributes on ApsimModel class

    Raises
    ------
    FileNotFoundError
        If the factor file does not exist.

    ValueError
        If an Excel factor file is supplied without a worksheet name.

    RuntimeError
        If the installed APSIM version does not support
        ``Models.Factorial.FactorFromFile``.

    Examples
    --------
    Create an experiment from a CSV file:

    >>> model = create_experiment_from_file(
    ...     model="Maize",
    ...     experiment_from_file="factors.csv",
    ...     name_column="FactorFromFile",
    ...     base_simulation=0,
    ...     experiment_name="SensitivityExperiment",
    ... )

    Create an experiment from an Excel worksheet:

    >>> model = create_experiment_from_file(
    ...     model="Maize",
    ...     experiment_from_file="factors.xlsx",
    ...     name_column="Treatment",
    ...     sheet="SobolSamples",
    ... )

    .. versionadded:: 1.5.6
    """
    experiment_from_file = Path(experiment_from_file)

    if not experiment_from_file.is_file():
        raise FileNotFoundError(
            f"Factor file was not found: {experiment_from_file}"
        )

    return _create_experiment_from_file(
        model=model,
        experiment_from_file=experiment_from_file,
        name_column=name_column,
        sheet=sheet,
        base_simulation=base_simulation,
        experiment_name=experiment_name,
    )


example = """experiment = create_experiment_from_models(
              model="Maize.apsimx",
              specifications={
                  "fertiliser_type": (
                      "[Fertilise at sowing].Script."
                      "FertiliserType=DAP,NO3N"
                  ),
                  "amount": (
                      "[Fertilise at sowing].Script.Amount=0,300"
                  ),
              },
              base_simulation=0,
              permutation=True,
              experiment_name="FertiliserExperiment",
          )

          experiment.run()
          results = experiment.results
"""


class ExperimentManager(ApsimModel):
    """
    .. deprecated:: 1.5.7

       ``ExperimentManager`` is deprecated and will be removed in a future
       release. Use :func:`create_experiment_from_models` instead. The
       functional API provides a simpler experiment-building workflow and
       avoids the state and inheritance requirements of this class.

       For example:

       .. code-block:: python

          experiment = create_experiment_from_models(
              model="Maize.apsimx",
              specifications={
                  "fertiliser_type": (
                      "[Fertilise at sowing].Script.FertiliserType=DAP,NO3N"),
                  "amount": (
                      "[Fertilise at sowing].Script.Amount=0,300"),
              },
              base_simulation=0,
              permutation=True,
              experiment_name="FertiliserExperiment",
          )

          experiment.run()
          results = experiment.results

    Notes
    -----
    This class is retained temporarily for backward compatibility. New code
    should use :func:`create_experiment_from_models`, which produces an instance of ApsimModel with the same functionality as ExperimentManager instance

    It inherits methods and attributes from: :class:`~apsimNGpy.core.apsim.ApsimModel` to manage APSIM Experiments
    with pure factors or permutations. You first need to initiate the instance of this class and then initialize the
    experiment itself with: :meth:`init_experiment`, which creates a new experiment from the suggested base simulation and ``permutation`` type

    The flow of method for :class:`ExperimentManager` class is shown in the diagram below:

    .. code-block:: none

      PlotManager ---> CoreModel ---> ApsimModel ---> ExperimentManager

    Class Roles
    ---------------
    - :class:`~apsimNGpy.core.plotmanager.PlotManager` → Produces visual outputs from model results (Not exposed in the API reference)
    - :class:`~apsimNGpy.core.core.CoreModel`  → contains methods for running and manipulating models (Not exposed in the API reference)
    - :class:`~apsimNGpy.core.apsim.ApsimModel` → Extends :class:`~apsimNGpy.core.core.Coremodel` capabilities with more functionalities
    - :class:`~apsimNGpy.core.experimentmanager.ExperimentManager` → Manages and creates a new experiment from the suggested base.

    """

    def __init__(self, model, out_path=AUTO_PATH):
        message = textwrap.dedent(
            f"""
            ExperimentManager is deprecated and will be removed in a future release.
            Use create_experiment_from_models() instead.

            Migration example
            ----------------------------------------------------------------------
            from apsimNGpy.core.experiment import create_experiment_from_models

            {textwrap.dedent(example).strip()}
            ----------------------------------------------------------------------
            """
        ).strip()

        warnings.warn(
            message,
            FutureWarning,
            stacklevel=2,
        )
        super().__init__(model=model, out_path=out_path)
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
        if not CLR.file_format_modified:
            logger.warning(f"The experiment module is not supported for this APSIM version: {apsim_version} ")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        try:

            invoke_csharp_gc()

            self.clean_up(db=True)
            self.is_simulations_closed = True
        except PermissionError:
            print(self.model_info.datastore)

    # put here during debugging context db file manager, but sure will be removed after full tests

    def init_experiment(self, permutation: bool = True, base_simulation: str = None):

        """
            Initializes the factorial experiment structure inside the APSIM file.

            Parameters
            _____________
            permutation: (bool)
              If True, enables permutation mode; otherwise, uses standard factor crossing.
            base_simulation: (str)
               The base simulation name to use for the experiment. If None, the base simulation is selected
               from the available simulations

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
               experiment.tree()

            The method :meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.tree` is inherited from the
            :class:`~apsimNGpy.core.apsim.ApsimModel` class , but it is still useful here, for example, you can see
            that we added an experiment Model under Simulations as shown below.

            .. code-block:: None

               └── Simulations: .Simulations
                ├── DataStore: .Simulations.DataStore
                └── Experiment: .Simulations.Experiment
                    ├── Factors: .Simulations.Experiment.Factors
                    └── Simulation: .Simulations.Experiment.Simulation
                        ├── Clock: .Simulations.Experiment.Simulation.Clock
                        ├── Field: .Simulations.Experiment.Simulation.Field
                        │   ├── Fertilise at sowing: .Simulations.Experiment.Simulation.Field.Fertilise at sowing
                        │   ├── Fertiliser: .Simulations.Experiment.Simulation.Field.Fertiliser
                        │   ├── Harvest: .Simulations.Experiment.Simulation.Field.Harvest
                        │   ├── Maize: .Simulations.Experiment.Simulation.Field.Maize
                        │   ├── Report: .Simulations.Experiment.Simulation.Field.Report
                        │   ├── Soil: .Simulations.Experiment.Simulation.Field.Soil
                        │   │   ├── Chemical: .Simulations.Experiment.Simulation.Field.Soil.Chemical
                        │   │   ├── NH4: .Simulations.Experiment.Simulation.Field.Soil.NH4
                        │   │   ├── NO3: .Simulations.Experiment.Simulation.Field.Soil.NO3
                        │   │   ├── Organic: .Simulations.Experiment.Simulation.Field.Soil.Organic
                        │   │   ├── Physical: .Simulations.Experiment.Simulation.Field.Soil.Physical
                        │   │   │   └── MaizeSoil: .Simulations.Experiment.Simulation.Field.Soil.Physical.MaizeSoil
                        │   │   ├── Urea: .Simulations.Experiment.Simulation.Field.Soil.Urea
                        │   │   └── Water: .Simulations.Experiment.Simulation.Field.Soil.Water
                        │   ├── Sow using a variable rule: .Simulations.Experiment.Simulation.Field.Sow using a variable rule
                        │   └── SurfaceOrganicMatter: .Simulations.Experiment.Simulation.Field.SurfaceOrganicMatter
                        ├── Graph: .Simulations.Experiment.Simulation.Graph
                        │   └── Series: .Simulations.Experiment.Simulation.Graph.Series
                        ├── MicroClimate: .Simulations.Experiment.Simulation.MicroClimate
                        ├── SoilArbitrator: .Simulations.Experiment.Simulation.SoilArbitrator
                        ├── Summary: .Simulations.Experiment.Simulation.Summary
                        └── Weather: .Simulations.Experiment.Simulation.Weather

            .. seealso::

               :meth:`add_factor`


            """
        self.permutation = permutation

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

        def exp_refresher(mode):
            sim = _get_base_sim()
            print(sim.__dir__())
            print(sim.Children)
            if not sim:
                raise ValueError(f"No base simulation found")
            new_sim = Models.Core.Simulation()
            new_sim.Name = sim.Name
            new_sim.Children = sim.Children
            base = new_sim
            for simx in mode.simulations:  # it does not matter how many experiments exist; we need only one
                ModelTools.DELETE(simx)
            # replace before delete

            try:
                mode.simulations[0] = base
                base = mode.simulations[0]
            except IndexError:
                pass
            experiment = Models.Factorial.Experiment()
            self.experiment_node = experiment
            factor = Models.Factorial.Factors()
            self.factorial_node = factor
            if self.permutation:
                perm_node = Models.Factorial.Permutation()
                self.permutation_node = perm_node
                factor.AddChild(perm_node)
            experiment.AddChild(factor)
            experiment.AddChild(base)
            experi = ModelTools.find_child_of_class(mode.Simulations, Models.Factorial.Experiment)

            if experi:
                ModelTools.DELETE(experi)
            mode.model_info.Node.AddChild(experiment)
            sim_final = CastHelper.CastAs[Models.Core.Simulations](mode.model_info.Node)

            if is_higher_apsim_version():

                simx = ModelTools.find_all_in_scope(sim_final, Models.Core.Simulation)
                simy = [ModelTools.CLONER(i) for i in simx]

                simx = [CastHelper.CastAs[Models.Core.Simulations](i.Node) for i in simy]

                ...

            else:
                simx = list(sim_final.FindAllDescendants[Models.Core.Simulation]())

                if not mode.simulations:
                    mode.simulations.extend(simx)
            # mode.save()

        def refresher():

            replace_ments = ModelTools.find_child(self.Simulations, child_class=Models.Core.Folder,
                                                  child_name='Replacements')

            siM = self.Simulations
            # if replace_ments:
            #     siM.AddChild(replace_ments)
            # create experiment
            _experiments = list(siM.Node.FindAll[Models.Factorial.Experiment]())
            if _experiments:
                raise ValueError('Not supported at the moment, provide a base simulation and build from scratch')
            # add then new experiment Node
            experiment = Models.Factorial.Experiment()
            experiment.Children.Clear()
            self.experiment_node = experiment
            factor = Models.Factorial.Factors()
            factor.Children.Clear()
            self.factorial_node = factor
            # branch if it is a permutation experiment
            if self.permutation:
                perm_node = Models.Factorial.Permutation()
                self.permutation_node = perm_node
                factor.AddChild(perm_node)
            experiment.AddChild(factor)
            # add simulation before experiment to the simulation tree
            sim = _get_base_sim()
            base_full_path = sim.FullPath
            siM.Children.Add(experiment)
            sim.SetParent(experiment)
            experiment.Children.Add(sim)
            # remove base simulation
            simulation_node = get_node_by_path(siM, node_path=base_full_path)

            siM.RemoveChild(simulation_node.Model)
            # if simulation_node:
            #     ModelTools.DELETE(simulation_node.Model)
            datastore = ModelTools.find_child_of_class(siM, Models.Storage.DataStore)
            if datastore:
                datastore = CastHelper.CastAs[Models.Storage.DataStore](datastore)
            datastore.set_FileName(self.datastore)

            # siM.Write(self.path)

            self.Simulations = siM
            self.save()

        if is_higher_apsim_version():

            refresher()

        else:
            exp_refresher(self)

        self.init = True
        # compile

    def factor(
            self,
            *,
            param_node_location: str,
            node_type: Union[str, ModelTools.CLASS_MODEL],
            param_identifier: str,
            values: Union[str, Iterable[Union[str, int, float]]] = None,
            step: Union[int, float] = None,
            bounds: tuple = None,
            rename=""
    ):
        """
        Define a factor specification for APSIM sensitivity or factorial experiments, Then uses `add_factor` under the hood.
        Can be used if you don't want to go through the hassle of providing a specification

        This method constructs and registers a factor expression that varies a given
        parameter across a set of values. The parameter is identified by its parent
        node location and parameter name, and is formatted into APSIM-compatible syntax.

        Parameters
        ----------
        param_node_location : str
            Identifier of the node containing the parameter. Can be:
            - Node name (e.g., "Clock", "Soil")
            - Full node path (e.g., ".Simulations.Simulation.Clock")

        node_type : str | ModelTools.CLASS_MODEL
            Type of the node (e.g., "Manager", "Clock", Models.Clock).
            Used to resolve node context and formatting rules.
            Behind the scene, this parameter is used to check if the node, where the parameter is located exists

        param_identifier : str
            Name or path of the parameter within the node (e.g., "Start"). Other parameters identifiers may be long e.g., those related to
            Plant models, e.g Leaf.Photosynthesis.RUE.FixedValue for radiation use efficiency, etc. For Manager related paramters
            expected param identifier is 'Script.ParameterName' if script is not included it will be prefixed on it.

        values : Iterable[str | int | float]
            Sequence of values to assign to the parameter. Does not support step, so even if step is provided, it will be ignored

        step : int | float, optional
            Step size for APSIM factor definition. If provided, appended as:
            ``step <value>``. representing the interval of the values from each other

        bounds : tuple[int | float, int | float], optional
            Tuple specifying the lower and upper bounds for APSIM factor definition:

            - bounds[0] : lower_bound (int | float)
                Minimum value of the parameter.

            - bounds[1] : upper_bound (int | float)
                Maximum value of the parameter.

            Notes
            -----
            - Both lower and upper bounds must be provided together.
            - Partial specification (only one bound) is not allowed.
        rename: str, optional
          a new name used to identify the parameter. useful if you expect more than one paramters on the same node.
          if not given, the name will be the parameter identifier
        Raises
        ------
        ValueError
            If the specified node cannot be found for the given type.

        Notes
        -----
        - For ``Manager`` nodes, parameters are assumed to reside under ``Script``:
          ``[Node].Script.<param> = values``.
        - For all other nodes:
          ``[Node].<param> = values``.
        - If ``param_node_location`` is a full path, only the terminal node name
          is used in the factor specification.
        - add [index] if parameter is targeting the soil layered nodes such as Physical, Organic etc.,
        - if all values, lower_bound, upper_bound are provided priority is given to values because it is computationally less intensive

        Examples
        --------
        .. code-block:: python

            model.factor(
                param_node_location="Sow Using a variable rule",
                node_type="Manager",
                param_identifier="Population",
                values=[1, 5, 10],
            )
            # use a full path for adding nitrogen fertilizers
            model.factor(
                param_node_location='.Simulations.Experiment.Simulation.Field.Fertilise at sowing',
                node_type="Manager",
                param_identifier="Amount",
                values=[0, 100, 200],
                step=50,
            )
            # add organic related values
             model.factor(
                param_node_location="Organic",
                node_type="Organic",
                param_identifier="Carbon[1]", # represents first soil layer
                values=[0.45, 1, 3],
            )
            #use bounded values instead of lists
             model.factor(
                param_node_location="Organic",
                node_type="FOM",
                param_identifier="FOM[1]", # represents first soil layer
                bounds =(100, 4000), step =500
            )

        """

        node_info = self.has_node(param_node_location, node_type=node_type)
        if not node_info.get('ok'):
            raise NodeNotFoundError(f"node identifier {param_node_location} of type {node_type} does not exists")
        fullpath = node_info['fullpath']

        def _knit_param_path(*, node_id, _param, _values, _step):
            if _values:
                joined_values = ", ".join(map(str, _values))
            elif bounds:
                assert len(bounds) == 2, 'Bounds must have two values'
                lower_bound, upper_bound = bounds
                if upper_bound < lower_bound:
                    raise ValueError(f"upper bound cant be higher than the lower bound")
                joined_values = f"{lower_bound} to {upper_bound}"
                if _step is not None and _step is not False:
                    joined_values += f" step {_step}"
            else:
                raise ValueError(
                    f"Please provide either bounds or values, defined them as list in using values argument")

            if node_type.lower() == 'manager' and 'Script' not in _param:
                fup = f"[{node_id}].Script.{_param} = {joined_values}"
            else:
                fup = f"[{node_id}].{_param} = {joined_values}"

            return fup

        # get param info
        param = param_identifier
        if not fullpath:

            fp = _knit_param_path(node_id=param_node_location,
                                  _param=param, _values=values, _step=step)
        else:
            _name = param_node_location.split('.')[-1]
            fp = _knit_param_path(node_id=_name,
                                  _param=param, _values=values, _step=step)
        # add factor
        name = rename or param_identifier.replace(".", '')
        self.add_factor(specification=fp, factor_name=name)
        print(fp)
        print(node_info)

    def add_factor(self, specification: str, factor_name: str = None, **kwargs):
        """
        Add a new factor to the experiment from an APSIM-style script specification.

        Parameters
        ----------
        specification : str
            An APSIM script-like expression that defines the parameter variation,
            e.g. ``"[Organic].Carbon[1] = 1.2, 1.8"`` or
            ``"[Sow using a variable rule].Script.Population = 6, 10"``.
        factor_name : str, optional
            A unique name for the factor. If not provided, a name is auto-generated
            from the target variable in ``specification`` (typically the last token).
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

           from apsimNGpy.core.experimentmanager import ExperimentManager

           # initialize the model
           experiment = ExperimentManager('Maize', out_path='my_experiment.apsimx')

           # initialize experiment with permutation crossing of factors
           experiment.init_experiment(permutation=True)

        Inspect model components:

        .. code-block:: python

           experiment.inspect_model('Models.Manager')

        .. code-block:: none

           ['.Simulations.Experiment.Simulation.Field.Sow using a variable rule',
            '.Simulations.Experiment.Simulation.Field.Fertilise at sowing',
            '.Simulations.Experiment.Simulation.Field.Harvest']

        .. code-block:: python

           experiment.inspect_model('Models.Factorial.Experiment')

        .. code-block:: none

           ['.Simulations.Experiment']

        1) Add a factor associated with a manager script
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        .. code-block:: python

           experiment.add_factor(
               specification='[Sow using a variable rule].Script.Population = 6, 10',
               factor_name='Population'
           )

        2) Add a factor associated with a soil node (e.g., initial soil organic carbon)
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        .. code-block:: python

           experiment.add_factor(
               specification='[Organic].Carbon[1] = 1.2, 1.8',
               factor_name='initial_carbon'
           )

        Check how many factors have been added:

        .. code-block:: python

           experiment.n_factors
           # 2

        Inspect factors:

        .. code-block:: python

           experiment.inspect_model('Models.Factorial.Factor')

        .. code-block:: none

           ['.Simulations.Experiment.Factors.Permutation.Nitrogen',
            '.Simulations.Experiment.Factors.Permutation.initial_carbon']

        Get factor names only:

        .. code-block:: python

           experiment.inspect_model('Models.Factorial.Factor', fullpath=False)

        .. code-block:: none

           ['Nitrogen', 'initial_carbon']

        Run the model and summarize results:

        .. code-block:: python

           experiment.run()
           df = experiment.results
           df.groupby(['Population', 'initial_carbon'])['Yield'].mean()

        .. code-block:: none

                       Population  initial_carbon
           10          1.2         6287.538183
                       1.8         6225.861601
           6           1.2         5636.529504
                       1.8         5608.971306
           Name: Yield, dtype: float64

        Save the experiment (same as :class:`~apsimNGpy.core.apsim.ApsimModel`):

        .. code-block:: python

           experiment.save()

        See also :meth:`~apsimNGpy.core.apsim.ApsimModel.save`.

        Common Pitfalls
        ---------------
        1) Adding the same specification with only a different ``factor_name``
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        .. code-block:: python

           experiment.add_factor(
               specification='[Organic].Carbon[1] = 1.2, 1.8',
               factor_name='initial_carbon'
           )
           experiment.add_factor(
               specification='[Organic].Carbon[1] = 1.2, 1.8',
               factor_name='carbon'
           )

        By default, specifications are evaluated on their arguments, so the example above
        creates two identical factors—usually not desired.

        .. code-block:: python

           experiment.save()
           experiment.inspect_model('Models.Factorial.Factor')

        .. code-block:: none

           ['.Simulations.Experiment.Factors.Permutation.initial_carbon',
            '.Simulations.Experiment.Factors.Permutation.carbon']

        2) Invalid specification path to target parameters
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Common causes include referencing models not present in the script, adding quotes
        around numeric levels, or inserting stray spaces in paths.

        Invalid (extra quotes):

        .. code-block:: python

           experiment.add_factor(
               specification='[Organic].Carbon[1] = "1.2, 1.8"',
               factor_name='initial_carbon'
           )

        Correct:

        .. code-block:: python

           experiment.add_factor(
               specification='[Organic].Carbon[1] = 1.2, 1.8',
               factor_name='initial_carbon'
           )

        Invalid (extra space in path):

        .. code-block:: python

           experiment.add_factor(
               specification='[Organic]. Carbon[1] = 1.2, 1.8',
               factor_name='initial_carbon'
           )

        Correct:

        .. code-block:: python

           experiment.add_factor(
               specification='[Organic].Carbon[1] = 1.2, 1.8',
               factor_name='initial_carbon'
           )
        """

        if not self.init:
            raise ValueError("Please initialize the experiment first by calling: self.init_experiment method")
        # Auto-generate factor name from specification if not provided
        if factor_name is None:
            factor_name = specification.split("=")[0].strip().split(".")[-1]

        # If it's a Script-based specification, validate linkage
        if 'Script' in specification:
            matches = re.findall(r"\[(.*?)\]", specification)
            if matches:
                manager_names = set(self.inspect_model('Models.Manager', fullpath=False))
                linked = set(matches) & manager_names
                if not linked:
                    if matches:
                        matches = ', '.join(matches)
                    raise ValueError(f'Specification{specification} has no linked script `{matches}` in the model')

        # Record factor info
        self.factors[factor_name] = (specification, kwargs)

        # Choose parent node and parent class
        parent_factor = self.permutation_node if self.permutation else self.factorial_node
        parent_class = Models.Factorial.Permutation if self.permutation else Models.Factorial.Factors
        if is_higher_apsim_version():
            parent_factor = ModelTools.find_child_of_class(self.Simulations, parent_class)

        new_factor = Models.Factorial.Factor()
        new_factor.Name = factor_name
        new_factor.set_Specification(specification)

        self.specs[factor_name] = new_factor

        # Maintain counter and avoid index error
        index = len(self.specs) - 1
        try:
            # Try to remove existing child at index before inserting
            if 0 <= index < len(parent_factor.Children):
                old_child = parent_factor.Children[index]
                if old_child is not None:
                    ...
                    parent_factor.Children.Remove(old_child)
                    # NodeUtils.Node.RemoveChild(old_child)
                #  ModelTools.DELETE(old_child)

        except System.ArgumentOutOfRangeException:
            pass

        # Insert a new factor
        parent_factor.Children.Add(new_factor)
        self.parent_factor = parent_factor

    @property
    def n_factors(self):
        """
            Returns:
                int: The total number of active factor specifications currently added to the experiment.
            """
        return len(self.specs)

    def finalize(self):
        """"
        Finalizes the experiment setup by re-creating the internal APSIM factor nodes from specs.

        This method is designed as a guard against unintended modifications and ensures that all
        factor definitions are fully resolved and written before saving.

        Side Effects:
            Clears existing children from the parent factor node.
            Re-creates and attaches each factor as a new node.
            Triggers model saving.
    """
        self.parent_factor.Children.Clear()
        for name, spec in self.specs.items():
            node = NodeUtils.Node.Create(spec, parent=self.parent_factor)
            self.parent_factor.Children.Add(node.Model)
        self.save()
        invoke_csharp_gc()


def pre_experiment_test(params,
                        base_model,
                        outputs,
                        base_simulation=0,
                        func=create_experiment_from_file,
                        use_threads=True, ):
    """
        Test parameter paths before creating a large-scale experiment.

        Each parameter is tested against the base APSIM model to identify valid
        and invalid parameter paths.

        **params** : dict[str, tuple[Any, ...]] | list[dict[str, tuple[Any, ...]]]
            Parameter paths mapped to the values that should be tested.

        **base_model** : str | Path | object
            Base APSIM model or path to the model file.

        **base_simulation** : int, default=0
            Index of the simulation used for parameter testing.

        **outputs** : list, str, tuple required.
            The simulated output, which will be used to measure the parameters changes

        **func** : callable, default=_create_experiment_from_file
            Function used to create the experiment model.

        **use_threads** : bool, default=True
            Whether to use threads for parallel parameter testing.

        Returns
        -------
        dict
            A dictionary containing ``passed`` and ``failed`` parameter lists.
        Examples:
        -------------

        .. code-block:: python

            vals = {"[Maize].Leaf.Photosynthesis.RUE.FixedValue": (1, 3, 2.5),
                '[Sow using a variable rule].Script.Population': (1, 12, 6)}
            out = pre_experiment_test(vals, 'Maize', outputs=['Yield', 'Maize.Grain.Wt'])

        .. code-block:: python

            {'passed': [{'[Sow using a variable rule].Script.Population': (1, 12, 6)},
              {'[Maize].Leaf.Photosynthesis.RUE.FixedValue': (1, 3, 2.5)}],
             'failed': []}

        """
    return _pre_experiment_test(params,
                                base_model,
                                outputs=outputs,
                                base_simulation=base_simulation,
                                func=func,
                                use_threads=use_threads, )


__all__ = ['ExperimentManager', "create_experiment_from_file", 'create_factor_table', 'pre_experiment_test']
if __name__ == '__main__':
    with ExperimentManager("Maize", out_path='dtb.apsimx') as exp:
        exp.init_experiment(permutation=True)
        # exp.add_factor("[Fertilise at sowing].Script.Amount = 0 to 200 step 20")
        exp.add_factor("[Fertilise at sowing].Script.FertiliserType= DAP,NO3N")
        # exp.add_factor(specification="[Sow using a variable rule].Script.RowSpacing = 100, 450, 700",
        #                factor_name='Population')
        exp.factor(
            param_node_location="Organic",
            node_type="Organic",
            param_identifier="FOM[1]",  # represents first soil layer
            bounds=(100, 4000), step=500
        )
        exp.factor(
            param_node_location="Organic",
            node_type="Organic",
            param_identifier="FOM[2]",  # represents first soil layer
            bounds=(100, 4000), step=500
        )

        # exp.add_factor(specification="[Sow using a variable rule].Script.RowSpacing = 100, 450, 700",
        #                factor_name='Population')
        exp.factor(
            param_node_location="Maize",
            node_type="Models.PMF.Plant",
            param_identifier="Leaf.Photosynthesis.RUE.FixedValue",  #
            values=[0.9, 2, 3], rename=''
        )
        exp.factor(param_node_location='Sow using a variable rule', node_type='Manager',
                   **{'param_identifier': 'Script.Population', 'values': [10, 12, 4], 'step': None})
        exp.run()
        # exp.add_factor(specification="[Sow using a variable rule].Script.RowSpacing = 100, 450, 700",
        #                factor_name='Population')
        # exp.finalize()

    print('datastore Path exists after exit:', Path(exp.datastore).exists())
    vals = {"[Maize].Leaf.Photosynthesis.RUE.FixedValue": (1, 3, 2.5),
            '[Fertilise at sowing].Script.Amount': (0, 300),
            '[Sow using a variable rule].Script.Population': (1, 12, 6)}
    out = pre_experiment_test(vals, 'Maize', outputs=['Yield', 'Maize.Grain.Wt'])
    print(out)
