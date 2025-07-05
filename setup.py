import os

from setuptools import setup, find_packages

VERSION = '0.39.3.3'

DESCRIPTION = 'APSIM next generation package interface'
LONG_DESCRIPTION = 'Run, edit, download soils and weather and interact with the apsimx file'

with open('README.rst') as readme_file:
    readme = readme_file.read()

setup(
    name='apsimNGpy',
    version=VERSION,
    url='https://github.com/MAGALA-RICHARD/apsimNGpy.git',
    license_file="./LICENSE",
    author='Richard Magala',
    author_email='magalarich20@gmail.com',
    description=DESCRIPTION,
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'apsim=apsimNGpy.cli.cli:main_entry_point',
            'bp=apsimNGpy.cli.set_ups:apsim_bin_path',

            'apsim_bin_path=apsimNGpy.cli.set_ups:apsim_bin_path',
        ],
    },

    package_data={'': ['./apsimNGpy/data/*.apsimx',
                       './apsimNGpy/*.met',
                       "./apsimNGpy/experiment/*.py",
                       './apsimNGpy/examples/*.png',
                       './apsimNGpy/images/*.png'
                       './apsimNGpy/*.ini', "./*.ini"]},
    keywords=['python', 'APSIM Next Generation', 'pythonnet', 'crop modeling'],
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
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
        'joblib >= 1.3.2',
        'sqlalchemy >=2.0',
        'matplotlib',
        'seaborn >=0.13.2',
        'psutil >=6.0.0',
        'tenacity',
        'typer',
        'pymoo == 0.6.1.5',
        'wrapdisc==2.5.0',
        'summarytools>=0.3.0'

    ]
)
