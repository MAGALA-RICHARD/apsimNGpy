import glob
import os, sys
import platform
import shutil
from contextlib import contextmanager
from pathlib import Path
import logging

from apsimNGpy.settings import logger, MSG

current_path = os.path.dirname(os.path.abspath(__file__))
# Set up basic configuration for logging
logging.basicConfig(format='%(asctime)s :: %(message)s', level=logging.INFO)

user_id = current_path
# This will now print to the console

sys.path.append(current_path)
sys.path.append(os.path.dirname(current_path))
from apsimNGpy.core.config import auto_detect_apsim_bin_path
from apsimNGpy.core.config import get_apsim_bin_path

try:
    from core import APSIMNG
    from core.base_data import load_default_simulations
    from apsim import ApsimModel
    # auto-detect for some reason when imported after compiling, with compiling i mean installing the package so we
    # import directly from the package
except (ModuleNotFoundError, ImportError):
    # logging.info(" did not passed import error")
    from apsimNGpy.core.core import APSIMNG
    from apsimNGpy.core.apsim import ApsimModel
    from apsimNGpy.core.base_data import load_default_simulations

auto = auto_detect_apsim_bin_path() or os.getenv('APSIM')


def test():
    # test auto detect;
    if auto:
        logging.info(f"apsim path detected at: {auto}")
    # test pythonnet
    if get_apsim_bin_path():
        logging.info('Using apsim path at: {}'.format(get_apsim_bin_path()))
    else:
        logger.debug(MSG)
    from pathlib import Path
    from time import perf_counter
    # Model = FileFormat.ReadFromFile[Models.Core.Simulations](model, None, False)
    os.chdir(Path.home())
    from apsimNGpy.core.base_data import load_default_simulations

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


@contextmanager
def test_experiment(use_tread=False):
    path = Path.home().joinpath('scratchT')
    path.mkdir(exist_ok=True)

    try:
        # Import the model from APSIM and get the model path
        model_path = load_default_simulations('maize').path
        logging.info("Testing experiment module\n ______________________")

        # Set up the experiment
        FactorialExperiment = Experiment(
            database_name='test.db',
            datastorage='test.db',
            tag='th',
            base_file=model_path,
            wd=path,
            use_thread=use_tread,
            skip_completed=False,
            verbose=False,
            test=False,
            n_core=6,
            reports={'Report'}
        )

        # Add factors
        FactorialExperiment.add_factor(
            parameter='Carbon',
            param_values=[1.4, 0.2, 0.4, 0.9, 2.4, 0.6, 0.8],
            factor_type='soils',
            soil_node='Organic'
        )
        FactorialExperiment.add_factor(
            parameter='FBiom',
            param_values=[0.045, .4, 2.4, 0.8, 0.7],
            factor_type='soils',
            soil_node='Organic'
        )

        # Clear the database and start the experiment
        FactorialExperiment.clear_data_base()
        FactorialExperiment.start_experiment()

        # Yield control back to the block inside the `with` statement
        yield FactorialExperiment

        # Log successful test after the experiment block
        logging.info("Experiment module test successful\n____________________________________")

    except Exception as e:
        # Log any exceptions encountered during the experiment
        try:
            logging.exception(f"Experiment module test failed due to exception: {repr(e)}")
        except PermissionError as e:
            ...

    finally:
        # Clean up by removing the temporary directory
        try:
            shutil.rmtree(path)
            logging.info("files removed successfully")
        except PermissionError as e:
            ...


# Running the test
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    with test_experiment(use_tread=True) as experiment:
        sim_data = experiment.get_simulated_data()[0]
        mn = sim_data.groupby(['FBiom'])['Yield'].mean()
        logging.info(f"Simulation results (mean yield by FBiom):\n{mn}")
