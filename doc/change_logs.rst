Version 1.5
-----------

Improvements
~~~~~~~~~~~~

- Moved ``pythonet_config`` from the ``core`` module to the ``starter`` module
  to improve module organization and streamline initialization flow.

- Verified compatibility with the latest APSIM binary (build 7990).

- Added ``__len__`` to ``ApsimModel``:

  - ``len(model)`` now returns the number of loaded simulations.
  - Internally delegates to ``len(self.simulations)``.

- Added ``__getitem__`` to ``ApsimModel``:

  - ``model[index]`` returns the simulation at the specified index.
  - ``model["SimulationName"]`` returns the simulation matching the given name.


APSIM Runtime Loading Improvements
===================================

The ``apsimNGpy.bin_context`` class now lazily loads all apsimNGpy
modules and classes that depend on the .NET runtime and the APSIM binary path.
This ensures that APSIM-specific objects are initialized and atatched to a specific APSIM version defined by the binary path, improving version control.
startup performance and runtime safety.

In addition, a new ``Apsim`` class has been introduced at the top-level
``apsimNGpy`` module to enable dynamic management of different APSIM
versions across scripts or projects. This allows users to explicitly
control which APSIM binary is loaded at runtime.

Users may initialize the ``Apsim`` class in one of two modes:

- **Auto mode** — No binary path is provided; the system resolves the
  APSIM installation automatically from the config.in path located in the user directory or from from global env.
- **Explicit mode** — A binary path is supplied to load APSIM-dependent
  modules from a specific installation.

This design provides greater flexibility, version isolation, and
improved runtime control when working with multiple APSIM installations.

Examples
--------

Auto mode (automatic binary resolution):

.. code-block:: python

   from apsimNGpy import Apsim
   apsim = Apsim()
   Models = apsim.CLR.Models

Explicit mode (manual binary selection):

.. code-block:: python

   from apsimNGpy import Apsim
   apsim = Apsim(bin_path="path/to/apsim/bin")
   Models = apsim.CLR.Models

Using ``with context key word`` for scoped runtime control:

.. code-block:: python

   from apsimNGpy import Apsim
   with Apsim("path/to/apsim/bin") as apsim:
       with apsim.ApsimModel("Maize") as model:
           model.run()
           print(model.summarize_numeric())

use env path with a specified binary path key

.. code-block:: python

   from apsimNGpy import Apsim
   with Apsim(dotenv_path = "path/to/apsim/bin.env",bin_key = '9780') as apsim:
       with apsim.ApsimModel("Maize") as model:
           model.run()
           print(model.summarize_numeric())

Deprecations
~~~~~~~~~~~~

The following methods are deprecated and will be removed in **v1.6.0**:

- ``evaluate_simulated_output()``
   Use ``evaluate()`` instead.

- ``preview_simulation()``
   Use ``open_in_gui()`` instead.

- ``inspect_file()``
   Use ``tree()`` instead.