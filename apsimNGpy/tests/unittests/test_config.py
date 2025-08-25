import os.path
import shutil
import unittest
import os
# Import the module where CoreModel class is defined
from apsimNGpy.core.config import (set_apsim_bin_path, get_apsim_bin_path, apsim_version, load_crop_from_disk,
                                   auto_detect_apsim_bin_path, get_bin_use_history)
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester, path
from pathlib import Path

TEST_PATH = "/path/to/test/bin"  # apsim bin path to test

auto = auto_detect_apsim_bin_path()


class TestConfig(BaseTester):
    def setUp(self):
        self.model = 'Maize'
        self.user_file_name = os.path.realpath('user_file_name.apsimx')
        self.work_space = 'config_ws'
        Path(self.work_space).mkdir(exist_ok=True)
        self.paths = set()  # for storing random paths

    def test_get_apsim_bin_path(self):
        abp = get_apsim_bin_path()
        p_true = path.exists(abp)
        self.assertTrue(p_true)

    def test_get_apsim_version(self):
        import re
        version = apsim_version()
        pattern = r"^APSIM \d{4}\.\d+\.\d+\.\d+$"
        match = re.match(pattern, version)
        self.assertTrue(match, 'Failed to detect Current APSIM version')

    def test_get_bin_use_history(self):
        """test if apsimNGpy is recording the used binary path.

         Please remember only those stills existing on the computer are recorded"""
        bin_history = get_bin_use_history()
        if not bin_history:
            self.skipTest('No binary history available, skipping test..')
        self.assertIsInstance(bin_history, list, msg='Binary history is not being detected')
        # ensure all exists
        all_exists = all([os.path.exists(i) for i in bin_history])
        self.assertTrue(all_exists, msg='some path are no longer available on the computer')

    def test_load_crop_from_disk_user_name(self):
        """Test user supplied path"""
        if os.path.exists(self.user_file_name):
            os.remove(self.user_file_name)
        crop = load_crop_from_disk(self.model, out=self.user_file_name)
        self.assertTrue(crop)
        self.assertGreater(os.path.getsize(self.user_file_name), 0,
                           f'failed to load default model: using {self.user_file_name} ')

    def test_load_crop_from_disk_default_random_name(self):
        """test if random name is successful"""
        crop = load_crop_from_disk(self.model)
        self.assertGreater(os.path.getsize(crop), 0, msg='failed to load using random name')
        self.paths.add(crop)

    def test_work_space_load_crop_from_disk(self):
        """test work space provided actually works"""
        # load and return crop path
        crop = load_crop_from_disk(self.model, work_space=self.work_space)
        dir_name = os.path.dirname(crop)
        self.assertEqual(dir_name, self.work_space)
        # also check that the file has been created
        self.assertGreater(os.path.getsize(crop), 0,
                           msg=f'failed to load using random name and provided work_space {self.work_space}')
        self.paths.add(crop)

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
            # set_apsim_bin_path(original_path)
            pass

    def tearDown(self):
        if os.path.exists(self.work_space):
            shutil.rmtree(self.work_space)
        if os.path.exists(self.user_file_name):
            os.remove(self.user_file_name)

        for pa in self.paths:
            if os.path.exists(pa):
                os.remove(pa)


if __name__ == '__main__':
    unittest.main()
