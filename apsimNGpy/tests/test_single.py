from apsimNGpy.optimizer.single import ContinuousVariable, MixedVariable
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.settings import  logger
maize_model = ApsimModel("Maize") # replace with the template path

obs = [
    7000.0, 5000.505, 1000.047, 3504.000, 7820.075,
    7000.517, 3587.101, 4000.152, 8379.435, 4000.301
]

class Problem(ContinuousVariable):
    def __init__(self, apsim_model, obs):

        super().__init__(apsim_model=apsim_model)
        self.obs = obs

    def evaluate_objectives(self, **kwargs):
        # This function runs APSIM and compares the predicted maize yield results with observed data.
        predicted = self.apsim_model.run(verbose=False).results.Yield
        # Use root-mean-square error or another metric.
        return self.rmse(self.obs, predicted)

problem = Problem(maize_model, obs)

def maximize_yield(df):
    # Negate yield to convert to a minimization problem
    return -df.Yield.mean()

problem = ContinuousVariable(maize_model, objectives = maximize_yield)

problem.add_control(
    path='.Simulations.Simulation.Field.Fertilise at sowing',
    Amount="?", bounds=[50, 300], v_type='int', start_value=150
)
problem.add_control(
    path='.Simulations.Simulation.Field.Sow using a variable rule',
    Population="?", v_type='int', bounds=[4, 14], start_value=8
)

res_local = problem.minimize_with_a_local_solver(
    method='Nelder-Mead',
    options={
        'maxiter': 100,
        'disp': True
    }
)
# differential evoloution
res_de = problem.minimize_with_de(
    popsize=10,
    maxiter=100,
    polish=False  # Set to True if you want to refine with a local solver at the end
)
