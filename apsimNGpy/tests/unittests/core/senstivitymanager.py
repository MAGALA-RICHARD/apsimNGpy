import sys
import unittest
from apsimNGpy.core.senstivitymanager import SensitivityManager
import gc


# def test_sens_managers_morris():
#     """Test method=Morris"""
#     exp = SensitivityManager("Maize", out_path='morris.apsimx')
#     exp.add_sens_factor(name='cnr', path='Field.SurfaceOrganicMatter.InitialCNR', lower_bound=10, upper_bound=120)
#     exp.add_sens_factor(name='cn2bare', path='Field.Soil.SoilWater.CN2Bare', lower_bound=70, upper_bound=100)
#     exp.build_sense_model(method='morris', aggregation_column_name='Clock.Today')
#     exp.inspect_file()
#     # exp.preview_simulation()
#     exp.run(verbose=True)
#     print(exp.statistics)


class SensitivityManagerTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_sens_managers_sobol(self):
        "Test method = Sobol"
        gc.collect()
        if sys.platform != 'win32':
            self.skipTest('skipping sensitivity unsupported platform without containerization')
        print('running sensitivity test configuration for Sobol')
        exp = SensitivityManager("Maize", out_path='sob.apsimx')
        exp.add_sens_factor(name='cnr', path='Field.SurfaceOrganicMatter.InitialCNR', lower_bound=10, upper_bound=120)
        exp.add_sens_factor(name='cn2bare', path='Field.Soil.SoilWater.CN2Bare', lower_bound=70, upper_bound=100)
        exp.build_sense_model(method='sobol', aggregation_column_name='Clock.Today')
        # exp.inspect_file()
        # exp.preview_simulation()
        exp.run(verbose=True)
        self.assertFalse(exp.results.empty, "results are empty after running sensitivity manager")
        self.assertFalse(exp.statistics.empty, "statistics results are empty after running sensitivity manager")

    def test_sens_managers_morris(self):
        """Test method=Morris"""
        gc.collect()
        if sys.platform != 'win32':
            self.skipTest('skipping sensitivity unsupported platform without containerization')
        exp = SensitivityManager("Maize", out_path='morris.apsimx')
        exp.add_sens_factor(name='cnr', path='Field.SurfaceOrganicMatter.InitialCNR', lower_bound=10, upper_bound=120)
        exp.add_sens_factor(name='cn2bare', path='Field.Soil.SoilWater.CN2Bare', lower_bound=70, upper_bound=100)
        exp.build_sense_model(method='morris', aggregation_column_name='Clock.Today')
        exp.tree()
        # exp.preview_simulation()
        exp.run(verbose=True)
        self.assertFalse(exp.results.empty, "results are empty after running sensitivity manager")
        self.assertFalse(exp.statistics.empty, "statistics results are empty after running sensitivity manager")

    def tearDown(self):
        gc.collect()


if __name__ == '__main__':
    # test_sens_managers_morris()
    unittest.main()
