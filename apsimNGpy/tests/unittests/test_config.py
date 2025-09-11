import os.path
import shutil
import unittest
import os
# Import the module where CoreModel class is defined
from apsimNGpy.core.config import (set_apsim_bin_path, get_apsim_bin_path, apsim_version, load_crop_from_disk,
                                   GITHUB_RELEASE_NO,
                                   auto_detect_apsim_bin_path, get_bin_use_history)
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester, path
from pathlib import Path
from apsimNGpy.exceptions import ApsimBinPathConfigError

TEST_PATH = "/path/to/test/bin"  # apsim bin path to test

auto = auto_detect_apsim_bin_path()


def get_dir_size(path: Path) -> int:
    """Return total size of all files in directory (in bytes)."""
    total = 0
    for root, dirs, files in os.walk(path):
        for name in files:
            fp = Path(root) / name
            try:
                total += fp.stat().st_size
            except (OSError, FileNotFoundError):
                # skip files that might disappear during traversal
                pass
    return total


class TestConfig(BaseTester):
    def setUp(self):
        self.model = 'Maize'
        self.user_file_name = os.path.realpath('user_file_name.apsimx')
        self.work_space = 'config_ws'
        self.out_model_path_with_suffix = Path(f"{self._testMethodName}.apsimx")
        self.out_model_path_without_suffix = Path(f"w_{self._testMethodName}")
        Path(self.work_space).mkdir(exist_ok=True)
        self.paths = set()  # for storing random paths

    def test_get_apsim_bin_path(self):
        abp = get_apsim_bin_path()
        p_true = path.exists(abp)
        if not abp:
            self.skipTest('Could not find apsim bin. perhaps not yet set')
        self.assertTrue(p_true)
        # dir_size = get_dir_size(abp)
        # self.assertGreater(dir_size, 5, "Bin path is perhaps empty")

    def test_get_apsim_version(self):
        import re
        version = apsim_version(release_number=False)
        pattern = r"^APSIM \d{4}\.\d+\.\d+\.\d+$"
        pattern2 = r"^APSIM\d{4}\.\d+\.\d+\.\d+$"
        pattern3 = r"^\d{4}\.\d+\.\d+\.\d+$"
        match = re.match(pattern, version) or re.match(pattern2, version) or re.match(pattern3, version)
        version1 = apsim_version(release_number=True)
        if version1 == GITHUB_RELEASE_NO and match is None:
            self.skipTest(
                f'APSIM version is {version} un able to test apsim version number likely compiled from source')
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
        crop = load_crop_from_disk(self.model, out=self.out_model_path_with_suffix)
        self.assertGreater(os.path.getsize(crop), 0, msg='failed to load using random name')
        self.paths.add(crop)

    def test_loading_model_without_out_path_suffix(self):
        crop = load_crop_from_disk(self.model, out=self.out_model_path_without_suffix)
        is_apsimx = crop.suffix == '.apsimx'
        self.assertTrue(is_apsimx, msg='failed to load model without suffix')
        self.out_model_path_with_suffix.unlink(missing_ok=True)

    def test_loading_not_available_model(self):
        with self.assertRaises(FileNotFoundError, msg='model not available loaded why'):
            load_crop_from_disk('Maize_Test',out=self.out_model_path_with_suffix)


    def _test_work_space_load_crop_from_disk(self):
        """test work space provided actually works"""
        # load and return crop path
        crop = load_crop_from_disk(self.model, work_space=self.work_space)
        dir_name = os.path.dirname(crop)
        self.assertEqual(dir_name, self.work_space)
        # also check that the file has been created
        self.assertGreater(os.path.getsize(crop), 0,
                           msg=f'failed to load using random name and provided work_space {self.work_space}')
        self.paths.add(crop)

    def test_set_apsim_bin_path_invalid(self):
        """
        Test that set_apsim_bin_path raises an ApsimBinPathConfigError
        when given a non-existent APSIM binary path.
        """
        invalid_path = Path(f"{self._testMethodName}_invalid_path")
        if not invalid_path.exists():
            invalid_path.mkdir(parents=True, exist_ok=True)

        with self.assertRaises(ApsimBinPathConfigError):
            set_apsim_bin_path(invalid_path, raise_errors=True)
        try:
            shutil.rmtree(invalid_path)
        except PermissionError:
            pass

    def test_set_apsim_bin_path(self):
        """
        Test that set_apsim_bin_path
        This will always fail if the TEST_PATH above is not pointing correctly to the correct path of APSIM bin files
        @return:
        """
        # Initially retrieve the current APSIM binary path
        current_path = get_apsim_bin_path()
        if not current_path:
            self.skipTest('skipping test_set_apsim_bin_path')

        # Set a new test path

        success = set_apsim_bin_path(current_path, raise_errors=False)

        # Check if the new path is as expected
        self.assertEqual(success, True, "The APSIM binary path was not tested correctly.")

    def tearDown(self):
        if os.path.exists(self.work_space):
            shutil.rmtree(self.work_space)
        if os.path.exists(self.user_file_name):
            os.remove(self.user_file_name)
        self.out_model_path_with_suffix.unlink(missing_ok=True)
        self.out_model_path_without_suffix.unlink(missing_ok=True)

        for pa in self.paths:
            if os.path.exists(pa):
                os.remove(pa)


if __name__ == '__main__':
    unittest.main()
