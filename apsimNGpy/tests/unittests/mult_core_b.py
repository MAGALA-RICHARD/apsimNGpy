from apsimNGpy.core.mult_cores import MultiCoreManager
from pathlib import Path
Parallel = MultiCoreManager(db_path=Path("test_agg_3.db").resolve(), agg_func=None)
jobs = ({'model': 'Maize', 'ID': i, 'inputs': [{'path': '.Simulations.Simulation.Field.Fertilise at sowing',
                                                'Amount': i}]} for i in range(120))
if __name__ == '__main__':
    Parallel.run_all_jobs(jobs=jobs, n_cores=8, engine='csharp')
    dff = Parallel.results
    print(dff.shape)
