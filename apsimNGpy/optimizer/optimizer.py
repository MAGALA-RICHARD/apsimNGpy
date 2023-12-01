from builtins import function

import pandas as pd
import time
from scipy.optimize import minimize, least_squares
from apsimNGpy.utililies.utils import delete_simulation_files, timer

import numpy as np
from apsimNGpy.core.apsim import ApsimModel
from enum import Enum

df = pd.read_csv("simu_rn.csv")
residue = list(df.residue.unique())
nitrogen = list(df.nitrogen.unique())
m = 0
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





class algarithms(Enum):
    L_BFGS_B = 'L-BFGS-B'
    BFGS = 'BFGS'
    Powell = 'Powell'
    Newton_CG = 'Newton-CG'
    lm = 'lm'


@timer
class Optimize():
    def __init__(self, func: function, init_params: np.ndarray, bounds: list, options: dict = None, method='L-BFGS-B',
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


