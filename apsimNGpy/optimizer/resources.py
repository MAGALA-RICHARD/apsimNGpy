from apsimNGpy.optimizer.base import AbstractProblem, VarDesc
from apsimNGpy.core.apsim import ApsimModel
from dataclasses import dataclass, field
from scipy.optimize import minimize
import wrapdisc
from tqdm import tqdm
from typing import Union
SIMULATIONS = object()

class BaseProblem(AbstractProblem):
    def __init__(self, model: str,
                 simulation=SIMULATIONS,
                 controls=None,
                 control_vars=None,
                 labels=None,

                 func = None,
                 cache_size=400):

        # Initialize parent classes explicitly
        AbstractProblem.__init__(self, model,max_cache_size=cache_size)
        self.model = model
        self.simulation = simulation if simulation is not SIMULATIONS else 'all'
        self.controls = controls or []
        self.control_vars = control_vars or []
        self.labels = labels or []
        self.cache = True
        self.cache_size = cache_size


    def add_control(self, model_type, model_name, parameter_name,
                    vtype, start_value, bounds=None):
        self._evaluate_args(model_type, model_name, parameter_name)
        label = f"{parameter_name}"
        self.control_vars.append(self.VarDesc(model_type, model_name, parameter_name, vtype, label, start_value, bounds))
        return self # To support method chaining

    def setup_edit(self, x) -> None:

        edit = self.edit_model
        for i, varR in enumerate(self.control_vars):
            vtype = varR.vtype
            value = x[i]
            if vtype==int or vtype =='int':
                value = int(value)
            else:
                value = round(value, 4)
            edit(
                model_type=varR.model_type,
                simulations=self.simulation,
                model_name=varR.model_name,
                cacheit=True,
                **{varR.parameter_name: value}
            )
            x[i] =value

        return x.tolist()


    def set_objective_function(self, x):
        xl = self.setup_edit(x)
        # Try local per-instance results cache first
        if self.cache and (cached := self.get_cached(*xl)):

               return cached

        SCORE  = self.evaluate(x)
        if self.cache:
            self.insert_cache_result(*xl, result=SCORE)
        self._last_score = SCORE
        return SCORE

    def minimize_problem(self, **kwargs):
        try:
            x0 = kwargs.pop("x0", [1] * len(self.control_vars))
            max_iter = kwargs.get("options", {}).get("maxiter", 400)
            labels = [i.label for i in self.control_vars]
            pbar = tqdm(total=max_iter, desc=f"Optimizing:: {','.join(labels)}", unit=" iterations")
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
        finally:
            print(self._cache)
            self.clear_cache()
def problemspec(model, simulation, factors):
    ...
if __name__ == "__main__":
    ##xample
    maize_model = "Maize"
    problem = BaseProblem(model=maize_model, simulation='Simulation', cache=True)
    class Problem(BaseProblem):
        def __init__(self, model=None, simulation='Simulation'):
            super().__init__(model, simulation, cache)
            self.cache = cache
            self.simulation = simulation

        def evaluate(self, x, **kwargs):
           return -self.run(verbose=False).results.Yield.mean()
    problem  = Problem(maize_model, simulation='Simulation')
    problem.add_control('Manager', "Sow using a variable rule", 'Population',  vtype=int)
    problem.add_control('Manager', "Sow using a variable rule", 'RowSpacing', vtype=int)

    res = problem.minimize_problem( method  ='Powell', x0=(5, 500), bounds =[(1, 12),(500, 750)],  options={
        # 'xatol': 1e-4,      # absolute error in xopt between iterations
        # 'fatol': 1e-4,      # absolute error in func(xopt) between iterations
        'maxiter': 1000,    # maximum number of iterations
        'disp': True ,      # display optimization messages

    })



