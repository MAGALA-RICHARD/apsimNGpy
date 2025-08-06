import os

import requests
from bs4 import BeautifulSoup

from apsimNGpy.tests.automate_tests import get_last_installed, get_next_version, v_next, extract_version_from_url
from apsimNGpy.tests.tester_main import send_report

email = os.environ.get('RECEIVER')


def notify_installer():

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
                msg = f"""
                  A new version of apsim: {next_v} is now available.
                 """
                send_report(msg, subject="apsimNGpy version notification")

    finally:
        pass


if __name__ == "__main__":
    import schedule, time, gc

    schedule.every(1).hour.do(notify_installer)

    while True:
        schedule.run_pending()
        gc.collect()
        time.sleep(40 * 60)

