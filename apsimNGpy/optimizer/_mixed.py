"""
This allows for mixed variable optimization by encoding the categorical _variables
"""
from pathlib import Path

import numpy as np
from abc import abstractmethod
from apsimNGpy.core_utils.utils import timer
from scipy.optimize import minimize, differential_evolution
import subprocess

from apsimNGpy.optimizer._one_obj import AbstractProblem, SIMULATIONS, ContVarProblem, cache, VarDesc, SING_OBJ_MIXED_VAR
from apsimNGpy.core_utils.progbar import ProgressBar
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


class MixedVarProblem(ContVarProblem):
    """
    Defines an optimization problem for continuous variables in APSIM simulations.

    This class configure and solves optimization problems involving continuous
    control variables in APSIM models. It provides utilities to declare variables,
    set bounds and starting values, inject values into APSIM configurations, and run
    optimization with local solvers or Differential Evolution.

    Inherits From
    -------------
    :class:`~apsimNGpy.Optimizer.single.ContinuousVariableProblem`

    Parameters
    ----------
    model : str
        Name or path to the APSIM template file.
    simulation : str | list[str] | None, optional
        Name(s) of the APSIM simulation(s) to target. Defaults to all simulations.
    decision_vars : list[VarDesc] | None, optional
        Variable descriptors defining the optimization variables.
    labels : list[str] | None, optional
        Human-readable labels used in displays and result tracking.
    cache_size : int, optional
        Maximum number of results to store in the evaluation cache.

    Attributes
    ----------
    model : str
        APSIM model template file name or path.
    simulation : str | list[str] | None
        Target simulation(s).
    decision_vars : list[VarDesc]
        Defined control variables for optimization.
    labels : list[str]
        Labels corresponding to the decision variables.
    pbar : tqdm.tqdm | None
        Progress bar instance (opened during optimization when enabled).
    cache : bool
        Whether evaluation results are cached.
    cache_size : int
        Size of the local evaluation cache.

    Methods
    -------
    :meth:`add_control`
        Add a new control variable to the optimization problem.
    :attr:`bounds` -> tuple[list[float], list[float]]
        Return lower and upper bounds for all control variables.
    :attr:`starting_values` -> list[float]
        Return the initial values for all control variables.
    :meth:`minimize_with_local_solver`
        Optimize with :func:`scipy.optimize.minimize`.
    :meth:`optimize_with_differential_evolution`
        Optimize with :func:`scipy.optimize.differential_evolution`.


    Examples
    --------
    .. code-block:: python

        class Problem(ContinuousVariableProblem):
            def evaluate(self, x):
                # Example objective: maximize mean yield (hence the negative sign)
                return -self.run(verbose=False).results.Yield.mean()

        problem = Problem(model="Maize", simulation="Sim")
        problem.add_control(
            model_path="Manager/Sow using a rule",
            var_name="Population",
            dtype=int,
            start=5,
            bounds=(2, 15),
        )

        result = problem.minimize_with_local_solver(method="Powell")
        print(result.x_vars)
    """

    def __init__(self, apsim_model: 'ApsimNGpy.Core.Model', max_cache_size=400, objectives=None, decision_vars=None):

        # Initialize parent classes explicitly
        AbstractProblem.__init__(self, apsim_model, max_cache_size, objectives, decision_vars)
        self.model = apsim_model
        self.decision_vars = decision_vars or []
        self.objectives = objectives

        self.cache = True
        self.cache_size = max_cache_size
        self.pbar = None
        self.counter = 0
        self.maxiter = 0

    def wrap_vars(self):
        wrapped_variables = []

        for var in self.decision_vars:
            var_type = var['v_type']
            bounds = var.get('bounds')
            categories = var.get('categories')
            q = var.get('q', 1)

            # Map variable type to wrapdisc class
            type_map = {
                'int': RandintVar,
                'float': UniformVar,
                'uniform': UniformVar,
                'choice': ChoiceVar,
                'grid': ChoiceVar,  # Alias
                'categorical': ChoiceVar,
                'qrandint': QrandintVar,
                'quniform': QuniformVar
            }

            if var_type not in type_map:
                raise ValueError(f"Unsupported variable type: {var_type}")

            wrap_class = type_map[var_type.lower()]

            if wrap_class in {RandintVar, UniformVar}:
                if bounds is None:
                    raise ValueError(f"Bounds must be provided for variable: {var}")
                if wrap_class is RandintVar:
                    wrapped = RandintVar(lower=bounds[0], upper=bounds[1])
                else:
                    wrapped = UniformVar(lower=bounds[0], upper=bounds[1])
            elif wrap_class is ChoiceVar:
                if categories is None:
                    raise ValueError(f"'values' must be provided for categorical or grid variable: {var}")
                wrapped = ChoiceVar(categories=categories)
            elif wrap_class is QrandintVar:
                wrapped = QrandintVar(lower=bounds[0], upper=bounds[1], q=q)
            elif wrap_class is QuniformVar:
                wrapped = QrandintVar(lower=bounds[0], upper=bounds[1], q=q)

            else:
                raise NotImplementedError(f"Handler not implemented for variable type: {var_type}")

            wrapped_variables.append(wrapped)
            # this is the last time we need them


        return wrapped_variables

    @property
    def _variables(self):

        return self.wrap_vars()

    def _set_objective_function(self, x):
        self._insert_controls(x)
        SCORE = self.evaluate_objectives()
        return SCORE

    def  optimization_type(self):
         return SING_OBJ_MIXED_VAR

    @abstractmethod
    def minimize_with_alocal_solver(self, **kwargs):
        'To be implimneted in sub class'
        pass

    @abstractmethod
    def minimize_with_de(self):
        """
        To be implimented in sub-class
        """
if __name__ == "__main__":
    maize_model = "Maize"

    obs = [
        7000.0,
        5000.505,
        1000.047,
        3504.000,
        7820.075,
        7000.517,
        3587.101,
        4000.152,
        8379.435,
        4000.301
    ]
    class Problem(MixedVarProblem):
        def __init__(self, apsim_model: 'ApsimNGpy.Core.Model', obs, max_cache_size=400, objectives=None,
                     decision_vars=None):
            super().__init__(apsim_model=apsim_model, max_cache_size=max_cache_size, objectives=objectives,
                             decision_vars=decision_vars)
            self.obs = obs

        def evaluate_objectives(self, **kwargs):
            # set up everything you need here
            predicted = self.apsim_model.run(verbose=False).results.Yield
            ans = self.rmse(self.obs, predicted)

            return -predicted.mean()


    def maximize_yield(df):
        return -df.Yield.mean()


    from apsimNGpy.core.cal import OptimizationBase

    maize_model = OptimizationBase('Maize')
    problem = Problem(maize_model, obs, objectives=maximize_yield)
    problem.add_control(
        **{'path': '.Simulations.Simulation.Field.Fertilise at sowing', 'Amount': "?", "bounds": None,
           "v_type": "choice"}, start_value=100,  categories= [100, 200, 250, 300])
    problem.add_control(
        **{'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': "?", 'v_type': 'qrandint',
           'bounds': [4, 14]}, start_value=8, q=2, )
    # de_res = problem.optimize_with_differential_evolution()
    res = problem.minimize_with_alocal_solver(method='Powell', )
    de = problem.minimize_with_differential_evolution(popsize=20, polish =True)
