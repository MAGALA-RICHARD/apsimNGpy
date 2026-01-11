import gc
import os
import sys

from apsimNGpy.core_utils.database_utils import write_results_to_sql
from apsimNGpy.optimizer.minimize.single_mixed import MixedVariableOptimizer
from apsimNGpy.optimizer.problems.smp import MixedProblem
from apsimNGpy.settings import logger
from apsimNGpy.tests.unittests.test_factory import obs
from apsimNGpy.core_utils.database_utils import read_db_table
from persistqueue.queue import Queue
from pathlib import Path
from sqlalchemy import create_engine
import pandas as pd
import dotenv

dotenv.load_dotenv()
dbp = os.getenv('SUPABASE_DB_PASSWORD')

from sqlalchemy import create_engine
import os
passWord = os.getenv('SUPABASE_DB_PASSWORD')
from sqlalchemy import create_engine
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password=passWord,   # raw password is OK here
    host="db.elheeekvqchcvvdwlnzc.supabase.co",
    port=5432,
    database="postgres",
)

engine = create_engine(url)
engine.connect()

#pd.DataFrame([{'text':2}, {'text':1}]).to_sql('__test__', engine, if_exists='replace')
def problem(metric):
    def create_problem(_metric):
        return MixedProblem(model='Maize', trainer_dataset=obs, pred_col='Yield', metric=_metric, table='Report',
                            index='year', trainer_col='observed')

    return create_problem(_metric=metric)


db1 = r"De:\package\fun_evaluation.db"
db2 = r'C:\Users\vanguard\Box\post-doc\fun_eval.db'
metrics_table = 'metrics'
if Path(db1).parent.exists():
    db = db1
elif Path(db2).parent.exists():
    db = db2


# @write_results_to_sql(db_path=db, table=metrics_table)
def write_results(de, metric, pop_size=20, algorithm='de', time_taken=None):
    from pandas import DataFrame
    metrics = de.all_metrics
    metrics['popsize'] = pop_size
    metrics['method'] = metric
    metrics['ndv'] = de.ndv
    metrics['algorithm'] = algorithm
    metrics['nit'] = de.nit
    metrics['nfev'] = de.nfev
    metrics['time_taken'] = time_taken
    df = DataFrame([metrics])
    df[list(de.cal_param_values.keys())] = [list(de.cal_param_values.values())]
    logger.info(f"succeeded writing data for: algorithm: {algorithm} and method: {metric}")
    return df.to_sql(metrics_table, con=engine, if_exists='append', index=False)


' System.ArgumentOutOfRangeException'
metrics = ("ME", "WIA", "R2", "CCC", "MSE", "RRMSE",  "RMSE", "MAE",)
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


    def main( function_objective, if_exists="append", pop_size=20, algorithm='de'):
        import time
        def run_for_metric(metric, algorithm=algorithm):
            print(f"Running metric: {metric} for algorithm: {algorithm}")
            mp = problem(metric=metric)
            optimizer = MixedVariableOptimizer(problem=mp)
            mp.submit_factor(**cultivar_param_p.copy())
            t1 = time.perf_counter()
            if algorithm == "de":
                de = optimizer.minimize_with_de(popsize=pop_size, use_threads=False, workers=14, disp=False, )
            else:
                de = optimizer.minimize_with_local(options={'maxiter': 200}, method=algorithm)
            t2 = time.perf_counter()
            time_taken = t2 - t1
            print('time taken is: ', time_taken)
            out = de
            print('Number of iterations:', out.nit)
            print('Number of function valuations:', out.nfev)
            print(f"x vars: ", out.cal_param_values)
            write_results(de=de, metric=metric, algorithm=algorithm, pop_size=pop_size, time_taken=time_taken)
            dd = de.data
            dd['metric'] = metric
            dd['pop_size'] = pop_size
            dd['time_taken'] = time_taken
            dd['algorithm'] = algorithm
            dd['ndv'] = len(out.cal_param_values)
            dd.to_sql('simulations', con=engine, if_exists='append', index=False)

        run_for_metric(metric=function_objective, )


    from pathlib import Path


    def _update_table(var, value):
        df = read_db_table(db, metrics_table)
        df[var] = value
        return df


    # _update_table('ndv', 2)

    # for m in {"RRMSE","bias", "RMSE","MAE"}:
    #     print(m)
    #     main(db_path=db, function_objective=m, algorithm="L-BFGS-B")
    #     gc.collect()
    #
    # data = read_db_table(db, metrics_table)
    from itertools import product

    m_f_c = list(product(['BFGS'], metrics))
    idx = [i for i, _ in enumerate(m_f_c)]
    jobs = dict(zip(idx, m_f_c))
    q = Queue(str(Path(__file__).parent), )

    for i in idx:
        q.put(i)
    while not q.empty():
        key = q.get()
        method = jobs.get(key)
        print(key, method)
        if not method:
            continue
        alg, fun = method
        #main(function_objective=fun, algorithm=alg, pop_size=20)
        q.task_done()
        gc.collect()
        q.task_done()
    sys.exit(1)
    # d = read_db_table(db, metrics_table)
