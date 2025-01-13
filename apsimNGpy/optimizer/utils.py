import inspect
from collections import namedtuple
from dataclasses import dataclass


@dataclass
class Solvers:
    L_BFGS_B = 'L-BFGS-B'
    BFGS = 'BFGS'
    Powell = 'Powell'
    Newton_CG = 'Newton-CG'
    lm = 'lm'
    Nelder_Mead = 'Nelder-Mead'
    SLSQP = 'SLSQP'


def create_data(fields: list, values: list):
    assert len(fields) == len(values), 'length not equal'
    int_set = namedtuple('data', [i for i in fields])
    return int_set(*values)


def fun_inspector(fun):
    assert callable(fun), 'method supplied is not a callable object'
    sign = inspect.signature(fun)
    params = [i.name for i in sign.parameters.values()]
    return params
