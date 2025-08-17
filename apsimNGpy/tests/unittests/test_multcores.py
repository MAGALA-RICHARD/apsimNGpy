import os.path
from pathlib import Path
from apsimNGpy.core_utils.database_utils import get_db_table_names, read_db_table
import pandas as pd
from apsimNGpy.core.mult_cores import MultiCoreManager
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester
import sys
import unittest

from apsimNGpy.settings import logger


class TestMultiCoreManager(BaseTester):
    def setUp(self):
        self.model = 'Maize'
        self.data_db = Path('test12.db').resolve()
        self.db_path_agg_func = Path('test22.db').resolve()
        self.out_path_no_agg = os.path.realpath('maize_multi_core_test_no_agg.apsimx')
        self.out_path_mean = os.path.realpath('maize_multi_core_test_mean.apsimx')
        self.jobs = ['Maize', "Soybean", 'Barley', 'Canola']
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

    def _test_run_all_jobs(self, agg_func=None, clear_db_test=True, threads=True, cores=2):
        """tests if run_all_tests work udner various conditions"""
        core_manager_mean = MultiCoreManager(db_path=self.data_db, agg_func=agg_func)

        # using processes will fail in this environment, so threads are appropriate
        core_manager_mean.run_all_jobs(jobs=self.jobs, threads=threads, n_cores=cores, clear_db=clear_db_test,
                                       clean_up=True)
        df = core_manager_mean.results
        self.assertFalse(df.empty)
        # if mean aggregators worked, then number of rows are two
        if agg_func is not None:
            rows = df.shape[0] == len(self.jobs)

            self.assertTrue(rows, f"agg function {agg_func} failed")
        else:
            rows = df.shape[0] > len(self.jobs)
            self.assertTrue(rows)

    def test_run_all_jobs(self):
        logger.info('testing run_all_tests. agg_func = mean')
        self._test_run_all_jobs(agg_func='mean', clear_db_test=True)
        logger.info('testing run_all_tests. agg_func = None')
        self._test_run_all_jobs(agg_func=None, clear_db_test=True)
        # logger.info('testing run_all_tests. agg_func = mean, threads = False')
        # # try multiprocess
        # try:
        #     self._test_run_all_jobs(agg_func='mean', threads=False)
        # except Exception as e:
        #     pass
        #     logger.error(e)
        #     logger.info(f'testing run_all_tests. agg_func = mean, threads =False, Failed\n because of {e}')


def test_multiprocessing():
    """this is being run separately for multiprocessing in test_main"""
    if __name__ == '__main__':
        if sys.platform.startswith('win'):
            import multiprocessing as mp
            mp.freeze_support()
        unittest.main()


test_multiprocessing()
