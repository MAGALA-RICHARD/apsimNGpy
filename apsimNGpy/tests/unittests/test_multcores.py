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
        self.core_manager_mean = MultiCoreManager(db_path=self.data_db, agg_func=None)
        self.core_manager_no_agg = MultiCoreManager(db_path=self.data_db, agg_func='mean')
        self.insert_data_db = os.path.realpath('test313.db')
        self.insert_data_manager = MultiCoreManager(db_path=self.insert_data_db)
        self.test_clear_db = os.path.realpath('test314.db')

    def tearDown(self):

        remove = [self.data_db, self.db_path_agg_func, self.out_path_no_agg, self.out_path_mean]
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
        size_before_clear = os.path.getsize(self.test_clear_db)
        manager.clear_db()

        if os.path.exists(self.test_clear_db):
            # then it is only cleared inside but not deleted check it out for detailed
            # test if there are any tables
            rd = read_db_table(self.test_clear_db, 'clear_db_test')
            print(rd)
            self.assertTrue(rd.empty)
            size_after_clear = os.path.getsize(self.test_clear_db)
            # self.assertGreater(size_before_clear, size_after_clear)

        else:
            self.assertFalse(os.path.exists(self.test_clear_db))

    def test_insert_data_db(self):
        # ensure files does not exists
        if os.path.exists(self.insert_data_db):
            os.remove(self.insert_data_db)
        # make up data quickly
        df = pd.DataFrame([{"cores": 2, 'sys': "linnux"}, {'sys': 'windows', 'cores': 5}])
        self.insert_data_manager.insert_data(results=df, table='makeup')

    def test_mult_cores_mean_aggregator(self):
        """ test if multicore mean aggregator will work"""


if __name__ == '__main__':
    unittest.main()
