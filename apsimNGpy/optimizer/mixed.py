"""
This allows for mixed variable optimization by encoding the categorical variables
"""
from pathlib import Path

from optimizer import Problem, Solvers

import subprocess

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


def _variable_type(type_name: str) -> str:
    variable_types = {
        'choice': ChoiceVar,
        'grid': GridVar,
        'qrandint': QrandintVar,
        'quniform': QuniformVar,
        'randint': RandintVar,
        'uniform': UniformVar
    }
    return variable_types[type_name.lower()]


class MixedVariable(Problem):
    def __init__(self):
        self.reset_data()

    def add_control_var(self, updater: str, main_param, params: dict, label: str, var_desc: str,

                        **kwargs):
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

        self.updaters.add(updater)
        self.params.append(params)
        self.main_params.add(main_param)
        self.predictor_names.add(label)
        self.variable_type.add(var_desc)
        print(self.variable_type)

        print(f"existing vars are: {self.predictor_names}")

    def minimize_wrap_vars(self, ig: list):
        wrap = Objective(
            self.update_params,
            variables=list(self.variable_type)
        )
        bounds = wrap.bounds
        optional_fixed_args = ("arg1", 2, 3.0)
        optional_initial_decoded_guess = ig
        optional_initial_encoded_guess = wrap.encode(optional_initial_decoded_guess)

        result = scipy.optimize.differential_evolution(wrap, bounds=bounds, seed=0,
                                                       args=optional_fixed_args,
                                                       x0=optional_initial_encoded_guess)
        cache_usage = wrap.cache_info
        encoded_solution = result.x
        decoded_solution = wrap.decode(encoded_solution)
        assert result.fun == wrap(encoded_solution, *optional_fixed_args)
        assert result.fun == wrap(decoded_solution, *optional_fixed_args)
        setattr("cache_info", cache_usage)


MixedOptimizer = MixedVariable()
if __name__ == '__main__':
    # define the problem
    from apsimNGpy.core.base_data import load_default_simulations

    mode = Path.home() / 'Maize.apsimx'

    maize = load_default_simulations(crop='maize', simulations_object=False)


    def func(model):
        sm = model.results.Yield.sum()
        mn = model.results.Yield.mean()
        ans = sm * sm / mn
        return -ans


    prob = MixedOptimizer.set_up_data(model=r'Maize.apsimx', out_path='out.apsimx', func=func)
    man = {'path': "Simulation.Manager.Fertilise at sowing.None.Amount"}
    prob.add_control_var(updater='update_mgt_by_path', params=man, main_param='param_values',
                         label='nitrogen_fertilizer', var_desc=QrandintVar(100, 300, 2), )
    si = {'parameter': 'Carbon',
          'soil_child': 'Organic',
          'simulations': 'Simulation',
          'indices': [0], }
    prob.add_control_var(params=si, updater='replace_soil_property_values', main_param='param_values', label='carbon',
                         var_desc=UniformVar(1.2, 3.4), )
    options = {'maxiter': 1000, 'disp': True}

    mn = prob.minimize_wrap_vars(ig=(104, 1.2))
