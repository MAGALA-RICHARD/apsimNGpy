from pathlib import Path
from apsimNGpy import configuration
from apsimNGpy import Apsim
import os

bin_path = Path(os.environ.get('TEST_APSIM_BINARY', '/.bin.bin'))
bp = bin_path
apsim = Apsim(bp)
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
