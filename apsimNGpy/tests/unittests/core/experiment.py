import sys
import unittest
from pathlib import Path
from pandas import DataFrame
from apsimNGpy.starter.starter import CLR
if CLR.file_format_modified:
    from apsimNGpy.core.experiment import ExperimentManager as Experiment
    from apsimNGpy.tests.unittests.base_unit_tests import BaseTester

    cwd = Path.cwd()


    class TestExperiment(BaseTester):
        def setUp(self):
            # """set up is called before each method"""
            self.experiment_path = Path(f"exp_r{self._testMethodName}.apsimx").resolve()
            self.save_file_name = Path(f"save_r{self._testMethodName}.apsimx").resolve()
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

        def test_context_manager(self):
            with Experiment("Maize") as model:
                datastore = Path(model.datastore)
                model.init_experiment(permutation=True)
                model.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                 factor_name='Population')

                model.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                 factor_name='Population')

                model.run()
                df = model.results
                self.assertFalse(df.empty, msg=f'Empty data frame encountered')
                self.assertTrue(Path(model.path).exists())
            self.assertFalse(Path(model.path).exists(), 'Path exists; context manager not working as expected')
            if sys.platform == 'win32':
                self.skipTest('skipping windows tests for data clean up on experiment manager')
            self.assertFalse(datastore.exists(), msg=f'data store exists context manager not working as expected')

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

        def _test_inspection(self):

            t_experiment = self.experiment_model
            t_experiment.init_experiment(permutation=True)
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

        def test_ensure_edits_are_registered_while_in_context(self):
            with Experiment('Maize') as experiment:
                experiment.init_experiment(permutation=True)
                experiment.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2",
                                      factor_name='Population')
                experiment.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
                                      factor_name='Nitrogen')
                n1 = experiment.run().results.groupby('Nitrogen')['Yield'].mean()

                # edit
                experiment.edit_model('Models.Manager', 'Sow using a variable rule', StartDate='02-may')
                n2 = experiment.run().results.groupby('Nitrogen')['Yield'].mean()
                self.assertNotEqual(n1.max(), n2.max(), 'edits are not working under context manager')
            print(Path(experiment.datastore).exists())

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

        def tearDown(self):
            self.clean_up_apsim_data(self.experiment_path)
            self.clean_up_apsim_data(self.save_file_name)


    if __name__ == '__main__':
        unittest.main()
