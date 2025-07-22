import stat
import unittest
from pathlib import Path
from apsimNGpy.core.pythonet_config import is_file_format_modified
import logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
IS_NEW_APSIM = is_file_format_modified()
if IS_NEW_APSIM:
    from apsimNGpy.tests.unittests import test_experiment
from apsimNGpy.tests.unittests import test_model_loader, unit_test_apsim, test_cast_helper, unit_tests_core, test_weathermanager, \
    test_edit_model, test_config

modules = [m for m in (unit_tests_core,
                       unit_test_apsim,
                       test_config,
                       test_edit_model,
                       test_cast_helper,
                       test_model_loader,
                       test_weathermanager)]
if IS_NEW_APSIM:
    modules.append(test_experiment)
    modules = (i for i in modules)


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
        result = runner.run(suite)

        total_tests = result.testsRun
        num_failures = len(result.failures)
        num_errors = len(result.errors)
        num_passed = total_tests - num_failures - num_errors
        failure_rate = (num_failures + num_errors) / total_tests * 100 if total_tests else 0

        logger.info(f"\n📊 Test Summary:")
        logger.info(f"  ✅ Passed  : {num_passed}")
        logger.info(f"  ❌ Failures: {num_failures}")
        logger.info(f"  💥 Errors  : {num_errors}")
        logger.info(f"  📉 Failure Rate: {failure_rate:.2f}%")

        # Optional: Exit with non-zero status code if any test fails
        if not result.wasSuccessful():
            exit(1)
    finally:
        clean_up()


if __name__ == '__main__':
    run_suite(verbosity_level=2)
