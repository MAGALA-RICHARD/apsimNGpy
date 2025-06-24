from typing import Union
from dataclasses import dataclass
from pydantic import BaseModel
import numpy as np

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.config import Config
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize

# Disable compilation warning
Config.warnings['not_compiled'] = False


class Val(BaseModel):
    pop_size: int
    n_var: int
    xl: list
    xu: list
    n_obj: int
    n_ieq_constr: Union[None, int] = None


def moop(pop_size, n_var, xl, xu, n_obj, n_ieq_constr=None):
    user = Val(pop_size=pop_size, n_var=n_var, xl=xl, xu=xu,
               n_obj=n_obj, n_ieq_constr=n_ieq_constr)

    assert len(user.xl) == len(user.xu) == user.n_var, "Bounds must match number of variables"

    user.xl = np.array(user.xl)
    user.xu = np.array(user.xu)

    class CustomProblem(ElementwiseProblem):
        def __init__(self):
            super().__init__(
                n_var=user.n_var,
                n_obj=user.n_obj,
                n_ieq_constr=user.n_ieq_constr or 0,
                xl=user.xl,
                xu=user.xu
            )

        def _evaluate(self, x, out, *args, **kwargs):
            print(x)
            # Example: Sphere function for 2 goals
            f1 = np.sum((x - 0.5) ** 2)
            f2 = np.sum((x - 0.8) ** 2)
            out["F"] = np.array([f1, f2])

            if self.n_ieq_constr >= 2:
                out["G"] = np.array([0.1 - f1, f2 - 0.5])

    return CustomProblem()


# Example usage
problem = moop(pop_size=200, n_var=3,
               xl=[0, 0, 0], xu=[100, 400, 300],
               n_obj=2, n_ieq_constr=2)

algorithm = NSGA2(pop_size=100)

res = minimize(
    problem,
    algorithm,
    termination=('n_gen', 10),
    seed=1,
    verbose=0
)
