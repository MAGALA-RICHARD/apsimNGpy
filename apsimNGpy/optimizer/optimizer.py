from copy import deepcopy, copy
from pathlib import Path
from functools import partial, cache
import pandas as pd
import time

from attr import dataclass
from past.builtins import reload
from scipy.optimize import minimize, least_squares
from apsimNGpy.utililies.utils import delete_simulation_files, timer

import numpy as np
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.replacements.replacements import Replacements
from enum import Enum

from abc import ABC, abstractmethod


class AbstractExecutor(ABC):

    def __init__(self, func):
        self.func = func

    @abstractmethod
    def execute(self, *args, **kwargs):
        pass


class FunctionExecutor(AbstractExecutor):

    def execute(self, *args, **kwargs):
        result = self.func(*args, **kwargs)
        return result


# Define a sample function
def sample_function(x, y):
    return x + y


# Create an instance of FunctionExecutor with the sample_function
executor = FunctionExecutor(sample_function)

# Execute the function with arguments
result = executor.execute(5, 3)
print(result)  # Output: 8


@dataclass
class Solvers:
    L_BFGS_B = 'L-BFGS-B'
    BFGS = 'BFGS'
    Powell = 'Powell'
    Newton_CG = 'Newton-CG'
    lm = 'lm'
    Nelder_Mead = 'Nelder-Mead'
    SLSQP = 'SLSQP'


class Problem(ApsimModel):

    def __init__(self, model, out_path=None):
        super().__init__(model, out_path)
        """
        APSIM model file, apsimNGpy object, apsim file str or dict we want to use in the minimization
        """

    def function(self, *args):
        """
        Ths class is  holder for the problem function
         use the replacement module to define the functional call for the methods
         once initiated, we have access to all the methods from the replacements module
         args must  correspond to the bounds deployed while initializing this class
        """
        pass


def minimize_problem(problem, **kwargs):
    """problem class inherited from Problem class
    kwargs: key word arguments as defined by the scipy minimize method
    see scipy manual for each method https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
    """
    if 'bounds' in kwargs:
        kwargs.pop('bounds')

    return minimize(problem.function, bounds=problem.bounds,
                    **kwargs)


if __name__ == '__main__':
    # define the problem
    from apsimNGpy.core.base_data import load_default_simulations

    mode = Path.home() / 'Maize.apsimx'

    from apsimNGpy.core.core import APSIMNG


    class MyProblem(Replacements):
        def __init__(self, model, out):
            # Call to the parent class constructor
            super().__init__(model)
            self.Mpath = model

            # Instance attributes
            self.bounds = [(100, 400)]  # Example bound for value

            # self.run()

        def function(self, x):
            """
            Class method to run the APSIM simulation with a given fertilization value.
i


            Returns:
                float: The negative mean yield (for minimization).
            """

            def evaluate_function(yu):
                # Define the management action based on the input value
                management_action = {"Name": 'Fertilise at sowing', "Amount": yu[0]},

                # Update management actions in the simulation
                model = ApsimModel(self.Mpath)

                self.update_mgt(simulations=['Simulation'], management=management_action)

                # print(model.extract_user_input('Fertilise at sowing'))

                # Run the simulation with the specified report name
                self.run(report_name='Report', )
                print(self.extract_user_input('Fertilise at sowing'))
                # Process the results from the simulation
                df = self.results

                if df is not None and 'Yield' in df.columns:
                    # Compute the mean yield, and negate it for minimization
                    mean_yield = df['Yield'].mean()
                    print(f"Mean Yield: {mean_yield}")
                    return -mean_yield

            my = evaluate_function(x)
            return my


    maize = load_default_simulations(crop='maize', simulations_object=False)

    prob = MyProblem(model=r'Maize.apsimx', out='out.apsimx')
    options = {'maxiter': 10000}
    res = minimize_problem(prob, x0=(100,), method=Solvers.SLSQP, options=options, tol=5)

    print(res)
