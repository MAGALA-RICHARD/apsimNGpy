from apsimNGpy.optimizer.moo import ApsimOptimizationProblem, Runner, compute_hyper_volume, NSGA2
from pymoo.optimize import minimize
import matplotlib.pyplot as plt
import numpy as np
# 1. Setup APSIM model
runner = Runner("Maize")
runner.add_report_variable('[Soil].Nutrient.NO3.kgha[1] as nitrate', report_name='Report')



# below enables defining other parameters that will be required for editing
_vars = [
    {'path': '.Simulations.Simulation.Field.Fertilise at sowing', 'Amount': "?", "bounds": [50, 300],
     "v_type": "float"},
    {'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': "?", 'v_type': 'float',
     'bounds': [4, 14]}
]


# 3. Define objective functions
def maximize_yield(df):
    return -df['Yield'].mean()


def nitrate_leaching(df):
    return df['nitrate'].sum()


objectives = [maximize_yield, nitrate_leaching]


# prob = ApsimOptimizationProblem(runner, _vars, objectives)

def run_example():
    # 4. Define problem and optimizer
    problem = ApsimOptimizationProblem(runner, objectives=objectives, decision_vars=_vars)
    # problem.add_control(
    #     **{'path': '.Simulations.Simulation.Field.Fertilise at sowing', 'Amount': "?", "bounds": [50, 300],
    #        "v_type": "float"})
    # problem.add_control(
    #     **{'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': "?", 'v_type': 'float',
    #        'bounds': [4, 14]})
    algorithm = NSGA2(pop_size=20, )

    # 5. Optimize
    result = minimize(problem.get_problem(),
                      algorithm,
                      ('n_gen', 2),
                      seed=1,
                      verbose=True)

    # 6. View Pareto front
    import matplotlib.pyplot as plt

    F = result.F
    plt.scatter(F[:, 0] *-1, F[:, 1])
    plt.xlabel("Yield")
    plt.ylabel("N Leaching")
    plt.title("Trade-offs between yield and nitrate leaching")
    plt.show()

    hiv = compute_hyper_volume(F, normalize=True, )
    print(hiv)
    return result

if __name__ == '__main__':
    res= run_example()