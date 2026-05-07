from apsimNGpy import Apsim

apsim = Apsim(r"C:\Users\rmagala\AppData\Local\Programs\APSIM2026.2.7980.0\bin")
if __name__ =='__main__':
    #
    TR1_morris = apsim.SensitivityManager("Wheat", out_path='swob.apsimx')
    # TR1_morris.tree(cultivar=True)  #
    # TR1_morris.add_crop_replacements()
    # cls = sorted(set(TR1_morris.inspect_model('Models.PMF.Cultivar', fullpath=False)))

    TR1_morris.add_sens_factor(
        name='Basephylocrom',
        path='[Phenology].Phyllochron.BasePhyllochron.FixedValue',  # This is my full path
        lower_bound=90,
        upper_bound=130
    )

    TR1_morris.add_sens_factor(
        name='PhyllochronPpSensitivity',
        path='[Phenology].PhyllochronPpSensitivity.FixedValue',
        lower_bound=0.1,
        upper_bound=1.1
    )



    TR1_morris.build_sense_model(method='Morris',
                                 aggregation_column_name='Clock.Today',
                                 num_path=13,
                                 intervals=20,
                                 jumps=10)
    TR1_morris.run()#

pp = [{
    'base': '.Simulations.Simulation.Field.Fertilise at sowing', 'param':'population', 'Amount':200,
    'bounds': (0, 300)},
    {
        'base': '.Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82',
    'param': '[Leaf].Photosynthesis.RUE.FixedValue',
        'cultivar': True,
    'managers': {"Sow using a variable rule": "CultivarName"}
}]
ConfigProblem, run_sensitivity = apsim.ConfigProblem, apsim.run_sensitivity
if __name__ == '__main__':
    params = {
        ".Simulations.Simulation.Field.Sow using a variable rule?Population": (2, 10),
        ".Simulations.Simulation.Field.Fertilise at sowing?Amount": (0, 300),
        # ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82?[Leaf].Photosynthesis.RUE.FixedValue": (
        #     1.2, 2.2),
    }
    # runner = ConfigProblem(
    #     base_model="Maize",
    #     params=params,
    #     outputs=["Yield", "Maize.AboveGround.N"],
    # )
    # Si_morris = run_sensitivity(
    #     runner,
    #     method="morris", n_cores=10,
    #     sample_options={
    #         'seed': 42,
    #         "num_levels": 6,
    #         "optimal_trajectories": 6,
    #     },
    #     analyze_options={
    #         'conf_level': 0.95,
    #         "num_resamples": 1000,
    #         "print_to_console": True,
    #         'seed': 42
    #     },
    # )


