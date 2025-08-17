import os.path
from pathlib import Path
from apsimNGpy.core_utils.database_utils import get_db_table_names, read_db_table
import pandas as pd
from apsimNGpy.core.mult_cores import MultiCoreManager
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester
import sys
import unittest


class TestMultiCoreManager(BaseTester):
    def setUp(self):
        self.model = 'Maize'
        self.data_db = Path('test12.db').resolve()
        self.db_path_agg_func = Path('test22.db').resolve()
        self.out_path_no_agg = os.path.realpath('maize_multi_core_test_no_agg.apsimx')
        self.out_path_mean = os.path.realpath('maize_multi_core_test_mean.apsimx')
        self.jobs = ['Maize', "Soybean"]
        self.core_manager_no_agg = MultiCoreManager(db_path=self.data_db, agg_func='mean')
        self.insert_data_db = os.path.realpath('test313.db')

        self.test_clear_db = os.path.realpath('test314.db')

    def tearDown(self):

        remove = [self.data_db, self.db_path_agg_func,
                  self.test_clear_db,
                  self.out_path_no_agg, self.out_path_mean]
        for element in remove:
            try:
                if os.path.exists(element): os.remove(element)

            except PermissionError:
                ...

    @staticmethod
    def create_synthetic_data():
        df = pd.DataFrame([{"cores": 2, 'sys': "linnux"}, {'sys': 'windows', 'cores': 5}])
        return df

    def test_clear_db(self):
        manager = MultiCoreManager(db_path=self.test_clear_db)
        # clear before any data is inserted
        manager.clear_db()

        # test after any data is inserted
        df = self.create_synthetic_data()
        manager.insert_data(df, table='clear_db_test')
        table_names = get_db_table_names(self.test_clear_db)
        self.assertIn('clear_db_test', table_names)

        manager.clear_db()

        if os.path.exists(self.test_clear_db):
            # then it is only cleared inside but not deleted
            table_names = get_db_table_names(self.test_clear_db)
            # if clear was successful, then the table names are empty
            self.assertFalse(table_names)
        else:
            self.assertFalse(os.path.exists(self.test_clear_db))

    def test_insert_data_db(self):
        """tests if insert_data method on MultiCoreManager is working"""
        self.insert_data_manager = MultiCoreManager(db_path=self.insert_data_db)
        # ensure files does not exists
        if os.path.exists(self.insert_data_db):
            os.remove(self.insert_data_db)
        # make up data quickly
        df = self.create_synthetic_data()
        self.insert_data_manager.insert_data(results=df, table='makeup')
        df2 = read_db_table(self.insert_data_db, 'makeup')
        self.assertFalse(df2.empty)
        self.assertEqual(df2.shape[0], df.shape[0])

    def test_mult_cores_run_parallel_with_mean_aggregator(self):
        """ test if multicore mean aggregator will work"""
        core_manager_mean = MultiCoreManager(db_path=self.data_db, agg_func="mean")
        core_manager_mean.run_parallel(model=self.model)
        # using processes will fail in this environment, so threads are appropriate
        core_manager_mean.run_all_jobs(jobs=self.jobs, threads=True, n_cores=2, clear_db=True)
        df = core_manager_mean.results
        self.assertFalse(df.empty)
        # if mean aggregators worked, then number of rows are two
        rows = df.shape[0] == len(self.jobs)
        self.assertTrue(rows)

    def test_mult_cores_run_parallel_with_no_aggregator(self):
        """ test if multicore mean aggregator will work"""
        core_manager_mean = MultiCoreManager(db_path=self.data_db, agg_func=None)
        # using processes will fail in this environment, so threads are appropriate
        core_manager_mean.run_all_jobs(jobs=self.jobs, threads=True, n_cores=2, clear_db=True)
        df = core_manager_mean.results
        self.assertFalse(df.empty)
        # Without mean aggregators, number of rows are obviously greater than 2
        rows = df.shape[0] > len(self.jobs)
        self.assertTrue(rows)


def test_multiprocessing():
    """this is being run separately for multiprocessing in test_main"""
    if __name__ == '__main__':
        if sys.platform.startswith('win'):
           import multiprocessing as mp
           mp.freeze_support()
        unittest.main()


test_multiprocessing()
