
.. image:: https://img.shields.io/badge/License-Apache_2.0-blue.svg
   :target: https://opensource.org/licenses/Apache-2.0
   :alt: License: Apache-2.0

.. image:: https://img.shields.io/badge/Online-Documentation-magenta.svg
   :target: https://apsimngpy.readthedocs.io/en/latest
   :alt: Documentation

.. image:: https://img.shields.io/pypi/v/apsimNGpy?logo=pypi
   :target: https://pypi.org/project/apsimNGpy/
   :alt: PyPI version

.. image:: https://static.pepy.tech/badge/apsimNGpy
   :target: https://pepy.tech/project/apsimNGpy
   :alt: Total PyPI downloads

.. image:: https://img.shields.io/badge/Read%20Publication-blue.svg
   :target: https://www.sciencedirect.com/science/article/pii/S2352711025004625
   :alt: Read Publication

.. image:: https://img.shields.io/badge/Ask%20Through%20Teams-purple.svg
   :target: https://teams.live.com/l/community/FBAbNOQj7y9dPcoaAI
   :alt: Ask Teams


.. image:: https://img.shields.io/badge/Download--APSIM--NG-2026.01.7969.0-blue?style=flat&logo=apachespark
   :alt: APSIM Next Generation version
   :target: https://registration.apsim.info/?version=2026.01.7969.0&product=APSIM%20Next%20Generation

.. image:: ./images/run.gif
   :alt: Run APSIM simulation
   :align: center
   :width: 800px

Links
================

`Documentation <https://apsimngpy.readthedocs.io/en/latest/>`_

`Publication <https://www.sciencedirect.com/science/article/pii/S2352711025004625>`_.

apsimNGpy: The Next Generation Agroe-cosystem Simulation Library
===========================================================================

**apsimNGpy** is a cutting-edge, open-source framework for advanced agroecosystem modeling, built entirely in Python.
It enables **object-oriented**, **data-driven** workflows for interacting with APSIM Next Generation models, offering capabilities for:

- Batch file simulation and model evaluation
- APSIMX file editing and parameter inspection
- Weather data retrieval and pre-processing
- Optimization and performance diagnostics
- Efficient soil profile development and validation
- Parameter sensitivity analysis

`Python <https://www.python.org/>`_ serves as the execution environment, integrating scientific computing, data analysis, and automation for sustainable agricultural systems.


Requirements
*************

1. **.NET SDK** — install from https://learn.microsoft.com/en-us/dotnet/core/install/
2. **Python 3.10+**
3. **APSIM Next Generation** — ensure the directory containing ``Models.exe`` is added to your system PATH.
4. (Optional) Use the official APSIM installer for easiest setup.
5. Minimum 8 GB RAM recommended.


Installation
**************

## Run APSIM in Python




**Option 1 – Install from PyPI (stable)**

.. code-block:: bash

   pip install apsimNGpy

If using the `uv` virtual environment manager:

.. code-block:: bash

   uv pip install apsimNGpy

**Option 2 – Clone the development repository**

.. code-block:: bash

   git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git
   cd apsimNGpy
   pip install .

**Option 3 – Install directly from GitHub**

.. code-block:: bash

   pip install git+https://github.com/MAGALA-RICHARD/apsimNGpy.git


APSIM Next Generation (NG) Installation Tip
==============================================

Use the **pinned APSIM release** indicated on the documentation homepage to avoid forward-compatibility issues.
The pinned version represents the latest APSIM NG build verified against apsimNGpy’s API and unit tests.








