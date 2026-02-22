import os
from apsimNGpy.logger import logger
from apsimNGpy.config import apsim_bin_context, path_checker, configuration, Path, set_apsim_bin_path
import unittest
from dotenv import load_dotenv
import time
BIN_KEY = '7980'
BIN_KEY2 = '7990'
ENV_FILE = '../.env'

path_checker(ENV_FILE)


class TestConfigApsimBinContext(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        bin_path = os.getenv(BIN_KEY)
        self.bin_path = bin_path

    def test_bin_path_with_context(self):
        # first change it
        bp = os.getenv(BIN_KEY2)
        set_apsim_bin_path(bp)
        bin_context = apsim_bin_context(self.bin_path)
        eq = Path(self.bin_path) == Path(configuration.bin_path)
        self.assertTrue(eq)

    def test_bin_path_no_context(self):
        with apsim_bin_context(self.bin_path):
            eq = Path(self.bin_path) == Path(configuration.bin_path)
            self.assertTrue(eq)

    def skip(self):
        if not path_checker(self.bin_path):
            if not path_checker(ENV_FILE):
                skip_msg = f'{ENV_FILE} file does exist'
            else:
                sub_msg = (
                    f"is not set according to the env bin key `{BIN_KEY}`"
                    if self.bin_path is None
                    else f"'{self.bin_path}' does not exist"
                )

                skip_msg = (
                    f"Skipping test `{self._testMethodName}` because APSIM binary path {sub_msg} "

                )

            logger.warning(skip_msg)
            self.skipTest(skip_msg)

    def test_apsim_bin_context(self):
        """
        Test context manager WHEN ONLY env path and bin key are provided

        """
        self.skip()
        with apsim_bin_context(dotenv_path=ENV_FILE, bin_key=BIN_KEY) as bin_run_time:
            with bin_run_time.ApsimModel('Maize') as model:
                model.run()
                self.assertFalse(model.results.empty, 'Results are empty')

    def test_apsim_bin_context_direct_path(self):
        """
        Test context manager, WHEN BIN PATH is provided

        """
        self.skip()
        with apsim_bin_context(apsim_bin_path=self.bin_path) as bin_run_time:
            with bin_run_time.ApsimModel('Maize') as model:
                model.run()
                self.assertFalse(model.results.empty, 'Results are empty')

    def test_apsim_bin_context_no_context(self):
        """
              Test NO context manager

        """
        self.skip()
        bin_run_time = apsim_bin_context(apsim_bin_path=self.bin_path)
        with bin_run_time.ApsimModel('Maize') as model:
            model.run()
            self.assertFalse(model.results.empty, 'Results are empty')

    def test_attributes_attached_no_context(self):
        """Ensure required namespace attributes are exposed by apsim_bin_context."""
        self.skip()

        bin_runtime = apsim_bin_context(self.bin_path)

        # --- Attribute existence checks ---
        self.assertTrue(hasattr(bin_runtime, "ApsimModel"))
        self.assertTrue(hasattr(bin_runtime, "MultiCoreManager"))
        self.assertTrue(hasattr(bin_runtime, "run_apsim_by_path"))
        self.assertTrue(hasattr(bin_runtime, "sensitivity"))
        self.assertTrue(hasattr(bin_runtime, "ConfigProblem"))
        self.assertTrue(hasattr(bin_runtime, "ExperimentManager"))

        # --- Type / callable checks ---
        self.assertTrue(callable(bin_runtime.ApsimModel))
        self.assertTrue(callable(bin_runtime.MultiCoreManager))
        self.assertTrue(callable(bin_runtime.run_apsim_by_path))
        self.assertTrue(callable(bin_runtime.sensitivity))
        self.assertTrue(callable(bin_runtime.ConfigProblem))
        self.assertTrue(callable(bin_runtime.ExperimentManager))

    def test_attributes_attached_with_context(self):
        """Ensure required namespace attributes are exposed by apsim_bin_context."""
        self.skip()

        with  apsim_bin_context(self.bin_path) as bin_runtime:
            # --- Attribute existence checks ---
            self.assertTrue(hasattr(bin_runtime, "ApsimModel"))
            self.assertTrue(hasattr(bin_runtime, "MultiCoreManager"))
            self.assertTrue(hasattr(bin_runtime, "run_apsim_by_path"))
            self.assertTrue(hasattr(bin_runtime, "sensitivity"))
            self.assertTrue(hasattr(bin_runtime, "ConfigProblem"))
            self.assertTrue(hasattr(bin_runtime, "ExperimentManager"))

            # --- Type / callable checks ---
            self.assertTrue(callable(bin_runtime.ApsimModel))
            self.assertTrue(callable(bin_runtime.MultiCoreManager))
            self.assertTrue(callable(bin_runtime.run_apsim_by_path))
            self.assertTrue(callable(bin_runtime.sensitivity))
            self.assertTrue(callable(bin_runtime.ConfigProblem))
            self.assertTrue(callable(bin_runtime.ExperimentManager))


if __name__ == '__main__':
    unittest.main(verbosity=2)
