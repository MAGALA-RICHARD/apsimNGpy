import os.path
import unittest
from pandas import DataFrame
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester
from apsimNGpy.core.experiment import Experiment
from pathlib import Path

cwd = Path.cwd()


class TestExperiment(unittest.TestCase):

    def test_add_factor_with_permutes(self):
        t_experiment = Experiment('Maize', out=cwd.joinpath('my_experiment.apsimx'))
        t_experiment.init_experiment(permutation=True)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.run()
        self.assertIsInstance(t_experiment.results, DataFrame)
        if isinstance(t_experiment.results, DataFrame):
            self.assertFalse(t_experiment.results.empty, msg='results are empty')

    def test_add_factor_with_permutes_2_factors(self):
        t_experiment = Experiment('Maize', out=cwd.joinpath('my_experiment2.apsimx'))
        t_experiment.init_experiment(permutation=True)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                factor_name='Population')
        # Make sure APSIM runs after experiment set up
        t_experiment.run()
        self.assertIsInstance(t_experiment.results, DataFrame)
        if isinstance(t_experiment.results, DataFrame):
            self.assertFalse(t_experiment.results.empty, msg='results are empty')

    def test_inspection(self):

        t_experiment = Experiment('Maize', out=cwd.joinpath('my_experiment2.apsimx'))
        t_experiment.init_experiment(permutation=True)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                factor_name='Population')
        # Make sure APSIM runs after experiment set up
        t_experiment.run()
        self.assertIsInstance(t_experiment.results, DataFrame)
        if isinstance(t_experiment.results, DataFrame):
            self.assertFalse(t_experiment.results.empty, msg='results are empty')
        managers = all(t_experiment.inspect_model('Manager'))
        self.assertTrue(managers, msg='managers not found in the experiment')

    def test_save(self):
        t_experiment = Experiment('Maize', out=os.path.realpath('my_experiment3.apsimx'))
        t_experiment.init_experiment(permutation=True)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                factor_name='Population')
        filename = str(cwd.joinpath('my_experiment_saved.apsimx'))
        t_experiment.save(file_name=filename)
        self.assertTrue(os.path.exists(filename), msg='saving experiment failed')

    def test_save_add_factor(self):
        t_experiment = Experiment('Maize', out=os.path.realpath('my_experiment5.apsimx'))
        t_experiment.init_experiment(permutation=True)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                factor_name='Population')
        filename = str(cwd.joinpath('my_experiment_saved2.apsimx'))
        t_experiment.save(file_name=filename)
        self.assertTrue(os.path.exists(filename), msg='saving experiment failed')
        try:
            error = False
            t_experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                    factor_name='Population')
        except Exception as e:
            print(e)
            error = True
        self.assertFalse(error, 'saving and adding factor failed')

    def test_add_factor_with_permutes_fct_rep(self):
        """
        Test that we can handle the unmistakable addition of factors which are identical
        @return:
        """
        t_experiment = Experiment('Maize', out=cwd.joinpath('my_experiment33.apsimx'))
        t_experiment.init_experiment(permutation=True)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                factor_name='Population')

        t_experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                factor_name='Population')

        self.assertEqual(t_experiment.n_factors, 2)
        # t_experiment.finalize()
        t_experiment.run()
        self.assertIsInstance(t_experiment.results, DataFrame)
        if isinstance(t_experiment.results, DataFrame):
            self.assertFalse(t_experiment.results.empty, msg='results are empty')
        self.assertEqual(t_experiment.n_factors, 2, msg='n_factors is greater than 3  factor repetition tests failed')

    def test_add_factor_without_permutes(self):
        t_experiment = Experiment('Maize', out=cwd.joinpath('my_experiment3.apsimx'))
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
