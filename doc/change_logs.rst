Version 1.5.3
=============

API improvements
--------------------------

- **Added ``append_simulation`` method**
------------------------------------------

  Added a new :meth:`~apsimNGpy.core.apsim.ApsimModel.append_simulation`` method for appending simulations
  into the current ``ApsimModel`` instance. Unlike
  ``clone_simulation``, this method supports transferring simulations
  from external ``ApsimModel`` objects in addition to duplicating
  simulations already present within the current model instance.

Advantages:

- Reuse simulations across APSIM models without manual copying.
- Build complex scenario collections from multiple source models with minimal effort.
- Quickly create simulation variants by duplicating existing simulations.
- Avoid naming conflicts through optional simulation renaming.
- Improve productivity when assembling large simulation ensembles.
- Improves execution efficiency by allowing multiple simulations to be managed within a single APSIM model instance, reducing the overhead associated with repeatedly loading and initializing `Models.exe`.
- Rapidly generate multiple simulation scenarios using the ``payload`` argument, enabling efficient exploration of management, soil, weather, or cultivar variations and their impacts on model outputs.
- Simplify what-if analysis by automatically creating simulation variants from different input configurations, reducing the effort required to evaluate alternative strategies and outcomes.

Basic example::

      from apsimNGpy import ApsimModel
      base_model =ApsimModel('Maize')
      other_simulation  = ApsimModel("Soybean")[0] # gets the first simulation

      base_model.append_simulation(
          simulation=other_simulation,
          rename="Simulation2"
      )

Duplicating an existing simulation::

      from apsimNGpy import ApsimModel
      model =ApsimModel('Maize')
      model.append_simulation(
      model[0]
          rename="Simulation_copy"
      )
Edit the added simulation on the fly::

        with ApsimModel('Maize') as model:
            model.append_simulation(simulation=model[0], rename='pop12',
                                          payload=dict(model_type='Models.Manager',
                                                       model_name='Sow using a variable rule',
                                                       Population=12))


  .. note::

     This method should not be used with ``ExperimentManager`` objects,
     even though ``ExperimentManager`` inherits from ``ApsimModel``. These objects supports one base simulation
     and may produce unintended behavior when appended directly.

     Normally you may need to edit the newly edited simulation surgically to make it unique from the existing simulation but
     the method allows editing via key word payload which could be a dict or a list of dicts as follows::
     model.append_simulation(fixed_model[0], rename='clone1', [payload=dict(model_type='Models.Manager',
                                                                                        model_name='Sow using a variable rule',
                                                                                        Population=12)])


  For additional usage examples and implementation details see::

      help(model.append_simulation)
- ** Added add_node_from` method**
------------------------------------------

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

Added ``clone_simulation`` method
----------------------------------
   Added support for cloning existing simulations with a new name, enabling users to easily create and manage multiple simulation
   scenarios within the same model. This update facilitates
   comparative analyses (e.g., varying management practices such as fertilization rates) while preserving the original simulation configuration.
   see doc; :meth:`~apsimNGpy.core.ApsimModel.clone_simulation`. see example below:

.. code-block:: python

    from apsimNGpy import ApsimModel
    model = ApsimModel("Maize")
    # Create a new simulation with a different population
    population = 10
    simulation_name = f"sim_{population}"
    model.clone_simulation(
        rename=simulation_name,
        base_simulation=0,
    )

    # Update the cloned simulation
    model.edit_model(
        model_type="Models.Manager",
        model_name="Sow using a variable rule",
        simulations=simulation_name,
        Population=population,
    )

    # Update the original simulation
    model.edit_model(
        model_type="Models.Manager",
        model_name="Sow using a variable rule",
        simulations="Simulation",
        Population=4,
    )

    # Verify that two simulations now exist in the model
    model.inspect_model("Simulation")

    # Output:
    # ['.Simulations.Simulation', '.Simulations.sim_10']

    # APSIM assigns a SimulationID in the report tables, but the
    # simulation name is often easier to interpret during analysis.
    # Add the simulation name to the report output.
    model.edit_model(
        model_type="Models.Report",
        model_name="Report",
        variable_spec=[
            "[Simulation].Name as SimulationName"
        ],
    )

    model.run()

    # Compare average yield by simulation
    model.results.groupby("SimulationName")["Yield"].mean()

    # Output:
    #
    # SimulationName
    # Simulation    4786.670976
    # sim_10        6287.776688
    # Name: Yield, dtype: float64


Added ``has_node`` method
---------------------------------

  Added a new ``has_node`` method that allows users to check whether a given
  node name or path exists within the current APSIM model or specified scope.
  see doc; :meth:`~apsimNGpy.core.ApsimModel.has_node`.

.. code-block:: python

   from apsimNGpy import ApsimModel
   with ApsimModel('Maize') as model:
      has = model.has_node('Sow using a variable rule', 'Models.Manager')
      # {'ok': True, 'fullpath': False}
      has = model.has_node('.Simulations.Simulation.Field.Sow using a variable rule', "Models.Manager")
      #  {'ok': True, 'fullpath': True}

Added switch_wm_to_swim3 method
----------------------------------

This method to simplifies replacing the default APSIM water balance model with the physically based SWIM3 module.

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
for more information see::

   help(model.switch_wm_to_swim3)

* **Cultivar editing interface API**

  Introduced an explicit cultivar editing class; `CultivarEditor` using a composition-based
  design. Due to limitations in the APSIM API, replacement nodes cannot
  currently be edited in place. As a workaround, edited cultivars are added
  directly under the plant's children rather than modifying the replacement
  nodes themselves.
  see doc: :class:`~apsimNGpy.core.ce.CultivarEditor`

* **``add_new_model`` method**

  Added a new utility for dynamically constructing and inserting APSIM
  model nodes from Python dictionaries. This method simplifies
  programmatic APSIM model generation and editing while providing
  improved control over insertion, replacement, and renaming behavior.

  Key features:

  - Create APSIM model nodes directly from Python dictionaries
  - Support APSIM-standard ``"$type"`` or Python-friendly ``"type"``
    declarations
  - Automatically resolve and instantiate APSIM CLR model types
  - Insert nodes into arbitrary APSIM parent nodes
  - Optionally replace existing nodes with matching type and name
  - Optionally rename inserted nodes
  - Automatically parse APSIM ``Clock`` date fields
  - Automatically convert ``Manager.Parameters`` into compatible
    .NET structures
  - Gracefully ignore unsupported or incompatible attributes during
    assignment

  Basic example::

      from apsimNGpy import ApsimModel

      model = ApsimModel("Maize")

      model.add_new_model(
          parent_identifier="Simulation",
          parent_type="Simulation",
          source={
              "$type": "Models.Clock, Models",
              "Start": "2000-01-01",
              "End": "2020-12-31"
          }
      )

  Adding a Manager script::

      model.add_new_model(
          parent_identifier=".Simulations.Simulation.Field",
          parent_type="Zone",
          source={
              "type": "Models.Manager, Models",
              "Name": "IrrigationManager",
              "Parameters": [
                  {"Key": "Amount", "Value": 30}
              ],
              "CodeArray": [] # code needed here
          },
          replace=False,
          rename="IrrigationManager_v2"
      )

  For more information and additional examples see::

      help(model.add_new_model)

or

See doc: :meth:`~apsimNGpy.core.apsim.ApsimModel.add_new_model`



Bug Fixes
---------

* **``add_replacement`` duplication bug**

  Fixed an issue where running the replacement code multiple times created
  duplicate replacement nodes. The method now prevents replication of
  existing replacements.

:meth:`~apsimNGpy.core.apsim.inspect_model` now return [] if specified model type does non exist in the simulation tree

Removed the fixed 8000-second execution timeout and replaced it with unlimited runtime by default,
preventing premature termination of computationally intensive simulations such as Sobol sensitivity analyses.

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