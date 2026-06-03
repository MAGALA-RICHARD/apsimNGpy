# test_collect_returned_results.py
import unittest
from pathlib import Path
import pandas as pd

from apsimNGpy.core_utils.database_utils import read_db_table, delete_all_tables
# import your decorator
from apsimNGpy.parallel.data_manager import write_results_to_sql


class CollectReturnedResultsTests(unittest.TestCase):
    def setUp(self):

        self.tmp_dir = Path(__file__).parent.parent

        # base path without suffix; decorator should add ".db"
        self.db_base = self.tmp_dir / "runs"
        self.db_expect = str(self.db_base.with_suffix(".db"))
        self.db_path = self.tmp_dir / f'_{self._testMethodName}_db.db'

        self.make_decorator = write_results_to_sql

    def test_worker_df(self):
        try:
            self.db_path.unlink(missing_ok=True)
        except PermissionError:
            pass

        @self.make_decorator(db_path=self.db_path, table='Report')
        def worker_df():
            return pd.DataFrame({"sim_id": [1, 2], "yield": [10.2, 9.8]})
            # ____________delete table if exists_________________

        if self.db_path.exists():
            delete_all_tables(str(self.db_path))
        res = worker_df()
        # _____________ read data from self.db_path _______________________
        df = self.read(tables='Report')
        self.assertEqual(df.shape, (2, 2))

    def test_worker_dict_table(self):
        try:
            self.db_path.unlink(missing_ok=True)
        except PermissionError:
            pass

        records = [
            {"sim": 1, "status": "ok"},
            {"sim": 2, "status": "ok"},
        ]

        @self.make_decorator(db_path=self.db_path)
        def worker_dict_table():
            return records

        # ____________delete tables if exists_________________
        if self.db_path.exists():
            delete_all_tables(str(self.db_path))
        worker_dict_table()
        # _____________ read data from self.db_path _______________________
        df = self.read('Report')
        self.assertEqual(df.shape, (2, 2))

    def test_worker_multi_mapping(self):
        try:
            self.db_path.unlink(missing_ok=True)
        except PermissionError:
            pass

        df1 = pd.DataFrame({"sim": [1, 2], "yield": [8.1, 8.3]})
        df2 = pd.DataFrame({"sim": [3, 4], "yield": [7.4, 7.9]})
        run_records = [{"sim": 1, "status": "ok"}, {"sim": 2, "status": "fail"}]

        @self.make_decorator(db_path=self.db_path, if_exists='append')
        def worker_multi():
            return {
                "Maize": df1,
                "Soybean": df2,
                "Runs": run_records,  # list[dict] -> DataFrame
            }

        # ____________delete tables if exists_________________
        if self.db_path.exists():
            delete_all_tables(str(self.db_path))
        _ = worker_multi()
        # _____________ read data from self.db_path _______________________
        df = self.read(tables=('Maize', "Runs", "Soybean"))
        self.assertEqual(df.shape, (6, 3))

    def test_worker_pairs(self):
        try:
            self.db_path.unlink(missing_ok=True)
        except PermissionError:
            pass

        df1 = pd.DataFrame({"id": [1, 2], "n2o": [0.8, 0.7]})
        df2 = pd.DataFrame({"id": [3, 4], "n2o": [0.5, 0.6]})

        @self.make_decorator(db_path=self.db_path)
        def worker_pairs():
            return [("Maize", df1), ("Soybean", df2)]

        # ____________delete tables if exists_________________
        if self.db_path.exists():
            delete_all_tables(str(self.db_path))
        _ = worker_pairs()
        # _____________ read data from self.db_path _______________________
        df = self.read(tables=["Maize", "Soybean"])
        self.assertEqual(df.shape, (4, 2))
        soybean = self.read(tables=["Soybean"])
        self.assertEqual(soybean.shape, (2, 2))

    def read(self, tables):
        if isinstance(tables, str):
            tables = [tables]
        df = [read_db_table(db=self.db_path, report_name=i) for i in tables]
        if df:
            df = pd.concat(df)
        return df

    def tearDown(self):
        try:
            self.db_path.unlink(missing_ok=True)
        except PermissionError:
            pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
