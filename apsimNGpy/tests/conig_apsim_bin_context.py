import os
from apsimNGpy.logger import logger
from apsimNGpy.config import apsim_bin_context, path_checker
import unittest
from dotenv import load_dotenv

BIN_KEY = '7980'
ENV_FILE = '../.env'

path_checker(ENV_FILE)


class TestConfigApsimBinContext(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        bin_path = os.getenv(BIN_KEY)
        self.bin_path = bin_path

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
                print(model.summarize_numeric())

    def test_apsim_bin_context_direct_path(self):
        """
        Test context manager, WHEN BIN PATH is provided

        """
        self.skip()
        with apsim_bin_context(apsim_bin_path=self.bin_path) as bin_run_time:
            with bin_run_time.ApsimModel('Maize') as model:
                model.run()
                print(model.summarize_numeric())

    def test_apsim_bin_context_no_context(self):
        """
              Test NO context manager

        """
        self.skip()
        bin_run_time = apsim_bin_context(apsim_bin_path=self.bin_path)
        with bin_run_time.ApsimModel('Maize') as model:
            model.run()
            print(model.summarize_numeric())


if __name__ == '__main__':
    unittest.main(verbosity=2)
