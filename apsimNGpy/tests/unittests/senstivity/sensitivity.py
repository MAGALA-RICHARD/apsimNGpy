from apsimNGpy.sensitivity.sensitivity import run_sensitivity, ConfigProblem

if __name__ == "__main__":
    params = [
        {'base': ".Simulations.Simulation.Field.Sow using a variable rule", 'param': "Population", 'bounds': (2, 10), },
        {"base": ".Simulations.Simulation.Field.Fertilise at sowing", "param": "Amount", 'bounds': (0, 300), },
        dict(base=".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82",
             param="[Leaf].Photosynthesis.RUE.FixedValue", bounds=(
                0.7, 2.2), managers={'Sow using a variable rule': 'CultivarName'}, plant='Maize')
    ]
    runner = ConfigProblem(
        base_model="Maize",
        params=params,
        outputs=["Yield", "Maize.AboveGround.N"],
    )
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
