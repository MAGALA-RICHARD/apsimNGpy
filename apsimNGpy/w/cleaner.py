from pathlib import Path
import os
import schedule
import time
def clean():
    path = Path("../../")
    ax = path.rglob('*.apsimx')
    db = path.rglob('*.db')
    remove = list(ax) + list(db) + list(path.rglob('*.db-shm')) + list(path.rglob('*.csv'))
    fl = len(remove)
    for i in remove:
        try:
            os.remove(str(i))
        except PermissionError:
            print(f"skipping '{i}' due to permission error")
    if fl >0:
      print(f" cleaned {fl} unwanted files")

if __name__ == "__main__":
    def job_with_argument(name):
        print(f"I am {name}")


    schedule.every(2).seconds.do(clean)

    while True:
        schedule.run_pending()
        time.sleep(1)
