"""
This allows for multi-objective optimization and mixed variable optimization by encoding the categorical _variables
"""
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


def your_mixed_optimization_objective(x: tuple, *args: Any) -> float:
    print(x)
    return float(sum(x_i if isinstance(x_i, (int, float)) else len(str(x_i)) for x_i in (*x, *args)))


wrapped_objective = Objective(
    your_mixed_optimization_objective,
    variables=[
        ChoiceVar(["foobar", "baz"]),
        ChoiceVar([operator.index, abs, operator.invert]),
        GridVar([0.01, 0.1, 1, 10, 100]),
        GridVar(["good", "better", "best"]),
        RandintVar(-8, 10),
        QrandintVar(1, 10, 2),
        UniformVar(1.2, 3.4),
        QuniformVar(-11.1, 9.99, 0.22),
    ],
)
bounds = wrapped_objective.bounds
optional_fixed_args = ("arg1", 2, 3.0)
optional_initial_decoded_guess = ("foobar", operator.invert, 10, "better", 0, 8, 2.33, 8.8)
optional_initial_encoded_guess = wrapped_objective.encode(optional_initial_decoded_guess)

result = scipy.optimize.differential_evolution(wrapped_objective, bounds=bounds, seed=0, args=optional_fixed_args,
                                               x0=optional_initial_encoded_guess)
cache_usage = wrapped_objective.cache_info
encoded_solution = result.x
decoded_solution = wrapped_objective.decode(encoded_solution)
assert result.fun == wrapped_objective(encoded_solution, *optional_fixed_args)
assert result.fun == your_mixed_optimization_objective(decoded_solution, *optional_fixed_args)

