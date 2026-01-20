import gc
import os
import sys

from SALib.sample.morris import strategy

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
    password=passWord,  # raw password is OK here
    host="db.elheeekvqchcvvdwlnzc.supabase.co",
    port=5432,
    database="postgres",
)

engine = create_engine(url)
engine.connect()


# pd.DataFrame([{'text':2}, {'text':1}]).to_sql('__test__', engine, if_exists='replace')
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
def write_results(de, metric, pop_size=20, algorithm='de', time_taken=None, init='sobol', strategy = 'rand1bin'):
    from pandas import DataFrame
    metrics = de.all_metrics
    metrics['popsize'] = pop_size
    metrics['method'] = metric
    metrics['ndv'] = de.ndv
    metrics['algorithm'] = algorithm
    metrics['nit'] = de.nit
    metrics['nfev'] = de.nfev
    metrics['time_taken'] = time_taken
    if algorithm == 'de':
        metrics['init'] = init
        metrics['strategy'] = strategy
    df = DataFrame([metrics])
    df[list(de.cal_param_values.keys())] = [list(de.cal_param_values.values())]
    logger.info(f"succeeded writing data for: algorithm: {algorithm} and method: {metric}")
    if algorithm == 'de':
        table = 'de_metrics'
    else:
        table = metrics_table
    return df.to_sql(table, con=engine, if_exists='append', index=False)


' System.ArgumentOutOfRangeException'
metrics = ("ME", "WIA", "R2", "CCC", "MSE", "RRMSE", "RMSE", "MAE",)
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


    def main(function_objective, if_exists="append", pop_size=20, algorithm='de', strategy='rand1bin'):
        if if_exists == "replace":
            raise ValueError("attempting to override data base table not allowed at this moment")
        import time
        def run_for_metric(metric, algorithm=algorithm):
            print(f"Running metric: {metric} for algorithm: {algorithm}")
            mp = problem(metric=metric)
            optimizer = MixedVariableOptimizer(problem=mp)
            mp.submit_factor(**cultivar_param_p.copy())
            t1 = time.perf_counter()
            init = 'sobol'
            if algorithm == "de":
                de = optimizer.minimize_with_de(popsize=pop_size, use_threads=False, workers=14, disp=False, init=init, strategy=strategy, rng=44)
            else:
                de = optimizer.minimize_with_local(options={'maxiter': 200}, method=algorithm)
            t2 = time.perf_counter()
            time_taken = t2 - t1
            print('time taken is: ', time_taken)
            out = de
            print('Number of iterations:', out.nit)
            print('Number of function valuations:', out.nfev)
            print(f"x vars: ", out.cal_param_values)
            write_results(de=de, metric=metric, algorithm=algorithm, pop_size=pop_size, time_taken=time_taken,
                          init=init, strategy=strategy)
            dd = de.data
            dd['metric'] = metric
            dd['pop_size'] = pop_size
            dd['time_taken'] = time_taken
            dd['algorithm'] = algorithm
            dd['ndv'] = len(out.cal_param_values)
            if algorithm == 'de':
                dd['init'] = init
                dd['strategy'] = strategy
            if algorithm == 'de':
                table = f'de_simulations'
            else:
                table = 'simulations'
            dd.to_sql(table, con=engine, if_exists=if_exists, index=False)

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
    from json import loads, dumps

    m_f_c = list(product(['Nelder-Mead', "L-BFGS-B"], metrics))
    idx = [i for i, _ in enumerate(m_f_c)]
    jobs = dict(zip(idx, m_f_c))
    q = Queue(str(Path(__file__).parent), )
    from apsimNGpy.parallel._process import register_key, get_key, clear_db

    db = Path(__file__).parent / 'metrics_db.db'
    for metric in metrics:
        get_met = get_key(db, value=metric, )
        if not get_met:
            q.put(metric, block=False)
    while not q.empty():
        key = q.get()
        print(key)
        if not key:
            q.task_done()
            continue
        main(function_objective=key, algorithm='de', pop_size=15, strategy='rand1bin')
        q.task_done()
        gc.collect()
        register_key(key=key, db=db, )
    clear_db(db)

    d = read_db_table(engine, metrics_table)
    sim_table = read_db_table(engine, 'simulations')
    # de_sim = sim_table[sim_table['algorithm'] == 'de']
    # de_sim['init'] = 'lhs'
    # de_sim['strategy'] = 'rand1bin'
    # de_sim.to_sql('de_simulations', con=engine, if_exists='replace', index=False)
    #
    # de = d[d['algorithm'] == 'de']
    # de['init'] = 'lhs'
    # de['strategy'] = 'rand1bin'
    # de.to_sql('de_metrics', con=engine, if_exists='replace', index=False)

# sys.exit(1)
