.. _Installation:

.. meta::
   :description lang=en:
      Run APSIM models sequentially with `run` or in parallel using `MultiCoreManager.run_all_jobs`.

Operating System
====================

- **Windows**

- **Linux and macOS** are also supported, provided APSIM is installed and running locally on your machine.

Python Requirements
---------------------

- **Python ≥ 3.10 and < 3.14**

  .. note::

     Python 3.14 is not currently supported due to upstream limitations in
     ``pythonnet``. However, the development team is working around the clock to make sure it is also supported

Required Dependencies
==========================

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

Installing apsimNGpy
=====================

You can install ``apsimNGpy`` using one of the methods below.

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

Method 3: Install directly from GitHub (Recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

   pip install git+https://github.com/MAGALA-RICHARD/apsimNGpy.git

.. tip::

   Installing directly from GitHub may be convenient for Anaconda users, as
   apsimNGpy is not currently distributed through the Anaconda package manager.


Editable installation (for developers)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

   git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git
   cd apsimNGpy
   pip install -e .

Prerequisites
-------------

.. important::

   APSIM application can be installed by following the links below:

   - Windows: https://www.apsim.info/download-apsim/downloads/
   - macOS / Linux: https://apsimnextgeneration.netlify.app/install/
   - APSIM documentation: https://docs.apsim.info/

.. tip::

   If you are new to using APSIM, try the following tutorials
   `here <https://apsimnextgeneration.netlify.app/user_tutorials/>`_.

.. tip::

    Unless you have a specific reason to do otherwise, always use the **pinned APSIM
    version (or an earlier compatible release)** shown on the apsimNGpy home page
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

Option 2: Using the apsimNGpy config API (recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from apsimNGpy.core.config import set_apsim_bin_path
   set_apsim_bin_path(r"path/to/your/apsim/binary/folder/bin")

.. seealso::

   API reference: :func:`~apsimNGpy.core.config.set_apsim_bin_path`

Option 3: Command-line update
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

The quickest alternative for all the above is to temporarily provide the APSIM ``bin`` path using a
context manager. This approach is useful for short scripts or interactive sessions
and assumes that you do **not** import any other ``apsimNGpy`` modules outside of
the :mod:`~apsimNGpy.core.config` module before entering the with block as shown below:

.. code-block:: python

   from apsimNGpy.core.config import apsim_bin_context
   with apsim_bin_context(
       apsim_bin_path=r"your_apsim_binary_path"):
       from apsimNGpy.core.apsim import ApsimModel
       model = ApsimModel("Soybean")
       df = model.run()


.. note::

   When using the APSIM ``bin`` context manager as shown above, the APSIM binaries
   are loaded only within the scope of that context, and the global APSIM binary
   configuration is not modified. This means the same context setup must be applied
   in each script where ``apsimNGpy`` is used. Whether this is an inconvenience
   depends on the use case—for example, it can be beneficial if you do not want to
   modify the global APSIM installation because it is used by other projects, or
   if you need to test or compare results across specific APSIM versions.

.. attention::

    Due to the way APSIM binaries are initialized globally within the runtime
    environment, only **one** APSIM ``bin`` context manager can be active at a time.
    As a result, starting another APSIM ``bin`` context manager within or after an
    existing one will not behave as expected and may lead to difficult-to-diagnose
    errors. In simple terms, multiple APSIM ``bin`` context managers cannot be used
    sequentially or nested within the same process, and attempting to do so is
    strongly discouraged.
