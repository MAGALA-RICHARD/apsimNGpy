Managing apsimNGpy project environment
========================================


If you have multiple Python projects using apsimNGpy, or you want to pin a project to a specific APSIM NG build, use a .env file for each project settings.

Prerequisite

.. code-block:: bash

    pip install python-dotenv
    pip install uv
    mkdir my_project
    cd my_project
    uv venv # activate as required
    uv init
    uv pip install apsimNGpy

Step 1 — Create .env in your project root
=========================================

Add your local APSIM bin path and the build or release No you expect:

The bin path is the one extracted after APSIM install, if you are going to port the project to another person indicate it and provide .env.example file, as this path is different for every computer

The content of the file might look as follows but customize it the way you want it to be.

.. code-block:: ini
   :caption: .env



    # Path to the installed APSIM NG's bin folder (quote if it has spaces); use forward slashes on macOS/Linux.
    APSIM_BIN="C:\Program Files\APSIM2025.8.7837.0\bin" #replace with your path

    # Expected APSIM build (for checks)
    APSIM_VERSION=2025.8.7837.0


Step 2 — Load and enforce in code

==================================

.. code-block:: python
   :caption: config.py


    from apsimNGpy.core.config import set_apsim_bin_path, get_apsim_bin_path, apsim_version
    from dotenv import load_dotenv
    from pathlib import Path
    import os

    # load env
    load_dotenv()
    # get current bin path
    CUR_BIN_PATH  = get_apsim_bin_path()


    # get bin bath
    env_BIN_PATH  = os.getenv('APSIM_BIN', None)

    # decide whether to exit and raise if env bin path is not valid

    class ConfigurationError(Exception): # u can also use apsimNgpy built in exceptions
        pass
    if not os.path.exists(env_BIN_PATH):
      raise ConfigurationError('APSIM bin path provided in the .env file is not valid. please try again')
      # alternative is to exit
      import sys
      sys.exit(0)

    # logic for setting bin if valid
    if Path(env_BIN_PATH) != Path(CUR_BIN_PATH)
       set_apsim_bin_path(env_BIN_PATH)



Set 3.Use it in your app:
=============================

Make sure you import it in your app, such that the rules are enforced and everytime you run that project, it uses the specified path

.. code-block:: python

   from config import APSIM_BIN
   print("APSIM bin:", APSIM_BIN)

.. admonition:: Highlight

    apsimNGpy version **0.39.10.20** introduces a context manager for managing APSIM version efficiently.
    It allows users to specify a local APSIM-NG installation path for a given script/module while preserving
    the global default in memory — enabling cleaner multi-version testing or workflow portability without rewriting environment variables. from the above workflow
    we can manage our APSIM path in two ways:

1. Use the bin path in the context manager as follows.

.. code-block:: python

   from apsimNGpy.core.config import apsim_bin_context

   with apsim_bin_context("C:/APSIM/2025.05.1234/bin"):
       # All CLR and APSIM assemblies are resolved from this bin path
       from Models.Core import Simulations
       from apsimNGpy.core.apsim import ApsimModel

.. attention::

   The APSIM bin context **must be activated before** importing any modules
   that rely on ``pythonnet`` or APSIM C# assemblies.

   Once a CLR assembly is loaded, it is cached for the lifetime of the Python
   process. If APSIM-related modules are imported *before* entering
   ``apsim_bin_context``, those cached assemblies will continue to be used,
   and changing the bin path afterward will have **no effect**.

   To avoid this issue, always enter ``apsim_bin_context`` at the **very
   beginning** of your script or interactive session, before importing:

   Define your APSIM workflows inside **functions** rather than at the
   module or global scope.  Encapsulating logic within functions helps to clearly separate **local**
   state from **global** state, reducing unintended side effects caused by
   module-level imports, cached objects, or persistent runtime state
   (e.g., ``pythonnet`` and CLR assemblies).

   OR

   It is advisable that you don't mixed direct imports with context depended imports in one script.


2. Use the env file in the context manager as follows

.. code-block:: python

    with apsim_bin_context(dotenv_path = './config/.env', bin_key ='APSIM_BIN'): # assumes that .env is in the config directory
        from apsimNGpy.core.apsim import ApsimModel # uses the above bin path for loading

.. admonition:: Highlight

    Since the model assemblies are already loaded into memory inside the apsim_bin_context,
    you do not need to remain inside the with block to keep using them. Once loaded, those modules (and their namespaces)
    are global within the process, and they retain their reference to the APSIM bin path that was supplied during loading.

.. tip::

   Each project keeps its own .env, so paths/versions don’t clash.

   For multiple installs, create variant files (e.g., .env.2025.8) and load with:

   ``load_dotenv(dotenv_path=".env.2025.8", override=True)``
   

   On Windows, keep quotes around paths with spaces.

   Thank you