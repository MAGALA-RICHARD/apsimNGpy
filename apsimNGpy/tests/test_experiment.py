import unittest
from pandas import DataFrame
from apsimNGpy.tests.base_test import BaseTester, os


class TestExperiment(BaseTester):

    def test_experiment(self):
        # experiment is initialized in base_tester class SetUp
        file = self.experiment.path
        self.assertTrue(os.path.exists(file))

    def test_add_factor(self):
        # experiment is initialized in base_tester class SetUp
        self.experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20",
                                   factor_name='Nitrogen')
        self.experiment.run()
        self.assertIsInstance(self.experiment.results, DataFrame)
        if isinstance(self.experiment.results, DataFrame):
            self.assertFalse(self.experiment.results.empty, msg='results are empty')


if __name__ == '__main__':
    unittest.main()
