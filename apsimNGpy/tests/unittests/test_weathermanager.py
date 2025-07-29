import os.path
import unittest

from tests.unittests.base_unit_tests import BaseTester

from apsimNGpy.manager import weathermanager

LONLAT = 35.582520, 0.347596  # location is kampala
AMES_LONLAT = -93.0, 42.03534

AMES_LONLAT2 = -92.0, 42.03534


class test_weatherManager(BaseTester):
    def test_get_weather(self):
        met = weathermanager.get_weather(LONLAT, start=2000, end=2001, source='nasa', filename='nasa_2.met')
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

    def test_read_met(self):
        wf = weathermanager.get_weather(AMES_LONLAT2, start=2000, end=2002, source='daymet',
                                        filename='ame_met_test.met')
        if wf is not None:
            df = weathermanager.read_apsim_met(wf)
            if df is not None:
                self.assertFalse(df.empty, 'read_apsim_met failed')
                # test writing to file
                write_file = weathermanager.write_edited_met(wf, df, filename='ames-test_write-to-file.met')
                self.assertTrue(write_file)
                exi_file = os.path.isfile(write_file)
                self.assertTrue(exi_file, msg=f"Writing met to file failed")


if __name__ == '__main__':
    unittest.main()
