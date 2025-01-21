"""
This allows for mixed variable optimization by encoding the categorical variables
"""
from pathlib import Path

from apsimNGpy.utililies.utils import timer

from simple_problem import Problem, Solvers, _initial_guess

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

        self.updaters.append(updater)
        self.params.append(params)
        self.main_params.append(main_param)
        self.predictor_names.append(label)
        self.variable_type.append(var_desc)

        print(f"existing vars are: {self.predictor_names}")

    @timer
    def minimize_wrap_vars(self, ig: list = None, **kwargs):
        self._freeze_data()

        wrap = Objective(
            self.update_predictors,
            variables=[i.var_type for i in self.controls]
        )
        bounds = wrap.bounds
        optional_fixed_args = ("arg1", 2, 3.0)
        if not ig:
            auto_ig = [_initial_guess(data.var_type) for data in self.controls]
            optional_initial_decoded_guess = auto_ig
        else:
            optional_initial_decoded_guess = ig

        optional_initial_encoded_guess = wrap.encode(optional_initial_decoded_guess)

        result = scipy.optimize.differential_evolution(wrap, bounds=bounds, seed=0,
                                                       args=optional_fixed_args,
                                                       x0=optional_initial_encoded_guess, **kwargs)
        cache_usage = wrap.cache_info
        encoded_solution = result.x
        decoded_solution = wrap.decode(encoded_solution)
        # assert result.fun == wrap(encoded_solution, *optional_fixed_args)
        # assert result.fun == wrap(decoded_solution, *optional_fixed_args)
        setattr(result, "cache_info", cache_usage)
        setattr(result, "decoded_solution", decoded_solution)
        setattr(result, 'encoded_solution', encoded_solution)
        att_lab = dict(zip([va.label for va in self.controls], result.decoded_solution))
        setattr(result, 'decoded_solution', att_lab)
        return result


MixedOptimizer = MixedVariable()



