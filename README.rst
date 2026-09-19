
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


.. image:: https://img.shields.io/badge/Download--APSIM--NG-2026.2.7980.0-blue?style=flat&logo=apachespark
   :alt: APSIM Next Generation version
   :target: https://registration.apsim.info/?version=2026.02.7980.0&product=APSIM%20Next%20Generation

.. image:: ./images/run.gif
   :alt: Run APSIM simulation
   :align: center
   :width: 800px

Links
================

`Documentation <https://apsimngpy.readthedocs.io/en/latest/>`_

`Publication <https://www.sciencedirect.com/science/article/pii/S2352711025004625>`_.

Version 1.5.5 passed unit tests under Python 3.14+

For the complete list of new features, improvements, and bug fixes, see the
`v1.5.3 release notes <https://github.com/MAGALA-RICHARD/apsimNGpy/releases/tag/v1.5.3>`_.

apsimNGpy: The Next Generation Agroe-cosystem Simulation Library
===========================================================================

**apsimNGpy** is an open-source framework for advanced agroecosystem modeling, built entirely in Python.
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

Projects and Agentic Systems Built With or Inspired by apsimNGpy
=================================================================

* `apsim-mcp: Natural-Language Agent Interface for APSIM Next Generation by Briggs599 (2026) <https://github.com/Briggs599/apsim-mcp>`_.
  This MCP server allows an LLM to operate APSIM Next Generation using natural language.
  The agent can open APSIM models, inspect their structure, modify model parameters,
  attach soil and weather data, configure report variables, execute individual or
  factorial experiments, and retrieve simulation outputs. Its engine dependency
  explicitly includes `apsimNGpy`, making `apsimNGpy` the bridge between MCP/LLM
  tool calls and APSIM/.NET. The project has been tested with Claude Desktop and
  Claude Code and has also been presented in the APSIM community as an LLM interface
  for APSIM.

* `Coupled Process-Based and Machine-Learning Ensemble Modeling for Agricultural N2O Flux Prediction <https://github.com/harbor-framework/terminal-bench-science/discussions/472>`_
  by Kyungdoe Han / Terminal-Bench Science (2026).
  This AI-for-science benchmark requires an autonomous agent to use
  `apsimNGpy >= 1.5.3` to repeatedly execute APSIM, extract SOC, NH4, NO3,
  soil moisture/WFPS, and temperature, align those mechanistic outputs with field
  N2O observations, and train an XGBoost model for blind N2O prediction.
  It is particularly interesting because `apsimNGpy` is not merely supporting a
  researcher—the **AI agent itself is expected to learn and operate apsimNGpy as a
  scientific tool**. The proposal was subsequently approved for implementation by
  Terminal-Bench Science.

* `Nitrogen Digital Twin by Taylor Sharpe / BEEM Lab, University of Colorado Boulder (2026) <https://github.com/TaylorJSharpe/nitrogen-digital-twin>`_.
  This project develops a farm-scale nitrogen digital twin combining low-cost soil
  sensors, Ensemble Kalman Filter data assimilation, spatial kriging, forecasting,
  nitrogen balance calculations, and mechanistic modeling. Its project specification
  identifies `apsimNGpy + APSIM-X` as the intended production replacement for the
  current simplified nitrogen-cycle ODE model.

* `apsimNGpy-soils: APSIM-ready Soil Profile Construction Tools by Abhi-Plant (2026) <https://github.com/Abhi-Plant/apsimNGpy-soils>`_.
  **Downstream apsimNGpy ecosystem extension.** This independent project provides
  tools for creating APSIM-ready soil profiles using SSURGO and SoilGrids data,
  pedotransfer functions, polygon queries, and APSIM soil-parameter editors.






