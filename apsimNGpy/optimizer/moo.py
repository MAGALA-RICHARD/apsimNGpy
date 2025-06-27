from typing import Union
from dataclasses import dataclass
import numpy as np

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.config import Config
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.optimize import minimize
from apsimNGpy.core.cal import OptimizationBase as Runner, OptimizationBase
import numpy as np
from apsimNGpy.optimizer.optutils import compute_hyper_volume, edit_runner

from pymoo.core.problem import ElementwiseProblem
from apsimNGpy.core.cal import OptimizationBase as Runner
import numpy as np

# Disable compilation warning
Config.warnings['not_compiled'] = False

class ApsimOptimizationProblem:

    def __init__(self, apsim_runner: Runner, objectives: list, *, decision_vars: list = None):
        """
                   Parameters
                   ----------
                   apsim_runner : apsimNGpy.core.cal.OptimizationBase
                       Instance to run APSIM simulations.
                   objectives : list of callable
                       List of functions that take simulation output (DataFrame) and return scalar objective values.
                   decision_vars : list of dict, optional
                       Each dict must have: 'path', 'bounds', 'v_type', 'kwargs'.
                   """

        self.apsim_runner = apsim_runner
        self.objectives = objectives
        self.params = []
        self.decision_vars = decision_vars if decision_vars is not None else []

        assert all(callable(obj) for obj in objectives), "All objectives must be callable"

    class SetUpProblem(ElementwiseProblem):
        def __init__(self, core_problem, **kwargs):
            self.core_problem = core_problem
            xl, xu = core_problem.extract_bounds()
            super().__init__(
                n_var=len(core_problem.decision_vars),
                n_obj=len(core_problem.objectives),
                n_ieq_constr=0,
                xl=np.array(xl),
                xu=np.array(xu), *kwargs
            )

        def _evaluate(self, x, out, *args, **kwargs):
            # `x` is a single solution (vector), because this is ElementwiseProblem
            for val, spec in zip(x, self.core_problem.decision_vars):
                edit_runner(self.core_problem.apsim_runner, decision_specs=spec, x_values=val)

            df = self.core_problem.apsim_runner.run().results
            out["F"] = np.array([obj(df) for obj in self.core_problem.objectives])

    def extract_bounds(self):
        xl, xu = [], []
        for var in self.decision_vars:
            if var['v_type'] not in {'int', 'float'}:
                raise ValueError(f"Unsupported variable type: {var['v_type']}")
            xl.append(var['bounds'][0])
            xu.append(var['bounds'][1])
        return xl, xu

    def get_problem(self):
        return self.SetUpProblem(self)

    def add_parameters(self, path: str, *, bounds, v_type, **kwargs):
        """
        Adds a single APSIM parameter to be optimized.

        Parameters
        ----------
        path : str
            APSIM component path.
        bounds : tuple
            Lower and upper bounds for optimization variable.
        v_type : str
            Variable type: 'int' or 'float'.
        kwargs : dict
            One of the key-values must be '?' to be filled during optimization.
        """
        self.apsim_runner.evaluate_kwargs(path, **kwargs)

        to_fill = [k for k, v in kwargs.items() if v in ('?', 'fill', "")]
        if len(to_fill) != 1:
            raise ValueError("Exactly one parameter must be unspecified with '?' or 'fill'.")

        var_spec = {
            'path': path,
            'bounds': bounds,
            'v_type': v_type,
            'kwargs': kwargs
        }

        if var_spec not in self.decision_vars:
            self.decision_vars.append(var_spec)

    def is_mixed_type_vars(self):
        """Detect if decision vars contain types other than float or int."""
        return any(var['v_type'] not in {'int', 'float'} for var in self.decision_vars)


# 1. Setup APSIM model
runner = Runner("Maize")
runner.add_report_variable('[Soil].Nutrient.NO3.kgha[1] as nitrate', report_name='Report')

# 2. Define decision variables
decision_vars = [
    {'name': '.Simulations.Simulation.Field.Fertilise at sowing.Amount', 'v_type': 'float', 'bounds': [50, 300]},
    {'name': '.Simulations.Simulation.Field.Sow using a variable rule.Population', 'v_type': 'float', 'bounds': [4, 14]}
]

# below enables defining other parameters that will be required for editing
_vars = [
    {'path': '.Simulations.Simulation.Field.Fertilise at sowing', 'Amount': "?", "bounds": [50, 300],
     "v_type": "float"},
    {'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': "?", 'v_type': 'float',
     'bounds': [4, 14]}
]


# 3. Define objective functions
def negative_yield(df):
    return -df['Yield'].mean()


def nitrate_leaching(df):
    return df['nitrate'].sum()


objectives = [negative_yield, nitrate_leaching]




















