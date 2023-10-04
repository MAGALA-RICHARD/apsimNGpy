import sys
import Cython
from distutils.extension import Extension
from setuptools import setup
from Cython.Distutils import build_ext
from Cython.Build import cythonize
import numpy as np
from setuptools import setup, find_packages

setup(
    name='apsimNGpy',
    version='1.0.0',
    url='https://github.com/MAGALA-RICHARD/apsimNGpy.git',
    license='MIT',
    author='Richard Magala',
    author_email='magalarich20@gmail.com',
    description='Package for reading apsimx files and processing data or runing optimisation of required paramters',
    packages=find_packages(),
    include_package_data=True,
)
