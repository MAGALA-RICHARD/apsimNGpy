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


class Problem:

    def __init__(self, model, func, out_path=None, observed_values=None):
        self.model = model
        self.out_path = out_path
        self.params = []
        self.func = func
        self.observed = observed_values

        """
       model: APSIM model file, apsimNGpy object, apsim file str or dict we want to use in the minimization
       func: is the callable that takes in apsimNGpy object and return the desired loss function. we will use it to extract 
       the result meaning the user can create a callable object to manipulate the results objects
        """

    def add_param(self, simulation_name: str, param_class: str,
                  param_name: str,
                  cultivar_info: dict = None,
                  soil_info: dict = None,
                  manager_info: dict = None, **kwargs):
        """
        it is one factor at a time
        @param soil_info (dict): corresponding parameters for soil parameter. Accepted values:
                                     parameter: str,
                                     soil_child: str,
                                     simulations: list = None,
                                     indices: list = None,
                                     crop=None,
        also see replace_soil_property_values, param_values argument is not allowed in this dictionary

        @param cultivar_info: corresponding functional paramters for edit_cultivar method from APSIMNG object.
        Accepted values are CultivarName: str, commands: tuple, value arguments are not allowed here.

        @param param_class: parameters belong to classes like manager, Soil, Cultivar, this is useful for determining
        the replacement method.

        @param manager_info: info accompanying the parameters of the manager params, e.g.,
        {'Name': 'Fertilise at sowing', 'param_description': 'Amount'} script name and parameters going to it.

         @param simulation_name: e.g. Simulation, which is the default for apsim files @param param_class: includes, Manager,
        soil, cultivar
         @param param_name: name to hold in place the params, to optimize
         kwargs, contains extra arguments needed,
         @return: None
        """
        params = dict(simulations=simulation_name, param_class=param_class,
                      param_name=param_name, manager_info=manager_info,
                      soil_info=soil_info,
                      cultivar_info=cultivar_info)
        self.params.append(params)

    def update_params(self, x):
        """This updates the parameters of the model during the optimization"""
        model = ApsimModel(self.model)
        for counter, param in enumerate(self.params):
            if param['param_class'].lower() == 'manager':
                # create a new dictionary
                mgt_info = param['manager_info']
                mgt_info.update({mgt_info['param_description']: x[counter]})
                model.update_mgt(management=mgt_info, **self.params[counter])
            if param['param_class'].lower() == 'cultivar':
                model.edit_cultivar(**param['cultivar_info'], values=x[counter])
            if param['param_class'].lower() == 'soil':
                model.replace_soil_property_values(**param['soil_info'], param_values=x[counter])
        # now time to run
        model.run(report_name='Report')
        ans = self.func(model, self.observed)
        print(ans)
        return ans

    def minimize_problem(self, **kwargs):
        """
        kwargs: key word arguments as defined by the scipy minimize method
        see scipy manual for each method https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
        """

        return minimize(self.update_params,
                        **kwargs)


if __name__ == '__main__':
    # define the problem
    from apsimNGpy.core.base_data import load_default_simulations

    mode = Path.home() / 'Maize.apsimx'

    from apsimNGpy.core.core import APSIMNG

    maize = load_default_simulations(crop='maize', simulations_object=False)


    def func(model, ob):
        return model.results.Yield.mean() * -1


    prob = Problem(model=r'Maize.apsimx', out_path='out.apsimx', func=func)
    prob.add_param(simulation_name='Simulation', param_name='Nitrogen',
                   manager_info={'Name': 'Fertilise at sowing', 'param_description': 'Amount'}, param_class='Manager')
    options = {'maxiter': 10000}

    prob.update_params([100])
    mn = prob.minimize_problem(bounds=[(100, 400)], x0=[100], method=Solvers.Nelder_Mead)
