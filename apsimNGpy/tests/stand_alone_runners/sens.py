from apsimNGpy.senstivity.sensitivity import run_sensitivity, ConfigProblem

if __name__ == "__main__":
    params = {
        ".Simulations.Simulation.Field.Sow using a variable rule?Population": (2, 10),
        ".Simulations.Simulation.Field.Fertilise at sowing?Amount": (0, 300),
        ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82@[Phenology].GrainFilling.Target.FixedValue": (
        400, 850),
        ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82?[Leaf].Photosynthesis.RUE.FixedValue": (
            1.2, 2.2),
    }
    runner = ConfigProblem(
        base_model="Maize",
        params=params,
        outputs=["Yield", "Maize.AboveGround.N"],
    )
    #######################################
    # Method Sobol
    #######################################
    Si_sobol = run_sensitivity(
        runner,
        method="sobol",
        N=2 ** 5,  # ← base sample size
        n_cores=-6,
        sample_options={
            "calc_second_order": True,
            "skip_values": 1024,
            # "seed": 42,
        },
        analyze_options={
            "conf_level": 0.95,
            "num_resamples": 1000,
            "print_to_console": True,
            "calc_second_order": True,
        },
    )
    #######################################
    # Method Morris
    #######################################
    Si_morris = run_sensitivity(
        runner,
        method="morris", n_cores=10,
        sample_options={
            'seed': 42,
            "num_levels": 6,
            "optimal_trajectories": 6,
        },
        analyze_options={
            'conf_level': 0.95,
            "num_resamples": 1000,
            "print_to_console": True,
            'seed': 42
        },
    )
    #######################################
    # Method efast
    #######################################
    si_fast = run_sensitivity(
        runner,
        method="fast",
        sample_options={
            "M": 2,

        },
        analyze_options={
            'conf_level': 0.95,
            "num_resamples": 1000,
            "print_to_console": True,
        },
    )
