import os
import unittest
from unittest.mock import patch

import pandas as pd

from apsimNGpy.core.core import CoreModel, find_model, _eval_model, Models
# Import the module where CoreModel class is defined
from apsimNGpy.core.model_loader import save_model_to_file
from apsimNGpy.tests.base_test import BaseTester, set_wd

set_wd()


class TestCoreModel(BaseTester):

    def test_run(self):

        """ Test the run method's behavior under normal conditions.
         ==========================================================="""
        with patch.object(self.test_ap_sim, '_DataStore', create=True) as mock_datastore:
            # if we just run without
            """There are several ways to check if the run was successful, here I have tried all of them"""
            self.test_ap_sim.run(report_name=['Report'])
            self.assertIsInstance(self.test_ap_sim.results, pd.DataFrame,
                                  msg="an error occurred while passing  alist "
                                      "of report names")
            # one more test
            # check if the use pass  report name as str a strict a pandas.core.frame.DataFrame' is returned
            self.test_ap_sim.run(report_name='Report', verbose=False)
            df = self.test_ap_sim.results
            self.assertIsInstance(df, pd.DataFrame)
            # check if it is not empty
            self.assertEqual(df.empty, False, msg='Model was run, but results are empty')
            self.assertTrue(self.test_ap_sim.ran_ok, f'something happened in {repr(self.test_ap_sim)}')

    #            self.assertTrue(mock_datastore.Close.called)

    def test_update_mgt(self):
        """ Test the update method's behavior under
        ==========================================="""
        Amount = 23.557777
        script_name = 'Fertilise at sowing'
        mgt_script = {'Name': script_name, 'Amount': Amount},
        self.test_ap_sim.update_mgt(management=mgt_script)
        # extract user infor
        value = self.test_ap_sim.inspect_model_parameters('Manager', simulations='Simulation',
                                                          model_name='Fertilise at sowing', parameters='Amount')
        amountIn = float(value['Amount'])
        self.assertEqual(amountIn, Amount)

    def test_find_simulations(self):
        """ Test find_simulations based on three input None, lists and string
        =====================================================================
        """
        # test None
        sim = 'Simulation'
        MSG = f'test_find_simulations failed to return requested simulation object: {sim}'
        self.assertTrue(self.test_ap_sim.find_simulations(), msg=MSG)
        # test str
        self.assertTrue(self.test_ap_sim.find_simulations(simulations=sim), msg=MSG)
        # test tuple

        self.assertTrue(self.test_ap_sim.find_simulations(simulations=(sim,)), msg=MSG)
        # test list input
        self.assertTrue(self.test_ap_sim.find_simulations(simulations=[sim]), msg=MSG)

    def test_get_simulated_output(self):
        """ Test load_simulated_results
        requires that the models are run first
        ================================================
        """
        self.test_ap_sim.run()
        if not self.test_ap_sim.ran_ok:
            raise unittest.SkipTest(f'skipping test_simulated_results because model did '
                                    f'not run successfully or db was deleted')
        repos = self.test_ap_sim.get_simulated_output(report_names='Report')
        msg = f"expected pd.dataframe but received {type(repos)}"
        self.assertIsInstance(repos, pd.DataFrame, msg=msg)
        # test if dict not empty
        msg = 'expected dict is empty'

    def test_get_reports(self):
        self.assertIsInstance(self.test_ap_sim.inspect_model('Report'), list)

    def test_inspect_clock(self):
        self.assertIsInstance(self.test_ap_sim.inspect_model('Clock'), list)

    def test_inspect_simulation(self):
        self.assertIsInstance(self.test_ap_sim.inspect_model('Models.Core.Simulation', fullpath=False), list)

    def test_replace_soil_property_values(self):
        parameter = 'Carbon'
        param_values = [2.4, 1.4]
        self.test_ap_sim.replace_soil_property_values(parameter=parameter, param_values=param_values,
                                                      soil_child='Organic', )
        lisT = self.test_ap_sim.inspect_model_parameters(model_type='Organic', simulations='all', model_name='Organic',
                                                         parameters='Carbon')
        lisT = lisT['Carbon'].tolist()
        self.assertIsInstance(lisT, list, msg='expected a list got {}'.format(type(lisT)))
        self.assertTrue(lisT)
        self.assertIsInstance(lisT, list, msg='expected a list got {}'.format(type(lisT)))
        self.assertTrue(lisT)
        # if it was successful
        testP = self.test_ap_sim.inspect_model_parameters(model_type='Organic', model_name='Organic',
                                                          parameters='Carbon')
        testP = testP['Carbon'].tolist()
        self.assertEqual(lisT[:2], param_values,
                         msg=f'replace_soil_property_values was not successful returned {testP}\n got {param_values}')

    def test_replace_soil_properties_by_path(self):
        param_values = [1.45, 1.95]
        self.test_ap_sim.edit_model(model_type='Organic', model_name='Organic', Carbon=param_values)

    def test_update_mgt_by_path(self):
        # test when fmt  ='.'
        pathto = '.Simulations.Simulation.Field.Sow using a variable rule'
        self.test_ap_sim.update_mgt_by_path(path=pathto, Population=7.5, fmt='.')
        self.test_ap_sim.run()
        self.assertTrue(self.test_ap_sim.ran_ok, msg='simulation was not ran when fmt was .')
        # test when fmt = '/'
        pathto = '/Simulations/Simulation/Field.Sow using a variable rule'
        self.test_ap_sim.update_mgt_by_path(path=pathto, Population=7.5, fmt='/')
        self.test_ap_sim.run()
        self.assertTrue(self.test_ap_sim.ran_ok, msg='simulation was not ran when fmt was /')

    def test_create_experiment(self):
        """creates a factorial experiment adds a factor, then test if it runs successfully
        =====================================================================================
        """
        self.test_ap_sim.create_experiment()
        # add factor
        self.test_ap_sim.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20",
                                    factor_name='Nitrogen')
        self.test_ap_sim.run()
        self.assertTrue(self.test_ap_sim.ran_ok, msg='after adding the experiment and factor running apsim failed')

    def test_add_crop_replacements(self):
        self.test_ap_sim.add_crop_replacements(_crop='Maize')
        xp = self.test_ap_sim.Simulations.FindInScope('Replacements')
        if xp:
            rep = True
        else:
            rep = False
        self.assertTrue(rep, msg='replacement was not successful')

    def test_replace_soils_values_by_path(self):
        node = '.Simulations.Simulation.Field.Soil.Organic'
        self.test_ap_sim.replace_soils_values_by_path(node_path=node,
                                                      indices=[0], Carbon=1.3)
        v = self.test_ap_sim.get_soil_values_by_path(node, 'Carbon')['Carbon'][0]
        self.assertEqual(v, 1.3)

    def test_add_db_table(self):
        # self.test_ap_sim.add_db_table(variable_spec=['[Clock].Today', '[Soil].Nutrient.TotalC[1]/1000 as SOC1'], rename='report2')
        self.test_ap_sim.add_db_table(
            variable_spec=['[Clock].Today', '[Soil].Nutrient.TotalC[1]/1000 as SOC1',
                           '[Maize].Grain.Total.Wt*10 as Yield'],
            rename='report4', set_event_names=['[Maize].Harvesting', '[Clock].EndOfYear'])
        # check if report is created
        _reports = self.test_ap_sim.inspect_model('Models.Report()', fullpath=False)

        assert 'report4' in _reports, 'report4 was not found in reports'
        # try running
        self.test_ap_sim.run('report4')

        self.assertTrue(self.test_ap_sim.ran_ok, msg='simulation was not ran after adding the report table report2.')

    def test_loading_defaults_with(self):
        model = CoreModel(model='Maize')
        model.run()
        self.assertTrue(model.ran_ok, 'simulation was not ran after using defualt within CoreModel class')

    def test_find_model_andeval_models(self):
        """
        Unit test for the `find_model` and `_eval_model` functions.
        Verifies that:
        - Models can be found correctly by name (case-insensitive).
        - Strings representing full module paths are evaluated correctly.
        """

        # Test finding a model by simple string name
        clok_model = find_model('clock')
        _eval_model(clok_model)  # Validate model lookup
        self.assertEqual(clok_model, Models.Clock)  # Ensure it matches the Clock model

        simulation_model = find_model('Simulation')
        _eval_model(simulation_model)  # Validate model lookup
        self.assertEqual(simulation_model, Models.Core.Simulation)  # Ensure correct match

        # Test direct evaluation of model paths as strings
        clock = _eval_model('Models.Clock')
        self.assertEqual(clock, Models.Clock)  # Confirm evaluation matches Clock model

        simulation = _eval_model('Models.Core.Simulation')
        self.assertEqual(simulation, Models.Core.Simulation)  # Confirm evaluation matches Core.Simulation model

        # Test direct evaluation of just model name
        experiment = _eval_model('Experiment')
        self.assertEqual(experiment,
                         Models.Factorial.Experiment)  # Confirm evaluation matches Models.Factorial.Experiment model

        factors = _eval_model('Factors')
        self.assertEqual(factors, Models.Factorial.Factors)  # Confirm evaluation matches Models.Factorial.Factors model

    def test_add_model_simulation(self):
        try:
            self.test_ap_sim.add_model('Simulation', adoptive_parent='Simulations', rename='soybean_replaced',
                                       source='Soybean', override=True)
            self.test_ap_sim.inspect_file()
            assert 'soybean_replaced' in self.test_ap_sim.inspect_model('Simulation',
                                                                        fullpath=False), 'testing adding simulations was not successful'
        # clean up
        finally:
            from apsimNGpy.core.core import get_or_check_model
            try:
                self.test_ap_sim.remove_model(model_type='Simulation', model_name='soybean_replaced')
            except Exception as e:
                pass

    def test_edit_model(self):
        self.test_ap_sim.edit_model(model_type='Clock', simulations="Simulation", model_name='Clock',
                                    Start='1900-01-01', End='1990-01-12')
        start = self.test_ap_sim.Start != 'unknown'
        end = self.test_ap_sim.End != 'unknown'
        self.assertTrue(start, 'Simulation start date was not successfully changed')
        self.assertTrue(end, 'Simulation end date was not successfully changed')

    def __test_edit_cultivar_edit_model_method(self):
        """
        Test the edit_cultivar requires that we have replacements in place
        @return:
        """
        from apsimNGpy.core.structure import add_crop_replacements
        add_crop_replacements(self.test_ap_sim, _crop='Maize')
        in_cul = self.test_ap_sim.extract_user_input('Sow using a variable rule')
        in_cultivar = in_cul['Simulation'].get('CultivarName')
        if not in_cultivar:
            raise unittest.SkipTest('skipping test edit cultivar because cultivar not found')
        new_juvenile = 289.777729777
        self.test_ap_sim.edit_model(model_type='Cultivar', model_name=in_cultivar,
                                    commands='[Phenology].Juvenile.Target.FixedValue', values=new_juvenile,
                                    cultivar_manager='Sow using a variable rule')

        # first we check the current '[Phenology].Juvenile.Target.FixedValue': '211'
        cp = self.test_ap_sim.read_cultivar_params(name=in_cultivar)
        com_path = '[Phenology].Juvenile.Target.FixedValue'
        juvenile_original = float(cp.get(com_path))

        self.test_ap_sim.edit_cultivar(commands=com_path, values=new_juvenile, CultivarName=in_cultivar)
        # read again
        juvenile_replacements = self.test_ap_sim.read_cultivar_params(name=in_cultivar)[com_path]
        if juvenile_replacements:
            juvenile_replacements = float(juvenile_replacements)
        self.assertEqual(new_juvenile, juvenile_replacements)
        self.test_ap_sim.run()
        # self.assertGreater(juvenile_replacements, juvenile_original, msg= 'Juvenile target value was not replaced')

    def test_inspect_model_parameters(self):

        w_file = self.test_ap_sim.inspect_model_parameters(model_type='Weather', simulations='Simulation',
                                                           model_name='Weather')
        self.assertIsInstance(w_file, str, msg='Inspect weather model parameters failed, when simulation is a str')
        # test a list of simulations
        w_file = self.test_ap_sim.inspect_model_parameters(model_type='Weather', simulations=['Simulation'],
                                                           model_name='Weather')
        self.assertIsInstance(w_file, dict, msg='Inspect weather model parameters failed, when simualtion is a list')


if __name__ == '__main__':
    ...
    unittest.main()
