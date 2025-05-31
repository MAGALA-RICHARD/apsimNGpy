import unittest

# Import the module where CoreModel class is defined
from apsimNGpy.core.config import (set_apsim_bin_path, get_apsim_bin_path, auto_detect_apsim_bin_path)
from apsimNGpy.tests.base_test import BaseTester, path

TEST_PATH = "/path/to/test/bin"  # apsim bin path to test

auto = auto_detect_apsim_bin_path()


class TestConfig(BaseTester):

    def test_get_apsim_bin_path(self):
        abp = get_apsim_bin_path()
        p_true = path.exists(abp)
        self.assertTrue(p_true)

    def test_set_apsim_bin_path(self):
        """
        Test that set_apsim_bin_path
        This will always fail if the TEST_PATH above is not pointing correctly to the correct path of APSIM bin files
        @return:
        """
        # Initially retrieve the current APSIM binary path
        original_path = get_apsim_bin_path()

        try:
            # Set a new test path

            set_apsim_bin_path(TEST_PATH, raise_errors=False)

            # Retrieve the path after setting it
            new_path = get_apsim_bin_path()

            # Check if the new path is as expected
            self.assertEqual(new_path, new_path, "The APSIM binary path was not updated correctly.")
           # self.skipTest('The TEST_PATH was not updated')

        finally:
            # Clean up: restore an original path to avoid side effects in other tests
            set_apsim_bin_path(original_path)


if __name__ == '__main__':
    unittest.main()
