from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.starter.starter import CLR
from pydantic import BaseModel, ConfigDict
from apsimNGpy.core.sim_tools import get_root_model

Models = CLR.Models


class Specification(BaseModel):
    name: str
    specification: str

    @property
    def factor_model(self):
        fm = Models.Factorial.Factor()
        fm.Name = self.name
        fm.set_Specification(self.specification)
        return fm, self.specification


class ExperimentData(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="forbid",
        strict=True,
    )
    apsim_model: ApsimModel
    experiment: Models.Factorial.Experiment
    factors: Models.Factorial.Factors | Models.Factorial.Permutation
    experiment_name: str
    permutation: bool


def build_experiment(model, *, experiment_name, base_simulation, permutation) -> ExperimentData:
    obj = get_root_model(model, simulation_name=base_simulation)
    root, base_sim = obj["root"], obj["simulation"]
    exp = Models.Factorial.Experiment()
    exp.Name = experiment_name
    factor_holder_node = Models.Factorial.Factors()
    exp.Children.Add(factor_holder_node)
    exp.Children.Add(base_sim)
    root.Simulations.Children.Add(exp)
    parent_node = factor_holder_node if not permutation else Models.Factorial.Permutation()
    if permutation:
        factor_holder_node.Children.Add(parent_node)
    return ExperimentData(apsim_model=root, experiment=exp, factors=parent_node,
                          permutation=permutation,
                          experiment_name=experiment_name)
