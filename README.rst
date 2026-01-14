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

.. image:: https://img.shields.io/badge/Read%20Publication-blue.svg
   :target: https://www.sciencedirect.com/science/article/pii/S2352711025004625
   :alt: Read Publication

.. image:: https://img.shields.io/badge/Ask%20Through%20Teams-purple.svg
   :target: https://teams.live.com/l/community/FBAbNOQj7y9dPcoaAI
   :alt: Ask Teams

.. image:: https://img.shields.io/badge/Download--APSIM--NG-2025.12.7939.0-blue?style=flat&logo=apachespark
   :target: https://registration.apsim.info/?version=2025.12.7939.0&product=APSIM%20Next%20Generation
   :alt: APSIM Next Generation version

===============================================================
apsimNGpy: The Next Generation Agroecosystem Simulation Library
===============================================================

**apsimNGpy** is a cutting-edge, open-source framework for advanced agroecosystem modeling, built entirely in Python.
It enables **object-oriented**, **data-driven** workflows for interacting with APSIM Next Generation models, offering capabilities for:

- Batch file simulation and model evaluation
- APSIMX file editing and parameter inspection
- Weather data retrieval and pre-processing
- Optimization and performance diagnostics
- Efficient soil profile development and validation

`Python <https://www.python.org/>`_ serves as the execution environment, integrating scientific computing, data analysis, and automation for sustainable agricultural systems.

---

Requirements
*************

1. **.NET SDK** — install from https://learn.microsoft.com/en-us/dotnet/core/install/
2. **Python 3.10+**
3. **APSIM Next Generation** — ensure the directory containing ``Models.exe`` is added to your system PATH.
4. (Optional) Use the official APSIM installer for easiest setup.
5. Minimum 8 GB RAM recommended.

---

Installation
************

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
===========================================

Use the **pinned APSIM release** indicated on the documentation homepage to avoid forward-compatibility issues.
The pinned version represents the latest APSIM NG build verified against apsimNGpy’s API and unit tests.

What is New in apsimNGpy 1.0.0
=============================

apsimNGpy 1.0.0 represents a major milestone in the development of the framework,
transitioning from an experimental research tool to a stable, production-ready
release. This version consolidates years of development and introduces key
improvements in performance, usability, reproducibility, and analytical
capability.

1. Stable, Reproducible Release
-------------------------------

- First official 1.0.0 release, signifying a stable public API.
- Backward compatibility is guaranteed for future minor releases.

2. Core Engine Improvements
---------------------------

- Refactored multiprocessing engine for robust, scalable execution across
  multiple CPU cores, including safer handling of parallel APSIM runs on Windows.
- Improved failure reporting and retry mechanisms with configurable policies
  (for example, tenacity-based retries), reducing silent errors in large batch
  jobs.
- Improved job submission logic allowing multiple edits to be submitted
  simultaneously.

3. Expanded Sensitivity and Uncertainty Analysis
------------------------------------------------

- Updated Sobol sampling with configurable skip values for improved
  space-filling designs.
- Clean handling of ``calc_second_order`` options with consistent propagation
  between sampling and analysis layers.
- Support for additional SALib methods with stable default parameterization.
- Sensitivity analysis workflows fully compatible across operating systems.

4. Improved Database and Output Management
------------------------------------------

- Schema-hash-based table naming to avoid SQLite collisions during parallel
  execution.
- A stable persistence layer with:

  - deterministic table identifiers
  - execution and process metadata
  - chunked writes for large result sets

- Cleaner error handling for database writes under heavy parallel workloads.

5. Workflow and Developer Quality of Life
-----------------------------------------

- Initial test modules executed using Windows batch scripts.
- Support for locking APSIM versions to a specific project configuration.

6. Fixes and Stability Enhancements
-----------------------------------

- Resolution of common SQLite locking issues under heavy parallel throughput.
- Deterministic hashing for table identifiers, even in multiprocessing contexts.
- Preflight validation and guidance for schema drift, unsupported data types,
  and mixed index or column structures.
- Improved error reporting for model-editing callbacks and APSIM parameter sets.

Summary
-------

apsimNGpy 1.0.0 delivers:

- A stable, reproducible foundation for agri-environmental modeling workflows.
- Improved scalability and reliability for large batch, single-objective, and
  multi-objective experiments.
- Stronger integration of APSIM with decision support, sensitivity analysis,
  and spatial optimization routines.
- An enduring API designed to remain robust under a wide range of modeling
  uncertainties.

This release establishes a solid platform for future enhancements while
remaining reliable for both academic research and applied decision-support
workflows in productivity, environmental impacts, and landscape planning.


apsimNGpy 0.39.11.20 – Release Notes
======================================

This release introduces a dedicated simulation file context manager that automatically removes transient .apsimx files and all associated output database files (.db, .db-wal, .db-sha, etc.) at the end of a with block.
This lets users run temporary simulations with confidence that intermediate files will not accumulate on disk — especially important for large workflows such as optimization loops, Monte-Carlo runs, or multi-site batch simulations.

To achieve this, the context manager now coordinates more carefully with APSIM-NG’s I/O locking behavior. In particular, it triggers the underlying C# garbage collector (when necessary) to ensure the write-locks on the result database are fully released before deletion.
Because of that, there is a small (but practically negligible) performance overhead; future versions may expose a switch to disable this behaviour for users who do not require automatic cleanup.

This release also adds a second context manager for temporary APSIM bin-path management.
It allows users to specify a local APSIM-NG installation path for a given script/module while preserving the global default in memory — enabling cleaner multi-version testing or workflow portability without rewriting environment variables.

1) Temporally simulations using a context manager
---------------------------------------------------
.. code-block:: python

   from apsimNGpy.core.apsim import ApsimModel
    with Apsim_model("template.apsimx") as temp_model:
        temp_model.run()   # temporary .apsimx + .db files created
        df= temp_model.results
        print(df)

Immediately after exiting the with block, the temporary .apsimx file (and its associated .db files) are deleted,
since only clones of the original model file are used inside the context.

2) Temporary APSIM-bin path
----------------------------
.. code-block:: python

    from apsimNGpy.core.config import apsim_bin_context
    with apsim_bin_context("C:/APSIM/2025.05.1234/bin"):
        from Models.Core import Simulations   # uses this bin path for loading
        from apsimNGpy.core.apsim import ApsimModel

Immediately after exiting the with block, the path is restored back to the global APSIM path — meaning that other projects and modules can continue to access their own settings normally. The importance of this pattern is reproducibility: it allows your project to be “locked” to a specific APSIM binary path.
APSIM versions change frequently, and a future run of your current project might fail or give different results if a newer APSIM version is picked up without you realizing it. By scoping a local APSIM bin path for this project, you ensure that reruns in the future use exactly the same APSIM version that generated the original results.
This makes the workflow both reproducible and stable.

.. note::

    Since the model assemblies are already loaded into memory inside the `apsim_bin_context`, you do not need to remain inside the
    `with` block to keep using them. Once loaded, those modules (and their namespaces) are global within the process, and they retain
    their reference to the APSIM bin path that was supplied during loading.



The bin path can also be substituted with just the project `.env` path as follows

.. code-block:: python

   with apsim_bin_context( dotenv_path = './config/.env', bin_key ='APSIM_BIN_PATH'):
        from Models.Core import Simulations   # uses this bin path for loading
        from apsimNGpy.core.apsim import ApsimModel # uses this bin path for loading


v0.39.10.18 (2025-10-24)
=========================

Added
------

- ``preview_simulation(watch=True)`` now supports **interactive edit syncing**:
  - Opens the ``.apsimx`` file in the APSIM NG GUI and *watches* for saved edits.
  - When a user saves in the GUI, changes are automatically reloaded into the active ``ApsimModel`` instance.
  - Console messages guide users during the live session (e.g., *“Watching for GUI edits... Save in APSIM to sync back.”*).
  - Graceful shutdown supported via ``Ctrl+C``; after termination, the Python model reflects the most recent GUI state.
  - Users should close the GUI after completing edits before continuing with the Python model instance.

Notes
------

- This feature is **experimental** but stable in tests.
- Synchronization assumes that both APSIM GUI and Python edit the same ``.apsimx`` file path.
- If ``watch=False`` (default), ``preview_simulation`` behaves as before — no live syncing.
- GUI edits must be **saved** before synchronization occurs. Unsaved edits are ignored.

Developer impact
----------------

- New function signature: ``preview_simulation(self, watch=False)``
- Existing scripts calling ``preview_simulation()`` remain fully compatible.
- File-watching currently uses file modification times; future releases may support event-based detection.



v0.39.10.17
===========

Release Notes
-------------

This build is stable for day-to-day work, with incremental API refinements.

Highlights
----------

- Updated ``save`` method on ``ApsimModel`` to include a ``reload`` parameter.
- Improved documentation navigation and linked related APIs.

Full Documentation
------------------

`Read the live docs <https://magala-richard.github.io/apsimNGpy-documentations/index.html>`_
Or read the docs at `apsimNGpy documentation <https://apsimngpy.readthedocs.io/en/v1.0.0/>`_.




