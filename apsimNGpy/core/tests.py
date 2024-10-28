import glob
import os,sys
import platform
from pathlib import Path
import logging
current_path  = os.path.dirname(os.path.abspath(__file__))
# Set up basic configuration for logging
logging.basicConfig(format='%(asctime)s :: %(message)s', level=logging.INFO)

user_id = current_path
# This will now print to the console

sys.path.append(current_path)
sys.path.append(os.path.dirname(current_path))
from path_finders import  auto_detect_apsim_bin_path
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

    from pathlib import Path
    from time import perf_counter
    # Model = FileFormat.ReadFromFile[Models.Core.Simulations](model, None, False)
    os.chdir(Path.home())
    from apsimNGpy.core.base_data import LoadExampleFiles, load_default_simulations

    model = load_default_simulations(crop='maize')

    for _ in range(2):

        for rn in ['Maize, Soybean, Wheat', 'Maize', 'Soybean, Wheat']:
            a = perf_counter()
            # model.RevertCheckpoint()

            model.run('report')
            # print(model.results.mean(numeric_only=True))

            # print(model.results.mean(numeric_only=True))
            msg  =f"{perf_counter() - a} seconds, taken"
            logging.info(msg=msg, )

        a = perf_counter()

        res = model.run_simulations(reports="Report", clean_up=False, results=True)
        b = perf_counter()
        print(b - a, 'seconds')
        mod = model.Simulations



if __name__ == '__main__':
    test()

