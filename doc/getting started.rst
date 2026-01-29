.. _Installation:

.. meta::
   :description lang=en:
      Run APSIM models sequentially with `run` or in parallel using `MultiCoreManager.run_all_jobs`.

Operating System
----------------

- **Windows**

- **Linux and macOS** are also supported, provided APSIM is installed and running locally on your machine.

Python Requirements
-------------------

- **Python ≥ 3.10 and < 3.14**

  .. note::

     Python 3.14 is not currently supported due to upstream limitations in
     ``pythonnet``. However, the development team is working around the clock to make sure it is also supported

Required Dependencies
---------------------

- **APSIM** (installed locally)

  - APSIM must be installed and accessible on the system.
  - A compatible APSIM version matching your workflow is required.

- **pythonnet ≥ 3.0.5**

  - Used to interface with APSIM’s .NET runtime.

- **NumPy**

- **Pandas**

- **SQLAlchemy**

- **matplotlib and seaborn**

These dependencies are installed automatically via ``pip``.

Installation
============

You can install ``apsimNGpy`` using one of the methods below.

Installing apsimNGpy
--------------------

Method 1: Install from PyPI (stable releases)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

   pip install apsimNGpy

Method 2: Clone the development repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

   git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git
   cd apsimNGpy
   pip install .

Method 3: Install directly from GitHub (recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

   pip install git+https://github.com/MAGALA-RICHARD/apsimNGpy.git

.. tip::

   Installing directly from GitHub is **strongly recommended**, as the repository
   is actively maintained and receives continuous bug fixes as soon as issues
   are reported by users.

Editable installation (for developers)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

   git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git
   cd apsimNGpy
   pip install -e .

Prerequisites
-------------

.. important::

   Before using ``apsimNGpy``, **APSIM Next Generation must be installed**.

   - Windows: https://www.apsim.info/download-apsim/downloads/
   - macOS / Linux: https://apsimnextgeneration.netlify.app/install/
   - APSIM documentation: https://docs.apsim.info/

   ``apsimNGpy`` assumes users have a basic understanding of APSIM as a
   process-based crop model. The goal of this package is to provide a
   programmatic and reproducible interface.

.. tip::

   Use the **pinned APSIM release** shown on the apsimNGpy home page
   (:ref:`Download it here <apsim_pin_version>`) to avoid forward-compatibility issues.

Verifying the APSIM Binary Path
-------------------------------

Using the command line
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

   apsim_bin_path -s

Automatic search
^^^^^^^^^^^^^^^^

.. code-block:: console

   apsim_bin_path --auto_search

.. hint::

   Shortcut:

   .. code-block:: console

      apsim_bin_path -a

Using Python
^^^^^^^^^^^^

.. code-block:: python

   from apsimNGpy.core import config
   print(config.get_apsim_bin_path())

.. seealso::

   API reference: :func:`~apsimNGpy.core.config.get_apsim_bin_path`

How apsimNGpy Locates APSIM Binaries
-----------------------------------

.. tip::

   ``apsimNGpy`` locates APSIM binaries using the following priority order:

   1. User-supplied binary path
   2. Environment variables
   3. System PATH
   4. Known installation directories

   If no valid path is found, a ``ValueError`` is raised.

Setting or Updating the APSIM Binary Path
-----------------------------------------

Option 1: Manual configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Locate ``APSIMNGpy_meta_data`` in your home directory.
2. Open ``apsimNGpy_config.ini``.
3. Update the ``apsim_location`` entry.

Option 2: Environment variable (temporary)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import os
   os.environ["APSIM"] = r"path/to/your/apsim/binary/folder/bin"

.. caution::

   This approach must be executed **before** importing ``apsimNGpy``.

Option 3: Using the apsimNGpy config API (recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from apsimNGpy.core.config import set_apsim_bin_path
   set_apsim_bin_path(r"path/to/your/apsim/binary/folder/bin")

.. seealso::

   API reference: :func:`~apsimNGpy.core.config.set_apsim_bin_path`

Option 4: Command-line update
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

   apsim_bin_path -u "path/to/your/apsim/binary/folder/bin"

or

.. code-block:: console

   apsim_bin_path --update "path/to/your/apsim/binary/folder/bin"

Verifying Successful Configuration
----------------------------------

.. code-block:: python

   from apsimNGpy.core.apsim import ApsimModel

.. attention::

   If this import fails, verify the APSIM binary path and Python.NET setup.

.. admonition:: Final Note

   The APSIM binary path only needs to be set once and can be reused across
   projects. ``apsimNGpy`` also supports switching between multiple APSIM
   versions when required.

   - :ref:`API Reference <api_ref>`
   - :ref:`Download Stable APSIM Version <apsim_pin_version>`

Containerization and Portability
--------------------------------

**apsimNGpy** simplifies containerization and project portability. Entire
projects can be transferred to another machine **without reinstalling APSIM**,
provided the APSIM binaries are correctly referenced.
