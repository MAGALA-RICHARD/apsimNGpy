import argparse
import os
import stat
import unittest
from datetime import datetime
from pathlib import Path

from apsimNGpy.logger import logger
from apsimNGpy.mailer.mail import send_report

date_STR = datetime.now().strftime("%y-%m-%d-%H-%M-%S")
from apsimNGpy.config import path_checker
from apsimNGpy.config import apsim_bin_context, get_apsim_bin_path, set_apsim_bin_path

parser = argparse.ArgumentParser()
parser.add_argument(
    '-bp', "--bin",
    required=False,
    help="Path to APSIM binary directory")

args = parser.parse_args()
bin_path = args.bin or Path(os.environ.get('TEST_APSIM_BINARY', )) or get_apsim_bin_path()

if not path_checker(bin_path):
    new_path = input(
        "APSIM binary path is not valid.\n"
        "Please enter a valid APSIM binary path "
        "or configure it using apsimNGpy.set_apsim_bin_path(): "
    ).strip()

    if not path_checker(new_path):
        raise ValueError(f"Invalid APSIM binary path: {new_path}")

    set_apsim_bin_path(new_path)
    bin_path = new_path

logger.info('Using apsim bin: {}'.format(bin_path))


def run_suite(_bin_path, verbosity_level=2):
    """

    @param _bin_path: apsim installation path
    @param verbosity_level: level of verbosity for printing stdout messages
    @return: None
    """
    with apsim_bin_context(_bin_path) as apsimx:
        CLR = apsimx.CLR
        from apsimNGpy.tests.unittests import apsimNGpy__init__
        apsim_version = CLR.apsim_compiled_version
        IS_NEW_APSIM = CLR.file_format_modified
        from apsimNGpy.tests.unittests.core import data_insights
        from apsimNGpy.tests.unittests.manager import weathermanager, test_get_weather_from_web_filename
        from apsimNGpy import unittests

        modules = {
            unittests.starter,
            unittests.model_tools,
            unittests.senstivitymanager,
            unittests.core,
            unittests.apsim,
            unittests.vars,
            unittests.smp,
            apsimNGpy__init__,
            unittests.edit_model_by_path,
            unittests.cs_resources,
            unittests.core_edit_model,
            unittests.model_loader,
            unittests.config,
            unittests.weathermanager,
            test_get_weather_from_web_filename,
            unittests.plot_manager,
            unittests.soilmanager,

            data_insights
        }
        if IS_NEW_APSIM:
            from apsimNGpy.tests.unittests.core import experiment
            modules.add(experiment)
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

        def _run_suite(verbosity_level=2):
            logger.info('Running all tests')
            try:
                runner = unittest.TextTestRunner(verbosity=verbosity_level)
                result = runner.run(suite)

                total_tests = result.testsRun
                num_failures = len(result.failures)
                num_errors = len(result.errors)
                num_passed = total_tests - num_failures - num_errors
                failure_rate = (num_failures / total_tests) * 100 if total_tests else 0
                error_rate = (num_errors / total_tests) * 100 if total_tests else 0

                logger.info(f"\n Test Summary:")
                print(f"=====================================")
                logger.info(f"✅ Passed  : {num_passed}")
                logger.info(f"❌ Failures: {num_failures}")
                logger.info(f"❌ Errors  : {num_errors}")
                logger.info(f"📉 Failure Rate: {failure_rate:.2f}%")
                logger.info(f"📉 Error Rate: {error_rate:.2f}%\n")

                # Create report string
                report = (
                    f"Test Suite Summary for {apsim_version}\n"
                    f"====================================\n"
                    f"✅ Passed  : {num_passed}\n"
                    f"❌ Failures: {num_failures}\n"
                    f"💥 Errors  : {num_errors}\n"
                    f"📉 Failure Rate: {failure_rate:.2f}%\n"
                    f"📉 Error Rate: {error_rate:.2f}%\n"
                    f"Date: {date_STR}"
                )
                logger.info(f"tested APSIM is {bin_path}")
                # Send report

                send_report(sms=report,
                            subject=f"{apsim_version} Test Suite Report"
                            )

                return report
            finally:

                clean_up()

        _run_suite(verbosity_level=verbosity_level)


if __name__ == '__main__':
    import subprocess
    import sys
    from apsimNGpy import unittests

    # MULTI-CORE TEST IS TESTED ELSE WHERE
    # run = (run_suite(bin_path, verbosity_level=2))
    processes = []
    # this should run in separate processes
    Parent = Path(__file__).parent / 'unittests'
    for test in ['laze_import_tests.py', 'config_apsim_bin_context.py']:
        t = os.path.realpath(Parent.joinpath(test))
        p = subprocess.Popen(
            [sys.executable, t],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        out, err = p.communicate()

        if p.returncode != 0:
            failed = True
            print(err)
            logger.error(err)
            logger.error(f'tests from {t} failed')
        logger.info(f'test {test} passed {out}')

        # run = (run_suite(bin_path, verbosity_level=2))
