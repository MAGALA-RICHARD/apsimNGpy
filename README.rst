.. image:: https://img.shields.io/badge/License-Apache_2.0-blue.svg
   :target: https://opensource.org/licenses/Apache-2.0
   :alt: License: Apache-2.0

.. image:: https://img.shields.io/badge/Online-Documentation-magenta.svg
   :target: https://magala-richard.github.io/apsimNGpy-documentations/index.html
   :alt: Documentation

.. image:: https://img.shields.io/pypi/v/apsimNGpy?logo=pypi
   :target: https://pypi.org/project/apsimNGpy/
   :alt: PyPI version

.. image:: https://static.pepy.tech/badge/apsimNGpy
   :target: https://pepy.tech/project/apsimNGpy
   :alt: Total PyPI downloads

.. image:: https://static.pepy.tech/badge/apsimNGpy/month
   :target: https://pepy.tech/project/apsimNGpy
   :alt: Weekly PyPI downloads

.. image:: https://static.pepy.tech/badge/apsimNGpy/week
   :target: https://pepy.tech/project/apsimNGpy
   :alt: Weekly PyPI downloads

.. image:: https://img.shields.io/badge/Join%20Discussions-blue.svg
   :target: https://discord.gg/SU9A6nNv
   :alt: Join Discussions

.. image:: https://img.shields.io/badge/Ask%20Through%20Teams-purple.svg
   :target: https://teams.live.com/l/community/FBAbNOQj7y9dPcoaAI
   :alt: Ask Teams

.. image:: https://img.shields.io/badge/APSIM--NG-2025.7.7811.0-blue?style=flat&logo=apachespark
   :target: https://www.apsim.info
   :alt: APSIM Next Generation version



apsimNGpy: The Next Generation Agroecosytem Simulation Library
====================================================================
Our cutting-edge open-source framework, **apsimNGpy**, empowers advanced agroecosystem modeling through the utilization
of object-oriented principles directly within the `Python`_ environment. It features fast batch file simulation, model prediction, evaluation,
APSIMX file editing, seamless weather data retrieval, optimization, and efficient soil profile development.

.. _Python: https://www.python.org/


Requirements
***********************************************************************************
1. Dotnet, install from https://learn.microsoft.com/en-us/dotnet/core/install/
2. Python 3.10 +
3. APSIM: Add the directory containing the models executable to the system's PATH or python path (to locate the required .dll files). This can be achieved in either of the following ways:
4. Utilize the APSIM installer provided for this purpose.
5. Minimum; 8GM RAM, CPU Core i7

.. _Installation:

Installation

********************************************************************************

All versions are currently in development, phase and they can be installed as follows:

- Method 1. Stable versions can be installed from PyPI

.. code:: bash

    pip install apsimNGpy

If you are using the fleeting uv virtual environment manager.
.. code-block:: python

    uv pip install apsimNGpy

- Method 1. clone the current development repository

.. code:: bash

    git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git
    cd apsimNGpy
    pip install .

- Method 2. Use pip straight away and install from github

.. code:: bash

     pip install git+https://github.com/MAGALA-RICHARD/apsimNGpy.git


Full documentation can be found here; https://magala-richard.github.io/apsimNGpy-documentations/index.html


