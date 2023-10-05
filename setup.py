from setuptools import setup, find_packages
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

