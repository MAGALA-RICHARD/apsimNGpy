import configparser
import os
import stat
import subprocess
import sys
import unittest
from pathlib import Path
from apsimNGpy.core.pythonet_config import is_file_format_modified
import logging
import smtplib
from email.mime.text import MIMEText
from apsimNGpy.core.config import get_apsim_bin_path, apsim_version
from datetime import datetime
from email import encoders

from pathlib import Path

date_STR = datetime.now().strftime("%y-%m-%d-%H-%M-%S")
logging.basicConfig(level=logging.INFO, format='  [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='  [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
from apsimNGpy.core.pythonet_config import is_file_format_modified

IS_NEW_APSIM = is_file_format_modified()
config = configparser.ConfigParser()
config_file = config.read('./unittests/configs.ini')


def send_report(sms, subject, attachment_path=None):
    # Works only on the local machine for the robot to run automatically and send results of what is going on
    # the env vars are set manually on the local machine for security purposes
    all_envs = False
    sender = None
    receiver = None
    key = None
    if os.environ.get('REPORT_TESTS', None):
        sender = os.environ.get('SENDER', sender)
        receiver = os.environ.get('RECEIVER', receiver)
        key = os.environ.get('PASSCODE', key)
        all_envs = all([receiver, sender, key])
    if all_envs:
        from email.mime.base import MIMEBase
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        # Email credentials
        SMTP_SERVER = "smtp.gmail.com"
        SMTP_PORT = 587
        EMAIL_SENDER = sender
        EMAIL_PASSWORD = key
        EMAIL_RECEIVER = receiver

        # Create the email message
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = subject

        # Attach text message
        msg.attach(MIMEText(sms, "plain"))

        # Attach a file if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(attachment_path)}",
            )
            msg.attach(part)

        # Send the email
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()  # Secure the connection
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
                logger.info("Email sent successfully!")
        except Exception as e:
            print("Error:", e)


if IS_NEW_APSIM:
    from apsimNGpy.tests.unittests import test_experiment
from apsimNGpy.tests.unittests import test_model_loader, unit_test_apsim, test_cast_helper, unit_tests_core, \
    test_weathermanager, test_multcores, \
    test_edit_model, test_config, model_tools, test_get_weather_from_web_filename

modules = [m for m in (model_tools,
                       unit_tests_core,
                       unit_test_apsim,
                       test_edit_model,
                       test_cast_helper,
                       test_model_loader,
                       test_config,
                       test_weathermanager,
                       test_get_weather_from_web_filename,

                       )]
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

        logger.info(f"\n Test Summary:")
        print(f"=====================================")
        logger.info(f"  ✅ Passed  : {num_passed}")
        logger.info(f"  ❌ Failures: {num_failures}")
        logger.info(f"  💥 Errors  : {num_errors}")
        logger.info(f"  📉 Failure Rate: {failure_rate:.2f}%")

        # Create report string
        report = (
            f"Test Suite Summary for {apsim_version()}\n"
            f"====================================\n"
            f"✅ Passed  : {num_passed}\n"
            f"❌ Failures: {num_failures}\n"
            f"💥 Errors  : {num_errors}\n"
            f"📉 Failure Rate: {failure_rate:.2f}%\n"
            f"Date: {date_STR}"
        )

        # Send report

        send_report(sms=report,
                    subject=f"{apsim_version()} Test Suite Report"
                    )

        return report
    finally:
        clean_up()


if __name__ == '__main__':

   # run multi_cores test before
    try:
        result = subprocess.run(
            [sys.executable, str(test_multcores.__file__)],
            capture_output=True,
            text=True,
            check=True
        )
        send_report('✅ Passed', 'Multi Processing Results')  # normal output
        logger.info(result.stdout)
    except subprocess.CalledProcessError as e:
        failed_report = (f"{e.stdout}",
                         f"Errors: {e.stderr}")

        logger.info("Script failed!")
        logger.info("STDOUT:\n", e.stdout)
        logger.info("STDERR:\n", e.stderr)
        send_report(sms= failed_report, subject='Multi Processing Failure Report')

    run_suite(verbosity_level=0)
