import os
from pathlib import Path
from apsimNGpy.config import apsim_bin_context, configuration
import time

bin_path = Path(os.environ.get('TEST_APSIM_BINARY'))
from apsimNGpy.logger import logger


def edit_weather(model):
    model.get_weather_from_web(lonlat=(-92.034, 42.012), start=1989, end=2020, source='daymet')
    model.get_soil_from_web(simulations=None, lonlat=(-92.034, 42.012), source='ssurgo')


if __name__ == '__main__':
    # set the database where data will be stores
    db = (Path.home() / "test_agg_3.db").resolve()
    # get the APSIM binary path

    logger.info(configuration.bin_path, )
    bn = r"C:\Users\rmagala\AppData\Local\Programs\APSIM2026.2.7989.0\bin"
    with apsim_bin_context(bn, disk_cache=False) as ap:
        time.sleep(2)
        from apsimNGpy.core.mult_cores import MultiCoreManager

        logger.info(configuration.bin_path)

        workspace = Path('D:/')
        os.chdir(workspace)

        # initialize the API
        Parallel = MultiCoreManager(db_path=db, agg_func='mean', table_prefix='di', )
        # define the batch simulation jobs
        jobs = ({'model': 'Maize', 'ID': i, 'payload': [{'path': '.Simulations.Simulation.Field.Fertilise at sowing',
                                                         'Amount': i}]} for i in range(100, 122))
        start = time.perf_counter()
        # run all the jobs defined above
        Parallel.run_all_jobs(jobs=jobs, n_cores=1, engine='csharp', threads=False, chunk_size=100,
                              subset=['Yield'], callback=edit_weather,
                              progressbar=True)
        # extract the results
        dff = Parallel.results
        print(dff.shape)
        print(time.perf_counter() - start)

    print(configuration.bin_path)

# using a context manager to load APSIM
