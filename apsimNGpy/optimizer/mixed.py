"""
This allows for mixed variable optimization by encoding the categorical variables
"""
from pathlib import Path

import numpy as np

from apsimNGpy.core_utils.utils import timer

from apsimNGpy.optimizer.simple_problem import Problem, Solvers, auto_guess
from scipy.optimize import minimize, differential_evolution
import subprocess
from tqdm import tqdm
from apsimNGpy.optimizer.resources import AbstractProblem, SIMULATIONS, ContinuousVariableProblem, cache, VarDesc
try:
    import wrapdisc
except ModuleNotFoundError as mnf:
    print('installing wrapdisc package')
    package_name = "wrapdisc"
    command = ["pip", "install", package_name]
    # Running the command
    subprocess.run(command, check=True)

import operator
from typing import Any

import scipy.optimize

from wrapdisc import Objective
from wrapdisc.var import ChoiceVar, GridVar, QrandintVar, QuniformVar, RandintVar, UniformVar

@cache
def _variable_type(type_name: str) -> str:
    variable_types = {
        'choice': ChoiceVar,
        'grid': GridVar,
        'qrandint': QrandintVar,
        'quniform': QuniformVar,
        'randint': RandintVar,
        'uniform': UniformVar
    }
    try:
       return variable_types[type_name.lower()]
    except KeyError:
          raise ValueError(f"Invalid type '{type_name}'. Use one of: {', '.join(var_map)}")


class MixedVariableProblem(ContinuousVariableProblem):
    def __init__(self, model: str,
                 simulation=SIMULATIONS,
                 controls=None,
                 control_vars=None,

                 func=None,
                 cache_size=400):

        # Initialize parent classes explicitly
        AbstractProblem.__init__(self, model, simulation)
        self.model = model
        self.simulation = simulation if simulation is not SIMULATIONS else 'all'
        self.controls = controls or []
        self.control_vars = control_vars or []
        self.labels =  []
        self.cache = False
        self.cache_size = cache_size
        self.max_cache_size =cache_size
        self.pbar = None


    def add_control(
            self,
            model_type,
            model_name,
            parameter_name,
            vtype,
            start_value,
            bounds=None,
            categories=None,
            values=None,
            q=None
    ) -> "ContinuousVariableProblem":
        """
        Adds a control variable to the optimization problem.

        Parameters:
            model_type (str): APSIM model type (e.g., 'Manager').
            model_name (str): Name of the model instance.
            parameter_name (str): Name of the parameter to control.
            vtype (type): Variable type class (e.g., ChoiceVar, RandintVar).
            start_value: Initial value for the variable.
            bounds (tuple, optional): Lower and upper bounds for numeric variables.
            categories (list, optional): Category names for categorical variables.
            values (list, optional): Grid values for GridVar.
            q (float, optional): Quantization value for quantized variables.

        Returns:
            self: Enables method chaining.
        """

        self._evaluate_args(model_type, model_name, parameter_name, vtype)

        label = f"{parameter_name}"
        vtype_cls = _variable_type(vtype)

        if vtype_cls == ChoiceVar:
            _vtype = ChoiceVar(categories=categories)
        elif vtype_cls == GridVar:
            _vtype = GridVar(values)
        elif vtype_cls == QuniformVar:
            if not bounds or q is None:
                raise ValueError("QuniformVar requires bounds and q.")
            _vtype = QuniformVar(lower=bounds[0], upper=bounds[1], q=q)
        elif vtype_cls == RandintVar:
            if not bounds:
                raise ValueError("RandintVar requires bounds.")
            _vtype = RandintVar(lower=bounds[0], upper=bounds[1])
        elif vtype_cls == QrandintVar:
            if not bounds or q is None:
                raise ValueError("QrandintVar requires bounds and q.")
            _vtype = QrandintVar(lower=bounds[0], upper=bounds[1], q=q)
        else:
            raise TypeError(f"Unsupported variable type: {vtype_cls}")
        self.labels.append(label)
        self.control_vars.append(
            VarDesc(
                model_type=model_type,
                model_name=model_name,
                parameter_name=parameter_name,
                vtype=_vtype,
                label=label,
                start_value=start_value,
                bounds=bounds
            )
        )

        return self  # Enable method chaining
    def _insert_controls(self, x) -> None:

        edit = self.edit_model

        for i, varR in enumerate(self.control_vars):
            vtype = varR.vtype
            value = x[i]
            edit(
                model_type=varR.model_type,
                simulations=self.simulation,
                model_name=varR.model_name,
                cacheit=True,
                **{varR.parameter_name: value}
            )


        return x

    @property
    def variables(self):
        var_s = []
        for index, value in enumerate(self.control_vars):
           var_s.append(value.vtype)
        return var_s

    from scipy.optimize import differential_evolution
    from tqdm import tqdm
    def set_objective_function(self, x):
        xl = self._insert_controls(x)
        SCORE  = self.evaluate(xl)
        return SCORE

    def minimize_with_de(self,
            args=(),
            strategy='best1bin',
            maxiter=1000,
            popsize=15,
            tol=0.01,
            mutation=(0.5, 1),
            recombination=0.7,
            rng=None,
            callback=None,
            disp=True,
            polish=True,
            init='latinhypercube',
            atol=0,
            updating='immediate',
            workers=1,
            constraints=(),
            x0=None,
            *,
            integrality=None,
            vectorized=False):
        """
        Runs differential evolution on the wrapped objective function.
        Reference: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html
        """

        try:

            self.open_pbar(labels = [l.label for l in self.control_vars])
            call_counter = {"count": 0}
            func = getattr(self, 'set_objective_function')
            def wrapped_obj(x, *args):
                call_counter["count"] += 1
                self.pbar.update(1)
                return self.set_objective_function(x)

            wrapped = Objective(
                func= wrapped_obj,
                variables=self.variables
            )

            bounds = wrapped.bounds


            # Handle initial guess
            initial_guess = self.starting_values()

            encoded_initial = wrapped.encode(initial_guess)


            # Run optimization
            result = differential_evolution(
                wrapped,
                bounds=wrapped.bounds,
                args=args,
                strategy=strategy,
                maxiter=maxiter,
                popsize=10,
                tol=tol,
                mutation=mutation,
                recombination=recombination,
                seed=0,
                disp=disp,
                polish=polish,
                init=init,
                atol=atol,
                updating='deferred',
                workers=1,
                constraints=constraints,
                x0=encoded_initial,
                integrality=integrality,
                vectorized=vectorized
            )

            # Attach labeled solution
            decoded_solution = wrapped.decode(result.x)
            result.x_vars = dict(zip(self.labels, decoded_solution))
            self.outcomes = result
            return result

        finally:
            self.clear_cache()
            self.close_pbar()

    def minimize(self, **kwargs):
        try:

            self.open_pbar(labels=[i.label for i in self.control_vars])
            call_counter = {"count": 0}
            func = getattr(self, 'set_objective_function')
            def wrapped_obj(x, *args):
                call_counter["count"] += 1
                self.pbar.update(1)
                return self.set_objective_function(x)

            wrapped = Objective(
                func= wrapped_obj,
                variables=self.variables
            )

            bounds = wrapped.bounds


            # Handle initial guess
            initial_guess = self.starting_values()

            encoded_initial = wrapped.encode(initial_guess)


            result = minimize(wrapped, x0=encoded_initial, bounds=bounds, **kwargs)

            # Attach labeled solution
            decoded_solution = wrapped.decode(result.x)
            result.x_vars = dict(zip(self.labels, decoded_solution))
            self.outcomes = result
            return result

        finally:
            self.clear_cache()
            self.close_pbar()

if __name__ == "__main__":
    maize_model = "Maize"
    class Problem(MixedVariableProblem):
        def __init__(self, model=None, simulation='Simulation'):
            super().__init__(model, simulation)
            self.simulation = simulation

        def evaluate(self, x, **kwargs):
            return -self.run(verbose=False).results.Yield.mean()


    problem = Problem(maize_model, simulation='Simulation')
    problem.add_control('Manager', "Sow using a variable rule", 'Population',vtype='grid',
                        start_value=5, values=[2,11, 13, 9, 5, 15])
    problem.add_control('Manager', "Sow using a variable rule", 'RowSpacing', vtype='grid', start_value=400,
                        values=[400, 600, 750, 800, 900, 1000, 1100, 1200])
    de_res = problem.minimize_with_de()
    res= problem.minimize(method='Powell')

