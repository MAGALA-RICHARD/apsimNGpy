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

.. image:: https://img.shields.io/badge/Join%20Discussions-blue.svg
   :target: https://discord.gg/SU9A6nNv
   :alt: Join Discussions

.. image:: https://img.shields.io/badge/Ask%20Through%20Teams-purple.svg
   :target: https://teams.live.com/l/community/FBAbNOQj7y9dPcoaAI
   :alt: Ask Teams

.. image:: https://img.shields.io/badge/Download--APSIM--NG-2025.08.7844-blue?style=flat&logo=apachespark
   :target: https://registration.apsim.info/?version=2025.08.7844.0&product=APSIM%20Next%20Generation
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
5. Minimum; 8GM RAM

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

APSIM Next Generation (NG) installation Tip:
===============================================
For APSIM installation, Please use the pinned release shown on documentation home page/or on this page to avoid forward-compatibility issues. That release features the latest APSIM NG version that has passed all unit tests against apsimNGpy’s programmatic API.


v0.39.9.17
==============

Release notes
==========================
This build is stable for day-to-day work, although API improvement continues to take shape

Highlights
===================
Whole-profile replacement remains possible but is limited to the U.S mainland only.
the get_soil_from_web method from ApsimModel class is flagged as ready for this purpose.

multi-core processing made better and thread-safe, with real time tracking of failed jobs,
to allow for re-runs based on number of user specified retries; currently defaults to one retry

The **add_report_variables** from ApsimModel class has been fixed to avoid un mistaken duplicates
the opposite method **remove_report_variable** has been added; it allows users to remove some variables from their reporting tables.

Split seemingly large simulations into chunks to avoid resource overload during multi-processing.


Plot polish:
=============
Cleaner figure-level labeling utilities for multi-facet plots; fewer overlaps and nicer defaults.

Optimization hooks:
====================
Smoother integration points for multi-objective runs (e.g., NSGA-II/III), with simpler objective setups.

Stability & perf:
==================
More robust multicore execution, chunking and progress signaling; lighter memory footprint on large scenario batches.

Docs & warnings:
=====================
Clear warnings for soil layer mismatches (Physical/Organic/Chemical) and guidance to use get_soil_from_web as a consistent starting point.

Breaking changes / deprecations

 -A few legacy utilities are marked Deprecated.
  Final removal will be announced in the next tagged release. replace_downloaded soils from the ApsimModel will soon be deprecated

- The plotting and visualisation API has slightly changed, it now requires supplying the database table or leaving it to None,
   if the latter, is true the x and y columns are drawn from all tables in the simulation database, after concatenating the results.

- The execution to csv file via the kwargs in ``ApsimModel.run`` is now set to False by default

Upgrade
============
>>> pip install -U apsimNGpy

Which version is safe to install?
====================================
Use the APSIM NG version pinned on the apsimNGpy homepage to avoid runtime mismatches.


Call for feedback
================================
    Soil profile edits across mixed layer structures

    Large multi-objective runs (performance & logging)

    Open an issue with a minimal repro + platform details. Your notes now shape the final release.

    logging model activities from apsim Models summary module

    Managing multi-core runs and their associated simulated datasets

Known issues (seeking cases)
====================================
Newer version of APSIM may not be compatible with the current versions. Please use the pinned versions lower versions before the pinned version.

Some soil locations may not have all the required data for building APSIM soil profiles, be careful, as this may raise ApsimRunTimeError during model runs


Compatibility
=========================

Python: 3.10–3.13 (tested).

APSIM NG: use the version pinned on the apsimNGpy homepage to avoid API/runtime mismatches.

Thanks
==============
Huge thanks to early testers for stress-testing soil edits and optimization paths. Your feedback now will harden the final release.


Full documentation can be found here; https://magala-richard.github.io/apsimNGpy-documentations/index.html





