import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

from apsimNGpy.core.mult_cores import MultiCoreManager as ParallelRunner
from apsimNGpy.core.apsim import ApsimModel


class TestParallelRunner(unittest.TestCase):

    def _run_case(self, tmpdir: Path, agg_func, cores=2, clear=True):
        SIZE = 10
        # unique DB per case
        db_path = tmpdir / f"my_{'noagg' if agg_func is None else 'agg'}.db"
        if os.path.exists(db_path):
            os.remove(db_path)

        # build jobs
        create_jobs1 = [ApsimModel('Maize').path for _ in range(SIZE)]

        # run
        runner = ParallelRunner(db_path=str(db_path), agg_func=agg_func)
        runner.run_all_jobs(create_jobs1, n_cores=cores, threads=False, clear_db=clear)

        time.sleep(0.1)  # tiny grace period for OS file handles on Windows
        df = runner.get_simulated_output(axis=0)

        shape = df.shape[0] == 10
        # quick check
        self.assertIsNotNone(df)
        if clear and agg_func is not None:
            # ensure data is deleted
            self.assertTrue(shape, "clearing the data base table failed")
        else:
            self.assertFalse(shape, "data base is clearing itself")
        # runner2.close()  # uncomment if available
        del runner

        # cleanup scratch dirs created by this run

    def test_parallel_runner_sequential(self):
        """
        Run no-aggregation first, wait for it to finish, then run aggregation.
        Ensures no overlap in processes/DB usage.
        """
        with TemporaryDirectory() as td:
            tmpdir = Path(td)

            # move CWD work into the temp dir to contain scratch/artifacts
            cwd = Path.cwd()
            try:

                # 1) no aggregation
                self._run_case(tmpdir, agg_func=None, cores=2, clear=True)
                time.sleep(1)
                # 2) aggregation (runs only after #1 completing)
                self._run_case(tmpdir, agg_func="mean", cores=2, clear=True)
            finally:

                for p in Path('.').glob("*scratch*"):
                    try:
                        shutil.rmtree(p, ignore_errors=True)
                        print('removed scratch directory', os.path.realpath(p))
                    except PermissionError:
                        pass
                time.sleep(1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
