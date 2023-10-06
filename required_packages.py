from subprocess import check_call
from pkgutil import find_loader
import sys
import importlib
import os
import pkgutil

def check_if_package_Loaded(package):
  load_package  = find_loader(package)
  if load_package != None:
    value = True
    return value
# check if the package is loaded, then install it
for pkg in ['xmltodict', 'urllib', 'scipy', 'pandas', 'numpy', 'pythonnet', 'clr', 'geopandas', 'matplotlib',
            'requests', 'tqdm', 'progressbar', 'numpy', 'shapely']:
  if check_if_package_Loaded(pkg) !=True:
    check_call([sys.executable, '-m', 'pip', 'install', pkg])
    print(f'{pkg} was installed successfully')
    # import it again
    try:
        globals()[pkg] = importlib.import_module(pkg)
        # print the success
        print(f' confirmed {pkg} has been imported successfully')
    except ImportError as e:
       print(e)
       print(f"package{pkg} installation failed")

