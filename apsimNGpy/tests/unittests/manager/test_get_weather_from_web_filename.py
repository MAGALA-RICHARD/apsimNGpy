import unittest
from pathlib import Path
from uuid import uuid4
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester
import os


class TestWeatherDownload(BaseTester):
    """Test weather data download functionality"""

    # Set up the model to use
    def setUp(self):
        self.model = ApsimModel('Maize')
        self.out = f'{uuid4()}_test_edit_model.apsimx'
        self.model.edit_model(model_type='Clock', model_name='Clock', simulations='Simulation', start='1990-01-01',
                              end='2000-01-01')
        self.LONLAT = 35.582520, 0.347596
        self.test_filename = f'{uuid4()}_test_nasa_download.met'
        self.default_filename = f'{uuid4()}_Maize_nasa_2000_2001.met'
        # Clean up any existing test files
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def tearDown(self):
        """Cleanup work after testing"""
        # Clean up test files
        # if os.path.exists(self.test_filename):
        #     os.remove(self.test_filename)
        if os.path.exists(self.default_filename):
            os.remove(self.default_filename)

    def test_weather_file_download_with_specified_filename(self):
        """Test if downloaded met file is saved with user-specified filename"""
        # Ensure test file doesn't exist
        self.assertFalse(os.path.exists(self.test_filename),
                         f"Test file {self.test_filename} should not exist before testing")

        # Download with specified filename
        self.model.get_weather_from_web(
            lonlat=self.LONLAT,
            start=2000,
            end=2001,
            simulations='Simulation',
            source='nasa',
            filename=self.test_filename
        )

        # Check if specified filename is used
        inspect_met_file = self.model.inspect_model_parameters(model_type='Weather', model_name='Weather',
                                                               simulations='Simulation')
        self.assertEqual(self.test_filename, os.path.basename(inspect_met_file['FileName']),
                         f"Inspected met file should be {self.test_filename}")

        # Verify file is created with specified filename
        self.assertTrue(os.path.exists(self.test_filename),
                        f"Downloaded met file should be saved with specified filename {self.test_filename}")

        # Verify file is not empty
        self.assertGreater(os.path.getsize(self.test_filename), 0,
                           "Downloaded met file should not be empty")

        # Don't check file content, only verify file exists and is not empty

    def test_weather_file_download_default_filename(self):
        """Test default behavior when filename is not specified"""
        # Ensure test file doesn't exist
        Path(self.test_filename).unlink(missing_ok=True)
        self.assertFalse(os.path.exists(self.default_filename),
                         f"Test file {self.default_filename} should not exist before testing")

        # Download with default filename

        f_before = self.model.inspect_model_parameters(model_type='Weather', model_name='Weather',
                                                       simulations='Simulation')['FileName']
        default_expected = f"{str(Path(self.model._model).stem)}_nasa_2000_2001.met"
        Path(default_expected).unlink(missing_ok=True)
        self.model.get_weather_from_web(
            lonlat=self.LONLAT,
            start=2000,
            end=2001,
            simulations='Simulation',
            source='nasa',

        )

        # Check if the default filename is used
        file_after = self.model.inspect_model_parameters(model_type='Weather', model_name='Weather',
                                                         simulations='Simulation')['FileName']

        self.assertEqual(default_expected, os.path.basename(file_after),
                         f"Inspected met file should be {default_expected}")

        # Check if default met file is created (usually has default naming rules)
        self.assertNotEqual(str(f_before), str(file_after),
                            f"Downloaded met file should be saved with default filename {self.default_filename}")

        # There should be at least one met file
        self.assertGreater(os.path.getsize(file_after), 0, "Downloaded met file should not be empty")



if __name__ == '__main__':
    unittest.main()
