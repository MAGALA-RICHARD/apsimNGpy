import re
import sys

from apsimNGpy.core.apsim import ApsimModel
from collections import OrderedDict
from apsimNGpy.core.model_tools import ModelTools, Models
from apsimNGpy.core.cs_resources import CastHelper
from apsimNGpy.core.pythonet_config import is_file_format_modified
from apsimNGpy.core.config import APSIM_VERSION_NO, BASE_RELEASE_NO
from apsimNGpy.core.model_loader import to_json_string
if is_file_format_modified():
    import APSIM.Core as NodeUtils
    import System
    structure = Models.Core.ApsimFile.Structure
else:
    from apsimNGpy.core.config import apsim_version

    raise ValueError(f"The experiment module is not supported for this type of {apsim_version()} ")


class ExperimentManager(ApsimModel):
    def __init__(self, model, out_path=None, out=None):
        super().__init__(model=model, out_path=out_path, out=out)
        self.parent_factor = None
        self.experiment_node = None
        self.factorial_node = None
        self.permutation_node = None
        self.factors = OrderedDict()
        self.specs = OrderedDict()
        self.counter = 0
        self.sims = self.simulations
        self.init = False

    def init_experiment(self, permutation=True):

        """
            Initializes the factorial experiment structure inside the APSIM file.

            Args:
                permutation (bool): If True, enables permutation mode; otherwise, uses standard factor crossing.

            Side Effects:
                Replaces any existing ExperimentManager node with a new configuration.
                Clones the base simulation and adds it under the experiment.
            """
        self.permutation = permutation

        def exp_refresher(mode):
            sim = mode.simulations[0]
            base = ModelTools.CLONER(sim)
            for simx in mode.simulations:  # it does not matter how many experiments exist, we need only one
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

            if APSIM_VERSION_NO > BASE_RELEASE_NO:

                simx = ModelTools.find_all_in_scope(sim_final, Models.Core.Simulation)
                simy= [ModelTools.CLONER(i) for i in simx]

                simx = [CastHelper.CastAs[Models.Core.Simulations](i.Node) for i in simy]

                ...

            else:
                simx = list(sim_final.FindAllDescendants[Models.Core.Simulation]())

                if not mode.simulations:
                    mode.simulations.extend(simx)
            # mode.save()

        def refresher():
            sims = Models.Core.Simulations()
            siM = NodeUtils.Node.Create(Models.Core.Simulations())
            siM.AddChild(Models.Storage.DataStore())
            # create experiment
            experiment = Models.Factorial.Experiment()
            self.experiment_node = experiment
            factor = Models.Factorial.Factors()
            self.factorial_node = factor
            if self.permutation:
                perm_node = Models.Factorial.Permutation()
                self.permutation_node = perm_node
                factor.AddChild(perm_node)
            experiment.AddChild(factor)
            # add simulation before experiment to simulation tree
            sim = self.simulations[0]
            #simx = NodeUtils.Node.Create(sim)
            base = ModelTools.CLONER(sim)

            siM.AddChild(experiment)

            # add experiment



        if APSIM_VERSION_NO > BASE_RELEASE_NO:
           refresher()
        else:
            exp_refresher(self)
        self.init = True

    def add_factor(self, specification: str, factor_name: str = None, **kwargs):
        """
           Adds a new factor to the experiment based on an APSIM script specification.

           Args:
               specification (str): A script-like APSIM expression that defines the parameter variation.
               factor_name (str, optional): A unique name for the factor; auto-generated if not provided.
               **kwargs: Optional metadata or configuration (not yet used internally).

           Raises:
               ValueError: If a Script-based specification references a non-existent or unlinked manager script.

           Side Effects:
               Inserts the factor into the appropriate parent node (Permutation or Factors).
               If a factor at the same index already exists, it is safely deleted before inserting the new one.
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
                    raise ValueError('Specification has no linked script in the model')

        # Record factor info
        self.factors[factor_name] = (specification, kwargs)

        # Choose parent node and parent class
        parent_factor = self.permutation_node if self.permutation else self.factorial_node
        parent_class = Models.Factorial.Permutation if self.permutation else Models.Factorial.Factors

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
