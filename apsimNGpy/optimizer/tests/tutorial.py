"""
APSIMNGpy Optimization Tutorial

This tutorial introduces both the theoretical foundation and practical application of optimization techniques using APSIMNGpy. The goal is to guide users through continuous and mixed-variable optimization problems, explaining each step as if teaching a new user or researcher in the agroecosystem modeling field.

--------------------------------------------------------------------------------

1. Overview of Optimization in Agricultural Systems

Optimization is the science of selecting the best input values (decision variables) to achieve a desired output (objective). In the context of crop modeling, this might mean finding the optimal fertilizer rate or planting density to maximize yield or minimize nutrient leaching. Optimization problems can be:

- Single-objective (e.g., maximize yield)
- Multi-objective (e.g., maximize yield while minimizing nitrate leaching)
- Continuous (variables take any value within bounds)
- Discrete or categorical (variables take on fixed options)
- Mixed (a combination of variable types)

In APSIMNGpy, we define an optimization problem, add decision variables (e.g., fertilization rate, sowing density), specify an objective function (like RMSE or mean yield), and run solvers to find optimal values.

--------------------------------------------------------------------------------

2. Tutorial Walkthrough
"""

from apsimNGpy.optimizer.single import ContinuousVariable, MixedVariable
from apsimNGpy.core.apsim import ApsimModel

# STEP 1: Load the APSIM model and observed data.
# This is typically a single simulation file you want to calibrate or optimize.
maize_model = ApsimModel("Maize")
obs = [
    7000.0, 5000.505, 1000.047, 3504.000, 7820.075,
    7000.517, 3587.101, 4000.152, 8379.435, 4000.301
]

print('Testing continuous variable optimization...')

# STEP 2A: Inheriting from ContinuousVariable
# This shows how to define a custom optimization problem class.
# You override the evaluate_objectives() method with your own objective function.
class Problem(ContinuousVariable):
    def __init__(self, apsim_model, obs):
        super().__init__(apsim_model=apsim_model)
        self.obs = obs

    def evaluate_objectives(self, **kwargs):
        # This function runs APSIM and compares the predicted results with observed data.
        predicted = self.apsim_model.run(verbose=False).results.Yield
        # Use root mean square error or another metric.
        return self.rmse(self.obs, predicted)

problem = Problem(maize_model, obs)

# STEP 2B: Alternatively, you can define the objective directly
# This is useful for simpler problems where you only need to extract something from the APSIM report table.
def maximize_yield(df):
    # Negate yield to convert to a minimization problem
    return -df.Yield.mean()

# STEP 3: Add control variables (i.e., what you want the optimizer to change).
# You can use 'add_control' to specify the path, type, and bounds.
# 'Amount' will be filled in by the optimizer. '?' marks the variable to optimize.
problem.add_control(
    path='.Simulations.Simulation.Field.Fertilise at sowing',
    Amount="?", bounds=[50, 300], v_type='qrandint', start_value=150
)

problem.add_control(
    path='.Simulations.Simulation.Field.Sow using a variable rule', CultivarName = 'B_110',
    Population="?", v_type='int', bounds=[4, 14], start_value=8
)

# # STEP 4A: Run a local optimization solver
# # This is suitable for smooth problems and quick feedback.
# res_local = problem.minimize_with_alocal_solver(
#     method='Powell',
#     options={
#         'maxiter': 100,
#         'disp': True
#     }
# )
#
# # STEP 4B: Run a global optimizer using differential evolution
# # This is useful when the surface is noisy or has many local minima.
# res_de = problem.minimize_with_de(popsize=10, maxiter=100, polish=False)
#
# print('Testing mixed variable optimization...')
#
# # STEP 5: Define a mixed-variable problem
# # MixedVariable allows combining categorical, integer, and continuous decision variables.
# problem = MixedVariable(maize_model, objectives=maximize_yield)
#
# # For a categorical variable, use 'choice' and provide a list of categories
# problem.add_control(
#     path='.Simulations.Simulation.Field.Fertilise at sowing',
#     Amount="?", v_type='choice', categories=[100, 150, 200, 250, 300], start_value=150
# )
#
# # For quantized integers, you can define a step size 'q' with 'qrandint'
# problem.add_control(
#     path='.Simulations.Simulation.Field.Sow using a variable rule',
#     Population="?", v_type='qrandint', bounds=[4, 14], start_value=8, q=2
# )
#
# # STEP 6: Run optimizers on the mixed-variable problem
# res_mixed_local = problem.minimize_with_alocal_solver(method='Powell')
# res_mixed_de = problem.minimize_with_de(popsize=20, polish=True)
#
# # STEP 7: Review results
# # Use .x, .fun, or convert to DataFrame to review the best configurations and scores.
