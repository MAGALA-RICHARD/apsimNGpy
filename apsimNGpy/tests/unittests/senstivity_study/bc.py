from apsimNGpy import ApsimModel
from xlwings import view
bounds = [
    dict(
        base="Field.SurfaceOrganicMatter",
        param="InitialResidueMass",
        bounds=(0, 5000)
    ),

    dict(
        base="Field.Soil.SoilWater",
        param="CN2Bare",
        bounds=(70, 85)
    ),

    dict(
        base="Field.Soil.SoilWater",
        param="SummerCona",
        bounds=(3, 9)
    ),

    dict(
        base="Field.Soil.SoilWater",
        param="SummerU",
        bounds=(1, 9)
    ),

    dict(
        base="Field.SurfaceOrganicMatter",
        param="InitialCNR",
        bounds=(40, 120)
    ),

    dict(
        base="Field.Soil.SoilWater",
        param="SWCON",
        bounds=(0.1, 0.5)
    ),
]

from apsimNGpy.sensitivity.sensitivity import CustomSensitivityManager

if __name__ == "__main__":
    manager = CustomSensitivityManager(base_model=r'D:\package\apsimNGpy\apsimNGpy\tests\unittests\senstivity_study\benchmark.apsimx',
                                       response_vars=['TotalMinN',
                                                      'FinalResidueCover',
                                                      'FallowRunoff',
                                                      'FallowRainfall',
                                                      'FinalResidueWt'])
    for p in bounds:
        base = p['base']
        param = p['param']
        parameter = dict(base=f".Simulations.FallowSensitivityBase.{base}",
                         param=param, bounds=p['bounds'],
                        # managers={'Sow using a variable rule': 'CultivarName'}, plant='Maize'
                          )
        print(parameter)
        manager.add_sens_factor(**parameter)
    print('No of factors: ',manager.n_factors)

    ccMorris = manager.build_sense_model(method="morris", n_cores=10, agg_func='mean',
                                    sample_options={
                                        'seed': 42,
                                        "num_levels": 20,
                                        "optimal_trajectories": 16,
                                    },
                                    analyze_options={
                                        'conf_level': 0.95,
                                        "num_resamples": 1000,
                                        "print_to_console": True,
                                        'seed': 42
                                    }, )
    dfs = ccMorris.to_df()
    manager.get_list_sens_factors()

    with ApsimModel("Morris") as mor:
        mor.run()
        res= mor.results
        mor.edit_model()
        ms = mor.get_simulated_output('FallowSensitivityStatistics')
        summary = ms.groupby('Parameter').mean(numeric_only=True)
        view(summary)
        mor.open_in_gui(watch=True)
