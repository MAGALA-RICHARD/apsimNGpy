import gc
import os
import unittest
from pathlib import Path
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester

wd = Path.cwd() / "test_apsim"
wd.mkdir(parents=True, exist_ok=True)
os.chdir(wd)
from apsimNGpy import Apsim

apsim = Apsim()


class TestCoreModel(BaseTester):
    def setUp(self):

        self.out_path = Path(f"{self._testMethodName}.apsimx")
        self.wd = wd
        self.test_ap_sim = apsim.ApsimModel("Maize", out_path=self.out_path)
        self.mock_sim_path_name = Path(f"__mock__{self._testMethodName}.apsimx")
        self.thickness_sequence_test_values = [100, 200, 200, 200, 300, 250, 400, 450]
        self.expect_ts_auto = [50.0, 50.0, 50.0, 316.0, 318.0, 319.0, 321.0, 322.0, 324.0, 325.0]

    def test_run(self):
        self.test_ap_sim.run()
        self.assertTrue(self.test_ap_sim.ran_ok)
        self.test_ap_sim.clean_up(db=True)

    def test_ensures_all_simulations_are_loaded(self):
        # this has about 4 simulations
        with apsim.ApsimModel('Report') as model:
            sims = model.simulations_list
            self.assertGreater(len(model), 1)

    def helper_nested_sims(self, model):
        pa = model.inspect_model_parameters(model_type='Models.Manager', model_name='AutomaticIrrigation',
                                            simulations='Seasonal')
        # by default manager parameters are integers
        self.assertEqual(pa['maximumAmount'], '21')
        self.assertEqual(pa['returndays'], '3')

    def test_editing_nested_simulations(self):
        with apsim.ApsimModel('Report') as model:
            model.edit_model(model_type='Models.Manager', model_name='AutomaticIrrigation', simulations='Seasonal',
                             returndays=3, maximumAmount=21)
            self.helper_nested_sims(model)

    def test_edit_nested_simulations_by_path(self):
        with apsim.ApsimModel('Report') as model:
            model.edit_model_by_path('.Simulations.Grouping.Seasonal.Field.AutomaticIrrigation', returndays=3,
                                     maximumAmount=21)
            self.helper_nested_sims(model)

    def test_tree_on_nested_sims(self):
        """
        Test that we can graphically represent the model tree elements

        """
        with apsim.ApsimModel('Report') as model:
            con = model.tree(console=False)
            false = dict(con) == dict()
            self.assertFalse(false)

    def test_inspect_on_nested_sims(self):
        """
        test if all clocks for each simulation are successfully inspected by inspect_model method

        """
        with apsim.ApsimModel('Report') as model:
            clk_str = model.inspect_model('Models.Clock')
            self.assertEqual(len(clk_str), len(model))

    def test_set_params_cultivar(self):
        with apsim.ApsimModel('Maize') as model:
            model.run()
            # mean 1
            mn1 = model.results.mean(numeric_only=True)
            rename = "edited_RUE"
            model.set_params(values=[1.4], commands=['[Leaf].Photosynthesis.RUE.FixedValue'],
                             sowed=True, rename=rename, plant='Maize',
                             managers={'Sow using a variable rule': 'CultivarName'},
                             path=".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82", )
            model.run()
            mn2 = model.results.mean(numeric_only=True)
            out = list(mn2 - mn1)
            out = [i == 0 for i in out]

            out = all(out)
            self.assertFalse(out, msg='editing cultivar failed to change simulated values')
            sower = model.inspect_model_parameters(model_type='Models.Manager', model_name='Sow using a variable rule')
            self.assertIn(rename, sower.values())

    def test_evaluate_simulated_output(self):
        from apsimNGpy.tests.unittests.test_factory import obs

        with apsim.ApsimModel('Maize') as model:
            model.add_report_variable(variable_spec='[Clock].Today.Year as year', report_name='Report')
            model.run()
            metrics = model.evaluate(ref_data=obs, table='Report', index_col=['year'],
                                     target_col='Yield', ref_data_col='observed')
            self.assertIsInstance(metrics, dict, f'Metrics should be a dictionary, got {type(metrics)}')
            self.assertIn('data', metrics.keys(), f'data  key not found in {metrics.keys()}')

    def test_evaluate_simulated_output_runtime_error(self):
        from apsimNGpy.tests.unittests.test_factory import obs

        with apsim.ApsimModel('Maize') as model:
            model.add_report_variable(variable_spec='[Clock].Today.Year as year', report_name='Report')

            with self.assertRaises(RuntimeError, msg="expected to raise runtime error"):
                metrics = model.evaluate(ref_data=obs, table='Report', index_col=['year'],
                                         target_col='Yield', ref_data_col='observed')

    def test_evaluate_simulated_output_direct_predicted_data_as_table(self):
        from apsimNGpy.tests.unittests.test_factory import obs

        with apsim.ApsimModel('Maize') as model:
            model.add_report_variable(variable_spec='[Clock].Today.Year as year', report_name='Report')
            model.run('Report')
            metrics = model.evaluate(ref_data=obs, table=model.results, index_col=['year'],
                                     target_col='Yield', ref_data_col='observed')
            self.assertIsInstance(metrics, dict, f'Metrics should be a dictionary, got {type(metrics)}')
            self.assertIn('data', metrics.keys(), f'data  key not found in {metrics.keys()}')

    def test_evaluate_simulated_output_type_error(self):
        from apsimNGpy.tests.unittests.test_factory import obs

        with apsim.ApsimModel('Maize') as model:
            model.add_report_variable(variable_spec='[Clock].Today.Year as year', report_name='Report')
            model.run()
            with self.assertRaises(TypeError, msg="expected to raise  TypeError"):
                metrics = model.evaluate(ref_data=[obs], table='Report', index_col=['year'],
                                         target_col='Yield', ref_data_col='observed')
            with self.assertRaises(TypeError, msg="expected to raise TypeError"):
                metrics = model.evaluate(ref_data=obs, table=[model.results], index_col=['year'],
                                         target_col='Yield', ref_data_col='observed')

    def test_context_manager(self):
        with apsim.ApsimModel("Maize") as model:
            datastore = Path(model.datastore)
            model.run()
            df = model.results
            self.assertFalse(df.empty, msg=f'Empty data frame encountered')
            self.assertTrue(Path(model.path).exists())
        self.assertFalse(Path(model.path).exists(), 'Path exists; context manager not working')
        self.assertFalse(datastore.exists(), msg=f'data store exists context manager not working')
        print('context manager working in ApsimModel Class')

    def test_model_editing_in_test_context_manager(self):
        """
        Ensure that changes are occurring with model editing in test context manager
        """

        with apsim.ApsimModel('Maize') as model:
            model.edit_model('Models.Manager', 'Sow using a variable rule', Population=8)
            mn1 = model.run().results.Yield.mean()
            model.edit_model('Models.Manager', 'Sow using a variable rule', Population=9.2)
            mn2 = model.run().results.Yield.mean()
            # expect high-planting density to produce more yield that a lower one hence, asserting greater than lower population density
            self.assertGreater(mn2, mn1,
                               'mean corn yield at high population density is not greater than mean at low population density')
        # should be called after exiting with block
        self.assertFalse(Path(model.datastore).exists(), 'context manager not working as expected while model editing')
        self.assertFalse(Path(model.path).exists(), 'context manager now working as expected while model editing')

    def test_saving_while_using_auto_context_manager_reload(self):
        """
            Ensure that saving apsimx file and reloading within the with block works correctly, and that the file will still be deleted
            """

        with apsim.ApsimModel('Maize') as model:
            model.edit_model('Models.Manager', 'Sow using a variable rule', Population=4)

            model.edit_model('Models.Manager', 'Sow using a variable rule', Population=9.2)
            model.run().results.Yield.mean()
            fname = f"{self._testMethodName}_with_block.apsimx"
            model.save(file_name=fname, reload=True)
            # it will be deleted anyway but just testing
            self.assertTrue(Path(fname).exists(), 'saving failed while in with block')
            # it must have been deleted by this time
        try:
            self.assertFalse(Path(fname).exists(), 'saved file still exists even after exiting the with block')
        finally:
            try:
                Path(fname).unlink(missing_ok=True)
            except PermissionError:
                pass

    def test_saving_while_using_auto_context_manager_no_reload(self):
        """
          Ensure that the simulations are written to file when the .apsimx file is saved and reloaded below the with block.
         If the saved filename differs from the current one, that new file should be retained.
         Saving inside the with block, however, defeats the purpose of this context manager,
          which is intended to use a temporary working file and automatically delete it on exit. So, here we are just testing the expected behaviors
            """

        with apsim.ApsimModel('Maize') as model:
            model.edit_model('Models.Manager', 'Sow using a variable rule', Population=4)
            model.edit_model('Models.Manager', 'Sow using a variable rule', Population=9.2)
            fname = f"{self._testMethodName}_with_block.apsimx"
            model.save(file_name=fname, reload=False)
            # it will be deleted anyway but just testing
            self.assertTrue(Path(fname).exists(), 'saving failed while in with block')
        # it must still exist on the computer
        try:
            self.assertTrue(Path(fname).exists(), 'saved file does not exists after exiting the with block')
        finally:
            try:
                Path(fname).unlink(missing_ok=True)
            except PermissionError:
                pass

    def test_clone_model(self):
        from apsimNGpy.core.run_time_info import BASE_RELEASE_NO, APSIM_VERSION_NO, GITHUB_RELEASE_NO
        model = self.test_ap_sim
        sim_name = 'clone_test'
        if APSIM_VERSION_NO > BASE_RELEASE_NO or APSIM_VERSION_NO == GITHUB_RELEASE_NO:
            self.skipTest(f"This version of apsimNGpy {APSIM_VERSION_NO} is not supported by clone_method because"
                          f"it is greater than version {BASE_RELEASE_NO}")
        model.clone_model('Models.Core.Simulation', 'Simulation',
                          'Models.Core.Simulations', rename=sim_name)
        model.run()
        self.assertTrue(model.ran_ok)
        # inspect simulations
        sims = model.inspect_model(model_type='Models.Core.Simulation', fullpath=False)
        assert sim_name in sims, (f'{sim_name} is not among the current simulations, implying simulation was not '
                                  f'successful')
        model.clean_up(db=True)

    def test_get_weather_from_web_auto(self):

        self.test_ap_sim.get_soil_from_web(simulations=None, lonlat=(-93.045, 42.0541), thickness_sequence='auto')
        thickness = self.test_ap_sim.inspect_model_parameters(model_type='Models.Soils.Physical', model_name='Physical',
                                                              parameters='Thickness')
        # if it is auto
        ts = thickness['Thickness']
        self.assertEqual(self.expect_ts_auto, ts)

    def test_add_simulations_from_name(self):
        with apsim.ApsimModel('Maize') as model:
            RENAME = 'new_added'
            out = model.clone_simulation(rename=RENAME, base_simulation='Simulation')
            self.assertTrue(out, 'simulation was not cloned')
            sims = {i.Name for i in model.simulations}
            self.assertIn(RENAME, sims, f'{RENAME} was not found {sims}')

    def test_add_simulations_from_index(self):
        with apsim.ApsimModel('Maize') as model:
            RENAME = 'new_added2'
            out = model.clone_simulation(rename=RENAME, base_simulation=0)
            self.assertTrue(out, 'simulation was not cloned')
            sims = {i.Name for i in model}
            self.assertIn(RENAME, sims, f'{RENAME} was not found {sims}')

    def test_get_weather_from_web_seq(self):

        self.test_ap_sim.get_soil_from_web(simulations=None, lonlat=(-93.045, 42.0541),
                                           thickness_sequence=self.thickness_sequence_test_values)
        thickness = self.test_ap_sim.inspect_model_parameters(model_type='Models.Soils.Physical', model_name='Physical',
                                                              parameters='Thickness')
        # if it is auto
        ts = thickness['Thickness']
        self.assertEqual(ts, self.thickness_sequence_test_values)

    def test_switch_wm_tp_swim3(self):
        mo = apsim.ApsimModel('Maize')
        mo.run()
        swat_yield = float(mo.results.Yield.mean())
        from apsimNGpy.core.water import geometric_layers
        mo.switch_wm_to_swim3(layer_structure_th=None, ss_tile_drainage={}, swim_model_params={}
                              )
        th = geometric_layers(max_depth=1800, max_thickness=10, growth=1.1, top_thickness=10)
        mo.switch_wm_to_swim3(layer_structure_th=th, ss_tile_drainage=None, swim_model_params={}
                              )
        mo.switch_wm_to_swim3(
            ss_tile_drainage={
                "DrainDepth": 1201,
                "DrainSpacing": 30000,
                "ImpermDepth": 3000
            },
            swim_model_params={"eo_time": "05:00", "eo_durn": 600.0,
                               "default_rain_time": "00:00",
                               "default_rain_duration": 500.0,
                               "Diagnostics": False,
                               # 'WaterTable': 1400
                               }
        )
        swim = mo.inspect_model_parameters('Models.Soils.Swim3', "Swim3")
        sub = mo.inspect_model_parameters('Models.Soils.SwimSubsurfaceDrain', "SwimSubsurfaceDrain")

        self.assertEqual(swim['default_rain_duration'], 500)
        self.assertEqual(sub['DrainDepth'], 1201)
        self.assertEqual(swim["eo_durn"], 600.0)
        with mo:
            mo.run()
            self.assertFalse(mo.results.empty)
            swim_yield = float(mo.results.Yield.mean())
            self.assertNotEqual(swat_yield, swim_yield, msg='Both swim3 and SWAT yield are the same meaning the changes were not successfully implemented')  # there is no way both models can agree with similar precission

        print(swim)

    def test_get_weather_from_web_soil_node_missing(self):
        """
        ensure that if soil node is missing, then a soil node is created
        @return:
        """
        from apsimNGpy.starter.starter import CLR
        Models = CLR.Models
        NodeUtils = CLR.APsimCore
        CastHelper = CLR.CastHelper
        if not CLR.file_format_modified:
            self.skipTest('version can not mock simulations object using nodes')
        # creates a Models.Core.Simulations object
        mock_sims = NodeUtils.Node.Create(Models.Core.Simulations())
        sim = Models.Core.Simulation()
        # add zone
        zone = Models.Core.Zone()
        sim.Children.Add(zone)
        datastore = Models.Storage.DataStore()
        # add simulation and datastore
        for i in (sim, datastore):
            mock_sims.AddChild(i)
        casted_mock_sims = CastHelper.CastAs[Models.Core.Simulations](mock_sims.Model)
        casted_mock_sims.Write(str(self.mock_sim_path_name))
        load_mocked = apsim.ApsimModel(self.mock_sim_path_name, out_path=self.out_path)
        # test it
        load_mocked.get_soil_from_web(simulations=None, lonlat=(-93.045, 42.0541),
                                      thickness_sequence=self.thickness_sequence_test_values)
        thickness = load_mocked.inspect_model_parameters(model_type='Models.Soils.Physical', model_name='Physical',
                                                         parameters='Thickness')
        if thickness is not None:
            soil_node = True
        else:
            soil_node = False
        self.assertTrue(soil_node, 'missing soil node failed to be added and edited')

    def tearDown(self):
        try:
            self.out_path.unlink(missing_ok=True)
        except  PermissionError:
            pass
        del self.test_ap_sim
        del self.thickness_sequence_test_values
        gc.collect()

    @classmethod
    def tearDownClass(cls):
        cls._clean_up(where=wd)


# initialize the model
if __name__ == '__main__':
    unittest.main()
