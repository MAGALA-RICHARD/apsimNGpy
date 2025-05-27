from apsimNGpy.optimizer.base import AbstractProblem, VarDesc
from apsimNGpy.core.apsim import ApsimModel
from dataclasses import dataclass, field
from scipy.optimize import minimize, differential_evolution
import wrapdisc
from functools import cache
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
        self.control_vars.append(VarDesc(model_type, model_name, parameter_name, vtype, label, start_value, bounds))
        return self # To support method chaining
    @property
    def bounds(self):
        bounds = []
        for var in self.control_vars:
            bounds.append(var.bounds)
        return tuple(bounds)

    def starting_values(self):
        starting_values = []
        for var in self.control_vars:
            starting_values.append(var.start_value)
        return tuple(starting_values)
    def insert_controls(self, x) -> None:

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
        xl = self.insert_controls(x)
        # Try local per-instance results cache first
        if self.cache and (cached := self.get_cached(*xl)):

               return cached

        SCORE  = self.evaluate(x)
        if self.cache:
            self.insert_cache_result(*xl, result=SCORE)
        self._last_score = SCORE
        return SCORE

    def minimize_problem(self, **kwargs):
        """
        scipy.optimize.minimize provide a number of optimization algorithms see table below or for details check their website:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html#scipy.optimize.minimize
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+
        | Method           | Type                  | Gradient Required | Handles Bounds | Handles Constraints | Notes                                       |
        +==================+=======================+===================+================+=====================+=============================================+
        | Nelder-Mead      | Local (Derivative-free)| No                | No             | No                  | Simplex algorithm                           |
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+
        | Powell           | Local (Derivative-free)| No                | Yes            | No                  | Direction set method                        |
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+
        | CG               | Local (Gradient-based) | Yes               | No             | No                  | Conjugate Gradient                          |
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+
        | BFGS             | Local (Gradient-based) | Yes               | No             | No                  | Quasi-Newton                                |
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+
        | Newton-CG        | Local (Gradient-based) | Yes               | No             | No                  | Newton's method                             |
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+
        | L-BFGS-B         | Local (Gradient-based) | Yes               | Yes            | No                  | Limited memory BFGS                         |
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+
        | TNC              | Local (Gradient-based) | Yes               | Yes            | No                  | Truncated Newton                            |
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+
        | COBYLA           | Local (Derivative-free)| No                | No             | Yes                 | Constrained optimization by linear approx.  |
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+
        | SLSQP            | Local (Gradient-based) | Yes               | Yes            | Yes                 | Sequential Least Squares Programming        |
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+
        | trust-constr     | Local (Gradient-based) | Yes               | Yes            | Yes                 | Trust-region constrained                    |
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+
        | dogleg           | Local (Gradient-based) | Yes               | No             | No                  | Requires Hessian                            |
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+
        | trust-ncg        | Local (Gradient-based) | Yes               | No             | No                  | Newton-CG trust region                      |
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+
        | trust-exact      | Local (Gradient-based) | Yes               | No             | No                  | Trust-region, exact Hessian                 |
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+
        | trust-krylov     | Local (Gradient-based) | Yes               | No             | No                  | Trust-region, Hessian-free                  |
        +------------------+-----------------------+-------------------+----------------+---------------------+---------------------------------------------+

        """

        try:
            x0 = kwargs.pop("x0", [1] * len(self.control_vars))
            if 'bounds' not in kwargs.keys():
                kwargs['bounds'] = self.bounds
            max_iter = kwargs.get("options", {}).get("maxiter", 400)
            labels = [i.label for i in self.control_vars]
            pbar = tqdm(total=max_iter, desc=f"Optimizing:: {','.join(labels)}", unit=" iterations")
            call_counter = {"count": 0}
            def wrapped_obj(x):
                call_counter["count"] += 1
                pbar.update(1)
                #pbar.set_postfix({"score": round(self._last_score, 2)})
                return self.set_objective_function(x)

            result = differential_evolution(wrapped_obj, x0=self.starting_values(), **kwargs)
            labels = [c.label for c in self.control_vars]
            result.x_vars = dict(zip(labels, result.x))
            return result
        finally:
            self.clear_cache()
    def minimize_with_de(self, **kwargs):

        try:
            x0 = kwargs.pop("x0", [1] * len(self.control_vars))
            if 'bounds' not in kwargs.keys():
                kwargs['bounds'] = self.bounds
            max_iter = kwargs.get("options", {}).get("maxiter", 400)
            labels = [i.label for i in self.control_vars]
            pbar = tqdm(total=max_iter, desc=f"Optimizing:: {','.join(labels)}", unit=" iterations")
            call_counter = {"count": 0}
            def wrapped_obj(x):
                call_counter["count"] += 1
                pbar.update(1)
                #pbar.set_postfix({"score": round(self._last_score, 2)})
                return self.set_objective_function(x)

            result = differential_evolution(wrapped_obj, self.bounds, args=(), strategy='best1bin',
                                      maxiter=1000, popsize=15, tol=0.01,
                                      mutation=(0.5, 1), recombination=0.7,
                                      seed=None, callback=None, disp=False,
                                      polish=True, init='latinhypercube',
                                      atol=0, updating='immediate',
                                      workers=1, constraints=())
            labels = [c.label for c in self.control_vars]
            result.x_vars = dict(zip(labels, result.x))
            return result
        finally:
            self.clear_cache()
def problemspec(model, simulation, factors):
    ...
if __name__ == "__main__":
    ##xample
    maize_model = "Maize"
    class Problem(BaseProblem):
        def __init__(self, model=None, simulation='Simulation'):
            super().__init__(model, simulation)
            self.cache = True
            self.simulation = simulation

        def evaluate(self, x, **kwargs):
           return -self.run(verbose=False).results.Yield.mean()
    problem  = Problem(maize_model, simulation='Simulation')
    problem.add_control('Manager', "Sow using a variable rule", 'Population',  int,5, bounds=[2, 15])
    #problem.add_control('Manager', "Sow using a variable rule", 'RowSpacing', int, 500)

    # res = problem.minimize_problem( method  ='Powell',  options={
    #     # 'xatol': 1e-4,      # absolute error in xopt between iterations
    #     # 'fatol': 1e-4,      # absolute error in func(xopt) between iterations
    #     'maxiter': 1000,    # maximum number of iterations
    #     'disp': True ,      # display optimization messages
    #
    # })
    res = problem.minimize_with_de()



