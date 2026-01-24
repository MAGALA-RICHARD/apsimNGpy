import os

from apsimNGpy.core.mult_cores import MultiCoreManager
from pathlib import Path

db = (Path.home() / "test_agg_3.db").resolve()
import time

if __name__ == '__main__':
    workspace = Path('D:/')
    os.chdir(workspace)

    Parallel = MultiCoreManager(db_path=db, agg_func='sum', table_prefix='di',)
    jobs = ({'model': 'Maize', 'ID': i, 'payload': [{'path': '.Simulations.Simulation.Field.Fertilise at sowing',
                                                    'Amount': i}]} for i in range(200))
    start = time.perf_counter()
    Parallel.run_all_jobs(jobs=jobs, n_cores=6, engine='csharp', threads=False, chunk_size=100,
                          subset=['Yield'],
                          progressbar=True)
    dff = Parallel.results
    print(dff.shape)
    print(time.perf_counter() - start)

