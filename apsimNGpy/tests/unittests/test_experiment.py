import unittest
from pandas import DataFrame
from tests.unittests.base_unit_tests import BaseTester, set_wd
from apsimNGpy.core.experiment import Experiment

set_wd()


class TestExperiment(BaseTester):

    def test_add_factor_with_permutes(self):
        t_experiment = Experiment('Maize', out='my_experiment.apsimx')
        t_experiment.init_experiment(permutation=True)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.run()
        self.assertIsInstance(t_experiment.results, DataFrame)
        if isinstance(t_experiment.results, DataFrame):
            self.assertFalse(t_experiment.results.empty, msg='results are empty')

    def test_add_factor_with_permutes_2_fctrs(self):
        t_experiment = Experiment('Maize', out='my_experiment2.apsimx')
        t_experiment.init_experiment(permutation=True)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                factor_name='Population')
        t_experiment.run()
        self.assertIsInstance(t_experiment.results, DataFrame)
        if isinstance(t_experiment.results, DataFrame):
            self.assertFalse(t_experiment.results.empty, msg='results are empty')

    def test_add_factor_with_permutes_fct_rep(self):
        '''
        Test that we can handle unmistakable addition of factors which are identical
        @return:
        '''
        t_experiment = Experiment('Maize', out='my_experiment33.apsimx')
        t_experiment.init_experiment(permutation=True)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                factor_name='Population')

        t_experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                factor_name='Population')
        #t_experiment.finalize()
        t_experiment.run()
        self.assertIsInstance(t_experiment.results, DataFrame)
        if isinstance(t_experiment.results, DataFrame):
            self.assertFalse(t_experiment.results.empty, msg='results are empty')
        self.assertEqual(t_experiment.n_factors, 2, msg='n_factors is greater than 3  factor repetition tests failed')

    def test_add_factor_without_permutes(self):
        t_experiment = Experiment('Maize', out='my_experiment3.apsimx')
        t_experiment.init_experiment(permutation=False)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.run()
        self.assertIsInstance(t_experiment.results, DataFrame)
        if isinstance(t_experiment.results, DataFrame):
            self.assertFalse(t_experiment.results.empty, msg='results are empty')


if __name__ == '__main__':
    unittest.main()
