.. apsimNGpy documentation master file.

apsimNGpy: The Next-Generation Agro-ecosystem Simulation Library
================================================================

.. image:: https://img.shields.io/badge/License-Apache_2.0-blue.svg
   :target: https://opensource.org/licenses/Apache-2.0
   :alt: License: Apache-2.0

.. image:: https://img.shields.io/badge/docs-online-blue.svg
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

.. image:: https://img.shields.io/badge/Latest--Unittest--APSIM--NG-2025.08.7844-blue?style=flat&logo=apachespark
   :target: https://registration.apsim.info/?version=2025.08.7844.0&product=APSIM%20Next%20Generation
   :alt: APSIM Next Generation version



.. admonition:: Introduction

   apsimNGpy is a cutting-edge, open-source Python framework designed for advanced modeling with APSIM process-based model.
   Built on object-oriented principles. apsimNGpy extends and augments APSIM Next Generation functionalities within the Python scientific ecosystem,
   turning GUI-centric workflows into scriptable, reproducible, and scalable pipelines. apsimNGpy functionalities include, but not limited to the following:

    **Scalable performance.** Run large experiment sets efficiently via ``multiprocessing/multithreading`` (e.g., factorials, ensembles, calibrations) using a clean, high-level API.

    **Spatial & data integration**. Leverage Python’s geospatial stack and built-in helpers to fetch and manage soil/weather inputs, enabling landscape-scale analyses.

    **Optimization & calibration**. Access multi-objective optimization and sensitivity analysis to quantify trade-offs (e.g., yield vs. nitrate loss/GHG) and calibrate parameters.

    **Reproducible automation**. Run ``APSIM`` using Jupyter/CLI/scripts; outputs land in ``pandas DataFrames`` for downstream analysis, plotting, and reporting.

    **Full model manipulation**. A modular, ``object-oriented`` design supports inspection, editing, experiments, and custom reports without manual GUI interface.

    **Version resilience**. rather than tying ``apsimNGpy`` to a fixed APSIM version, ``apsimNGpy`` is developed with forward- and backward-compatibility in mind and is actively synchronized with upstream APSIM.

    **Open and extensible**. ``Apache-2.0`` licensing, clear abstractions, and a plug-friendly architecture make it easy to extend and integrate into existing research pipelines.

    **Diverse model evaluation metrics**. Built-in model prediction evaluation metrics: RMSE, RRMSE, Willmott’s Index of Agreement (WIA), Bias, MAE, Lin's CCC, and R\ :sup:`2`


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
   :maxdepth: 2
   :caption: EDITING & INSPECTION

   model inspection
   inspect_model_parameters
   edit
   factorial_experiments
   weather

.. toctree::
   :maxdepth: 2
   :caption: DISTRIBUTED COMPUTING

   mult_core

.. toctree::
   :maxdepth: 2
   :caption: OPTIMIZATION & TRADE-OFF ANALYSIS

   OPT
   moo

.. toctree::
   :maxdepth: 3
   :caption: SUPPORT DEVELOPMENT

   how_to_cite

.. toctree::
   :maxdepth: 1
   :caption: TUTORIALS

   comp_cultivar

.. toctree::
   :maxdepth: 1
   :caption: CHEATSHEET

   cheat

.. toctree::
   :maxdepth: 1
   :caption: API REFERENCE

   api



