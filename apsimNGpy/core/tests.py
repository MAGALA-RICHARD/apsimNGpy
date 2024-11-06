import glob
import os, sys
import platform
from pathlib import Path
import logging

from settings import logger, MSG

current_path = os.path.dirname(os.path.abspath(__file__))
# Set up basic configuration for logging
logging.basicConfig(format='%(asctime)s :: %(message)s', level=logging.INFO)

user_id = current_path
# This will now print to the console

sys.path.append(current_path)
sys.path.append(os.path.dirname(current_path))
from apsimNGpy.config import auto_detect_apsim_bin_path
from apsimNGpy.config import get_apsim_bin_path

try:
    from core import APSIMNG
    from apsim import ApsimModel
    # auto-detect for some reasons when imported after compiling, with compiling i mean installing the package so we
    # import directly from the package
except ImportError:
    logging.info("passed import error")
    from apsimNGpy.core.core import APSIMNG
    from apsimNGpy.core.apsim import ApsimModel

auto = auto_detect_apsim_bin_path()



def test():
    # test auto detect;
    if auto:
        logging.info(f"apsim path detected automatically at: {auto}")
    # test pythonnet
    if get_apsim_bin_path():
        logging.info('Using apsim path at: {}'.format(get_apsim_bin_path()))
    else:
        logger.debug(MSG)
    from pathlib import Path
    from time import perf_counter
    # Model = FileFormat.ReadFromFile[Models.Core.Simulations](model, None, False)
    os.chdir(Path.home())
    from apsimNGpy.core.base_data import LoadExampleFiles, load_default_simulations

    model = load_default_simulations(crop='maize')
    logging.info(f"testing simulator time\n ______________________")
    for _ in range(2):
        a = perf_counter()
        # model.RevertCheckpoint()

        model.run_simulations('report')
        # print(model.results.mean(numeric_only=True))

        # print(model.results.mean(numeric_only=True))
        msg = f"{perf_counter() - a} seconds, taken"
        logging.info(msg=msg, )


from apsimNGpy.experiment.main import Experiment


def test_experiment(use_tread=False):
    try:
        path = Path.home().joinpath('scratchT')
        path.mkdir(exist_ok=True)
        from apsimNGpy.core.base_data import load_default_simulations

        # import the model from APSIM.
        # if we simulations_object it,
        # returns a simulation object of apsimNGpy, but we want the path only.
        # model_path = load_default_simulations(crop='maize', simulations_object=False, path=path.parent)
        model_path = load_default_simulations('maize').path
        logging.info(f"testing experiment module\n ______________________")
        FactorialExperiment = Experiment(database_name='test.db',
                                         datastorage='test.db',
                                         tag='th', base_file=model_path,
                                         wd=path,
                                         use_thread=use_tread,
                                         skip_completed=False,
                                         verbose=False,
                                         test=False,
                                         n_core=6,
                                         reports={'Report'})

        FactorialExperiment.add_factor(parameter='Carbon', param_values=[1.4, 0.2, 0.4, 0.9, 2.4, 0.8],
                                       factor_type='soils',
                                       soil_node='Organic')

        FactorialExperiment.add_factor(parameter='FBiom', param_values=[0.045, 1.4, 2.4, 0.8], factor_type='soils',
                                       soil_node='Organic')

        # # cultivar is edited via the replacement module, any simulation file supplied without Replacements appended
        # # to Simulations node, this method will fail quickly
        # FactorialExperiment.add_factor(parameter='grain_filling', param_values=[300, 450, 650, 700, 500], cultivar_name='B_110',
        #                                commands='[Phenology].GrainFilling.Target.FixedValue', factor_type='cultivar')

        FactorialExperiment.clear_data_base()
        # os.remove(FactorialExperiment.datastorage)
        FactorialExperiment.start_experiment()
        sim_data = FactorialExperiment.get_simulated_data()[0]
        mn = sim_data.groupby(['FBiom', 'Carbon'])['Yield'].mean()
        "if we dont see any variation for each of the factors then it is not working configure again"
        # print(mn)
        logging.info('experiment module test successful \n____________________________________')
    except Exception as e:
        logging.exception(f'experiment module test failed due to exception: {repr(e)}')


if __name__ == '__main__':
    test()
    test_experiment()
