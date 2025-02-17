import unittest

from apsimNGpy.tests.base_test import BaseTester

from apsimNGpy.manager import weathermanager

LONLAT = 35.582520, 0.347596  # location is kampala
AMES_LONLAT = -93.0, 42.03534


class test_weatherManager(BaseTester):
    def test_get_weather(self):
        met = weathermanager.get_weather(LONLAT, source='nasa')
        self.assertIsInstance(met, str)
        met = weathermanager.get_weather(AMES_LONLAT, source='daymet')
        self.assertIsInstance(met, str)

    def test_is_within_usa_mainland(self):
        type_bool = weathermanager._is_within_USA_mainland(LONLAT)
        assert isinstance(type_bool, bool)


if __name__ == '__main__':
    unittest.main()
