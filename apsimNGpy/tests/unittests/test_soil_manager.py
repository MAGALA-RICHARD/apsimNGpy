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
        """
        Both the soil thickness_sequence and thickness_value are optional.
            `thinnest_layer`. If both `thickness_sequence` and `thickness_value` are supplied,
            `thickness_sequence` takes precedence.

        """
        soil = self.soil_download(self.lonlat)
        sp = OrganiseSoilProfile(soil, thickness=200)
        self.assertIsInstance(sp.cal_missingFromSurgo(), dict)

    def test_soil_profile_with_inputs(self):
        """ensure that organize soil profile raises assertion error if no thickness-related values are
        passed into the caller"""
        with self.assertRaises(AssertionError):
            soil = self.soil_download(self.lonlat)
            sp = OrganiseSoilProfile(soil)
            sp.cal_missingFromSurgo()

    def test_soil_profile_with_invalid_thickness(self):
        """Note if thickness is not in mm and max_depth is in mm, there will be a lot of soil layers, a value error
        will be raised from soil_layer_calculator"""
        with self.assertRaises(ValueError):
            soil = self.soil_download(self.lonlat)
            sp = OrganiseSoilProfile(soil, thickness=5)
            sp.cal_missingFromSurgo()

    def test_soil_profile_calculation_with_seq_thickness_values(self):
        """
        At the moment, when the soil profile is calculated, a dict is returned with keys holding to the soil profile
        section values
        """
        soil = self.soil_download(self.lonlat)
        sp = OrganiseSoilProfile(soil, thickness_values=self.thickness_values)
        self.assertIsInstance(sp.cal_missingFromSurgo(), dict)

    def test_meta_info(self):
        """
        let go hard on meta_info
        @return:
        """
        soil = self.soil_download(self.lonlat)
        sp = OrganiseSoilProfile(soil, thickness_values=self.thickness_values)
        data = sp.cal_missingFromSurgo()
        self.assertIsInstance(data, dict)
        meta_info = data['meta_info']
        self.assertIsInstance(meta_info, dict, msg='expected a dict but got {}'.format(meta_info))

    def test_meta_info_typeerror(self):
        """
        ensure that the meta_info is a dict, and raise an error the wrong type is supplied
        @return:
        """
        soil = self.soil_download(self.lonlat)
        sp = OrganiseSoilProfile(soil, thickness_values=self.thickness_values)
        with self.assertRaises(TypeError, msg='why not raising a type error when list was supplied') as e:
            sp.cal_missingFromSurgo(metadata=[1, 2])


if __name__ == '__main__':
    unittest.main()
