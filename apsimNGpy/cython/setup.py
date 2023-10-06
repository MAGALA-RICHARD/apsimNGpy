
from distutils.extension import Extension
from setuptools import setup
from Cython.Distutils import build_ext
from Cython.Build import cythonize
import numpy as np
from setuptools import setup, find_packages


ext = [Extension("soil", ["soil.pyx"],
                include_dirs=[np.get_include()]),
Extension("utils", ["utils.pyx"],
                include_dirs=[np.get_include()])
       ]
setup(
    ext_modules = cythonize(ext)
)
