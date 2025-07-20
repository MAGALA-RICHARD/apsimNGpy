import stat
import unittest
from pathlib import Path

from apsimNGpy.tests.unittests import test_model_loader, unit_test_apsim, test_cast_helper, unit_tests_core, test_weathermanager, \
    test_edit_model, test_config

modules = (m for m in (unit_tests_core,
                       unit_test_apsim,
                       test_config,
                       test_edit_model,
                       test_cast_helper,
                       test_model_loader,
                       test_weathermanager))


def clean_up():
    sc = Path('../scratch')
    for path in sc.rglob("temp_*"):
        try:
            # Ensure file is writable (especially on Windows)
            path.chmod(stat.S_IWRITE)
            path.unlink(missing_ok=True)
        except (PermissionError, FileNotFoundError):
            ...


# Create a test suite combining all the test cases
loader = unittest.TestLoader()
suite = unittest.TestSuite()

for mod in modules:
    suite.addTests(loader.loadTestsFromModule(mod))


def run_suite(verbosity_level=2):
    try:
        runner = unittest.TextTestRunner(verbosity=verbosity_level)
        runner.run(suite)
    finally:
        clean_up()


if __name__ == '__main__':
    run_suite(verbosity_level=2)
