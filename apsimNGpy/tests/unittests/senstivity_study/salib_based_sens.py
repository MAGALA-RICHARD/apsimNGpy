from apsimNGpy import ApsimModel
from apsimNGpy.sensitivity.sensitivity import CustomSensitivityManager
from maize_parameters import maize_params
from xlwings import view

cultivarName = 'B_110'
if __name__ == '__main__':
    baseFile = r"D:\Elimin_rye_cover_crop_2026\APSIMX\S.apsimx"
    with ApsimModel(baseFile) as model:
        fp = model.inspect_model('Models.PMF.Cultivar')

        reps = dict(zip(model.inspect_model('Models.Report', fullpath=False), model.inspect_model('Models.Report')))
        for name, repo in reps.items():
            if name not in {'MaizeR', "Annual"}:
                model.remove_node(repo)
        # model.open_in_gui(watch=True)
        nam = model.inspect_model('Models.PMF.Cultivar', fullpath=False)
        cls = dict(zip(nam, fp))
        cpath = cls[cultivarName]
        # model.edit_model('Models.Report', model_name='Report',
        #                  variable_spec=['sum([Soil].Nutrient.TotalC[1:2])/1000 as SOC2',
        #                                 "sum of sum([Nutrient].N2Oatm[1:6]) from 01-jan to [Clock].Today as TopN2O"])
        model.save(reload=True)
        cc = CustomSensitivityManager(base_model=model.path, response_vars=["Yield", 'SOC2', 'TN2O'])
        # cc.add_sens_factor(**dict(base= '.Simulations.Sharpsburg.Field1.SurfaceOrganicMatter', param='InitialCNR', bounds=(60, 180)))
        for k, v in maize_params.items():
            for p, value in v.items():
                print(value)
                v = round(float(value), 3)
                upper, lower = 1.5 * v, round((0.5 * v), 4)
                if lower == 0:
                    continue
                bounds = lower, upper
                parameter = dict(base=cpath,
                                 param=f"{p}.FixedValue", bounds=bounds,
                                 managers={'.Simulations.Sharpsburg.Field1.SowMaize': 'CultivarName'}, plant='Maize')
                cc.add_sens_factor(**parameter)

        # cc.add_sens_factor(
        #     **{'base': ".Simulations.Simulation.Field.Sow using a variable rule", 'param': "Population", 'bounds': (2, 10),
        #        'managers': {1: 2}})
        # cc.add_sens_factor(
        #     **{"base": ".Simulations.Simulation.Field.Fertilise at sowing", "param": "Amount", 'bounds': (0, 300,)})
        # ccMorris = cc.build_sense_model(method="morris", n_cores=10, agg_func='mean',
        #                                 sample_options={
        #                                     'seed': 42,
        #                                     "num_levels": 10,
        #                                     "optimal_trajectories": 22,
        #                                 },
        #                                 analyze_options={
        #                                     'conf_level': 0.95,
        #                                     "num_resamples": 1000,
        #                                     "print_to_console": True,
        #                                     'seed': 42
        #                                 }, )
        si_fast = cc.build_sense_model(
            agg_func='mean',
            method="sobol",
            engine='python',
            N=256,
            sample_options={
                "calc_second_order": True,
                "skip_values": 1024,
                "seed": 42,


            },
            analyze_options={
                'conf_level': 0.95,
                "num_resamples": 1000,
                "print_to_console": True,
                "calc_second_order": True,
            },
        )
        # dfs = ccMorris.to_df()
        dfs = si_fast.to_df()
        # ccMorris
        view(dfs[0])
        view(dfs[1])
