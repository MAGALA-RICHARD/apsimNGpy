import os.path
import unittest

from tests.unittests.base_unit_tests import BaseTester

from apsimNGpy.manager import weathermanager

LONLAT = 35.582520, 0.347596  # location is kampala
AMES_LONLAT = -93.0, 42.03534


class test_weatherManager(BaseTester):
    def test_get_weather(self):
        met = weathermanager.get_weather(LONLAT, start =2000, end  =2001,source='nasa', filename='nasa_2.met')
        self.assertIsInstance(met, str)
        self.assertTrue(os.path.exists(met))
        met = weathermanager.get_weather(AMES_LONLAT, source='daymet')
        self.assertIsInstance(met, str)
        self.assertTrue(os.path.exists(met))
        self.logger.info('get_weather called successfully')

    def test_is_within_usa_mainland(self):
        type_bool = weathermanager._is_within_USA_mainland(LONLAT)
        assert isinstance(type_bool, bool)
        self.logger.info('is_within_USA_mainland ran successfully')


if __name__ == '__main__':
    unittest.main()

