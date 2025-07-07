import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize as pymoo_minimize
from pymoo.operators.sampling.rnd import FloatRandomSampling, IntegerRandomSampling
from pymoo.termination import get_termination

# Objective function
def fun(x):
    return x**2

# --- Nelder-Mead ---
res_nm = minimize(fun, x0=[-10], method='powell',bounds=[(-10, 10)], options={'maxiter': 1000})
print(res_nm)
# --- NSGA-II on single-objective ---
class MyProblem(ElementwiseProblem):
    def __init__(self):
        super().__init__(n_var=1, n_obj=1, n_constr=0, xl=-10.0, xu=10.0)

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = fun(x)

problem = MyProblem()
algorithm = NSGA2(
    pop_size=200,
    sampling= IntegerRandomSampling(),
    eliminate_duplicates=True,

)

termination = get_termination("n_gen", 1000)

res_nsga2 = pymoo_minimize(problem, algorithm, termination, seed=1, verbose=False)
print(res_nsga2.X,'\n')
nsg2 = res_nsga2.F
if nsg2 < res_nm.fun:
    print('NSG2 has won')
elif nsg2 == res_nm.fun:
    print('draw')
else:
    print('NSG2 has lost', '\n')


print(res_nsga2.F)
