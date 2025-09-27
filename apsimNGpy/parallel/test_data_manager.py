# test_collect_returned_results.py
import unittest
from pathlib import Path
import tempfile
import pandas as pd

# import your decorator
from apsimNGpy.parallel.data_manager import collect_returned_results


class InsertCollector:
    """Stub inserter: records (db_path, table, df, if_exists) calls."""
    def __init__(self):
        self.calls = []

    def __call__(self, db_path: str, df: pd.DataFrame, table: str, if_exists: str):
        # store a copy to avoid accidental mutation
        self.calls.append((db_path, table, df.copy(), if_exists))


class CollectReturnedResultsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmp_dir = Path(self.tmp.name)

        # base path without suffix; decorator should add ".db"
        self.db_base = self.tmp_dir / "runs"
        self.db_expect = str(self.db_base.with_suffix(".db"))

        self.collector = InsertCollector()

        def make_decorator(default_table="Report"):
            return collect_returned_results(
                db_path=self.db_base,
                table=default_table,
                insert_fn=self.collector,   # inject stub, no real DB
                ensure_parent=True,
            )
        self.make_decorator = make_decorator

    def test_worker_df(self):
        @self.make_decorator(default_table="Report")
        def worker_df():
            return pd.DataFrame({"sim_id": [1, 2], "yield": [10.2, 9.8]})

        res = worker_df()
        self.assertIsInstance(res, pd.DataFrame)

        self.assertEqual(len(self.collector.calls), 1)
        db_path, table, df, if_exists = self.collector.calls[0]
        self.assertEqual(db_path, self.db_expect)
        self.assertEqual(table, "Report")
        pd.testing.assert_frame_equal(
            df.reset_index(drop=True),
            pd.DataFrame({"sim_id": [1, 2], "yield": [10.2, 9.8]}),
            check_dtype=False,
        )
        self.assertEqual(if_exists, "append")

    def test_worker_dict_table(self):
        records = [
            {"sim": 1, "status": "ok"},
            {"sim": 2, "status": "ok"},
        ]

        @self.make_decorator(default_table="IGNORED")
        def worker_dict_table():
            return {"table": "Maize", "data": records}

        res = worker_dict_table()
        self.assertIsInstance(res, dict)

        self.assertEqual(len(self.collector.calls), 1)
        db_path, table, df, if_exists = self.collector.calls[0]
        self.assertEqual(db_path, self.db_expect)
        self.assertEqual(table, "Maize")
        pd.testing.assert_frame_equal(
            df.reset_index(drop=True),
            pd.DataFrame(records),
            check_dtype=False,
        )

    def test_worker_multi_mapping(self):
        df1 = pd.DataFrame({"sim": [1, 2], "yield": [8.1, 8.3]})
        df2 = pd.DataFrame({"sim": [3, 4], "yield": [7.4, 7.9]})
        run_records = [{"sim": 1, "status": "ok"}, {"sim": 2, "status": "fail"}]

        @self.make_decorator(default_table="Report")
        def worker_multi():
            return {
                "Maize": df1,
                "Soybean": df2,
                "Runs": run_records,  # list[dict] -> DataFrame
            }

        _ = worker_multi()

        self.assertEqual(len(self.collector.calls), 3)

        # FIX: correct dict-comprehension (key by table name)
        calls_by_table = {t: (db, t, d, ie) for (db, t, d, ie) in self.collector.calls}

        # Maize
        db_path, table, df, _ = calls_by_table["Maize"]
        self.assertEqual(db_path, self.db_expect)
        pd.testing.assert_frame_equal(df.reset_index(drop=True), df1.reset_index(drop=True), check_dtype=False)

        # Soybean
        db_path, table, df, _ = calls_by_table["Soybean"]
        self.assertEqual(db_path, self.db_expect)
        pd.testing.assert_frame_equal(df.reset_index(drop=True), df2.reset_index(drop=True), check_dtype=False)

        # Runs
        db_path, table, df, _ = calls_by_table["Runs"]
        self.assertEqual(db_path, self.db_expect)
        pd.testing.assert_frame_equal(
            df.reset_index(drop=True),
            pd.DataFrame(run_records),
            check_dtype=False,
        )

    def test_worker_pairs(self):
        df1 = pd.DataFrame({"id": [1, 2], "n2o": [0.8, 0.7]})
        df2 = pd.DataFrame({"id": [3, 4], "n2o": [0.5, 0.6]})

        @self.make_decorator(default_table="Report")
        def worker_pairs():
            return [("Maize", df1), ("Soybean", df2)]

        _ = worker_pairs()

        self.assertEqual(len(self.collector.calls), 2)
        # preserve order of inserts
        (db0, t0, d0, _), (db1, t1, d1, _) = self.collector.calls
        self.assertEqual(db0, self.db_expect)
        self.assertEqual(t0, "Maize")
        pd.testing.assert_frame_equal(d0.reset_index(drop=True), df1.reset_index(drop=True), check_dtype=False)
        self.assertEqual(db1, self.db_expect)
        self.assertEqual(t1, "Soybean")
        pd.testing.assert_frame_equal(d1.reset_index(drop=True), df2.reset_index(drop=True), check_dtype=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
