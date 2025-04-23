from apsimNGpy.core.base_data import load_default_simulations, load_default_sensitivity_model
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.tests.base_test import BaseTester, set_wd
import unittest
class TestCoreModel(BaseTester):

    def test_run(self):
        model = ApsimModel(model ='Maize')
        model.run()
        self.test_ap_sim =model
        self.assertTrue(model.ran_ok)
# initialize the model
if __name__ == '__main__':
    unittest.main()