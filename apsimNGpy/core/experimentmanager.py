import gc
import os
import re
import sys

from apsimNGpy.core.apsim import ApsimModel
from collections import OrderedDict
from apsimNGpy.core.model_tools import ModelTools, Models
from apsimNGpy.core.cs_resources import CastHelper
from apsimNGpy.core.pythonet_config import is_file_format_modified
from apsimNGpy.core.run_time_info import APSIM_VERSION_NO, BASE_RELEASE_NO, GITHUB_RELEASE_NO
from apsimNGpy.core.model_loader import to_json_string

if is_file_format_modified():
    import APSIM.Core as NodeUtils
    import System

    structure = Models.Core.ApsimFile.Structure
else:
    from apsimNGpy.core.config import apsim_version

    raise ValueError(f"The experiment module is not supported for this type of {apsim_version()} ")


class ExperimentManager(ApsimModel):
    def __init__(self, model, out_path=None):
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

    # noinspection GrazieInspection
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
                Replaces any existing ExperimentManager node with a new configuration.
                Clones the base simulation and adds it under the experiment.
                Never mind, though all this edits are made on a cloned model.

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

        def exp_refresher(mode):
            sim = mode.simulations[0]
            base = ModelTools.CLONER(sim)
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

            if APSIM_VERSION_NO > BASE_RELEASE_NO or APSIM_VERSION_NO == GITHUB_RELEASE_NO:

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
            siM = NodeUtils.Node.Create(Models.Core.Simulations())
            siM.AddChild(Models.Storage.DataStore())
            # create experiment
            experiment = Models.Factorial.Experiment()
            self.experiment_node = experiment
            factor = Models.Factorial.Factors()
            self.factorial_node = factor
            # branch if it is a permutation experiment
            if self.permutation:
                perm_node = Models.Factorial.Permutation()
                self.permutation_node = perm_node
                factor.AddChild(perm_node)
            experiment.AddChild(factor)
            # add simulation before experiment to the simulation tree
            if base_simulation:
                for _sim in self.simulations:
                    if _sim.Name == base_simulation:
                        sim = _sim
                        break
                else:
                    raise ValueError(f"No base simulation found for this name {base_simulation}")
            else:
                sim = self.simulations[0]
            siM.AddChild(experiment)
            experiment.AddChild(sim)
            siM = CastHelper.CastAs[Models.Core.Simulations](siM.Model)
            # siM.Write(self.path)
            self.Simulations = siM

            # add experiment

        if APSIM_VERSION_NO > BASE_RELEASE_NO or APSIM_VERSION_NO == GITHUB_RELEASE_NO:
            refresher()
        else:
            exp_refresher(self)
        self.init = True
        # compile
        self.save()
        c = gc.collect()

    def add_factor(self, specification: str, factor_name: str = None, **kwargs):
        """
           Adds a new factor to the experiment based on an APSIM script specification.

          Parameters
          ----------
           specification: (str)
               A script-like APSIM expression that defines the parameter variation.

           factor_name: (str, optional)
               A unique name for the factor. If not provided, factor_name auto-generated as the variable parameter name,
               usually the last string before real variables in specification string.

           **kwargs: Optional metadata or configuration (not yet used internally).

           Raises
           _______
               ValueError: If a Script-based specification references a non-existent or unlinked manager script.

           Side Effects:
               Inserts the factor into the appropriate parent node (Permutation or Factors).
               If a factor at the same index already exists, it is safely deleted before inserting the new one.

          Examples::

               from apsimNGpy.core.experimentmanager import ExperimentManager
               # initialize the model
               experiment = ExperimentManager('Maize', out_path = 'my_experiment.apsimx')
               # initialize experiment without permutation crossing of the factors
               experiment.init_experiment(permutation=True)

        All methods from :class:`~apsimNGpy.core.apsim.ApsimModel` are available in this
        class and are not altered in any way. For example, we can still inspect, run,
        and visualize the results:

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

        Now we are ready to add factors

        1. Add a factor associated with a manager script
        ------------------------------------------------

        .. code-block:: python

             experiment.add_factor(specification=f"[Sow using a variable rule].Script.Population = 6, 10", factor_name='Population')

        2. Add a factor associated with a soil sode e.g., soil organic like initial soil organic carbon
        -----------------------------------------------------------------------------------------------

        .. code-block:: python

            experiment.add_factor(specification='[Organic].Carbon[1] = 1.2, 1.8', factor_name='initial_carbon')

        Check how many factors have been added to the model

        .. code-block:: python

          experiment.n_factors
            2
        it is possible to inspect the factors

        .. code-block:: python

          experiment.inspect_model('Models.Factorial.Factor')

        .. code-block:: none

            ['.Simulations.Experiment.Factors.Permutation.Nitrogen',
            '.Simulations.Experiment.Factors.Permutation.'initial_carbon']

        Checking the names of the factors as given

        .. code-block:: python

           experiment.inspect_model('Models.Factorial.Factor', fullpath=False)

        .. code-block:: none
           ['Nitrogen', 'initial_carbon']

        We are ready to :meth:`~apsimNGpy.experimentmanager.ExperimentManager.run` the model

        .. code-block:: python

             experiment.run()
             # get results
             df = experiment.results
             # compute the mean across each experiment
             df.groupby(['Population', 'initial_carbon'])['Yield'].mean()

        .. code-block:: none

                     Population  initial_carbon
            10          1.2               6287.538183
                        1.8               6225.861601
            6           1.2               5636.529504
                        1.8               5608.971306
            Name: Yield, dtype: float64

        Saving the experiment is the same as in :class:`~apsimNGpy.core.apsim.ApsimModel`

       .. code-block:: python

           experiment.save()

       See more details in:
       :meth:`~apsimNGpy.core.apsim.ApsimModel.save`

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
        if APSIM_VERSION_NO > BASE_RELEASE_NO or APSIM_VERSION_NO == GITHUB_RELEASE_NO:
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
            self.parent_factor.AddChild(node.Model)
        self.save()


if __name__ == '__main__':
    exp = ExperimentManager('Soybean', out_path='exp.apsimx')
    exp.init_experiment(permutation=True)
    exp.add_factor("[Fertilise at sowing].Script.Amount = 0 to 200 step 20")
    exp.add_factor("[Fertilise at sowing].Script.FertiliserType= DAP,NO3N")
    exp.add_factor(specification="[Sow using a variable rule].Script.RowSpacing = 100, 450, 700",
                   factor_name='Population')
    exp.add_factor(specification="[Sow using a variable rule].Script.RowSpacing = 100, 450, 700",
                   factor_name='Population')
    # exp.add_factor(specification="[Sow using a variable rule].Script.RowSpacing = 100, 450, 700",
    #                factor_name='Population')
    # exp.finalize()
    # exp.preview_simulation()
