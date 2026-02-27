import argparse
import os
from pathlib import Path
from apsimNGpy import logger
from apsimNGpy import Apsim, get_apsim_bin_path

parser = argparse.ArgumentParser()
parser.add_argument(
    '-bp', "--bin",
    required=False,
    help="Path to APSIM binary directory")

args = parser.parse_args()
bin_path = args.bin or Path(os.environ.get('TEST_APSIM_BINARY',)) or get_apsim_bin_path()
bp = bin_path
apsim = Apsim(bin_path)
params = {
    ".Simulations.Simulation.Field.Sow using a variable rule?Population": (2, 10),
    ".Simulations.Simulation.Field.Fertilise at sowing?Amount": (0, 300),
    # ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82?[Leaf].Photosynthesis.RUE.FixedValue": (
    #     1.2, 2.2),
}

if __name__ == "__main__":

    runner = apsim.ConfigProblem(
        base_model="Maize",
        params=params,
        outputs=["Yield", "Maize.AboveGround.N"],
    )
    # custom
    # from SALib.sample import saltelli
    # from SALib.analyze import sobol
    #
    # param_values = saltelli.sample(runner.problem, 2 ** 4)
    # Y = runner.evaluate(param_values)
    # Si = [sobol.analyze(runner.problem, Y[:, i], print_to_console=True) for i in range(Y.ndim)]
    # print(Si)

    Si_sobol = apsim.run_sensitivity(
        runner,
        method="sobol",
        N=2 ** 4,  # ← base sample size
        n_cores=-6,
        engine='python',
        sample_options={
            "calc_second_order": True,
            "skip_values": 1024,
            # "seed": 42,
        },
        analyze_options={
            "conf_level": 0.95,
            "num_resamples": 5000,
            "print_to_console": True,
            "calc_second_order": True,
        },
    )
    logger.info('repeting tests')
    Si_sobol2 = apsim.run_sensitivity(
        runner,
        method="sobol",
        N=2 ** 3,  # ← base sample size
        n_cores=-6,
        engine='python',
        sample_options={
            "calc_second_order": True,
            "skip_values": 1024,
            # "seed": 42,
        },
        analyze_options={
            "conf_level": 0.95,
            "num_resamples": 5000,
            "print_to_console": True,
            "calc_second_order": True,
        },
    )
    logger.info('sensitivity test succeeded successfully')

