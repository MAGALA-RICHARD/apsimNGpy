from setuptools import setup, find_packages
from subprocess import check_call
from pkgutil import find_loader
import sys
import importlib
import os
import pkgutil
VERSION = '0.0.1dev'
DESCRIPTION = 'apsimx next generation package interface'
LONG_DESCRIPTION = 'run, edit, download soils and weather and interact with the apsimx file'
setup(
    name='apsimNGpy',
    version='1.0.0',
    url='https://github.com/MAGALA-RICHARD/apsimNGpy.git',
    license='MIT',
    author='Richard Magala',
    author_email='magalarich20@gmail.com',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    include_package_data=True,

     keywords=['python', 'apsim'],
     classifiers= [
            "Development Status :: trial",
            "Intended Audience :: Education",
            "Programming Language :: Python :: 3",
            "Operating System :: Microsoft :: Windows",
        ],
     install_requires=[
        'numpy>=1.20.0',
        'scipy>=1.7'
    ]
)

def check_if_package_Loaded(package):
  load_package  = find_loader(package)
  if load_package != None:
    value = True
    return value
# check if the package is loaded, then install it
for pkg in ['xmltodict', 'urllib', 'scipy', 'pandas', 'numpy', 'pythonnet', 'clr', 'geopandas', 'matplotlib'
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

