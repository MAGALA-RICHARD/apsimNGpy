from pathlib import Path
import copy
from dataclasses import dataclass
import inspect
from typing import Any

import numpy as np
from scipy.optimize import minimize
from collections import namedtuple
from apsimNGpy.core.apsim import ApsimModel


def create_data(fields: list, values: list):
    assert len(fields) == len(values), 'length not equal'
    int_set = namedtuple('data', [i for i in fields])
    return int_set(*values)


@dataclass
class Solvers:
    L_BFGS_B = 'L-BFGS-B'
    BFGS = 'BFGS'
    Powell = 'Powell'
    Newton_CG = 'Newton-CG'
    lm = 'lm'
    Nelder_Mead = 'Nelder-Mead'
    SLSQP = 'SLSQP'


def _fun_inspector(fun):
    assert callable(fun), 'method supplied is not a callable object'
    sign = inspect.signature(fun)
    params = [i.name for i in sign.parameters.values()]
    return params


def set_up_data(model: str, func: callable, out_path: str = None, observed_values: np.ndarray = None,
                options: dict = None):
    """
    model: APSIM model file, apsimNGpy object, apsim file str or dict we want to use in the minimization func: an
    evaluation function, which is callable.
    This is something you should write for your self.
    A typical evaluation function takes on the functional signature func(apsimNGpy.APSIMNG.model, *args) Additional
    arguments can be passed as a tuple.
    Example of this could be observed variables to be compared with the
    predicted, where a loss function like rmse errors can be computed.
    In case of extra argument, these should be
    passed via options e.g., options ={args: None}
     @return: an instance of problem class object.
    """
    # re-initialize all lists carrying the data
    value_sign = _fun_inspector(set_up_data)
    # this avoids mistakes in attacking the data
    fields = create_data(fields=value_sign,
                         values=[eval(va) for va in value_sign])
    evaluation_sign = _fun_inspector(func)
    # make sure the user is consistent with extra argument
    if 'args' in evaluation_sign and not options.get('args'):
        raise ValueError("function evaluator has extra arguments not specified")

    return fields


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
    'path': "Simulation.Manager.script_name.None.parameter_name" } and main_parm  = 'param_values', Here,
    'None' represents the path to recompile the model to, and 'Simulation' is typically the name used in the
    simulation, though it can vary. For further information, refer to the APSIMNG API documentation.

    Kwargs: Contains additional arguments needed.

    Returns:
        None
    """

    self.updaters.append(updater)
    self.params.append(params)
    self.main_params.append(main_param)
    self.predictor_names.append(label)

    print(f"existing vars are: {self.predictor_names}")


def minimize_problem(data, variables, **kwargs):
    """

    Minimizes the defined problem using scipy.optimize.minimize.
    kwargs: key word arguments as defined by the scipy minimize method
    see scipy manual for each method https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html

    Returns:
    Optimization result.

    """

    def evaluation_worker(x: tuple, *args: any):
        model = ApsimModel(data.model)
        for var, control in zip(variables, x):

            var.params[var.main_param] = control
            getattr(model, var.updater)(**var.params)
        # ready to run results
        model.run(report_name='Report')
        if 'args' in _fun_inspector(data.func):
            ans = data.func(model, *data.options['args'])
        else:
            ans = data.func(model)
        print(ans, end='\r')
        return ans

    initial_guess = kwargs.get('x0') or np.zeros(len(variables))
    if kwargs.get('x0'):
        kwargs.pop('x0')
    minim = minimize(evaluation_worker, initial_guess, **kwargs)
    predictor_names = [var.label for var in variables]
    res = dict(zip(predictor_names, minim.x))
    setattr(minim, 'x_vars', res)
    return minim


if __name__ == '__main__':
    # define the problem
    from apsimNGpy.core.base_data import load_default_simulations
    from update import manager, soil

    mode = Path.home() / 'Maize.apsimx'

    maize = load_default_simulations(crop='maize', simulations_object=False)


    def func(model):
        sm = model.results.Yield.sum()
        mn = model.results.Yield.mean()

        return -mn

    prob = set_up_data(model=r'Maize.apsimx', out_path='out.apsimx', func=func)
    man = {'path': "Simulation.Manager.Fertilise at sowing.None.Amount"}
    nitrogen = manager(updater='update_mgt_by_path', params=man, main_param='param_values',
                       label='nitrogen_fertilizer', var_desc=None)
    si = {'parameter': 'Carbon',
          'soil_child': 'Organic',
          'simulations': 'Simulation',
          'indices': [0], }
    carbon  = soil(params=si, updater='replace_soil_property_values', main_param='param_values', label='carbon', var_desc=None)
    options = {'maxiter': 1000, 'disp': True}

    mn = minimize_problem(prob, [nitrogen], bounds=[(100, 320)], x0=[100], method=Solvers.BFGS, options=options)
    print(mn)

