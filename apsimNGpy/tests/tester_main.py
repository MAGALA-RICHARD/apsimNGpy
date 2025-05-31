import unittest
from apsimNGpy.tests import (unit_tests_core,
                             unit_test_apsim,
                             test_config,
                             test_edit_model,
                             test_weathermanager)
from pathlib import Path

import os
import stat
from pathlib import Path


def clean_up():
    sc = Path('../scratch')
    for path in sc.rglob("temp_*"):
        try:
            # Ensure file is writable (especially on Windows)
            path.chmod(stat.S_IWRITE)
            path.unlink(missing_ok=True)
        except PermissionError:
            ...
        except Exception as e:
            ...


# Create a test suite combining all the test cases
loader = unittest.TestLoader()
suite = unittest.TestSuite()

suite.addTests(loader.loadTestsFromModule(test_config))
suite.addTests(loader.loadTestsFromModule(test_weathermanager))
suite.addTests(loader.loadTestsFromModule(unit_tests_core))
suite.addTests(loader.loadTestsFromModule(unit_test_apsim))
suite.addTests(loader.loadTestsFromModule(test_edit_model))


def run_suite():
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == '__main__':
    try:
        # Run the test suite
        clean_up()
        run_suite()

    finally:
        clean_up()
