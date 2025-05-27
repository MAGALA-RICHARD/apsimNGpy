from apsimNGpy.optimizer.base import AbstractProblem
from apsimNGpy.core.apsim import ApsimModel
from dataclasses import dataclass, field
from scipy.optimize import minimize
import wrapdisc
from tqdm import tqdm
SIMULATIONS = object()

class BaseProblem(AbstractProblem):
    def __init__(self, model: str,
                 simulation=SIMULATIONS,
                 controls=None,
                 control_vars=None,
                 labels=None,
                 cache=True,
                 func = None,
                 cache_size=300):

        # Initialize parent classes explicitly
        AbstractProblem.__init__(self, model,max_cache_size=cache_size)


        # Assign fields
        self.model = model
        self.simulation = simulation if simulation is not SIMULATIONS else 'all'
        self.controls = controls or []
        self.control_vars = control_vars or []
        self.labels = labels or []
        self.cache = cache
        self.cache_size = cache_size


    @dataclass(slots=True, frozen=True)
    class VarDesc:
        model_type: str
        model_name: str
        parameter_name: str
        var_type: wrapdisc.var
        label: str

    def add_control(self, model_type, model_name, parameter_name, vtype, label=None):
        self._evaluate_args(model_type, model_name, parameter_name, vtype)
        if label is None:
            label = f"{parameter_name}"
        self.control_vars.append(self.VarDesc(model_type, model_name, parameter_name, vtype, label))

    def setup_edit(self, x) -> None:

        edit = self.edit_model
        for i, varR in enumerate(self.control_vars):
            value = x[i]
            if isinstance(value, float):
                value = round(value, 5)# i guess we dont need to much precission here
            edit(
                model_type=varR.model_type,
                simulations=self.simulation,
                model_name=varR.model_name,
                cacheit=True,
                **{varR.parameter_name: value}
            )


    def set_objective_function(self, x):
        # Try local per-instance results cache first
        if self.cache and (cached := self.get_cached(*x)):
               print(cached)
               return cached
        self.setup_edit(x)
        SCORE  = self.evaluate(x)
        if self.cache:
            self.insert_cache_result(x, SCORE)
        self._last_score = SCORE
        return SCORE

    def minimize_problem(self, **kwargs):
        x0 = kwargs.pop("x0", [1] * len(self.control_vars))
        max_iter = kwargs.get("options", {}).get("maxiter", 100)
        labels = [i.label for i in self.control_vars]
        pbar = tqdm(total=max_iter, desc=f"Optimizing:: {','.join(labels)}", unit=" iter")
        call_counter = {"count": 0}
        def wrapped_obj(x):
            call_counter["count"] += 1
            pbar.update(1)
            #pbar.set_postfix({"score": round(self._last_score, 2)})
            return self.set_objective_function(x)

        result = minimize(wrapped_obj, x0=x0, **kwargs)
        labels = [c.label for c in self.control_vars]
        result.x_vars = dict(zip(labels, result.x))
        return result

if __name__ == "__main__":
    ##xample
    maize_model = "Maize"
    problem = BaseProblem(model=maize_model, simulation='Simulation', cache=True)
    class Problem(BaseProblem):
        def __init__(self, model=None, simulation='Simulation',cache=True):
            super().__init__(model, simulation, cache)
            self.cache = cache
            self.simulation = simulation

        def evaluate(self, x, **kwargs):
           return -self.run(verbose=False).results.Yield.mean()
    problem  = Problem(maize_model, simulation='Simulation', cache=True)
    problem.add_control('Manager', "Sow using a variable rule", 'Population', 'population')

    res = problem.minimize_problem( method  ='Powell', bounds =[(1, 12)], options={'maxiter': 26})



