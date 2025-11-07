import os
import shutil
import sys
import unittest
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from apsimNGpy.core.config import apsim_version, stamp_name_with_version
from apsimNGpy.core.core import CoreModel, Models
from apsimNGpy.core.model_tools import find_model, validate_model_obj, find_child
from apsimNGpy.settings import logger
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.core.pythonet_config import is_file_format_modified

IS_NEW_APSIM = is_file_format_modified()

wd = Path.cwd() / "test_core"


@lru_cache(maxsize=1)  # run once per process
def prepare():
    if wd.exists():
        try:
            shutil.rmtree(wd)
            logger.info(f"cleaned up directory {wd}")
        except PermissionError:
            for i in wd.iterdir():
                logger.info(f"removing {i}")
                if i.is_file():
                    try:
                        i.unlink(missing_ok=True)
                    except PermissionError:
                        pass


prepare()
wd.mkdir(parents=True, exist_ok=True)
os.chdir(wd)
VERSION = apsim_version()


class TestCoreModel(BaseTester):
    def setUp(self):
        self.user_file_name = stamp_name_with_version(
            os.path.realpath(f"{self._testMethodName}.apsimx"))  # do not delete until tearing up
        self.weather_file_nasa = os.path.realpath('test__met_nasa.met')
        self.weather_file_daymet = os.path.realpath('test_met_daymet.met')
        self.test_user_out_path = stamp_name_with_version(os.path.realpath(f'{self._testMethodName}.apsimx'))
        self.model = 'Maize'
        self.test_save_path = Path(f"save_{self._testMethodName}.apsimx")
        self.test_ap_sim = CoreModel(self.model, out_path=self.user_file_name)
        self.paths = {self.test_user_out_path,
                      self.weather_file_nasa,
                      self.weather_file_daymet,
                      self.user_file_name}

    def test_save_reload_false(self):

        try:
            self.test_save_path.unlink(missing_ok=True)
        except PermissionError:
            pass
        cp = self.test_ap_sim.path
        self.test_ap_sim.save(file_name=self.test_save_path, reload=False)
        self.assertGreater(self.test_save_path.stat().st_size, 0, 'saving the model failed when reload =False')
        self.assertEqual(cp, self.test_ap_sim.path)

    def test_save_reload_true(self):

        try:
            self.test_save_path.unlink(missing_ok=True)
        except PermissionError:
            pass
        cp = self.test_ap_sim.path
        self.test_ap_sim.save(file_name=self.test_save_path, reload=True)
        self.assertGreater(self.test_save_path.stat().st_size, 0, 'saving the model failed when reload =True')
        self.assertNotEqual(cp, self.test_ap_sim.path)

    def test_out_path(self):
        """
        Test that we can provide an output path for the file name
        @return:
        """
        user_name = stamp_name_with_version(os.path.realpath(f'use_name_ot_test.apsimx'))
        if os.path.exists(user_name):
            os.remove(user_name)
        model = CoreModel('Maize', out_path=user_name)
        in_path = str(model.path)
        # self.assertEqual(in_path, str(user_name))
        self.assertGreater(os.path.getsize(user_name), 0, 'out_path is empty')
        model.clean_up()

    def test_random_out_path(self):
        model = CoreModel(self.model, out_path=None)
        self.assertTrue(os.path.exists(model.path))
        self.paths.add(model.path)
        model.clean_up()

    def test_run(self):

        """ Test the run method's behavior under normal conditions.
         ==========================================================="""

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
        self.paths.add(self.user_file_name)
        self.test_ap_sim.clean_up(db=True)

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
        self.test_ap_sim.clean_up()

    def test_get_reports(self):
        self.assertIsInstance(self.test_ap_sim.inspect_model('Report'), list)

    def test_inspect_clock(self):
        self.assertIsInstance(self.test_ap_sim.inspect_model('Clock'), list)

    def test_inspect_simulation(self):
        self.assertIsInstance(self.test_ap_sim.inspect_model('Models.Core.Simulation', fullpath=False), list)

    def test_find__simulations(self):
        # get a list of simulations
        sims = self.test_ap_sim.find_simulations()
        self.assertIsInstance(sims, list)
        self.assertTrue(len(sims) > 0)
        sims = self.test_ap_sim.find_simulations(simulations=None)
        # ensures simulations are enclosed in a list
        self.assertIsInstance(sims, list)
        self.assertTrue(len(sims) > 0)
        self.test_ap_sim.clean_up()

    def test_rename(self):
        NEW_NAME = 'NEW_SIM_NAME'
        NEW_SIMs_NAME = 'NEW_SIMULATION_NAME'
        model = CoreModel(model='Maize')
        model.rename_model(model_type="Simulation", old_name='Simulation', new_name=NEW_NAME)
        # check if it has been successfully renamed
        sims = model.inspect_model(model_type='Simulation', fullpath=False)
        assert NEW_NAME in sims, 'rename not successful'
        # The alternative is to use model.inspect_file to see your changes
        model.rename_model(model_type="Simulations", old_name='Simulations', new_name=NEW_SIMs_NAME)
        assert NEW_SIMs_NAME in model.inspect_model(model_type='Simulations',
                                                    fullpath=False), 'renaming simulations was not successful'

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
        self.test_ap_sim.clean_up()

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
        if IS_NEW_APSIM:
            pass
            # being tested else where in another file
        else:

            self.test_ap_sim.create_experiment()
            # add factor
            self.test_ap_sim.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20",
                                        factor_name='Nitrogen')
            self.test_ap_sim.run()
            self.assertTrue(self.test_ap_sim.ran_ok, msg='after adding the experiment and factor running apsim failed')
            self.test_ap_sim.clean_up()

    def test_add_crop_replacements(self):
        self.test_ap_sim.add_crop_replacements(_crop='Maize')
        xp = find_child(self.test_ap_sim.Simulations, child_name='Replacements', child_class='Models.Core.Folder')
        # xp = self.test_ap_sim.Simulations.FindInScope('Replacements')
        if xp:
            rep = True
        else:
            rep = False
        self.assertTrue(rep, msg='replacement was not successful')
        self.test_ap_sim.clean_up()

    def test_replace_soils_values_by_path(self):
        node = '.Simulations.Simulation.Field.Soil.Organic'
        self.test_ap_sim.replace_soils_values_by_path(node_path=node,
                                                      indices=[0], Carbon=1.3)
        v = self.test_ap_sim.get_soil_values_by_path(node, 'Carbon')['Carbon'][0]
        self.assertEqual(v, 1.3)
        self.test_ap_sim.clean_up()

    def test_add_db_table(self):
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
        self.test_ap_sim.clean_up()

    def test_loading_defaults_with(self):
        model = CoreModel(model='Maize', out_path=Path('ld.apsimx'))
        model.run()
        self.assertTrue(model.ran_ok, 'simulation was not ran after using default within CoreModel class')
        self.paths.add(model.path)
        model.clean_up()

    def test_edit_with_path_som(self):
        model = CoreModel(model='Maize', out_path='path_som.apsimx')
        initial_ratio = 200.0
        model.edit_model_by_path('.Simulations.Simulation.Field.SurfaceOrganicMatter', InitialCNR=initial_ratio,
                                 verbose=False)
        # after inspecting if it was successfully updated
        icnr = model.inspect_model_parameters(model_type='SurfaceOrganicMatter', model_name='SurfaceOrganicMatter',
                                              parameters='InitialCNR')
        self.assertEqual(icnr['InitialCNR'], initial_ratio, msg='InitialCNR was not successfully updated by '
                                                                'edit_model_by_path method')
        self.paths.add(model.path)
        model.clean_up()

    def test_find_model_and_eval_models(self):
        """
        Unit test for the `find_model` and `_eval_model` functions.
        Verifies that:
        - Models can be found correctly by name (case-insensitive).
        - Strings representing full module paths are evaluated correctly.
        """

        # Test finding a model by simple string name
        clok_model = find_model('clock')
        validate_model_obj(clok_model)  # Validate model lookup
        self.assertEqual(clok_model, Models.Clock)  # Ensure it matches the Clock model

        simulation_model = find_model('Simulation')
        validate_model_obj(simulation_model)  # Validate model lookup
        self.assertEqual(simulation_model, Models.Core.Simulation)  # Ensure correct match

        # Test direct evaluation of model paths as strings
        clock = validate_model_obj('Models.Clock')
        self.assertEqual(clock, Models.Clock)  # Confirm evaluation matches Clock model

        simulation = validate_model_obj('Models.Core.Simulation')
        self.assertEqual(simulation, Models.Core.Simulation)  # Confirm evaluation matches Core.Simulation model

        # Test direct evaluation of just model name
        experiment = validate_model_obj('Experiment')
        self.assertEqual(experiment,
                         Models.Factorial.Experiment)  # Confirm evaluation matches Models.Factorial.ExperimentManager model

        factors = validate_model_obj('Factors')
        self.assertEqual(factors, Models.Factorial.Factors)  # Confirm evaluation matches Models.Factorial.Factors model

    def test_add_model_simulation(self):
        if not IS_NEW_APSIM:

            try:
                self.test_ap_sim.add_model('Simulation', adoptive_parent='Simulations', rename='soybean_replaced',
                                           source='Soybean', override=True)

                assert 'soybean_replaced' in self.test_ap_sim.inspect_model('Simulation',
                                                                            fullpath=False), 'testing adding simulations was not successful'
            # clean up
            finally:
                from apsimNGpy.core.core import get_or_check_model

                self.test_ap_sim.remove_model(model_class='Simulation', model_name='soybean_replaced')

    def test_inspect_file(self):
        _inspected = self.test_ap_sim.inspect_file(console=False)
        self.assertTrue(_inspected)

    def test_get_weather_from_web_nasa(self):
        model = load_default_simulations('Maize')
        try:
            model.get_weather_from_web(lonlat=(-93.50456, 42.601247), start=1990, end=2001, source='nasa',
                                       filename=self.weather_file_nasa)
            model.run()
            self.assertTrue(model.ran_ok)
            self.paths.add(model.path)
            model.clean_up()
        except KeyError:
            pass

    def test_get_weather_from_web_daymet(self):
        model = load_default_simulations('Maize')
        model.get_weather_from_web(lonlat=(-93.50456, 42.601247), start=1990, end=2001, source='daymet',
                                   filename=self.weather_file_daymet)
        model.run()
        self.assertTrue(model.ran_ok)
        self.paths.add(model.path)
        model.clean_up()

    def test_edit_model(self):
        self.test_ap_sim.edit_model(model_type='Clock', model_name='Clock', simulations="Simulation",
                                    Start='1900-01-01', End='1990-01-12')
        start = self.test_ap_sim.Start != 'unknown'
        end = self.test_ap_sim.End != 'unknown'
        self.assertTrue(start, 'Simulation start date was not successfully changed')
        self.assertTrue(end, 'Simulation end date was not successfully changed')

    def test_edit_cultivar_edit_model_method(self):
        """
        Test the edit_cultivar requires that we have replacements in place
        @return:
        """
        test_ap_sim = CoreModel('Maize', out_path=self.user_file_name)
        # test_ap_sim.add_crop_replacements(_crop='Maize')

        out_cultivar = 'B_110-e'
        new_juvenile = 289.777729777
        com_path = '[Phenology].Juvenile.Target.FixedValue'
        test_ap_sim.edit_model(model_type='Cultivar', model_name='B_110', new_cultivar_name=out_cultivar,
                               commands=com_path, values=new_juvenile, cultivar_manager='Sow using a variable rule')

        # first we check the current '[Phenology].Juvenile.Target.FixedValue': '211'
        cp = test_ap_sim.inspect_model_parameters(model_type='Cultivar', model_name=out_cultivar)
        self.assertEqual(new_juvenile, float(cp.get(com_path)))
        self.paths.add(test_ap_sim.path)
        test_ap_sim.clean_up()

    def _test_edit_cultivar(self):

        """This is deprecated though"""
        com_path = '[Phenology].Juvenile.Target.FixedValue'

        test_ap_sim = CoreModel("Maize", out_path=self.user_file_name)
        cp = test_ap_sim.inspect_model_parameters(model_type='Cultivar', model_name='B_110')

        new_juvenile = 289.888
        test_ap_sim.edit_cultivar(commands=com_path, values=new_juvenile, CultivarName='B_110')
        # read again
        juvenile_replacements = test_ap_sim.inspect_model_parameters(model_type='Cultivar', model_name='B_110')[
            com_path]
        if juvenile_replacements:
            juvenile_replacements = float(juvenile_replacements)
        self.assertEqual(new_juvenile, juvenile_replacements)
        test_ap_sim.run()
        self.paths.add(test_ap_sim.path)
        test_ap_sim.clean_up()

    def test_inspect_model_parameters(self):

        w_file = self.test_ap_sim.inspect_model_parameters(model_type='Weather', simulations='Simulation',
                                                           model_name='Weather')
        self.assertIsInstance(w_file, str, msg='Inspect weather model parameters failed, when simulation is a str')
        # test a list of simulations
        w_file = self.test_ap_sim.inspect_model_parameters(model_type='Weather', simulations=['Simulation'],
                                                           model_name='Weather')
        self.assertIsInstance(w_file, dict, msg='Inspect weather model parameters failed, when simulation is a list')

    def test_model_info_attributes(self):
        self.assertTrue(self.test_ap_sim.datastore, ' datastore is set to to empty or None')
        self.assertTrue(self.test_ap_sim._DataStore, '_DataStore model is set to to empty or None')
        self.assertTrue(self.test_ap_sim.Datastore, '_DataStore is set to empty or null')

    def test_model_info_types(self):
        self.assertIsInstance(self.test_ap_sim.Datastore, Models.Storage.DataStore,
                              msg='Inspect DataStore, data store was not casted to Models.Storage.DataStore')
        self.assertIsInstance(self.test_ap_sim._DataStore, Models.Storage.DataStore,
                              msg='Inspect DataStore, data store was not casted to Models.Storage.DataStore')

    def test_simulation_container(self):
        self.assertIsInstance(self.test_ap_sim.Simulations, Models.Core.Simulations,
                              msg=f'{self.test_ap_sim.Simulations} is expeced to be a Models.Core.Simulations object perhaps casting was not done')

    def test_remove_variable_spec(self):
        variable_spec = '[Clock].Today as Date'
        vs = self.test_ap_sim.inspect_model_parameters('Models.Report', 'Report')['VariableNames']
        vsIn = variable_spec in vs
        self.assertFalse(vsIn, msg=f'Variable {variable_spec} already in report')
        # safe to add it now
        self.test_ap_sim.add_report_variable(variable_spec=variable_spec, report_name='Report')
        vs = self.test_ap_sim.inspect_model_parameters('Models.Report', 'Report')['VariableNames']
        vsIn = variable_spec in vs
        self.assertTrue(vsIn, msg=f'Variable {variable_spec} successfully added')
        # remove it
        self.test_ap_sim.remove_report_variable(variable_spec='[Clock].Today as Date', report_name='Report')
        vs = self.test_ap_sim.inspect_model_parameters('Models.Report', 'Report')['VariableNames']
        vsIn = variable_spec in vs
        self.assertFalse(vsIn, msg=f'Variable {variable_spec} was not successfully removed')

    def test_context_manager(self):
        with CoreModel("Maize") as model:
            datastore= Path(model.datastore)
            model.run()
            df = model.results
            self.assertFalse(df.empty, msg=f'Empty data frame encountered')
            self.assertTrue(Path(model.path).exists())
        self.assertFalse(Path(model.path).exists(), 'Path exists; context manager not working')
        self.assertFalse(datastore.exists(), msg=f'data store exists context manager not working')

    def tearDown(self):
        self.test_ap_sim.clean_up(db=True)
        for path in self.paths:
            if os.path.exists(path):
                os.remove(path)
        try:
            self.test_save_path.unlink(missing_ok=True)
        except PermissionError:
            pass


if __name__ == '__main__':
    ...
    unittest.main()
