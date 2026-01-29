import os


from pathlib import Path

db = (Path.home() / "test_agg_3.db").resolve()
import time


def edit_weather(model):
    model.get_weather_from_web(lonlat=(-92.034, 42.012), start=1989, end=2020, source='daymet')


if __name__ == '__main__':
    from apsimNGpy.core.config import set_apsim_bin_path, apsim_bin_context
    from apsimNGpy.core.mult_cores import MultiCoreManager
    with apsim_bin_context(apsim_bin_path=r'C:\Users\rmagala\AppData\Local\Programs\APSIM2026.1.7969.0\bin'):
        from apsimNGpy.core.mult_cores import MultiCoreManager
        workspace = Path('D:/')
        os.chdir(workspace)
        Parallel = MultiCoreManager(db_path=db, agg_func='mean', table_prefix='di', )
        jobs = ({'model': 'Maize', 'ID': i, 'payload': [{'path': '.Simulations.Simulation.Field.Fertilise at sowing',
                                                         'Amount': i}]} for i in range(100))

        start = time.perf_counter()

        Parallel.run_all_jobs(jobs=jobs, n_cores=6, engine='csharp', threads=False, chunk_size=100,
                              subset=['Yield'],callback=edit_weather,
                              progressbar=True)
        dff = Parallel.results
        print(dff.shape)
        print(time.perf_counter() - start)
