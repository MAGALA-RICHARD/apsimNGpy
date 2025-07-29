import shutil
from pathlib import Path
import os
import schedule
import time
import logging

logging.basicConfig(
    level=logging.INFO,  # or DEBUG, WARNING, ERROR, CRITICAL
    format='[%(levelname)s]: %(message)s'
)


def clean():
    path = Path("../../")
    ax = path.rglob('*.apsimx')
    db = path.rglob('*.db')
    remove = list(ax) + list(db) + list(path.rglob('*.db-shm')) + list(path.rglob('*.csv'))
    fl = len(remove)
    dist = path / 'dist'
    if os.path.exists(dist):
        shutil.rmtree(dist)
        print('Removed', 'dist files')
    build = path / 'build'
    if os.path.exists(build):
        shutil.rmtree(build)
        print('Removed', 'build files')
    egg = path / 'apsimNGpy.egg-info'
    if os.path.exists(egg):
        shutil.rmtree(egg)
        print('Removed', 'apsimNgpy egg file')
    for i in remove:
        try:
            os.remove(str(i))
        except PermissionError:
            print(f"skipping '{i}' due to permission error")
    if fl > 0:
        logging.info(f" cleaned {fl} unwanted files")


if __name__ == "__main__":
    def job_with_argument(name):
        print(f"I am {name}")


    # schedule.every(1).minutes.do(clean)
    #
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)
    clean()
