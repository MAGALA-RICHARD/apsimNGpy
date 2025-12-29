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
from pandas import DataFrame
from apsimNGpy.core_utils.database_utils import write_results_to_sql, read_db_table
from loguru import logger

def problem(metric):
    def create_problem(_metric):
        return MixedProblem(model='Maize', trainer_dataset=obs, pred_col='Yield', metric=_metric, table='Report',
                            index='year', trainer_col='observed')

    return create_problem(_metric=metric)


db = r"D:\package\fun_evaluation.db"


@write_results_to_sql(db_path=db, table='de')
def write_results(de, metric, pop_size=20, algorithm='de'):

    from pandas import DataFrame
    metrics = de.all_metrics
    metrics['popsize'] = pop_size
    metrics['method'] = metric
    metrics['algorithm'] = algorithm
    metrics['nit'] = de.nit
    metrics['nfev'] = de.nfev
    df = DataFrame([metrics])
    df[list(de.cal_param_values.keys())] = [list(de.cal_param_values.values())]
    logger.info(f"succeeded writing data for: algorithm: {algorithm} and method: {metric}")
    return df


' System.ArgumentOutOfRangeException'

if __name__ == "__main__":
    cultivar_param_p = {
        "path": ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82",
        "start_value": [700, 1.5],
        'bounds': [(400, 800), (1, 2)],
        "candidate_param": ["[Grain].MaximumGrainsPerCob.FixedValue", '[Leaf].Photosynthesis.RUE.FixedValue'],
        "other_params": {"sowed": True},
        # other params must be on the same node or associated or extra arguments, e.g., target simulation name classified simulations
        'cultivar': True
    }
    results = {}

    def main(db_path, function_objective, if_exists="append", pop_size=20, algorithm='de'):

        @write_results_to_sql(db_path=db_path, table=f"{algorithm}_data", if_exists=if_exists)
        def run_for_metric(metric, algorithm=algorithm):
            logger.info(f"Running metric: {metric} for algorithm: {algorithm}")
            mp = problem(metric=metric)
            optimizer = MixedVariableOptimizer(problem=mp)
            mp.submit_factor(**cultivar_param_p.copy())
            if algorithm == "de":
                de = optimizer.minimize_with_de(popsize=pop_size, use_threads=False, workers=16, disp=False)
            else:
                de = optimizer.minimize_with_local(options={'maxiter': 200}, method=algorithm)
            write_results(de=de, metric=metric, algorithm=algorithm, pop_size=pop_size)
            out = de
            print('Number of iterations:', out.nit)
            print('Number of function valuations:', out.nfev)
            print(f"x vars: ", out.cal_param_values)

            return de.data

        run_for_metric(metric=function_objective,)


    db = r"D:\package\fun_evaluation.db"

    for m in ("MAE", "RRMSE",    "bias",    "RMSE" ,):
        print(m)
        main(db_path=db, function_objective=m)
        import gc
        gc.collect()
        import time
        time.sleep(1)




