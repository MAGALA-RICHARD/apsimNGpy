from apsimNGpy.optimizer.base import AbstractProblem
from apsimNGpy.core.apsim import ApsimModel
from dataclasses import dataclass, field
import wrapdisc

# this work in progress
@dataclass
class BaseProblem(AbstractProblem):
    apsim: ApsimModel
    simulation: str
    controls: list = field(default_factory=list)
    labels: list = field(default_factory=list)
    cache: bool = False
    cache_size: int = 100

    def __post_init__(self):
        super().__init__(max_cache_size=self.cache_size)
        self.results = {}

    @dataclass(slots=True, frozen=True)
    class VarDesc:
        model_type: str
        model_name: str
        parameter_name: str
        var_type: wrapdisc.var
        label: str

    def add_control(self, model_type, model_name, parameter_name, var_type, label=None):
        if label is None:
            label = f"{parameter_name}"
        self.controls.append(self.VarDesc(model_type, model_name, parameter_name, var_type, label))

    def setUP(self, x) -> None:
        edit = self.apsim.edit_model
        for i, varR in enumerate(self.controls):
            edit(
                model_type=varR.model_type,
                simulations=self.simulation,
                model_name=varR.model_name,
                cacheit=True,
                **{varR.parameter_name: x[i]}
            )


    def set_objective_function(x):
        # Try local per-instance results cache first
        if self.cache and (cached := self.get_cached(*x)):
            return cached

        SCORE  = self.evaluate(x)

        if self.cache:
            self.insert_cache_result(result=SCORE, *x)
        return SCORE

    def minimize_problem(self, **kwargs):
        x0 = kwargs.pop("x0", [1] * len(self.controls))
        result = minimize(self.set_objective_function, x0=x0, **kwargs)
        labels = [c.label for c in self.controls]
        result.x_vars = dict(zip(labels, result.x))
        return result

if __name__ == "__main__":
    model = ApsimModel("Maize")
    problem = BaseProblem(model, simulation='Simulation', cache=True)
    def evaluate(x, **kwargs):

        model.run()

    problem.add_control('Manager', "Sow using a variable rule", 'Population', 'population')
    print(problem.controls)



