# finally solved this problem
"""
This module will replace all other modules they are too complicated for nothing
"""
from apsimNGpy.core.core import APSIMNG, Models, RENAME


class Experiment(APSIMNG):
    def __init__(self, model, out_path=None, permutation:bool=True, base_model_simulation:str=None, **kwargs):
        """
        Initialize an Experiment instance, adding the necessary models and factors.

        Args:
            model: The base model.
            out_path: Output path for the APSIMNG simulation.
            **kwargs: Additional parameters for APSIMNG.
        """
        super().__init__(model, out_path, **kwargs)
        self.factor_names = []
        self.permutation = permutation
        # Add core experiment structure

        self.add_model(model_type=Models.Factorial.Experiment, adoptive_parent=Models.Core.Simulations)

        self.add_model(model_type=Models.Factorial.Factors, adoptive_parent=Models.Factorial.Experiment)

        if permutation:
            self.add_model(model_type=Models.Factorial.Permutation, adoptive_parent=Models.Factorial.Factors)

        # Add individual factors
        # self.add_model(model_type=Models.Factorial.Factor, adoptive_parent=Models.Factorial.Factors)

        # Move base simulation under the factorial experiment
        self.move_model(Models.Core.Simulation, Models.Factorial.Experiment, base_model_simulation, None)
        # pp = nexp.Simulations.FindInScope[Models.Factorial.Factor]()
        # pp.set_Specification("[Fertilise at sowing].Script.Amount = 0 to 100 step 20")
        self.save()

    def add_factor(self, specification, factor_name):
        # Add individual factors
        if factor_name in self.factor_names:
            raise ValueError(f"Factor {factor_name} already used")
        if self.permutation:
            parent_factor =Models.Factorial.Permutation
        else:
            parent_factor = Models.Factorial.Factors
        self.add_model(model_type=Models.Factorial.Factor, adoptive_parent=parent_factor, rename=factor_name)
        _added = self.Simulations.FindInScope[Models.Factorial.Factor](factor_name)
        _added.set_Specification(specification)
        self.save()
        self.factor_names.append(factor_name)


if __name__ == "__main__":
    from apsimNGpy.core.base_data import load_default_simulations

    path = load_default_simulations(simulations_object=False)
    experiment = Experiment(path, permutation=True)
    experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20",
                          factor_name='Nitrogen')
    experiment.preview_simulation()
    experiment.run()
