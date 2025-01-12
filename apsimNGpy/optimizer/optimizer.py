from pathlib import Path
import copy
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from apsimNGpy.core.apsim import ApsimModel


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

    def __init__(self):

        self.out_path = None
        self.model = None
        self.options = None
        self.params = None
        self.func = None
        self.observed = None
        self.predictor_names = None
        self.updaters = None
        self.main_params = None

    def set_up_data(self, model, func, out_path=None, observed_values=None, options=None):
        """
              model: APSIM model file, apsimNGpy object, apsim file str or dict we want to use in the minimization
              func: is the callable that takes in apsimNGpy object and return the desired loss function. we will use it to extract
              the result, meaning the user can create a callable object to manipulate the result objects
               """
        self.params = []
        self.updaters = []
        self.main_params = []
        self.predictor_names = []
        self.options = options
        self.model = model
        self.model = model
        self.observed = observed_values
        self.out_path = out_path
        self.func = func
        return self

    def add_control_var(self, updater: str, main_param, params: dict, label: str, **kwargs):
        """
        Updater: Specifies the name of the APSIMNG method used to update values from the optimizer.
        Params: A dictionary containing arguments for the updater method, excluding the value to be optimized.
        For example, with `replace_soil_property_values`, params could be defined as:
            {
                'parameter': 'Carbon',
                'soil_child': 'Organic',
                'simulations': None,
                'indices': [1],
                'crop': None
            }
        Note that this main_param = 'param_values', which is excluded here.

        To optimize variables defined via the manager module, use `update_mgt_by_path` and define params as: {
        'path': "Simulation.Manager.script_name.None.parameter_name" } and main_parm  = 'param_values', Here, 'None' represents the path to recompile
        the model to, and 'Simulation' is typically the name used in the simulation, though it can vary.
        For further information, refer to the APSIMNG API documentation.

        Kwargs: Contains additional arguments needed.

        Returns:
            None
        """

        self.updaters.append(updater)
        self.params.append(params)
        self.main_params.append(main_param)

        np.append(self.predictor_names, label)
        self.predictor_names.append(label)
        print(f"existing vars are: {self.predictor_names}")

    def update_params(self, x, *args):

        """This updates the parameters of the model during the optimization"""
        model = ApsimModel(self.model)
        if len(x) != len(self.params):
            ve = ValueError('params must have the same length as the suggested predictors')
            raise ve

        for x_var, method, param, x_holder in zip(x, self.updaters, self.params, self.main_params):
            if 'soil' in method:
                x_var = x_var,
            # update the params
            param[x_holder] = x_var
            getattr(model, method)(**param)
        # # now time to run
        model.run(report_name='Report')
        ans = self.func(model, self.observed)
        print(ans, end='\r')
        return ans

    def minimize_problem(self, **kwargs):

        """
       
        Minimizes the defined problem using scipy.optimize.minimize.
        kwargs: key word arguments as defined by the scipy minimize method
        see scipy manual for each method https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
        
        Returns:
        Optimization result.
        
        """
        initial_guess = kwargs.get('x0') or np.zeros(len(self.params))
        if kwargs.get('x0'):
            kwargs.pop('x0')
        minim = minimize(self.update_params, initial_guess, **kwargs)
        ap = dict(zip(self.predictor_names, minim.x))
        setattr(minim, 'x_vars', ap)
        return minim


# initialized before it is needed
SingleProblem = Problem()

if __name__ == '__main__':
    # define the problem
    from apsimNGpy.core.base_data import load_default_simulations

    mode = Path.home() / 'Maize.apsimx'

    maize = load_default_simulations(crop='maize', simulations_object=False)


    def func(model, ob):
        sm = model.results.Yield.sum()
        mn = model.results.Yield.mean()
        ans = sm * sm / mn
        return -ans


    prob = SingleProblem.set_up_data(model=r'Maize.apsimx', out_path='out.apsimx', func=func)
    man = {'path': "Simulation.Manager.Fertilise at sowing.None.Amount"}
    prob.add_control_var(updater='update_mgt_by_path', params=man, main_param='param_values',
                         label='nitrogen_fertilizer')
    si = {'parameter': 'Carbon',
          'soil_child': 'Organic',
          'simulations': 'Simulation',
          'indices': [0], }
    prob.add_control_var(params=si, updater='replace_soil_property_values', main_param='param_values', label='carbon')
    options = {'maxiter': 800, 'disp': True}

    mn = prob.minimize_problem(bounds=[(100, 320), (0, 1)], x0=[100, 0.1], method=Solvers.Nelder_Mead, options=options)
    prob.update_params([300, 3.3283740839260843e-09])
