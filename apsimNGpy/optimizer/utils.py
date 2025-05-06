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
    if len(fields) != len(values):
        raise ValueError('length not equal')
    init_data = namedtuple('data', [i for i in fields])
    return init_data(*values)


def fun_inspector(fun, values =True):
    assert callable(fun), 'method supplied is not a callable object'
    sign = inspect.signature(fun)
    if values:
        params = [i.name for i in sign.parameters.values()]
    else:
        params = [i for i in sign.parameters.keys()]

    return params


