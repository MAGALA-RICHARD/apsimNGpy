"""
This is an internal script to automate the tests. Therefore, some packages used are not added to apsimNGpy project requirements
Wakes up every specified period of time to run the test after checking if there is a new version
"""
import gc
import os
import sys
import time
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from pandas import DataFrame
from pywinauto import Application, keyboard
import requests
from apsimNGpy.core.config import set_apsim_bin_path
from apsimNGpy.settings import logger
from apsimNGpy.tests.tester_main import run_suite

home = Path.home().joinpath("AppData", 'Local', 'Programs')
csv_path = home.joinpath("test_logs.csv")

user_email = 'magalarich20@gmail.com'

df = pd.read_csv(csv_path)
from datetime import datetime

date_STR = datetime.now().strftime("%y-%m-%d-%H-%M-%S")
date_now = datetime.now()
# Constants
email = user_email
CURRENT_VERSION = "2025.07.7820.0"


RUNS = 0
def v_next(previous):
    _, _, sub_version, _ = previous.split('.')
    sub = int(sub_version)
    sub += 1
    return sub


def insert_data(file_name):
    file_name = str(file_name)
    if not os.path.exists(csv_path):
        DataFrame().to_csv(csv_path)
    date_str = datetime.now().strftime("%y-%m-%d-%H-%M-%S")
    df = pd.read_csv(csv_path)
    installer = df.get('installer', [])
    if installer is not None and not isinstance(installer, list):
        installer = installer.tolist()
    file_without_suffix = file_name.removesuffix('.exe')
    if not file_without_suffix in installer:

        installer.append(file_without_suffix)
        date_ti = df.get('date_time', [])
        if date_ti is not None and not isinstance(date_ti, list):
            date_ti = date_ti.tolist()
        date_ti.append(date_str)
        df = pd.DataFrame({'installer': installer, 'date_time': date_ti})
        logger.info('saving data succeeded')
        df.to_csv(csv_path, index=False)
        del df
        gc.collect()


def get_last_installed():
    installer = pd.read_csv(csv_path)['installer'].tolist()
    if installer is not None:
        return installer[-1]


def extract_version_from_url(url):
    from urllib.parse import urlparse, parse_qs
    # Parse the URL query
    query = urlparse(url).query
    params = parse_qs(query)

    version = params.get("version", [None])[0]
    return version


def get_next_version(last_version: str) -> str:
    try:
        parts = last_version.strip().split(".")
        if len(parts) != 4:
            raise ValueError("Invalid version format")

        # Convert last BUILD part to int and increment
        build = int(parts[2])
        revision = int(parts[3])  # usually 0, but handled anyway

        new_version = f"{parts[0]}.{parts[1]}.{build + 1}.0"
        return new_version

    except Exception as e:
        raise RuntimeError(f"Failed to compute next version from {last_version}: {e}")


def notify(NEXTVERSION):
    file_name = f"{NEXTVERSION}.exe"
    if os.path.exists(file_name):
        logger.info(f"skipping download finishing previously downloaded version ({file_name})")
        return True


def download_installer():
    global RUNS
    try:
        LAST = get_last_installed()
        # logger.info("last apsim version is {}".format(LAST))
        NEXTVERSION = get_next_version(LAST)

        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        # Step 1: Get the registration page to extract the token
        resp = session.get(
            "https://registration.apsim.info/?product=APSIM%20Next%20Generation&version",
            headers=headers
        )
        soup = BeautifulSoup(resp.text, "html.parser")

        token_input = soup.find("input", {"name": "__RequestVerificationToken"})
        token = token_input["value"]

        # Step 2: Submit the form with email and token
        post_data = {
            "email": email,
            "__RequestVerificationToken": token,
            "Sender": "LandingPage"
        }
        resp2 = session.post(
            "https://registration.apsim.info/?product=APSIM%20Next%20Generation&version",
            data=post_data,
            headers=headers
        )

        # Step 3: Parse the returned HTML for download links
        soup2 = BeautifulSoup(resp2.text, "html.parser")
        links = soup2.find_all("a")

        # Step 4: Find the correct version
        download_link = None
        vp = v_next(previous=LAST)
        for link in links:
            href = link.get("href", "")
            if f'{vp}' in href:
                print(href)
                next_v = extract_version_from_url(href)
                nv = notify(next_v)
                file_name =f'{next_v}.exe'
                if nv:
                    return file_name

                download_link = "https://registration.apsim.info" + href
                break
            else:
                #logger.info(f'Could not find APSIM version sub number: {vp}. perhaps no yet published')
                return 0

        print(f"✅ Found link: {download_link}")

        # Step 5: Use requests to get the installer
        resp3 = session.get(
            f"https://registration.apsim.info/?product=APSIM%20Next%20Generation&version={next_v}&platform=Windows",
            headers=headers,
            stream=True
        )

        with open(file_name, "wb") as f:
            for chunk in resp3.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info(f"✅ Downloaded and saved as: {file_name}")
        return file_name
    finally:
        RUNS +=1
        print(f'NO of attempts: {RUNS}')


def get_installed_path(file_path):
    file = str(file_path).removesuffix('.exe')
    six = file[-6:]
    installed_path = list(home.rglob(f"*{six}"))
    if installed_path:
        return installed_path[0]
    else:
        raise FileNotFoundError(f"no installed path for {file_path}")


def main():
    try:
        installer_name = download_installer()
        if not installer_name:
            return None
        logger.info(f'starting apsim{installer_name} installer')
        app = Application(backend='uia')
        app.start(cmd_line=installer_name)
        time.sleep(1)
        keyboard.send_keys("{DOWN}")
        keyboard.send_keys("{SPACE}")
        logger.info('selecting install path')
        time.sleep(1)
        keyboard.send_keys("{ENTER}")

        logger.info('selecting next')
        time.sleep(2)
        keyboard.send_keys("{ENTER}")
        logger.info('selecting apsimx icon or desktop')
        time.sleep(2)
        keyboard.send_keys("{SPACE}")
        time.sleep(2)
        keyboard.send_keys("{ENTER}")
        logger.info('waiting installation to finish')
        time.sleep(3)
        keyboard.send_keys("{ENTER}")
        time.sleep(20)
        keyboard.send_keys("{SPACE}")
        keyboard.send_keys("{ENTER}")
        logger.info('installation complete')
        # get the installed path
        time.sleep(1)
        installed = get_installed_path(installer_name)
        logger.info('setting bin path')

        set_apsim_bin_path(installed)
        logger.info('inserting installed path')
        insert_data(installed)
        # run tests now
        logger.info('installation complete: running test please wait....')
        run_suite(0)
    finally:
        gc.collect()


if __name__ == '__main__':
    import schedule

    schedule.every(1).seconds.do(main)

    while True:
        schedule.run_pending()
        time.sleep(1)
        # ap = main()
