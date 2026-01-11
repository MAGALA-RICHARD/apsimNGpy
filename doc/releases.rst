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


The bin path can also be substituted with just the project `.env` path as follows

.. code-block:: python

   with apsim_bin_context( dotenv_path = './config/.env', bin_key ='APSIM_BIN_PATH'):
        from Models.Core import Simulations   # uses this bin path for loading
        from apsimNGpy.core.apsim import ApsimModel # uses this bin path for loading


.. note::

    Since the model assemblies are already loaded into memory inside the `apsim_bin_context`, you do not need to remain inside the
    `with` block to keep using them. Once loaded, those modules (and their namespaces) are global within the process, and they retain
    their reference to the APSIM bin path that was supplied during loading.

