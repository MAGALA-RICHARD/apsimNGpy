.. _master:

.. meta::
   :description lang=en:
          apsimNGpy is a Python framework for running APSIM crop model simulations, large-scale experiment orchestration,
          sensitivity analysis, and multiple-processing among others.
   :keywords: APSIM, Python, crop modeling, agricultural simulation, sensitivity analysis, batch simulations

apsimNGpy: The Next-Generation Agro-ecosystem Simulation Library
=================================================================

.. image:: https://img.shields.io/badge/License-Apache_2.0-blue.svg
   :target: https://opensource.org/licenses/Apache-2.0
   :alt: License: Apache-2.0

.. image:: https://img.shields.io/badge/docs-online-blue.svg
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

.. _apsim_pinned_version:

.. image:: https://img.shields.io/badge/Download--APSIM--NG-2026.2.7980.0-blue?style=flat&logo=apachespark
   :alt: APSIM Next Generation version
   :target: https://registration.apsim.info/?version=2026.02.7980.0&product=APSIM%20Next%20Generation
   :name: apsim_pin_version

.. image:: ../images/run.gif
   :alt: Run APSIM simulation
   :align: center
   :width: 800px

Introduction
===============

   apsimNGpy is  an open-source Python framework designed for advanced modeling with APSIM process-based model.
   Built on object-oriented principles. apsimNGpy extends and augments APSIM Next Generation functionalities within the Python scientific ecosystem,
   turning GUI-centric workflows into scriptable, reproducible, and scalable pipelines. apsimNGpy functionalities include, but not limited to the following:

    - Run large experiment sets efficiently using multiprocessing or multithreading.
    - Integrate geospatial data with automated soil and weather input retrieval.
    - Perform multi-objective optimization and sensitivity analysis for model calibration.
    - Execute APSIM through Jupyter, CLI, or python scripts with results returned as pandas DataFrames.
    - Inspect, edit, and manage APSIM models programmatically without the GUI.
    - Maintain forward and backward compatibility with evolving APSIM versions.
    - Extend and integrate workflows using an open, Apache-2.0 licensed architecture.
    - Evaluate model predictions using built-in metrics such as RMSE, RRMSE, WIA, MAE, CCC, and R².
    - Port complete projects across machines using containerized execution with referenced binaries.

Discussion and Community Support
================================

Users who wish to ask questions, report issues, request new features,
or engage in general discussion about **apsimNGpy** are encouraged to
visit the project’s official `GitHub Discussions`_ page.

This forum serves as the preferred place for:

- Troubleshooting and “how-to” questions
- Sharing workflows or examples
- Feature proposals and use-case discussions
- Clarification on model editing, optimization, and calibration
- Community-driven enhancements
- Collaboration with other APSIM users

If your question is not answered in the documentation, feel free to
start a new discussion thread and tag it appropriately.

For reporting reproducible bugs or contributing code, please use the
`GitHub Issues`_ tracker.


.. _GitHub Discussions: https://github.com/MAGALA-RICHARD/apsimNGpy/discussions
.. _GitHub Issues: https://github.com/MAGALA-RICHARD/apsimNGpy/issues


.. toctree::
   :maxdepth: 2
   :caption: Table of Contents

   Home <self>

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting started
   instantiating
   Usage

.. toctree::
   :maxdepth: 2
   :caption: VERSION CONTROL

   version_control
   manage_env

.. toctree::
   :maxdepth: 3
   :caption: EDITING & INSPECTION

   model inspection
   preview
   inspect_model_parameters
   edit
   weather
   soil_refill

.. toctree::
   :maxdepth: 2
   :caption: FACTORIAL EXPERIMENTS

   factorial_experiments

.. toctree::
   :maxdepth: 2
   :caption: BATCH SIMULATIONS

   mult_core

.. toctree::
   :maxdepth: 2
   :caption: OPTIMIZATION & TRADE-OFF ANALYSIS

   calibrate
   moo

.. toctree::
   :maxdepth: 3
   :caption: SUPPORT DEVELOPMENT

   how_to_cite

.. toctree::
   :maxdepth: 3
   :caption: TUTORIALS

   comp_cultivar
   app_multi_process


.. toctree::
   :maxdepth: 3
   :caption: Sensitivity Analysis

   sens
   Tutorial

.. toctree::
   :maxdepth: 1
   :caption: CHEATSHEET

   cheat

.. toctree::
   :maxdepth: 3
   :caption: SIMULATED DATA PLOTTING & VISUALIZATION

   plotting

.. toctree::
   :maxdepth: 2
   :caption: API REFERENCE

   api


