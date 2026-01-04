
import gc

from apsimNGpy.core_utils.database_utils import write_results_to_sql
from apsimNGpy.optimizer.minimize.single_mixed import MixedVariableOptimizer
from apsimNGpy.optimizer.problems.smp import MixedProblem
from apsimNGpy.settings import logger
from apsimNGpy.tests.unittests.test_factory import obs
from apsimNGpy.core_utils.database_utils import read_db_table


def problem(metric):
    def create_problem(_metric):
        return MixedProblem(model='Maize', trainer_dataset=obs, pred_col='Yield', metric=_metric, table='Report',
                            index='year', trainer_col='observed')

    return create_problem(_metric=metric)


db = r"D:\package\fun_evaluation.db"
metrics_table = 'metrics'

@write_results_to_sql(db_path=db, table=metrics_table)
def write_results(de, metric, pop_size=20, algorithm='de', time_taken =None):

    from pandas import DataFrame
    metrics = de.all_metrics
    metrics['popsize'] = pop_size
    metrics['method'] = metric
    metrics['ndv'] =de.ndv
    metrics['algorithm'] = algorithm
    metrics['nit'] = de.nit
    metrics['nfev'] = de.nfev
    metrics['time_taken'] =time_taken
    df = DataFrame([metrics])
    df[list(de.cal_param_values.keys())] = [list(de.cal_param_values.values())]
    logger.info(f"succeeded writing data for: algorithm: {algorithm} and method: {metric}")
    return df


' System.ArgumentOutOfRangeException'
metrics = ( "ME","WIA","R2","CCC", "MSE","RRMSE","bias", "RMSE","MAE",)
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
        import time
        @write_results_to_sql(db_path=db_path, table=f"{algorithm}_data", if_exists=if_exists)
        def run_for_metric(metric, algorithm=algorithm):
            print(f"Running metric: {metric} for algorithm: {algorithm}")
            mp = problem(metric=metric)
            optimizer = MixedVariableOptimizer(problem=mp)
            mp.submit_factor(**cultivar_param_p.copy())
            t1 = time.perf_counter()
            if algorithm == "de":
                de = optimizer.minimize_with_de(popsize=pop_size, use_threads=False, workers=12, disp=False, )
            else:
                de = optimizer.minimize_with_local(options={'maxiter': 200}, method=algorithm)
            t2 = time.perf_counter()
            time_taken =t2-t1
            print('time taken is: ', time_taken)
            out = de
            print('Number of iterations:', out.nit)
            print('Number of function valuations:', out.nfev)
            print(f"x vars: ", out.cal_param_values)
            write_results(de=de, metric=metric, algorithm=algorithm, pop_size=pop_size, time_taken=time_taken)

            return de.data

        run_for_metric(metric=function_objective,)

    db = r"D:\package\fun_evaluation.db"
    from pathlib import Path
    if  not Path(db).exists():
        db =Path.home()/'packages'
        db.mkdir(exist_ok=True)
        db= str(db/'fun_ebaluation.db')

    @write_results_to_sql(db_path=db, table=metrics_table, if_exists='replace')
    def _update_table(var, value):
        df = read_db_table(db, metrics_table)
        df[var] = value
        return df
    #_update_table('ndv', 2)

    # for m in {"RRMSE","bias", "RMSE","MAE"}:
    #     print(m)
    #     main(db_path=db, function_objective=m, algorithm="L-BFGS-B")
    #     gc.collect()
    #
    for m in metrics:
        print(m)
        main(db_path=db, function_objective=m, algorithm="de")
        gc.collect()
    d= read_db_table(db, metrics_table)






