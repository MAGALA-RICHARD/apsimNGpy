from apsimNGpy import Apsim

apsim = Apsim(r"C:\Users\rmagala\AppData\Local\Programs\APSIM2026.2.7980.0\bin")
#
# TR1_morris = apsim.SensitivityManager("Wheat", out_path='sob.apsimx')
# TR1_morris.tree(cultivar=True)  #
# TR1_morris.add_crop_replacements()
# cls = sorted(set(TR1_morris.inspect_model('Models.PMF.Cultivar', fullpath=False)))

# TR1_morris.add_sens_factor(
#     name='phylocrom',
#     path='Replacements.Wheat.Cultivars.Australia.Bolac.Phenology.BasePhyllochron.FixedValue',  # This is my full path
#     lower_bound=90,
#     upper_bound=130
# )
#
# TR1_morris.add_sens_factor(
#     name='PhyllochronPpSensitivity',
#     path='Replacements.Wheat.Cultivars.Australia.Bolac.Phenology.PhyllochronPpSensitivity.FixedValue',
#     lower_bound=0.1,
#     upper_bound=1.1
# )

#
# TR1_morris.add_sens_factor(name='cnr', path='Field.SurfaceOrganicMatter.InitialCNR', lower_bound=10, upper_bound=120)
# TR1_morris.add_sens_factor(name='cn2bare', path='Field.Soil.SoilWater.CN2Bare', lower_bound=70, upper_bound=100)
#
# TR1_morris.build_sense_model(method='Morris',
#                              aggregation_column_name='Clock.Today',
#                              num_path=13,
#                              intervals=20,
#                              jumps=10)
# TR1_morris.run()#
# Here comes the error: System.Exception: Error in file: C:\Users\au792782\Codes\Python Scripts\Calibration of WW and WC\models\new\TR1_morris.apsimx Simulation: MorrisSimulation9
# ---> System.Exception: Cannot find property .Simulations.Annual Crops Tr 1.Tr1.Wheat.Bohr.Phenology.BasePhyllochron.FixedValue
from apsimNGpy import set_apsim_bin_path
from SALib.sample import saltelli
from SALib.analyze import sobol

ConfigProblem, run_sensitivity = apsim.ConfigProblem, apsim.run_sensitivity
if __name__ == '__main__':
    params = {
        ".Simulations.Simulation.Field.Sow using a variable rule?Population": (2, 10),
        ".Simulations.Simulation.Field.Fertilise at sowing?Amount": (0, 300),
        # ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82?[Leaf].Photosynthesis.RUE.FixedValue": (
        #     1.2, 2.2),
        ".Simulations.Simulation.Field.Wheat.Cultivars.Australia.Bolac?[Phenology].PhyllochronPpSensitivity.FixedValue":(0.1, 1.1)
    }
    runner = ConfigProblem(
        base_model="Wheat",
        params=params,
        outputs=["Yield", "Maize.AboveGround.N"],
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
