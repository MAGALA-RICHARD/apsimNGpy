import unittest

from apsimNGpy.tests.base_test import BaseTester

from apsimNGpy.manager import weathermanager


class test_weatherManager(BaseTester):
    def test_get_weather(self):
        wp = 35.582520, 0.347596
        met = weathermanager.get_weather(wp, source='nasa')
        self.assertIsInstance(met, str)


if __name__ == '__main__':
    unittest.main()
