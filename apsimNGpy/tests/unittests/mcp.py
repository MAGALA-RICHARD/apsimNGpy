import os
from pathlib import Path
from apsimNGpy.config import apsim_bin_context, configuration, get_apsim_bin_path
import time
from apsimNGpy import Apsim

bin_path = Path(os.environ.get('TEST_APSIM_BINARY'))
bp = bin_path
from apsimNGpy.logger import logger

def edit_weather(model):
    model.get_weather_from_web(lonlat=(-92.034, 42.012), start=1989, end=2020, source='daymet',
                               )
    model.get_soil_from_web(simulations=None, lonlat=(-92.034, 42.012), source='ssurgo', summer_date='15-may',
                            winter_date='01-nov')
    model.edit_model(model_type='Models.Manager', model_name='Sow using a variable rule', Population=8.65,
                     StartDate='28-apr', EndDate='03-may')


if __name__ == '__main__':
    # set the database where data will be stored
    db = (Path.home() / "test_agg_3.db").resolve()
    # get the APSIM binary path

    logger.info(configuration.bin_path, )
    bn = bin_path

    logger.info(configuration.bin_path)
    workspace = Path('D:/')
    os.chdir(workspace)
    # initialize the API
    with Apsim(bp) as apsim:
        Parallel = apsim.MultiCoreManager(db_path=db, agg_func='mean', table_prefix='di', )
        # define the batch simulation jobs
        jobs = ({'model': 'Maize', 'ID': i, 'payload': [{'path': '.Simulations.Simulation.Field.Fertilise at sowing',
                                                         'Amount': i}]} for i in range(0, 200))
        start = time.perf_counter()
        # run all the jobs defined above
        Parallel.run_all_jobs(jobs=jobs, n_cores=10, engine='python', threads=False, chunk_size=100,
                              subset=['Yield'], callback=edit_weather,
                              progressbar=True)
        # extract the results
        dff = Parallel.results
        print(dff.shape)
        print(time.perf_counter() - start)
        import matplotlib.pyplot as plt

        Parallel.relplot(x='Amount', y='Yield')
        plt.show()
        print(configuration.bin_path)

    # using a context manager to load APSIM
