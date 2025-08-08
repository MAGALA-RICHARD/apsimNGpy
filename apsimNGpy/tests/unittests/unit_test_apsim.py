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
    def test_run(self):
        model = ApsimModel(model='Maize')
        model.run()
        self.test_ap_sim = model
        self.assertTrue(model.ran_ok)
        model.clean_up(db=True)

    def test_clone_model(self):
        model = ApsimModel(model='Maize')
        sim_name = 'clone_test'
        model.clone_model('Models.Core.Simulation', 'Simulation',
                          'Models.Core.Simulations', rename=sim_name)
        model.run()
        self.assertTrue(model.ran_ok)
        # inspect simulations
        sims = model.inspect_model(model_type='Models.Core.Simulation', fullpath=False)
        assert sim_name in sims, (f'{sim_name} is not among the current simulations, implying simulation was not '
                                  f'successful')
        model.clean_up(db=True)


# initialize the model
if __name__ == '__main__':
    unittest.main()
