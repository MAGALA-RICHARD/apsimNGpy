import os.path
import unittest
from pandas import DataFrame
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester
from apsimNGpy.core.experimentmanager import ExperimentManager as Experiment
from pathlib import Path

cwd = Path.cwd()


class TestExperiment(unittest.TestCase):
    def setUp(self):
        self.experiment_path = Path(f"{self._testMethodName}.apsimx")
        self.save_file_name = Path(f"{self._testMethodName}.apsimx")

    def test_add_factor_with_permutes(self):
        t_experiment = Experiment('Maize', out_path=self.experiment_path)
        t_experiment.init_experiment(permutation=True)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.run()
        self.assertIsInstance(t_experiment.results, DataFrame)
        if isinstance(t_experiment.results, DataFrame):
            self.assertFalse(t_experiment.results.empty, msg='results are empty')

    def test_add_factor_with_permutes_2_factors(self):
        t_experiment = Experiment('Maize', out_path=self.experiment_path)
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

        t_experiment = Experiment('Maize', out_path=self.experiment_path)
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
        self.experiment_path.unlink(missing_ok=True)
        self.save_file_name.unlink(missing_ok=True)
        t_experiment = Experiment('Maize', out=os.path.realpath('my_experiment3.apsimx'))
        t_experiment.init_experiment(permutation=True)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                factor_name='Population')
        filename = str(cwd.joinpath('my_experiment_saved.apsimx'))
        t_experiment.save(file_name=str(self.save_file_name))
        self.assertTrue(os.path.exists(filename), msg='saving experiment failed')
        self.assertGreater(self.experiment_path.stat().st_size, 0, msg='experiment not successfully saved')
        self.assertGreater(self.save_file_name.stat().st_size, 0, msg='experiment not successfully saved')

    def test_save_add_factor(self):

        self.save_file_name.unlink(missing_ok=True)
        t_experiment = Experiment('Maize', out_path=self.experiment_path)
        t_experiment.init_experiment(permutation=True)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                factor_name='Population')

        t_experiment.save(file_name=str(self.save_file_name))
        self.assertGreater(self.save_file_name.stat().st_size, 0, msg='experiment not successfully saved')
        try:
            error = False
            t_experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                    factor_name='Population')
        except Exception as e:
            print(e)
            error = True
        self.assertFalse(error, 'saving and adding factor failed')
        # save again
        self.save_file_name.unlink(missing_ok=True)
        t_experiment.save(file_name=str(self.save_file_name))
        self.assertGreater(self.save_file_name.stat().st_size, 0,
                           msg='experiment not successfully saved after duplicate factor addition test')

    def test_add_factor_with_permutes_fct_rep(self):
        """
        Test that we can handle the unmistakable addition of factors which are identical
        @return:
        """
        t_experiment = Experiment('Maize', out_path=self.experiment_path)
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
        t_experiment = Experiment('Maize', out_path=self.experiment_path)
        t_experiment.init_experiment(permutation=False)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.run()
        self.assertIsInstance(t_experiment.results, DataFrame)
        if isinstance(t_experiment.results, DataFrame):
            self.assertFalse(t_experiment.results.empty, msg='results are empty')

    def tearDown(self):
        self.experiment_path.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
