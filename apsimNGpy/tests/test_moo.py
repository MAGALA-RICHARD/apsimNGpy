from apsimNGpy.core.cal import OptimizationBase, pd
import unittest
from apsimNGpy.tests.base_test import BaseTester

data = {
    "year": [1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000],
    "Yield": [7469.616, 4668.505, 555.047, 4504.0, 7820.075, 6823.517,
              3587.101, 2939.152, 6379.435, 7370.301]
}
df = pd.DataFrame(data)

print(df.columns)


class TestOptimizationBase(BaseTester):
    def _test_add_parameters(self):
        model = OptimizationBase('Maize')
        model.add_parameters(path='.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_110',
                             commands='[Phenology].Juvenile.Target.FixedValue', values='?',
                             cultivar_manager='Sow using a variable rule', new_cultivar_name='be',
                             parameter_name='CultivarName')
        fixed_juv = '157.7'
        model._do_model_edit([fixed_juv])
        edited = model.inspect_model_parameters(model_type='Cultivar', model_name='be')[
            '[Phenology].Juvenile.Target.FixedValue']
        self.assertEqual(fixed_juv, edited, 'editing cultivar failed')

    def test_clean_data_time_year(self):
        test_df = pd.DataFrame(data)
        model = OptimizationBase('Maize')
        clean_data = model.clean_data(obs=test_df, data_table='Report', output_column='Yield', obs_time_column='year',
                                      time_step='year')
        self.assertEqual(clean_data.empty, False, msg='Cleaning with year failed')

    def _test_clean_data_time_day(self):
        test_df = df.copy(deep=True)
        test_df['day'] = [i + 1 for i in range(test_df.shape[0])]
        print(test_df['day'])
        model = OptimizationBase('Maize')
        clean_data = model.clean_data(obs=test_df, data_table='Report', output_column='Yield', obs_time_column='day',
                                      time_step='day')
        self.assertEqual(clean_data.empty, False, 'Cleaning with day failed')


if __name__ == "__main__":
    # synthetic data

    mod = OptimizationBase('Maize')
    ar = df.to_numpy(copy=True)
    df = mod.clean_data(obs=df, data_table='Report', output_column='Yield', obs_time_column='year', time_step='year')
    mod.add_parameters('.Simulations.Simulation.Field.SurfaceOrganicMatter', InitialCNR='?', InitialCPR=10)
    # example of adding cultivar
    mod.add_parameters(path='.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_110',
                       commands='[Phenology].Juvenile.Target.FixedValue', values='?',
                       cultivar_manager='Sow using a variable rule', new_cultivar_name='be',
                       parameter_name='CultivarName')
    mod._do_model_edit([23, 156])

    mod.inspect_model_parameters(model_type='Cultivar', model_name='be')
    unittest.main()
