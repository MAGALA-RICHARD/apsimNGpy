import gc
import os
import unittest
from pathlib import Path
import gc
from apsimNGpy.core.apsim import ApsimModel, Models
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester

from apsimNGpy.core.pythonet_config import is_file_format_modified

wd = Path.cwd() / "test_apsim"
wd.mkdir(parents=True, exist_ok=True)
os.chdir(wd)

Models = Models


class TestCoreModel(BaseTester):
    def setUp(self):
        self.out_path = Path(f"{self._testMethodName}.apsimx")

        self.test_ap_sim = ApsimModel("Maize", out_path=self.out_path)
        self.mock_sim_path_name = Path(f"__mock__{self._testMethodName}.apsimx")
        self.thickness_sequence_test_values = [100, 200, 200, 200, 300, 250, 400, 450]
        self.expect_ts_auto = [100.0, 100.0, 100.0, 295.0, 297.0, 298.0, 300.0, 301.0, 303.0, 304.0]

    def test_run(self):
        self.test_ap_sim.run()
        self.assertTrue(self.test_ap_sim.ran_ok)
        self.test_ap_sim.clean_up(db=True)

    def test_context_manager(self):
        with ApsimModel("Maize") as model:
            datastore = Path(model.datastore)
            model.run()
            df = model.results
            self.assertFalse(df.empty, msg=f'Empty data frame encountered')
            self.assertTrue(Path(model.path).exists())
        self.assertFalse(Path(model.path).exists(), 'Path exists; context manager not working')
        self.assertFalse(datastore.exists(), msg=f'data store exists context manager not working')
        print('context manager working in ApsimModel Class')

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

        self.test_ap_sim.get_soil_from_web(simulation_name=None, lonlat=(-93.045, 42.0541), thickness_sequence='auto')
        thickness = self.test_ap_sim.inspect_model_parameters(model_type='Models.Soils.Physical', model_name='Physical',
                                                              parameters='Thickness')
        # if it is auto
        ts = thickness['Thickness'].tolist()
        self.assertEqual(self.expect_ts_auto, ts)

    def test_get_weather_from_web_seq(self):

        self.test_ap_sim.get_soil_from_web(simulation_name=None, lonlat=(-93.045, 42.0541),
                                           thickness_sequence=self.thickness_sequence_test_values)
        thickness = self.test_ap_sim.inspect_model_parameters(model_type='Models.Soils.Physical', model_name='Physical',
                                                              parameters='Thickness')
        # if it is auto
        ts = thickness['Thickness'].tolist()
        self.assertEqual(ts, self.thickness_sequence_test_values)

    def test_get_weather_from_web_soil_node_missing(self):
        """
        ensure that if soil node is missing, then a soil node is created
        @return:
        """
        import Models
        if is_file_format_modified():
            import APSIM.Core as NodeUtils
            from apsimNGpy.core.cs_resources import CastHelper
            import System
        else:
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
        load_mocked = ApsimModel(self.mock_sim_path_name, out_path=self.out_path)
        # test it
        load_mocked.get_soil_from_web(simulation_name=None, lonlat=(-93.045, 42.0541),
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


# initialize the model
if __name__ == '__main__':
    unittest.main()
