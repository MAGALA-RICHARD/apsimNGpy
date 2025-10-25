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

---

APSIM Next Generation (NG) Installation Tip
===========================================

Use the **pinned APSIM release** indicated on the documentation homepage to avoid forward-compatibility issues.
The pinned version represents the latest APSIM NG build verified against apsimNGpy’s API and unit tests.

---

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

---

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

`Read the docs → <https://magala-richard.github.io/apsimNGpy-documentations/index.html>`_

