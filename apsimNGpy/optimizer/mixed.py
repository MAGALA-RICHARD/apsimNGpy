"""
This allows for mixed variable optimization by encoding the categorical variables
"""
from pathlib import Path

import numpy as np

from apsimNGpy.utililies.utils import timer

from apsimNGpy.optimizer.simple_problem import Problem, Solvers, auto_guess
from scipy.optimize import minimize, differential_evolution
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
        super().__init__()
        self.reset_data()

    @timer
    def minimize_wrap_vars(self, de=True, **kwargs):
        self._freeze_data()

        wrap = Objective(
            self.update_predictors,
            variables=[i.var_type for i in self.controls]
        )
        bounds = wrap.bounds
        optional_fixed_args = ("arg1", 2, 3.0)

        auto_ig = [auto_guess(data.var_type) for data in self.controls]
        optional_initial_decoded_guess = kwargs.get('x0', auto_ig)
        kwargs.pop('x0') if 'x0' in kwargs else None
        optional_initial_encoded_guess = wrap.encode(optional_initial_decoded_guess)
        if de:
            result = differential_evolution(wrap, bounds=bounds, seed=0,
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
        else:

            result = minimize(wrap, bounds=bounds, x0=optional_initial_encoded_guess, **kwargs)

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
