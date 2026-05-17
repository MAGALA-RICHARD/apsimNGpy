Version 1.5.3
=============

New Features
------------
- **add_node_from method**

  Added a utility for transferring nodes between APSIM models with improved
  control and safety. The method now enforces **keyword-only arguments**
  (via ``*``) to prevent parameter mis-ordering and improve readability.

  Key features:

  - Copy nodes from external or internal APSIM models into a specified target location
  - Optionally delete existing nodes with matching name and type before insertion (``del_if_exists``)
  - Support renaming of inserted nodes (``rename``)
  - Allow node identification using either full paths or node names
  - Improved handling of multiple nodes of the same type (e.g., Manager scripts with different roles)

  This update enhances robustness model editing  and generation and usability for workflows involving
  model customization, scenario generation, and dynamic node manipulation.

* **``clone_simulation`` method**
   Added support for cloning existing simulations with a new name, enabling users to easily create and manage multiple simulation
   scenarios within the same model. This update facilitates
   comparative analyses (e.g., varying management practices such as fertilization rates) while preserving the original simulation configuration.
   see doc; :meth:`~apsimNGpy.core.ApsimModel.clone_simulation`

* **``has_node`` method**

  Added a new ``has_node`` method that allows users to check whether a given
  node name or path exists within the current APSIM model or specified scope.
  see doc; :meth:`~apsimNGpy.core.ApsimModel.has_node`

Added switch_wm_to_swim3() to simplify replacing the default APSIM water balance model with the physically based SWIM3 module.

New Features
   - Automatically replaces the existing soil water model with Models.Soils.Swim3
   - Supports optional subsurface tile drainage configuration
   - Allows custom SWIM3 parameter overrides through dictionaries
   - Adds validation for invalid drainage parameter keys
   - Supports custom layer structure thickness configuration

with this method, sub surface drainage can be declared with automatic configuration::

    model.switch_wm_to_swim3(
        ss_tile_drainage="auto"
    )

or custom settings::

    model.switch_wm_to_swim3(
        ss_tile_drainage={
            "DrainDepth": 1200,
            "DrainSpacing": 30000,
            "ImpermDepth": 2500
        }
    )

SWIM3 model parameters can can also be declared as follows::

    model.switch_wm_to_swim3(
    swim_model_params = {"eo_time": "05:00", "eo_durn": 600.0,
                     "default_rain_time": "00:00",
                      "default_rain_duration": 500.0,
                       "Diagnostics": False
            }
            )
for more information see:

   help(model.switch_wm_to_swim3)

* **Cultivar editing interface API**

  Introduced an explicit cultivar editing class; `CultivarEditor` using a composition-based
  design. Due to limitations in the APSIM API, replacement nodes cannot
  currently be edited in place. As a workaround, edited cultivars are added
  directly under the plant's children rather than modifying the replacement
  nodes themselves.
  see doc: :class:`~apsimNGpy.core.ce.CultivarEditor`

Bug Fixes
---------

* **``add_replacement`` duplication bug**

  Fixed an issue where running the replacement code multiple times created
  duplicate replacement nodes. The method now prevents replication of
  existing replacements.

# inspect_model return is node of a given type does not exist
the function now return [] if non existent

# model.inspect_model_parameters()` now returns a dictionary consistently across inspected APSIM model types.
- A dict allows to explicitly include the scalar values that are not layered in nature..



Version 1.5.2
=============

Improvements
------------
- Added lazy-loading support for APSIM runtime modules to prevent early CLR initialization.
- Consolidates all apsimNGpy public API into a single access point to enable easier discovery and support lazy importing.
Bug Fixes
---------
- Fixed issues with APSIM binary path configuration when importing ``apsimNGpy``.
- Improved compatibility with Ruff static analysis for ``TYPE_CHECKING`` imports.
- fixed f strings errors in early versions of python
- Fixed the add_crop_replacements method and removed the deprecated _crop argument. Future releases will allow this method to be called without arguments, automatically detecting available plant modules and adding them to the replacements folder.

Tests
-----
- Added tests verifying lazy attribute resolution and caching behavior.
- Added tests ensuring unittest modules are correctly exposed.


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