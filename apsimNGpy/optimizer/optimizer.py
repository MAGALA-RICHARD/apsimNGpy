from copy import deepcopy

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


class Problem(ApsimModel):

    def __init__(self, model, out_path = None, bounds =None):
        super().__init__(model, out_path)
        """
        APSIM model file, apsimNGpy object, apsim file str or dict we want to use in the minimization
        """
        # wrap the replacement methods here for easy access in the execution function below
        self.bounds = bounds # note that the bounds is a tuple for each variable we want to optimize

    def function(self, *args):
        """
        Ths class is  holder for the problem function
         use the replacement module to define the functional call for the methods
         once initiated, we have access to all the methods from the replacements module
         args must  correspond to the bounds deployed while initializing this class
        """
        pass


def minimize_problem(problem,**kwargs):
    """problem class inherited from Problem class
    kwargs: key word arguments as defined by the scipy minimize method
    """
    if 'bounds' in kwargs:
         kwargs.pop('bounds')
    return minimize(problem.function, bounds= problem.bounds,
                    **kwargs)

@timer
class Minimize():
    def __init__(self, func, init_params: tuple, bounds: tuple, options: dict = None, method='L-BFGS-B',
                 *args):

        self.method = method
        print(f"Using: {self.method} solver")
        if options:
            self.result = minimize(func, x0=init_params, bounds=bounds,
                                   options=options, method=self.method)
        else:
            self.result = minimize(func, x0=init_params, bounds=bounds,
                                   method=self.method)
        optimized_parameters = self.result.x
        print("Optimized Parameters:", optimized_parameters)

if __name__ == '__main__':
    # define the problem
    from apsimNGpy.core.base_data import load_default_simulations

    class MyProblem(Problem):
        def __init__(self, model):
              super().__init__(model)
              self.bounds = [(0, 100)]

        def function(self, value):

            #mgt ='None.Manager.Fertilise at sowing.e.Amount'
            mgt = ({"Name": 'Fertilise at sowing', "Amount":value},)
            self.update_mgt(simulations= ['Simulation'], management=mgt,out ='op.apsimx')
            self.run(report_name='Report')
            df = self.results

            ans = df.Yield.mean()
            print(ans)
            return ans * -1


    maize = load_default_simulations(crop='maize', simulations_object=False)
    prob = MyProblem(maize)
    res = minimize_problem(prob, x0 =[0], method='L-BFGS-B')