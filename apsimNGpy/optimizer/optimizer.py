
import numpy as np
from scipy.optimize import minimize, least_squares
from apsimNGpy.validation.evaluator import validate
from apsimNGpy.apsimpy import ApsimSoil
from pathlib import Path
from apsimNGpy.base_data import load_example_files
import pandas as pd
import time
from ..apsimpy import ApsimSoil
#=============================================================================================================
cwd  = Path.cwd()
data  = load_example_files(cwd)
file = data.get_maize
observed_yield  = pd.read_csv("observed_yield_prototype.csv")
observed_yield =observed_yield.Yield
# Define your process-based model as a function that takes model parameters as inputs and returns predicted yield
def process_model(radiation):
    try:
        apsim = ApsimSoil(file, copy = False)
        apsim.edit_cultivar(RUE = radiation, CultvarName='B_110')
        #apsim.dynamic_path_handler()
        apsim.run_edited_file()
        # Return the predicted yield
        return apsim.results['MaizeR'].Yield
    except Exception as e:
        print(f"An error occurred: {type(e).__name__} - {repr(e)}===*")

# Define an objective function to minimize, which quantifies the difference between observed and predicted yield
def optimization_function(x, *args):
    observed_yield = args[0]
    print(x[0])
    observed_yield = np.array(observed_yield)
    predicted_yield = process_model(x[0])
    # Let's use a suitable error metric, like, mean squared error
    metric = validate(observed_yield, predicted_yield)
    rmse = metric.evaluate("RMSE")
    WIA = metric.evaluate('WIA')
    ccc  = metric.evaluate("CCC")
    rrmse  = metric.evaluate("RRMSE")
    print(f"WIA is: {WIA}, CCC is: {ccc} rmse is: {rmse}, rrmse is : {metric.evaluate('RRMSE')}")
    return rmse

# Load your observed yield and radiation data here
observed_yield = np.array(observed_yield)
x0 = [1.2]
# Optimize the model parameters
class algarithms:
    def __init__(self):
        self.L_BFGS_B = 'L-BFGS-B'
        self.BFGS = 'BFGS'
        self.Powell  = 'Powell'
        self.Newton_CG = 'Newton-CG'
        self.lm = 'lm'

methods = algarithms()

class Problem:
    def __init__(self,
                 nu_var=-1,
                 nu_obj=1,
                 nu_ieq_constr=0,
                 **kwargs):
        self.n_var = nu_var
        self.n_obj = nu_obj
        self.n_ieq_constr = nu_ieq_constr

def substract():
    print("subtract")
class Optimize:
    def __init__(self, method= 'L-BFGS-B'):
        # tested algarithm:
        #'BFG'
        #'L-BFGS-B'
        # Powell
        self.method = method
        print(f"Using: {self.method} solver")
        self.result = minimize(optimization_function, x0=x0, bounds=[(1, 3)], args=(observed_yield,), method=self.method)
        optimized_parameters = self.result.x
        print("Optimized Parameters:", optimized_parameters)
        optimized_RUE = optimized_parameters[0]
        print("Optimized RUE:", optimized_RUE)
class optimized:
    def __init__(self,  function, apsim_param, X, bounds = None,  method= 'L-BFGS-B'):
        # tested algarithm:
        #'BFG'
        #'L-BFGS-B'
        # Powell
        self.method = method
        self.apsim_param = apsim_param
        self.optimisation_function  = function
        self.XO = X
        self.bounds = bounds
    def run_optimization(self):
        print(f"Using: {self.method} solver")
        self.result = minimize(self.optimisation_function, x0=self.XO, bounds=self.bounds, args=(self.apsim_param,), method=self.method)
        optimized_parameters = self.result.x
        print("Optimized Parameters:", optimized_parameters)
        optimized_RUE = optimized_parameters[0]
        print("Optimized RUE:", optimized_RUE)

class Optimize_ls:
    def __init__(self, method= 'L-BFGS-B'):
        # tested algarithm:
        #'BFG'
        ##'Newton-CG' NOT TESTED
        #'L-BFGS-B'
        # Powell
        self.method = method
        print(f"Using: {self.method} solver")
        if self.method == 'lm':
            self.result = least_squares(optimization_function, x0=x0, args=(observed_yield,), method=self.method)
        optimized_parameters = self.result.x

        # Print the optimized parameters
        print("Optimized Parameters:", optimized_parameters)

        # Calculate the optimized RUE value based on the optimized parameters
        optimized_RUE = optimized_parameters[0]

        # Print the optimized RUE value
        print("Optimized RUE:", optimized_RUE)
if __name__ == '__main__':
        for i in [ methods.Powell, methods.BFGS, methods.L_BFGS_B]:
              a = time.perf_counter()
              Optimize(method =i)
              b = time.perf_counter()
              print(f"{i} algarithms took:  {b-a} seconds")
