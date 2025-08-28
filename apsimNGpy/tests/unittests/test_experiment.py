import os.path
import unittest
from pandas import DataFrame
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester
from apsimNGpy.core.experimentmanager import ExperimentManager as Experiment
from pathlib import Path

cwd = Path.cwd()


class TestExperiment(BaseTester):
    def setUp(self):
        # """set up is called before each method"""
        self.experiment_path = Path(f"exp_{self._testMethodName}.apsimx")
        self.save_file_name = Path(f"save_{self._testMethodName}.apsimx")
        self.experiment_model = Experiment('Maize', out_path=self.experiment_path)

    def test_add_factor_with_permutes(self):
        t_experiment = self.experiment_model
        t_experiment.init_experiment(permutation=True)
        # experiment is initialized in base_tester class SetUp
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.run()
        self.assertIsInstance(t_experiment.results, DataFrame)
        if isinstance(t_experiment.results, DataFrame):
            self.assertFalse(t_experiment.results.empty, msg='results are empty')

    def test_add_factor_with_permutes_2_factors(self):
        t_experiment = self.experiment_model
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

        t_experiment = self.experiment_model
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
        try:
            self.save_file_name.unlink(missing_ok=True)
            t_experiment = self.experiment_model
            t_experiment.init_experiment(permutation=True)
            # experiment is initialized in base_tester class SetUp
            t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                    factor_name='Nitrogen')
            t_experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                    factor_name='Population')

            t_experiment.save(file_name=str(self.save_file_name))

            self.assertGreater(self.experiment_path.stat().st_size, 0, msg='experiment not successfully saved')
            self.assertGreater(self.save_file_name.stat().st_size, 0, msg='experiment not successfully saved')
        finally:
            pass
        #     self._clean(self.experiment_path)
        #     self._clean(self.save_file_name)

    def test_save_add_factor(self):

        self.save_file_name.unlink(missing_ok=True)
        t_experiment = self.experiment_model
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
        t_experiment = self.experiment_model
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
        t_experiment = self.experiment_model
        t_experiment.init_experiment(permutation=False)
        t_experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                factor_name='Nitrogen')
        t_experiment.run()
        self.assertIsInstance(t_experiment.results, DataFrame)
        if isinstance(t_experiment.results, DataFrame):
            self.assertFalse(t_experiment.results.empty, msg='results are empty')

    def _clean(self, apsimx_file):
        path = Path(apsimx_file)
        db = path.with_suffix('.db')
        bak = path.with_suffix('.bak')
        db_wal = path.with_suffix('.db-wal')
        db_shm = path.with_suffix('.db-shm')
        db_csv = path.with_suffix('.Report.csv')
        clean_candidates = {bak, db, bak, db_wal, path, db_shm, db_csv}
        for candidate in clean_candidates:
            try:
                candidate.unlink(missing_ok=True)
            except PermissionError:
                pass

    def tearDown(self):
        self.clean_up_apsim_data(self.experiment_path)
        self.clean_up_apsim_data(self.save_file_name)


if __name__ == '__main__':
    unittest.main()
