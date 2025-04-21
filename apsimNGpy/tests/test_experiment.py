import unittest
from pandas import DataFrame
from apsimNGpy.tests.base_test import BaseTester, set_wd

set_wd()


class TestExperiment(BaseTester):

    def test_add_factor_with_permutes(self):
        self.test_ap_sim.create_experiment(permutation=True)
        # experiment is initialized in base_tester class SetUp
        self.test_ap_sim.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                   factor_name='Nitrogen')
        self.test_ap_sim.run()
        self.assertIsInstance(self.test_ap_sim.results, DataFrame)
        if isinstance(self.test_ap_sim.results, DataFrame):
            self.assertFalse(self.test_ap_sim.results.empty, msg='results are empty')
    def test_add_factor_without_permutes(self):
        self.test_ap_sim.create_experiment(permutation=False)
        # experiment is initialized in base_tester class SetUp
        self.test_ap_sim.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                   factor_name='Nitrogen')
        self.test_ap_sim.run()
        self.assertIsInstance(self.test_ap_sim.results, DataFrame)
        if isinstance(self.test_ap_sim.results, DataFrame):
            self.assertFalse(self.test_ap_sim.results.empty, msg='results are empty')


if __name__ == '__main__':
    unittest.main()
