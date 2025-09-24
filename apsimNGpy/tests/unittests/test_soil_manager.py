from apsimNGpy.tests.unittests import base_unit_tests
from apsimNGpy.manager.soilmanager import DownloadsurgoSoiltables, OrganiseSoilProfile
import unittest
import pandas as pd
from functools import cache


class TestSoilManager(unittest.TestCase):
    def setUp(self):
        self.thickness_values = [100, 300, 200, 500, 200, 250]
        self.lonlat = (-93.045, 41.03458)
        self.thickness = 200

    @cache
    def soil_download(self, lonlat):
        soil = DownloadsurgoSoiltables(lonlat)
        return soil

    def test_soil_tables(self):
        soil = self.soil_download(self.lonlat)
        self.assertIsInstance(soil, pd.DataFrame)
        self.assertFalse(soil.empty)

    def test_soil_profile_calculation_with_singular_thickness_value_for_all(self):
        soil = self.soil_download(self.lonlat)
        sp = OrganiseSoilProfile(soil, thickness=200)
        self.assertIsInstance(sp.cal_missingFromSurgo(), dict)

    def test_soil_profile_with_inputs(self):
        with self.assertRaises(AssertionError):
            soil = self.soil_download(self.lonlat)
            sp = OrganiseSoilProfile(soil)
            sp.cal_missingFromSurgo()

    def test_soil_profile_with_invalid_thickness(self):
        with self.assertRaises(ValueError):
            soil = self.soil_download(self.lonlat)
            sp = OrganiseSoilProfile(soil, thickness=5)
            sp.cal_missingFromSurgo()

    def test_soil_profile_calculation_with_seq_thickness_values(self):
        soil = self.soil_download(self.lonlat)
        sp = OrganiseSoilProfile(soil, thickness_values=self.thickness_values)
        self.assertIsInstance(sp.cal_missingFromSurgo(), dict)


if __name__ == '__main__':
    unittest.main()
