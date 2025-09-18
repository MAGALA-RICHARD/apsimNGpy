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
from apsimNGpy.optimizer.base import AbstractProblem
from pymoo.core.problem import ElementwiseProblem
from apsimNGpy.core.cal import OptimizationBase as Runner
import numpy as np

# Disable compilation warning
Config.warnings['not_compiled'] = False


class MultiObjectiveProblem(AbstractProblem):

    def __init__(self, apsim_model: Runner, objectives: list, *, decision_vars: list = None, cache_size=100):
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
        AbstractProblem.__init__(self, apsim_model, max_cache_size=cache_size)
        self.apsim_model = apsim_model
        self.objectives = objectives
        self.params = []
        self.decision_vars = decision_vars if decision_vars is not None else []
        self.optimization_type = 'multi-objective'

        assert all(callable(obj) for obj in objectives), "All objectives must be callable"

    def evaluate_objectives(self, x, *args, **kwargs):
        for val, spec in zip(x, self.decision_vars):
            edit_runner(self.apsim_model, decision_specs=spec, x_values=val)
        # get results
        df = self.apsim_model.run().results
        return np.array([obj(df) for obj in self.objectives])

    def optimization_type(self):
        return 'multi-objective'

    def minimize_with_local_solver(self, **kwargs):
        pass  # not needed in this problem

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
            out["F"] = self.core_problem.evaluate_objectives(x, args, kwargs)

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

    def is_mixed_type_vars(self):
        """Detect if decision vars contain types other than float or int."""
        return any(var['v_type'] not in {'int', 'float'} for var in self.decision_vars)

    def minimize(self, **kwargs):
        return minimize

    def NSG2(self):
        return NSGA2


if __name__ == "__main__":
    # 1. Setup APSIM model
    runner = Runner("Maize")
    runner.add_report_variable('[Soil].Nutrient.NO3.kgha[1] as nitrate', report_name='Report')

    # 2. Define decision variables
    decision_vars = [
        {'name': '.Simulations.Simulation.Field.Fertilise at sowing.Amount', 'v_type': 'float', 'bounds': [50, 300]},
        {'name': '.Simulations.Simulation.Field.Sow using a variable rule.Population', 'v_type': 'float',
         'bounds': [4, 14]}
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
