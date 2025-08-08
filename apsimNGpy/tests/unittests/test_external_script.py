"""
This module contains unit tests for the testing external tests if added to the suite
"""
import unittest
from apsimNGpy.tests.tester_main import suite, loader, run_suite
from apsimNGpy.core.base_data import load_default_simulations


class TestCaseAddModule(unittest.TestCase):

    def setUp(self):
        self.model = load_default_simulations('Maize')
        self.out = 'test_edit_model.apsimx'

    def test_add_crop_replacement(self):
        "+++test adding crop replacement++"
        self.model.add_crop_replacements(_crop='Maize')
        self.model.create_experiment(permutation=True)


if __name__ == '__main__':
    suite.addTests(loader.loadTestsFromTestCase(TestCaseAddModule))
    run_suite(1)
