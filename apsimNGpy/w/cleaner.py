from pathlib import Path
from os.path import abspath
import os

path = Path("../../")
ax = path.rglob('*.apsimx')
db = path.rglob('*.db')
remove = list(ax) + list(db) + list(path.rglob('*.db-shm')) + list(path.rglob('*.csv'))
for i in remove:
    try:
        os.remove(str(i))
    except PermissionError as e:
        print(f"skipping '{i}' due to permission error")
