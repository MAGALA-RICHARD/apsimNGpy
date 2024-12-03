import os

from setuptools import setup, find_packages
config_path = os.path.realpath('config.ini')
if os.path.exists(config_path):
    try:
       os.remove(config_path)
    except:
        pass

VERSION = '0.0.3.0'
DESCRIPTION = 'apsimx next generation package interface'
LONG_DESCRIPTION = 'run, edit, download soils and weather and interact with the apsimx file'

with open('README.rst') as readme_file:
    readme = readme_file.read()
setup(
    name='apsimNGpy',
    version=VERSION,
    url='https://github.com/MAGALA-RICHARD/apsimNGpy.git',
    license='MIT',
    author='Richard Magala',
    author_email='magalarich20@gmail.com',
    description=DESCRIPTION,
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['./apsimNGpy/data/*.apsimx',
                       './apsimNGpy/*.met',
                       "./apsimNGpy/experiment/*.py",
                       './apsimNGpy/examples/*.png',
                       './apsimNGpy/*.ini', "./*.ini"]},
    keywords=['python', 'APSIM Next Generation', 'pythonnet', 'crop modeling'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
    ],
    install_requires=[
        'numpy>=1.20.0',
        'scipy>=1.7',
        'xmltodict >=0.13.0',
        'requests >=2.31.0',
        'pythonnet >= 3.0.1',
        'rasterio >=1.3.8',
        'shapely >=2.0.1',
        'clr >= 1.0.3',
        'geopandas >=0.13.2',
        'pandas >=2.0.3',
        'geopy >= 2.4.1',
        'tqdm >= 4.66.2',
        'progressbar >= 2.5',
        'joblib >= 1.3.2',
        'sqlalchemy >=2.0',
        'matplotlib',
        'psutil >=6.0.0',
        'tenacity'

    ]
)
