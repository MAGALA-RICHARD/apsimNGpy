import os
import unittest
from pathlib import Path

from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester
from apsimNGpy.core_utils.clean import clean
import tempfile

wd = Path.cwd() / "test_apsim"
wd.mkdir(parents=True, exist_ok=True)
os.chdir(wd)


class TestCoreModel(BaseTester):
    def setUp(self):
        self.out_path = Path(f"{self._testMethodName}.apsimx")
        self.test_ap_sim = ApsimModel("Maize", out_path=self.out_path)

    def test_run(self):
        self.test_ap_sim.run()
        self.assertTrue(self.test_ap_sim.ran_ok)
        self.test_ap_sim.clean_up(db=True)

    def test_clone_model(self):
        from apsimNGpy.core.run_time_info import BASE_RELEASE_NO, APSIM_VERSION_NO, GITHUB_RELEASE_NO
        model = self.test_ap_sim
        sim_name = 'clone_test'
        if APSIM_VERSION_NO > BASE_RELEASE_NO or APSIM_VERSION_NO == GITHUB_RELEASE_NO:
            self.skipTest(f"This version of apsimNGpy {APSIM_VERSION_NO} is not supported by clone_method becasue"
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

    def tearDown(self):
        pass


# initialize the model
if __name__ == '__main__':
    unittest.main()
