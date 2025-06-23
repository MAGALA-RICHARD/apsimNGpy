from pymoo.algorithms.moo import nsga3, nsga2
from dataclasses import dataclass
from pydantic import Field, BaseModel
import numpy as np
from pymoo.core.problem import ElementwiseProblem


class ElementwiseSphereWithConstraint(ElementwiseProblem):

    def __init__(self):
        xl = np.zeros(10)
        xl[0] = -5.0

        xu = np.ones(10)
        xu[0] = 5.0

        super().__init__(n_var=10, n_obj=1, n_ieq_constr=2, xl=xl, xu=xu)

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = np.sum((x - 0.5) ** 2)
        out["G"] = np.column_stack([0.1 - out["F"], out["F"] - 0.5])


class Val(BaseModel):
    pop_size: int
    n_var: int
