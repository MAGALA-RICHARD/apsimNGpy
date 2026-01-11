import gc
import os
import shutil
import sqlite3
from pathlib import Path
from shutil import rmtree, copy2, rmtree
from apsimNGpy.core.runner import _run_from_dir, collect_db_from_dir, aggregate_data, \
    dir_simulations_to_sql, dir_simulations_to_dfs, dir_simulations_to_csv  # (unused here but kept if you need later)
from apsimNGpy.core.config import load_crop_from_disk
from apsimNGpy.tests.unittests.test_factory import mimic_multiple_files
import unittest
from pandas import DataFrame


def _delete_file(obj):
    ob = Path(obj)
    if ob.is_dir():
        try:
            shutil.rmtree(ob)
        except PermissionError:
            pass
    else:
        try:
            ob.unlink(missing_ok=True)
        except PermissionError:
            pass


class TestRunner(unittest.TestCase):
    def setUp(self):
        """
        Prepare a temporary directory containing generated *.apsimx files for testing.

        The helper function ``mimic_multiple_files()`` can create either:
        - **Homogeneous files** (when ``mix=False``), where all generated APSIMX files
          share the same schema (e.g., all maize models), or
        - **Heterogeneous files** (when ``mix=True``), where two different schemas are
          produced (e.g., maize and soybean models).

        Subsequent test cases rely on this behavior:

        - When ``mix=True``:
            * The aggregated output from ``run_from_dir`` should consist of **two**
              DataFrames, one for each unique schema.
            * The sum of ``CollectionID`` values in the first DataFrame should be
              **half** the ``CollectionID`` sum in the second DataFrame, reflecting
              how the mixed files are generated.

        - When ``mix=False``:
            * ``run_from_dir`` should return **one** aggregated DataFrame (single schema).
            * The sum of ``CollectionID`` values in that DataFrame should equal the sum
              of the dictionary values returned internally by ``run_from_dir`` for the
              homogeneous set.

        This setup initializes two directories:
        ``Dir_mix`` containing heterogeneous files, and
        ``Dir_no_mix`` containing homogeneous files.
        """
        name = self._testMethodName
        self.size = 36
        self.Dir_mix = mimic_multiple_files(out_file=f'out_f1_{name}', size=self.size, mix=True)
        self.Dir_no_mix = mimic_multiple_files(out_file=f'out_f2_{name}', size=self.size, mix=False)

    def test_run_from_dir_mixed_files(self):
        df = dir_simulations_to_dfs(dir_path=self.Dir_mix, pattern="*__.apsimx", recursive=False,
                                    tables='Report',
                                    cpu_count=10)
        keys = df.keys().__len__()

        self.assertEqual(keys, 2)

    def _test_dir_simulation_to_csvs_mixed(self):
        try:
            dfs = dir_simulations_to_csv(dir_path=self.Dir_mix, pattern="*__.apsimx", recursive=False,
                                         cpu_count=10)
            df = list(dfs)

            self.assertTrue(df, 'data not collected from csv')
        finally:
            csvs = Path(self.Dir_mix).rglob("*.csv")
            for i in csvs:
                _delete_file(i)

    def test_data_types(self):
        df = dir_simulations_to_dfs(dir_path=self.Dir_mix, pattern="*__.apsimx", recursive=False,
                                    tables='Report',
                                    cpu_count=10)
        self.assertIsInstance(df, dict)
        pds = all(isinstance(d, DataFrame) for d in df.values())
        empty_or_not = all(d.empty for d in df.values())
        self.assertTrue(pds)
        self.assertFalse(empty_or_not)

    def _test_run_from_dir_not_mixed_files(self):
        df = dir_simulations_to_dfs(dir_path=self.Dir_no_mix, pattern="*__.apsimx", recursive=False,
                                    tables='Report',
                                    cpu_count=10)
        keys = len(df.keys())
        self.assertEqual(keys, 1)
        # here it is one data frame because files are homogenous
        collection_ids = list(df.values())[
            0].CollectionID.unique()
        self.assertEqual(self.size, len(collection_ids))

    def test_connection_homogenous_files(self):
        from sqlalchemy import create_engine, inspect
        database = 'temp_memory.db'
        _delete_file(database)
        engine = create_engine(f"sqlite:///{database}")
        try:

            dir_simulations_to_sql(dir_path=self.Dir_no_mix, pattern="*__.apsimx", recursive=False,
                                   tables='Report',
                                   cpu_count=10, connection=engine)
            tables = inspect(engine).get_table_names()
            print(tables)
            from apsimNGpy.core_utils.database_utils import read_db_table
            data = read_db_table(engine, 'group_1')
            self.assertFalse(data.empty)

            self.assertEqual(len(tables), 2, "There should be two tables, but got {}".format(tables))

        finally:
            engine.dispose(close=True)
            _delete_file(database)

    def test_connection_mixed_files(self):

        from sqlalchemy import create_engine, inspect
        db = f"{self._testMethodName}.db"
        engine = create_engine(f"sqlite:///{db}")
        _delete_file(db)
        try:

            dir_simulations_to_sql(dir_path=self.Dir_mix, pattern="*__.apsimx", recursive=False,
                                   tables='Report',
                                   cpu_count=10, connection=engine)
            tables = inspect(engine).get_table_names()
            schema_in = '_schemas' in tables
            self.assertTrue(schema_in, "_schema table not in available tables")
            self.assertEqual(len(tables), 3, "There should be 3 tables, but got {}".format(tables))
        finally:

            engine.dispose(close=True)
            _delete_file(db)

    def tearDown(self):
        to_delete = (i for i in [self.Dir_mix, self.Dir_no_mix])
        for obj in to_delete:
            _delete_file(obj)
        gc.collect()


if __name__ == "__main__":

    unittest.main()
