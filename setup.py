from setuptools import setup, find_packages
import sys
import os
VERSION = '0.0.3beta'
DESCRIPTION = 'apsimx next generation package interface'
LONG_DESCRIPTION = 'run, edit, download soils and weather and interact with the apsimx file'
with open('README.rst') as readme_file:
    readme = readme_file.read()
setup(
    name='apsimNGpy',
    version='0.0.3',
    url='https://github.com/MAGALA-RICHARD/apsimNGpy.git',
    license='MIT',
    author='Richard Magala',
    author_email='magalarich20@gmail.com',
    description=DESCRIPTION,
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['basefiles/*.apsimx', 'basefiles/*.met']},
     keywords=['python', 'apsim'],
     classifiers= [
            "Development Status :: trial",
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
         'pandas >=2.0.3'


    ]
)

