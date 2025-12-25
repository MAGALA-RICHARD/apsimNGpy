metrics = (
    "ME",
    "WIA",
    "R2",
    "CCC",
    "MSE",
    "RRMSE",
    "bias",
    "RMSE",
    "MAE",
)
from apsimNGpy.optimizer.minimize.single_mixed import MixedVariableOptimizer
from apsimNGpy.optimizer.problems.smp import MixedProblem
from apsimNGpy.tests.unittests.test_factory import obs

if __name__ == "__main__":
    cultivar_param_p = {
        "path": ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82",
        "start_value": [700],
        'bounds': [(400, 800), ],
        "candidate_param": ["[Grain].MaximumGrainsPerCob.FixedValue"],
        "other_params": {"sowed": True},
        # other params must be on the same node or associated or extra arguments, e.g., target simulation name classified simulations
        'cultivar': True
    }
    results = {}
    for metric in metrics:
        print("Using metirc: {}".format(metric))
        mp = MixedProblem(model='Maize', trainer_dataset=obs, pred_col='Yield', metric=metric, table='Report',
                          index='year', trainer_col='observed')
        optimizer = MixedVariableOptimizer(problem=mp)
        mp.submit_factor(**cultivar_param_p.copy())
        de = optimizer.minimize_with_de(popsize=10, use_threads=False, workers=16, disp=False)
        # out = optimizer.minimize_with_local(options={'maxiter': 200})
        results[metric] = de
        out = de
        print('Number of iterations:', out.nit)
        print('Number of function valuations:', out.nfev)
        print(f"x vars: ", out.cal_param_values)
