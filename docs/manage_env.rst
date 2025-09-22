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

.. tip::

   Each project keeps its own .env, so paths/versions don’t clash.

   For multiple installs, create variant files (e.g., .env.2025.8) and load with:

   ``load_dotenv(dotenv_path=".env.2025.8", override=True)``
   

   On Windows, keep quotes around paths with spaces.