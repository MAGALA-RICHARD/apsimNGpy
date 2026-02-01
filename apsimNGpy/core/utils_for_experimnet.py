import dataclasses
import gc
import re
from collections import OrderedDict

from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.model_loader import get_node_by_path
from apsimNGpy.core.model_tools import ModelTools, Models
from apsimNGpy.core.pythonet_config import CLR
from apsimNGpy.core.run_time_info import APSIM_VERSION_NO, BASE_RELEASE_NO, GITHUB_RELEASE_NO

CastHelper = CLR.CastHelper
NodeUtils = CLR.APsimCore
apsim_version = CLR.apsim_compiled_version
if not CLR.file_format_modified:
    raise ValueError(f"The experiment module is not supported for this type of {CLR.apsim_compiled_version} ")

GC = CLR.System.GC


# ________________helpers______________
def _get_base_sim(_model, base_simulation):
    if base_simulation:
        for _sim in _model.simulations:
            if _sim.Name == base_simulation:
                sim = _sim
                break
        else:
            raise ValueError(f"No base simulation found for this name {base_simulation}")
    else:
        # if not base_simulation, select the first one
        sim = _model.simulations[0]
    return sim


def create(_model, base_simulation, permutation=True):
    # mo = NodeUtils.Node.Clone(_model.Simulations.Node)
    mo = _model.Simulations
    try:
        pass
        data = {'permutation': permutation}
        if base_simulation:
            base = _get_base_sim(_model, base_simulation)
            base_full_path = base.FullPath
        else:
            base = _model.simulations[0]
            base_full_path = base.FullPath
        base_clone = NodeUtils.Node.Clone(base.Node)
        base_clone = CastHelper.CastAs[Models.Core.Simulation](base_clone.Model)
        experiment = Models.Factorial.Experiment()
        data['experiment_node'] = experiment
        factor = Models.Factorial.Factors()
        data['factorial_node'] = factor
        # branch if it is a permutation experiment
        if permutation:
            perm_node = Models.Factorial.Permutation()
            data['permutation_node'] = perm_node
            factor.AddChild(perm_node)
        experiment.AddChild(factor)
        #     # add simulation before experiment to the simulation tree
        experiment.AddChild(base_clone)
        mo.Children.Add(experiment)

        #     # delete base simulation outside the experiment if exists
        simulation_node = get_node_by_path(mo, node_path=base_full_path)
        if simulation_node:
            ModelTools.DELETE(simulation_node.Model)

        # mo.Write(_model.path)
        data['path'] = _model.path
        return data
    finally:
        GC.Collect()


@dataclasses.dataclass(order=True, frozen=False, )
class ExperimentManager:
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

    model: ApsimModel
    parent_factor = None
    experiment_node = None
    factorial_node = None
    permutation_node = None
    factors = None
    specs = None
    counter = 0
    sims = None
    Simulations = None
    init = False
    apsim_model = None

    def __post_init__(self):
        self.factors = OrderedDict()
        self.specs = OrderedDict()
        self.counter = 0
        self.sims = model.simulations
        self.Simulations = model.Simulations
        self.apsim_model = model

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
               experiment.inspect_file()

            The method :meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.inspect_file` is inherited from the
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

        try:
            if APSIM_VERSION_NO > BASE_RELEASE_NO or APSIM_VERSION_NO == GITHUB_RELEASE_NO:
                create(self.apsim_model, base_simulation=base_simulation, permutation=self.permutation)

                self.init = True
            # compile
        finally:

            GC.Collect()
            GC.WaitForPendingFinalizers()
            gc.collect()

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
                manager_names = set(self.apsim_model.inspect_model('Models.Manager', fullpath=False))
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
        if APSIM_VERSION_NO > BASE_RELEASE_NO or APSIM_VERSION_NO == GITHUB_RELEASE_NO:
            parent_factor = ModelTools.find_child_of_class(self.apsim_model.Simulations, parent_class)

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
        GC.Collect()

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
            self.parent_factor.AddChild(node.Model)
        self.apsim_model.save()


if __name__ == '__main__':
    from runner import trial_run as run_p

    with ApsimModel('Maize') as model:
        dt = run_p(model, )
