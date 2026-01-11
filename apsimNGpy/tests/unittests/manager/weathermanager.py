import os.path
import unittest

from apsimNGpy.tests.unittests.base_unit_tests import BaseTester

from apsimNGpy.manager import weathermanager

LONLAT = 35.582520, 0.347596  # location is kampala
AMES_LONLAT = -93.0, 42.03534

AMES_LONLAT2 = -92.0, 42.03534


class TestWeatherManager(BaseTester):
    def setUp(self):
        self.start = 2000
        self.end = 2001
        self.LONLAT = 35.582520, 0.347596
        self.weather_file_name = f"{self._testMethodName}_{self.start}_{self.end}.met"

    def test_get_weather(self):
        if os.path.isfile(self.weather_file_name):
            os.remove(self.weather_file_name)
        met = weathermanager.get_weather(LONLAT, start=self.start, end=self.end,
                                         source='nasa', filename=self.weather_file_name, )
        self.assertIsInstance(met, str)
        self.assertTrue(os.path.exists(met))
        met = weathermanager.get_weather(AMES_LONLAT, source='daymet')
        self.assertIsInstance(met, str)
        self.assertTrue(os.path.exists(met))

    def test_is_within_usa_mainland(self):
        type_bool = weathermanager._is_within_USA_mainland(self.LONLAT)
        self.assertIsInstance(type_bool, bool, f"{self._testMethodName} did not run successfully")

    def test_read_met(self):
        wf = weathermanager.get_weather(AMES_LONLAT2, start=self.start, end=self.end, source='daymet',
                                        filename=self.weather_file_name)
        if wf is not None:
            df = weathermanager.read_apsim_met(wf)
            if df is not None:
                self.assertFalse(df.empty, 'read_apsim_met failed')
                # test writing to file
                write_file = weathermanager.write_edited_met(wf, df, filename=self.weather_file_name)
                self.assertTrue(write_file)
                exi_file = os.path.isfile(write_file)
                self.assertTrue(exi_file, msg=f"Writing met to file failed")

    def tearDown(self):
        if os.path.isfile(self.weather_file_name):
            os.remove(self.weather_file_name)


if __name__ == '__main__':
    unittest.main()
