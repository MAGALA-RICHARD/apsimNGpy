apsimNGpy: API Reference
~~~~~~~~~~~~~~~~~~~~~~~~

apsimNGpy.core.apsim
--------------------

Interface to APSIM simulation models using Python.NET
author: Richard Magala
email: magalarich20@gmail.com

.. class:: apsimNGpy.core.apsim.ApsimModel

   Main class for apsimNGpy modules.
It inherits from the CoreModel class and therefore has access to a repertoire of methods from it.

This implies that you can still run the model and modify parameters as needed.
Example:
    >>> from apsimNGpy.core.apsim import ApsimModel
    >>> from pathlib import Path
    >>> model = ApsimModel('Maize', out_path=Path.home()/'apsim_model_example.apsimx')
    >>> model.run(report_name='Report') # report is the default, please replace it as needed

   .. method:: apsimNGpy.core.apsim.ApsimModel.get_soil_from_web(self, simulation_name: Union[str, tuple, NoneType] = None, *, lonlat: Optional[System.Tuple[Double,Double]] = None, soil_series: Optional[str] = None, thickness_sequence: Optional[Sequence[float]] = 'auto', thickness_value: int = None, max_depth: Optional[int] = 2400, n_layers: int = 10, thinnest_layer: int = 100, thickness_growth_rate: float = 1.5, edit_sections: Optional[Sequence[str]] = None, attach_missing_sections: bool = True, additional_plants: tuple = None, adjust_dul: bool = True)

      Download SSURGO-derived soil for a given location and populate the APSIM NG
soil sections in the current model.

This method updates the target Simulation(s) in-place by attaching a Soil node
(if missing) and writing section properties from the downloaded profile.

Parameters
----------
simulation : str | sequence[str] | None, default None
    Target simulation name(s). If ``None``, all simulations are updated.

lonlat : tuple[float, float] | None
    Location for SSURGO download, as ``(lon, lat)`` in decimal degrees
    (e.g., ``(-93.045, 42.012)``).

soil_series : str | None, optional
    Optional component/series filter. If ``None``, the dominant series
    by area is used. If a non-existent series is supplied, an error is raised.

thickness_sequence : sequence[float] | str | None, default "auto"
    Explicit layer thicknesses (mm). If ``"auto"``, thicknesses are generated
    from the layer controls (e.g., number of layers, growth rate, thinnest layer,
    and ``max_depth``). If ``None``, you must provide ``thickness_value`` and
    ``max_depth`` to construct a uniform sequence.

thickness_value : int | None, optional
    Uniform thickness (mm) for all layers. Ignored if ``thickness_sequence`` is
    provided; used only when ``thickness_sequence`` is ``None``.

max_depth : int, default 2400
    Maximum soil depth (mm) to cover with the thickness sequence.

edit_sections : sequence[str], optional
    Sections to edit. Default:
    ``("physical", "organic", "chemical", "water", "water_balance", "solutes", "soil_crop", "meta_info")``.
    Note: if sections are edited with differing layer counts, APSIM may error at run time.

attach_missing_sections : bool, default True
    If ``True``, create and attach missing section nodes before editing.

additional_plants : sequence[str] | None, optional
     Plant names for which to create/populate ``SoilCrop`` entries (e.g., to set KL/XF).

adjust_dul : bool, optional
    If ``True``, adjust layer values where ``SAT`` exceeds ``DUL`` to prevent APSIM runtime errors.

Returns
-------
self
    The same instance, to allow method chaining.

Raises
------
ValueError
    - ``thickness_sequence`` provided with any non-positive value(s).
    - ``thickness_sequence`` is ``None`` **and** ``thickness_value`` is ``None``.
    - Units mismatch or inconsistency between ``thickness_value`` and ``max_depth``.

Notes
-----
- Assumes soil sections live under a **Soil** node; when
  ``attach_missing_sections=True`` a Soil node is created if missing.
- Uses the optimized SoilManager routines (vectorized assignments / .NET double[] marshaling).
- Side effects (in place on the APSIM model):
    1. Creates/attaches **Soil** when needed.
    2. Creates/updates child sections (``Physical``, ``Organic``, ``Chemical``,
       ``Water``, ``WaterBalance``, ``SoilCrop``) as listed in ``edit_sections``.
    3. Overwrites section properties (e.g., layer arrays such as ``Depth``, ``BD``,
       ``LL15``, ``DUL``, ``SAT``; solutes; crop KL/XF) with downloaded values.
    4. Add **SoilCrop** children for any names in ``additional_plants``.
    5. Performs **network I/O** to retrieve SSURGO tables when ``lonlat`` is provided.
    6. Emits log messages (warnings/info) when attaching nodes, resolving thickness controls,
       or skipping missing columns.
    7. Caches the computed soil profile in the helper during execution; the in-memory APSIM
       tree remains modified after return.
    8. Does **not** write files; call ``save()`` on the model if you want to persist changes.
    9. The existing soil-profile structure is completed override by the newly generated soil profile.
       So, variables like soil thickness, number of soil layers, etc. might be different from the old one.

   .. method:: apsimNGpy.core.apsim.ApsimModel.adjust_dul(self, simulations: Union[tuple, list] = None)

      - This method checks whether the soil ``SAT`` is above or below ``DUL`` and decreases ``DUL``  values accordingly

- Need to call this method everytime ``SAT`` is changed, or ``DUL`` is changed accordingly.

``simulations``: str, name of the simulation where we want to adjust DUL and SAT according.

``returns``:

    model the object for method chaining

   .. method:: apsimNGpy.core.apsim.ApsimModel.replace_downloaded_soils(self, soil_tables: Union[dict, list], simulation_names: Union[tuple, list], **kwargs)

      @deprecated and will be removed in the future versions
        Updates soil parameters and configurations for downloaded soil data in simulation models.

        This method adjusts soil physical and organic parameters based on provided soil tables and applies these
        adjustments to specified simulation models.

        Parameters:
        ``soil_tables`` (list): A list containing soil data tables. Expected to contain: see the naming
        convention in the for APSIM - [0]: DataFrame with physical soil parameters. - [1]: DataFrame with organic
        soil parameters. - [2]: DataFrame with crop-specific soil parameters. - simulation_names (list of str): Names or identifiers for the simulations to
        be updated.s


        Returns:
        - self: Returns an instance of the class for ``chaining`` methods.

        This method directly modifies the simulation instances found by ``find_simulations`` method calls,
        updating physical and organic soil properties, as well as crop-specific parameters like lower limit (``LL``),
        drain upper limit (``DUL``), saturation (``SAT``), bulk density (``BD``), hydraulic conductivity at saturation (``KS``),
        and more based on the provided soil tables.

->> key-word argument

        ``set_sw_con``: Boolean, set the drainage coefficient for each layer
        ``adJust_kl``:: Bollean, adjust, kl based on productivity index
        ``CultvarName``: cultivar name which is in the sowing module for adjusting the rue
        ``tillage``: specify whether you will be carried to adjust some physical parameters

   .. method:: apsimNGpy.core.apsim.ApsimModel.spin_up(self, report_name: str = 'Report', start=None, end=None, spin_var='Carbon', simulations=None)

      Perform a spin-up operation on the aPSim model.

This method is used to simulate a spin-up operation in an aPSim model. During a spin-up, various soil properties or
_variables may be adjusted based on the simulation results.

Parameters:
----------
``report_name`` : str, optional (default: 'Report')
    The name of the aPSim report to be used for simulation results.

``start`` : str, optional
    The start date for the simulation (e.g., '01-01-2023'). If provided, it will change the simulation start date.

``end`` : str, optional
    The end date for the simulation (e.g., '3-12-2023'). If provided, it will change the simulation end date.

``spin_var`` : str, optional (default: 'Carbon'). the difference between the start and end date will determine the spin-up period
    The variable representing the child of spin-up operation. Supported values are 'Carbon' or 'DUL'.

``Returns:``
-------
self : ApsimModel
    The modified ``ApsimModel`` object after the spin-up operation.
    you could call ``save_edited`` file and save it to your specified location, but you can also proceed with the simulation

   .. method:: apsimNGpy.core.apsim.ApsimModel.read_apsimx_data(self, table=None)

      Read APSIM NG datastore for the current model. Raises FileNotFoundError if the model was initialized from
default models because those need to be executed first to generate a database.

The rationale for this method is that you can just access the results from the previous session without
running it, if the database is in the same location as the apsimx file.

Since apsimNGpy clones the apsimx file, the original file is kept with attribute name `_model`, that is what is
being used to access the dataset

table (str): name of the database table to read if none of all tables are returned

 Returns: pandas.DataFrame

 Raises
 ------------
  KeyError: if table is not found in the database

   .. method:: apsimNGpy.core.apsim.ApsimModel.restart_model(self, model_info=None) (inherited)

      ``model_info``: A named tuple object returned by `load_apsim_model` from the `model_loader` module.

Notes:
- This parameter is crucial whenever we need to ``reinitialize`` the model, especially after updating management practices or editing the file.
- In some cases, this method is executed automatically.
- If ``model_info`` is not specified, the simulation will be reinitialized from `self`.

This function is called by ``save_edited_file`` and ``update_mgt``.

:return: self

   .. method:: apsimNGpy.core.apsim.ApsimModel.save(self, file_name: 'Union[str, Path, None]' = None) (inherited)

      Saves the current APSIM NG model (``Simulations``) to disk and refresh runtime state.

This method writes the model to a file, using a version-aware strategy:

* If ``APSIM_VERSION_NO > BASE_RELEASE_NO`` **or**
  ``APSIM_VERSION_NO == GITHUB_RELEASE_NO``: call
  ``self.Simulations.Write(path)``.
* Otherwise: obtain the underlying node via
  ``getattr(self.Simulations, 'Node', self.Simulations)`` and call
  :func:`save_model_to_file`.

After writing, the model is recompiled via :func:`recompile(self)` and the
in-memory instance is refreshed using :meth:`restart_model`, ensuring the
object graph reflects the just-saved state.

Parameters
----------
file_name : str or pathlib.Path, optional
    Output path for the saved model file. If omitted (``None``), the method
    uses the instance's existing ``self.path``. The resolved path is also
    written back to ``self.path`` for consistency.

Returns
-------
Self
    The same model/manager instance to support method chaining.

Raises
------
OSError
    If the file cannot be written due to I/O errors, permissions, or invalid path.
AttributeError
    If required attributes (e.g., ``self.Simulations``) or methods are missing.
Exception
    Any exception propagated by :func:`save_model_to_file`, :func:`recompile`,
    or :meth:`restart_model`.

Side Effects
------------
- Sets ``self.path`` to the resolved output path (string).
- Writes the model file to disk (overwrites if it exists).
- Recompiles the model and restarts the in-memory instance.

Notes
-----
- **Version-aware save:** Uses either ``Simulations.Write`` or the legacy
  ``save_model_to_file`` depending on version constants.
- **Path normalization:** The path is stringified via ``str(file_name)`` /
  ``str(self.path)`` without additional validation. If you require parent
  directory creation or suffix checks (e.g., ``.apsimx``), perform them before
  calling ``save``.
- **Reload semantics: ** Post-save recompilation and restart ensure any code
  generation or cached reflection is refreshed to match the serialized model.

Examples
--------
Save to the current file path tracked by the instance::

    model.save()

Save to a new path and continue working with the refreshed instance::

    model.save("outputs/Scenario_A.apsimx").run()

See Also
--------
recompile : Rebuild internal/compiled artifacts for the model.
restart_model : Reload/refresh the model instance after recompilation.
save_model_to_file : Legacy writer for older APSIM NG versions.

   .. method:: apsimNGpy.core.apsim.ApsimModel.get_simulated_output(self, report_names: 'Union[str, list]', axis=0, **kwargs) -> 'pd.DataFrame' (inherited)

      Reads report data from CSV files generated by the simulation.

Parameters:
-----------
``report_names``: Union[str, list]
    Name or list names of report tables to read. These should match the
    report model names in the simulation output.

Returns:
--------
``pd.DataFrame``
    Concatenated DataFrame containing the data from the specified reports.

Raises:
-------
``ValueError``
    If any of the requested report names are not found in the available tables.

``RuntimeError``
    If the simulation has not been ``run`` successfully before attempting to read data.

Example::

  from apsimNGpy.core.apsim import ApsimModel
  model = ApsimModel(model= 'Maize') # replace with your path to the apsim template model
  ``model.run()`` # if we are going to use get_simulated_output, no to need to provide the report name in ``run()`` method
  df = model.get_simulated_output(report_names = ["Report"])
  print(df)
    SimulationName  SimulationID  CheckpointID  ... Maize.Total.Wt     Yield   Zone
 0     Simulation             1             1  ...       1728.427  8469.616  Field
 1     Simulation             1             1  ...        920.854  4668.505  Field
 2     Simulation             1             1  ...        204.118   555.047  Field
 3     Simulation             1             1  ...        869.180  3504.000  Field
 4     Simulation             1             1  ...       1665.475  7820.075  Field
 5     Simulation             1             1  ...       2124.740  8823.517  Field
 6     Simulation             1             1  ...       1235.469  3587.101  Field
 7     Simulation             1             1  ...        951.808  2939.152  Field
 8     Simulation             1             1  ...       1986.968  8379.435  Field
 9     Simulation             1             1  ...       1689.966  7370.301  Field
 [10 rows x 16 columns]

   .. method:: apsimNGpy.core.apsim.ApsimModel.run(self, report_name: 'Union[tuple, list, str]' = None, simulations: 'Union[tuple, list]' = None, clean_up: 'bool' = True, verbose: 'bool' = False, **kwargs) -> "'CoreModel'" (inherited)

      Run ``APSIM`` model simulations.

 Parameters
 ----------
 ``report_name`` : Union[tuple, list, str], optional
     Defaults to APSIM default Report Name if not specified.
     - If iterable, all report tables are read and aggregated into one DataFrame.
     - If None, runs without collecting database results.
     - If str, a single DataFrame is returned.

 ``simulations`` : Union[tuple, list], optional
     List of simulation names to run. If None, runs all simulations.

 ``clean_up``: bool, optional
     If True, removes the existing database before running.

 ``verbose``: bool, optional
     If True, enables verbose output for debugging. The method continues with debugging info anyway if the run was unsuccessful

 ``kwargs``: dict
     Additional keyword arguments, e.g., to_csv=True, use this flag to correct results from
     a csv file directly stored at the location of the running apsimx file.

 Warning:
 --------------
 In my experience with Models.exe, CSV outputs are not always overwritten; after edits, stale results can persist. Proceed with caution.


 Returns
 -------
 ``CoreModel``
     Instance of the class CoreModel.
``RuntimeError``
     Raised if the ``APSIM`` run is unsuccessful. Common causes include ``missing meteorological files``,
     mismatched simulation ``start`` dates with ``weather`` data, or other ``configuration issues``.

Example:

Instantiate an ``apsimNGpy.core.apsim.ApsimModel`` object and run::

       from apsimNGpy.core.apsim import ApsimModel
       model = ApsimModel(model= 'Maize')# replace with your path to the apsim template model
       model.run(report_name = "Report")

   .. method:: apsimNGpy.core.apsim.ApsimModel.rename_model(self, model_type, *, old_name, new_name) (inherited)

      Renames a model within the APSIM simulation tree.

This method searches for a model of the specified type and current name,
then updates its name to the new one provided. After renaming, it saves
the updated simulation file to enforce the changes.

Parameters
----------
model_type : str
    The type of the model to rename (e.g., "Manager", "Clock", etc.).
old_name : str
    The current name of the model to be renamed.
new_name : str
    The new name to assign to the model.

Returns
-------
self : object
    Returns the modified object to allow for method chaining.

Raises
------
ValueError
    If the model of the specified type and name is not found.

.. Note::

    This method uses ``get_or_check_model`` with action='get' to locate the model,
    and then updates the model's `Name` attribute. ``save()`` is called
    immediately after to apply and enfoce the change.

Example::
   from apsimNGpy.core.apsim import ApsimModel
   model = ApsimModel(model = 'Maize')
   model.rename_model(model_class="Simulation", old_name ='Simulation', new_name='my_simulation')
   # check if it has been successfully renamed
   model.inspect_model(model_class='Simulation', fullpath = False)
   ['my_simulation']
   # The alternative is to use model.inspect_file to see your changes
   model.inspect_file()

   .. method:: apsimNGpy.core.apsim.ApsimModel.clone_model(self, model_type, model_name, adoptive_parent_type, rename=None, adoptive_parent_name=None) (inherited)

      Clone an existing  ``model`` and move it to a specified parent within the simulation structure.
The function modifies the simulation structure by adding the cloned model to the ``designated parent``.

This function is useful when a model instance needs to be duplicated and repositioned in the ``APSIM`` simulation
hierarchy without manually redefining its structure.

Parameters:
----------
``model_class`` : Models
    The type of the model to be cloned, e.g., `Models.Simulation` or `Models.Clock`.
``model_name`` : str
    The unique identification name of the model instance to be cloned, e.g., `"clock1"`.
``adoptive_parent_type`` : Models
    The type of the new parent model where the cloned model will be placed.
``rename`` : str, optional
    The new name for the cloned model. If not provided, the clone will be renamed using
    the original name with a `_clone` suffix.
``adoptive_parent_name``: str, optional
    The name of the parent model where the cloned model should be moved. If not provided,
    the model will be placed under the default parent of the specified type.
``in_place``: bool, optional
    If ``True``, the cloned model remains in the same location but is duplicated. Defaults to ``False``.

Returns:
-------
None


Example:
-------
 Create a cloned version of `"clock1"` and place it under `"Simulation"` with the new name ``"new_clock`"`::

    from apsimNGpy.core.apsim import ApsimModel
    model = ApsimModel('Maize')
    model.clone_model('Models.Clock', "clock1", 'Models.Simulation', rename="new_clock",adoptive_parent_type= 'Models.Core.Simulations', adoptive_parent_name="Simulation")

   .. method:: apsimNGpy.core.apsim.ApsimModel.find_model(model_name: 'str') (inherited)

      Find a model from the Models namespace and return its path.

Args:
    model_name (str): The name of the model to find.
    model_namespace (object, optional): The root namespace (defaults to Models).
    path (str, optional): The accumulated path to the model.

Returns:
    str: The full path to the model if found, otherwise None.

Example::

     from apsimNGpy import core  # doctest:
     model =core.base_data.load_default_simulations(crop = "Maize")
     model.find_model("Weather")  # doctest: +SKIP
     'Models.Climate.Weather'
     model.find_model("Clock")  # doctest: +SKIP
     'Models.Clock'

   .. method:: apsimNGpy.core.apsim.ApsimModel.add_model(self, model_type, adoptive_parent, rename=None, adoptive_parent_name=None, verbose=False, source='Models', source_model_name=None, override=True, **kwargs) (inherited)

      Adds a model to the Models Simulations namespace.

Some models are restricted to specific parent models, meaning they can only be added to compatible models.
For example, a Clock model cannot be added to a Soil model.

Args:
    ``model_class`` (str or Models object): The type of model to add, e.g., `Models.Clock` or just `"Clock"`. if the APSIM Models namespace is exposed to the current script, then model_class can be Models.Clock without strings quotes

    ``rename`` (str): The new name for the model.

    ``adoptive_parent`` (Models object): The target parent where the model will be added or moved e.g ``Models.Clock`` or ``Clock`` as string all are valid

    ``adoptive_parent_name`` (Models object, optional): Specifies the parent name for precise location. e.g ``Models.Core.Simulation`` or ``Simulations`` all are valid

    ``source`` (Models, str, CoreModel, ApsimModel object): ``defaults`` to Models namespace, implying a fresh non modified model.
    The source can be an existing Models or string name to point to one fo the default model example, which we can extract the model

    ``override`` (bool, optional): defaults to `True`. When `True` (recomended) it delete for any model with same name and type at the suggested parent location before adding the new model
    if ``False`` and proposed model to be added exists at the parent location, ``APSIM`` automatically generates a new name for the newly added model. This is not recommended.
Returns:
    None: ``Models`` are modified in place, so models retains the same reference.

.. caution::
    Added models from ``Models namespace`` are initially empty. Additional configuration is required to set parameters.
    For example, after adding a Clock module, you must set the start and end dates.

Example::

    from apsimNGpy import core
    from apsimNGpy.core.core import Models

    model = core.base_data.load_default_simulations(crop="Maize")

    model.remove_model(Models.Clock)  # first delete the model
    model.add_model(Models.Clock, adoptive_parent=Models.Core.Simulation, rename='Clock_replaced', verbose=False)

    model.add_model(model_class=Models.Core.Simulation, adoptive_parent=Models.Core.Simulations, rename='Iowa')

    model.preview_simulation()  # doctest: +SKIP

    model.add_model(
        Models.Core.Simulation,
        adoptive_parent='Simulations',
        rename='soybean_replaced',
        source='Soybean')  # basically adding another simulation from soybean to the maize simulation

   .. method:: apsimNGpy.core.apsim.ApsimModel.detect_model_type(self, model_instance: 'Union[str, Models]') (inherited)

      Detects the model type from a given APSIM model instance or path string.

   .. method:: apsimNGpy.core.apsim.ApsimModel.edit_model_by_path(self, path: 'str', **kwargs) (inherited)

      Edit a model component located by an APSIM path, dispatching to type-specific editors.

This function resolves a node under ``self.Simulations`` using an APSIM path, then
edits that node by delegating to the appropriate editor based on the node’s runtime
type. It supports common APSIM NG components (e.g., Weather, Manager, Cultivar, Clock,
Soil subcomponents, Report, SurfaceOrganicMatter). Unsupported types raise
:class:`NotImplementedError`.

Resolution strategy
-------------------
1. Try ``self.Simulations.FindByPath(path)``.
2. If unavailable (older APIs), fall back to :func:`get_node_by_path(self.Simulations, path)`.
3. Extract the concrete model instance from either ``.Value`` or, if absent, attempts
   to unwrap via ``.Model`` and cast to known APSIM types with
   :class:`CastHelper.CastAs[T]`. If casting fails, a :class:`ValueError` is raised.

Parameters
----------
path : str
    APSIM path to a target node under ``self.Simulations`` (e.g.,
    ``'[Simulations].Ames.Maize.Weather'`` or similar canonical path).
**kwargs
    Keyword arguments controlling the edit. The keys accepted depend on the
    resolved component type (see **Type-specific editing** below). The following
    special keys are intercepted and *not* forwarded:
    - ``simulations`` / ``simulation`` : selector(s) used for cultivar edits
      and other multi-simulation operations; forwarded where applicable.
    - ``verbose`` : bool, optional; enables additional logging in some editors.

Type-specific editing
---------------------
The function performs a structural match on the resolved model type and dispatches to
the corresponding private helper or inline routine:

- :class:`Models.Climate.Weather`
  Calls ``self._set_weather_path(values, param_values=kwargs, verbose=verbose)``.
  Typical parameters include things such as a new weather file path (implementation-specific).

- :class:`Models.Manager`
  Validates that provided keys in ``kwargs`` match the manager script’s
  ``Parameters[i].Key`` set. On mismatch, raises :class:`ValueError`.
  On success, updates the corresponding parameter values by constructing
  ``KeyValuePair[String, String]`` entries. No extra keys are permitted.

- :class:`Models.PMF.Cultivar`
  Ensures cultivar replacements exist under ``Replacements`` (creates them if needed).
  Then calls ``_edit_in_cultivar(self, model_name=values.Name, simulations=simulations, param_values=kwargs, verbose=verbose)``.
  Expects cultivar-specific keys in ``kwargs`` (implementation-specific).

- :class:`Models.Clock`
  Calls ``self._set_clock_vars(values, param_values=kwargs)``. Typical keys:
  ``StartDate``, ``EndDate`` (exact names depend on your clock editor).

- Soil components
  ``Models.Soils.Physical`` | ``Models.Soils.Chemical`` | ``Models.Soils.Organic`` |
  ``Models.Soils.Water`` | ``Models.Soils.Solute``
  Delegates to ``self.replace_soils_values_by_path(node_path=path, **kwargs)``.
  Accepts property/value overrides appropriate to the soil table(s) addressed by ``path``.

- :class:`Models.Report`
  Calls ``self._set_report_vars(values, param_values=kwargs, verbose=verbose)``.
  Typical keys include columns/variables and event names (implementation-specific).

- :class:`Models.Surface.SurfaceOrganicMatter`
  Requires at least one of:
  ``'SurfOM', 'InitialCPR', 'InitialResidueMass', 'InitialCNR', 'IncorporatedP'``.
  If none supplied, raises: class:`ValueError`.
  Calls ``self._set_surface_organic_matter(values, param_values=kwargs, verbose=verbose)``.

Unsupported types
-----------------
If the resolved type does not match any of the above, a :class:`NotImplementedError`
is raised with the concrete type name.

Behavior of the method
------------------------
- Any of ``'simulation'``, ``'simulations'``, and ``'verbose'`` present in ``kwargs``
  are consumed by this function and not forwarded verbatim (except where explicitly used).
- For Manager edits, unknown parameter keys cause a hard failure (strict validation).
- For Cultivar edits, the function may mutate the model tree by creating necessary
  crop replacements under ``Replacements`` if missing.

Returns
-------
Self
    The same model/manager instance (to allow method chaining).

Raises
------
ValueError
    - If no node is found for ``path``.
    - If a Manager parameter key is invalid for the target Manager.
    - If a SurfaceOrganicMatter edit is requested with no supported keys.
    - If a model is un castable or unsupported for this method.
AttributeError
    If required APIs are missing on ``self.Simulations`` or resolved nodes.
NotImplementedError
    If the resolved node type has no implemented editor.
Exception
    Any error propagated by delegated helpers (e.g., file I/O, parsing).

Notes
-----
- **Path semantics: ** The exact path syntax should match what
  ``FindByPath`` or the fallback ``get_node_by_path`` expects in your APSIM build.
- **Type casting: ** When ``.Value`` is absent, the function attempts to unwrap from
  ``.Model`` and cast across a small set of known APSIM types using ``CastHelper``.
- **Non-idempotent operations: ** Some edits (e.g., cultivar replacements creation)
  may modify the model structure, not only values.
- **Concurrency: ** Edits mutate in-memory state; synchronize if calling from
  multiple threads/processes.

Examples
--------
Edit a Manager script parameter::

    model.edit_model_by_path(
        ".Simulations.Simulation.Field.Sow using a variable rule",
        verbose=True,
        Population =10)

Point a Weather component to a new ``.met`` file::

    model.edit_model_by_path(
        path='.Simulations.Simulation.Weather'
        FileName="data/weather/Ames_2020.met"
    )

Change Clock dates::

    model.edit_model_by_path(
       ".Simulations.Simulation.Clock",
        StartDate="2020-01-01",
        EndDate="2020-12-31"
    )

Update soil water properties at a specific path::

    model.edit_model_by_path(
        ".Simulations.Simulation.Field.Soil.Physical",
        LL15="[0.26, 0.18, 0.10, 0.12]",
    )

Apply cultivar edits across selected simulations::

    model.edit_model_by_path(".Simulations.Simulation.Field.Maize.CultivarFolder.mh18",
        simulations=("Sim_A", "Sim_B"),
        verbose=True,
        Phenology.EmergencePhase.Photoperiod="Short",
    )

   .. method:: apsimNGpy.core.apsim.ApsimModel.edit_model(self, model_type: 'str', model_name: 'str', simulations: 'Union[str, list]' = 'all', verbose=False, **kwargs) (inherited)

      Modify various APSIM model components by specifying the model type and name across given simulations.

Parameters
----------
``model_class``: str
    Type of the model component to modify (e.g., 'Clock', 'Manager', 'Soils.Physical', etc.).

``simulations``: Union[str, list], optional
    A simulation name or list of simulation names in which to search. Defaults to all simulations in the model.

``model_name``: str
    Name of the model instance to modify.
``cachit``: bool, optional
   used to cache results for model selection. Defaults to False. Important during repeated calls, like in optimization.
   please do not cache, when you expect to make model adjustment, such as adding new child nodes

``cache_size``: int, optional
   maximum number of caches that can be made to avoid memory leaks in case cacheit is true. Defaults to 300

``**kwargs``: dict
    Additional keyword arguments specific to the model type. These vary by component:

    - ``Weather``:
        - ``weather_file`` (str): Path to the weather ``.met`` file.

    - ``Clock``:
        - Date properties such as ``Start`` and ``End`` in ISO format (e.g., '2021-01-01').

    - ``Manager``:
        - Variables to update in the Manager script using `update_mgt_by_path`.

    - ``Soils.Physical | Soils.Chemical | Soils.Organic | Soils.Water:``
        - Variables to replace using ``replace_soils_values_by_path``.

    Valid ``parameters`` are shown below;

    +------------------+--------------------------------------------------------------------------------------------------------------------------------------+
    | Soil Model Type  | **Supported key word arguments**                                                                                                     |
    +==================+======================================================================================================================================+
    | Physical         | AirDry, BD, DUL, DULmm, Depth, DepthMidPoints, KS, LL15, LL15mm, PAWC, PAWCmm, SAT, SATmm, SW, SWmm, Thickness, ThicknessCumulative  |
    +------------------+--------------------------------------------------------------------------------------------------------------------------------------+
    | Organic          | CNR, Carbon, Depth, FBiom, FInert, FOM, Nitrogen, SoilCNRatio, Thickness                                                             |
    +------------------+--------------------------------------------------------------------------------------------------------------------------------------+
    | Chemical         | Depth, PH, Thickness                                                                                                                 |
    +------------------+--------------------------------------------------------------------------------------------------------------------------------------+

    - ``Report``:
        - ``report_name`` (str): Name of the report model (optional depending on structure).
        - ``variable_spec`` (list[str] or str): Variables to include in the report.
        - ``set_event_names`` (list[str], optional): Events that trigger the report.

    - ``Cultivar``:
        - ``commands`` (str): APSIM path to the cultivar parameter to update.
        - ``values`` (Any): Value to assign.
        - ``cultivar_manager`` (str): Name of the Manager script managing the cultivar, which must contain the `CultivarName` parameter. Required to propagate updated cultivar values, as APSIM treats cultivars as read-only.

.. warning::

    ValueError
        If the model instance is not found, required kwargs are missing, or `kwargs` is empty.
    NotImplementedError
        If the logic for the specified `model_class` is not implemented.

Examples::

    from apsimNGpy.core.apsim import ApsimModel
    model = ApsimModel(model='Maize')

Example of how to edit a cultivar model::

    model.edit_model(model_class='Cultivar',
         simulations='Simulation',
         commands='[Phenology].Juvenile.Target.FixedValue',
         values=256,
         model_name='B_110',
         new_cultivar_name='B_110_edited',
         cultivar_manager='Sow using a variable rule')

Edit a soil organic matter module::

    model.edit_model(
         model_class='Organic',
         simulations='Simulation',
         model_name='Organic',
         Carbon=1.23)

Edit multiple soil layers::

    model.edit_model(
         model_class='Organic',
         simulations='Simulation',
         model_name='Organic',
         Carbon=[1.23, 1.0])

Example of how to edit solute models::

   model.edit_model(
         model_class='Solute',
         simulations='Simulation',
         model_name='NH4',
         InitialValues=0.2)
   model.edit_model(
        model_class='Solute',
        simulations='Simulation',
        model_name='Urea',
        InitialValues=0.002)

Edit a manager script::

   model.edit_model(
        model_class='Manager',
        simulations='Simulation',
        model_name='Sow using a variable rule',
        population=8.4)

Edit surface organic matter parameters::

    model.edit_model(
        model_class='SurfaceOrganicMatter',
        simulations='Simulation',
        model_name='SurfaceOrganicMatter',
        InitialResidueMass=2500)

    model.edit_model(
        model_class='SurfaceOrganicMatter',
        simulations='Simulation',
        model_name='SurfaceOrganicMatter',
        InitialCNR=85)

Edit Clock start and end dates::

    model.edit_model(
        model_class='Clock',
        simulations='Simulation',
        model_name='Clock',
        Start='2021-01-01',
        End='2021-01-12')

Edit report _variables::

    model.edit_model(
        model_class='Report',
        simulations='Simulation',
        model_name='Report',
        variable_spec='[Maize].AboveGround.Wt as abw')

Multiple report _variables::

    model.edit_model(
        model_class='Report',
        simulations='Simulation',
        model_name='Report',
        variable_spec=[
        '[Maize].AboveGround.Wt as abw',
        '[Maize].Grain.Total.Wt as grain_weight'])
        @param simulations:

   .. method:: apsimNGpy.core.apsim.ApsimModel.add_report_variable(self, variable_spec: 'Union[list, str, tuple]', report_name: 'str' = None, set_event_names: 'Union[str, list]' = None) (inherited)

      This adds a report variable to the end of other _variables, if you want to change the whole report use change_report

Parameters
-------------------

``variable_spec``: (str, required): list of text commands for the report _variables e.g., '[Clock].Today as Date'

``param report_name``: (str, optional): name of the report variable if not specified the first accessed report object will be altered

``set_event_names`` (list or str, optional): A list of APSIM events that trigger the recording of _variables.
                                             Defaults to ['[Clock].EndOfYear'] if not provided.
:Returns:
    returns instance of apsimNGpy.core.core.apsim.ApsimModel or apsimNGpy.core.core.apsim.CoreModel
   raises an erros if a report is not found

Examples:

    >>> from apsimNGpy.core.apsim import ApsimModel
    >>> model = ApsimModel('Maize')
    >>> model.add_report_variable(variable_spec = '[Clock].Today as Date', report_name = 'Report')
    # inspct the report
    >>> model.inspect_model_parameters(model_type='Models.Report', model_name='Report')
    {'EventNames': ['[Maize].Harvesting'],
         'VariableNames': ['[Clock].Today',
          '[Maize].Phenology.CurrentStageName',
          '[Maize].AboveGround.Wt',
          '[Maize].AboveGround.N',
          '[Maize].Grain.Total.Wt*10 as Yield',
          '[Maize].Grain.Wt',
          '[Maize].Grain.Size',
          '[Maize].Grain.NumberFunction',
          '[Maize].Grain.Total.Wt',
          '[Maize].Grain.N',
          '[Maize].Total.Wt',
          '[Clock].Today as Date']}
The new report variable is appended at the end of the existing ones

   .. method:: apsimNGpy.core.apsim.ApsimModel.remove_report_variable(self, variable_spec: 'Union[list, tuple, str]', report_name: 'str | None' = None) (inherited)

      Remove one or more variable expressions from an APSIM Report component.

Parameters
----------
variable_spec : str | list[str] | tuple[str, ...]
    Variable expression(s) to remove, e.g. ``"[Clock].Today"`` or
    ``"[Clock].Today as Date"``. You may pass a single string or a list/tuple.
    Matching is done by exact text **after whitespace normalization**
    (consecutive spaces collapsed), so minor spacing differences are tolerated.
report_name : str, optional
    Name of the Report component to modify. If ``None``, the default
    resolver (``self._get_report``) is used to locate the target report.

Returns
-------
list[str]
    The updated list of variable expressions remaining in the report
    (in original order, without duplicates).

Notes
-----
- Variables not present are ignored (no error raised).
- Order is preserved; duplicates are removed.
- The model is saved at the end of this call.

Examples
--------
>>> model= CoreModel('Maize')
>>> model.add_report_variable(variable_spec='[Clock].Today as Date', report_name='Report')
>>> model.inspect_model_parameters('Models.Report', 'Report')['VariableNames']
['[Clock].Today',
 '[Maize].Phenology.CurrentStageName',
 '[Maize].AboveGround.Wt',
 '[Maize].AboveGround.N',
 '[Maize].Grain.Total.Wt*10 as Yield',
 '[Maize].Grain.Wt',
 '[Maize].Grain.Size',
 '[Maize].Grain.NumberFunction',
 '[Maize].Grain.Total.Wt',
 '[Maize].Grain.N',
 '[Maize].Total.Wt',
 '[Clock].Today as Date']
>>> model.remove_report_variable(variable_spec='[Clock].Today as Date', report_name='Report')
>>> model.inspect_model_parameters('Models.Report', 'Report')['VariableNames']
['[Clock].Today',
 '[Maize].Phenology.CurrentStageName',
 '[Maize].AboveGround.Wt',
 '[Maize].AboveGround.N',
 '[Maize].Grain.Total.Wt*10 as Yield',
 '[Maize].Grain.Wt',
 '[Maize].Grain.Size',
 '[Maize].Grain.NumberFunction',
 '[Maize].Grain.Total.Wt',
 '[Maize].Grain.N',
 '[Maize].Total.Wt']

   .. method:: apsimNGpy.core.apsim.ApsimModel.remove_model(self, model_class: 'Models', model_name: 'str' = None) (inherited)

      Removes a model from the APSIM Models.Simulations namespace.

 Parameters
 ----------
 ``model_class`` : Models
     The type of the model to remove (e.g., `Models.Clock`). This parameter is required.

 ``model_name`` : str, optional
     The name of the specific model instance to remove (e.g., `"Clock"`). If not provided, all models of the
     specified type may be removed.

 Returns:

    None

 Example::

        from apsimNGpy import core
        from apsimNGpy.core.core import Models
        model = core.base_data.load_default_simulations(crop = 'Maize')
        model.remove_model(Models.Clock) #deletes the clock node
        model.remove_model(Models.Climate.Weather) #deletes the weather node

   .. method:: apsimNGpy.core.apsim.ApsimModel.move_model(self, model_type: 'Models', new_parent_type: 'Models', model_name: 'str' = None, new_parent_name: 'str' = None, verbose: 'bool' = False, simulations: 'Union[str, list]' = None) (inherited)

      Args:

- ``model_class`` (Models): type of model tied to Models Namespace

- ``new_parent_type``: new model parent type (Models)

- ``model_name``:name of the model e.g., Clock, or Clock2, whatever name that was given to the model

-  ``new_parent_name``: what is the new parent names =Field2, this field is optional but important if you have nested simulations

Returns:

  returns instance of apsimNGpy.core.core.apsim.ApsimModel or apsimNGpy.core.core.apsim.CoreModel

   .. method:: apsimNGpy.core.apsim.ApsimModel.replicate_file(self, k: 'int', path: 'os.PathLike' = None, suffix: 'str' = 'replica') (inherited)

      Replicates a file ``k`` times.

If a ``path`` is specified, the copies will be placed in that dir_path with incremented filenames.

If no path is specified, copies are created in the same dir_path as the original file, also with incremented filenames.

Parameters:
- self: The core.api.CoreModel object instance containing 'path' attribute pointing to the file to be replicated.

- k (int): The number of copies to create.

- path (str, optional): The dir_path where the replicated files will be saved. Defaults to None, meaning the
same dir_path as the source file.

- suffix (str, optional): a suffix to attached with the copies. Defaults to "replicate"


Returns:
- A list of paths to the newly created files if get_back_list is True else a generator is returned.

   .. method:: apsimNGpy.core.apsim.ApsimModel.get_crop_replacement(self, Crop) (inherited)

      :param Crop: crop to get the replacement
:return: System.Collections.Generic.IEnumerable APSIM plant object

   .. method:: apsimNGpy.core.apsim.ApsimModel.inspect_model_parameters(self, model_type: 'Union[Models, str]', model_name: 'str', simulations: 'Union[str, list]' = <UserOptionMissing>, parameters: 'Union[list, set, tuple, str]' = 'all', **kwargs) (inherited)

      Inspect the input parameters of a specific ``APSIM`` model type instance within selected simulations.

This method consolidates functionality previously spread across ``examine_management_info``, ``read_cultivar_params``, and other inspectors,
allowing a unified interface for querying parameters of interest across a wide range of APSIM models.

Parameters
----------
``model_class``: str
    The name of the model class to inspect (e.g., 'Clock', 'Manager', 'Physical', 'Chemical', 'Water', 'Solute').
    Shorthand names are accepted (e.g., 'Clock', 'Weather') as well as fully qualified names (e.g., 'Models.Clock', 'Models.Climate.Weather').

``simulations``: Union[str, list]
    A single simulation name or a list of simulation names within the APSIM context to inspect.

``model_name``: str
    The name of the specific model instance within each simulation. For example, if `model_class='Solute'`,
    `model_name` might be 'NH4', 'Urea', or another solute name.

``parameters``: Union[str, set, list, tuple], optional
    A specific parameter or a collection of parameters to inspect. Defaults to `'all'`, in which case all accessible attributes are returned.
    For layered models like Solute, valid parameters include `Depth`, `InitialValues`, `SoluteBD`, `Thickness`, etc.

``kwargs``: dict
    Reserved for future compatibility; currently unused.

``Returns``
----------
    Union[dict, list, pd.DataFrame, Any]
    The format depends on the model type:
    ``Weather``: file path(s) as string(s)

- ``Clock``: dictionary with start and end datetime objects (or a single datetime if only one is requested).

- ``Manager``: dictionary of script parameters.

- ``Soil-related`` models: pandas DataFrame of layered values.

- ``Report``: dictionary with `VariableNames` and `EventNames`.

- ``Cultivar``: dictionary of parameter strings.

Raises
------
``ValueError``
    If the specified model or simulation is not found or arguments are invalid.

``NotImplementedError``
    If the model type is unsupported by the current interface.


Requirements
--------------
- APSIM Next Generation Python bindings (`apsimNGpy`)
- Python 3.10+

Examples::

   from apsimNGpy.core.core import CoreModel
   model_instance = CoreModel('Maize')

   or:
   from apsimNGpy.core.apsim import ApsimModel
   model_instance = ApsimModel('Maize')

Inspect full soil ``Organic`` profile::

    model_instance.inspect_model_parameters('Organic', simulations='Simulation', model_name='Organic')
       CNR  Carbon      Depth  FBiom  ...         FOM  Nitrogen  SoilCNRatio  Thickness
    0  12.0    1.20      0-150   0.04  ...  347.129032     0.100         12.0      150.0
    1  12.0    0.96    150-300   0.02  ...  270.344362     0.080         12.0      150.0
    2  12.0    0.60    300-600   0.02  ...  163.972144     0.050         12.0      300.0
    3  12.0    0.30    600-900   0.02  ...   99.454133     0.025         12.0      300.0
    4  12.0    0.18   900-1200   0.01  ...   60.321981     0.015         12.0      300.0
    5  12.0    0.12  1200-1500   0.01  ...   36.587131     0.010         12.0      300.0
    6  12.0    0.12  1500-1800   0.01  ...   22.191217     0.010         12.0      300.0
    [7 rows x 9 columns]

Inspect soil ``Physical`` profile::

    model_instance.inspect_model_parameters('Physical', simulations='Simulation', model_name='Physical')
        AirDry        BD       DUL  ...        SWmm Thickness  ThicknessCumulative
    0  0.130250  1.010565  0.521000  ...   78.150033     150.0                150.0
    1  0.198689  1.071456  0.496723  ...   74.508522     150.0                300.0
    2  0.280000  1.093939  0.488438  ...  146.531282     300.0                600.0
    3  0.280000  1.158613  0.480297  ...  144.089091     300.0                900.0
    4  0.280000  1.173012  0.471584  ...  141.475079     300.0               1200.0
    5  0.280000  1.162873  0.457071  ...  137.121171     300.0               1500.0
    6  0.280000  1.187495  0.452332  ...  135.699528     300.0               1800.0
    [7 rows x 17 columns]

Inspect soil ``Chemical`` profile::

    model_instance.inspect_model_parameters('Chemical', simulations='Simulation', model_name='Chemical')
       Depth   PH  Thickness
    0      0-150  8.0      150.0
    1    150-300  8.0      150.0
    2    300-600  8.0      300.0
    3    600-900  8.0      300.0
    4   900-1200  8.0      300.0
    5  1200-1500  8.0      300.0
    6  1500-1800  8.0      300.0

Inspect one or more specific parameters::

    model_instance.inspect_model_parameters('Organic', simulations='Simulation', model_name='Organic', parameters='Carbon')
      Carbon
    0    1.20
    1    0.96
    2    0.60
    3    0.30
    4    0.18
    5    0.12
    6    0.12

Inspect more than one specific properties::

    model_instance.inspect_model_parameters('Organic', simulations='Simulation', model_name='Organic', parameters=['Carbon', 'CNR'])
       Carbon   CNR
    0    1.20  12.0
    1    0.96  12.0
    2    0.60  12.0
    3    0.30  12.0
    4    0.18  12.0
    5    0.12  12.0
    6    0.12  12.0

Inspect Report module attributes::

     model_instance.inspect_model_parameters('Report', simulations='Simulation', model_name='Report')
     {'EventNames': ['[Maize].Harvesting'],
    'VariableNames': ['[Clock].Today',
    '[Maize].Phenology.CurrentStageName',
    '[Maize].AboveGround.Wt',
    '[Maize].AboveGround.N',
    '[Maize].Grain.Total.Wt*10 as Yield',
    '[Maize].Grain.Wt',
    '[Maize].Grain.Size',
    '[Maize].Grain.NumberFunction',
    '[Maize].Grain.Total.Wt',
    '[Maize].Grain.N',
    '[Maize].Total.Wt']}

Specify only EventNames:

   model_instance.inspect_model_parameters('Report', simulations='Simulation', model_name='Report', parameters='EventNames')
   {'EventNames': ['[Maize].Harvesting']}

Inspect a weather file path::

     model_instance.inspect_model_parameters('Weather', simulations='Simulation', model_name='Weather')
    '%root%/Examples/WeatherFiles/AU_Dalby.met'

Inspect manager script parameters::

    model_instance.inspect_model_parameters('Manager',
    simulations='Simulation', model_name='Sow using a variable rule')
    {'Crop': 'Maize',
    'StartDate': '1-nov',
    'EndDate': '10-jan',
    'MinESW': '100.0',
    'MinRain': '25.0',
    'RainDays': '7',
    'CultivarName': 'Dekalb_XL82',
    'SowingDepth': '30.0',
    'RowSpacing': '750.0',
    'Population': '10'}
Inspect manager script by specifying one or more parameters::

    model_instance.inspect_model_parameters('Manager',
    simulations='Simulation', model_name='Sow using a variable rule',
    parameters='Population')
    {'Population': '10'}

Inspect cultivar parameters::

    model_instance.inspect_model_parameters('Cultivar',
    simulations='Simulation', model_name='B_110') # lists all path specifications for B_110 parameters abd their values
    model_instance.inspect_model_parameters('Cultivar', simulations='Simulation',
    model_name='B_110', parameters='[Phenology].Juvenile.Target.FixedValue')
    {'[Phenology].Juvenile.Target.FixedValue': '210'}

Inspect surface organic matter module::

    model_instance.inspect_model_parameters('Models.Surface.SurfaceOrganicMatter',
    simulations='Simulation', model_name='SurfaceOrganicMatter')
    {'NH4': 0.0,
     'InitialResidueMass': 500.0,
     'StandingWt': 0.0,
     'Cover': 0.0,
     'LabileP': 0.0,
     'LyingWt': 0.0,
     'InitialCNR': 100.0,
     'P': 0.0,
     'InitialCPR': 0.0,
     'SurfOM': <System.Collections.Generic.List[SurfOrganicMatterType] object at 0x000001DABDBB58C0>,
     'C': 0.0,
     'N': 0.0,
     'NO3': 0.0}

Inspect a few parameters as needed::

    model_instance.inspect_model_parameters('Models.Surface.SurfaceOrganicMatter', simulations='Simulation',
    ... model_name='SurfaceOrganicMatter', parameters={'InitialCNR', 'InitialResidueMass'})
    {'InitialCNR': 100.0, 'InitialResidueMass': 500.0}

Inspect a clock::

     model_instance.inspect_model_parameters('Clock', simulations='Simulation', model_name='Clock')
     {'End': datetime.datetime(2000, 12, 31, 0, 0),
     'Start': datetime.datetime(1990, 1, 1, 0, 0)}

Inspect a few Clock parameters as needed::

    model_instance.inspect_model_parameters('Clock', simulations='Simulation',
    model_name='Clock', parameters='End')
    datetime.datetime(2000, 12, 31, 0, 0)

Access specific components of the datetime object e.g., year, month, day, hour, minute::

      model_instance.inspect_model_parameters('Clock', simulations='Simulation',
      model_name='Clock', parameters='Start').year # gets the start year only
      1990

Inspect solute models::

    model_instance.inspect_model_parameters('Solute', simulations='Simulation', model_name='Urea')
           Depth  InitialValues  SoluteBD  Thickness
    0      0-150            0.0  1.010565      150.0
    1    150-300            0.0  1.071456      150.0
    2    300-600            0.0  1.093939      300.0
    3    600-900            0.0  1.158613      300.0
    4   900-1200            0.0  1.173012      300.0
    5  1200-1500            0.0  1.162873      300.0
    6  1500-1800            0.0  1.187495      300.0

    model_instance.inspect_model_parameters('Solute', simulations='Simulation', model_name='NH4',
    parameters='InitialValues')
        InitialValues
    0 0.1
    1 0.1
    2 0.1
    3 0.1
    4 0.1
    5 0.1
    6 0.1

   .. method:: apsimNGpy.core.apsim.ApsimModel.inspect_model_parameters_by_path(self, path, *, parameters: 'Union[list, set, tuple, str]' = None) (inherited)

      Inspect and extract parameters from a model component specified by its path.

Parameters
----------
path : str
    A string path to the model component within the APSIM simulation hierarchy.

parameters : list, set, tuple, or str, optional
    One or more parameter names to extract from the model. If None, attempts to extract all available parameters.

Returns
-------
dict
    A dictionary of parameter names and their values.

.. note::

    This method wraps the `extract_value` utility to fetch parameters from a model component
    identified by a path string. Internally, it:
    1. Finds the model object using the given path.
    2. Extracts and returns the requested parameter(s).

   .. method:: apsimNGpy.core.apsim.ApsimModel.edit_cultivar(self, *, CultivarName: 'str', commands: 'str', values: 'Any', **kwargs) (inherited)

      @deprecated
Edits the parameters of a given cultivar. we don't need a simulation name for this unless if you are defining it in the
manager section, if that it is the case, see update_mgt.

Requires:
   required a replacement for the crops

Args:

  - CultivarName (str, required): Name of the cultivar (e.g., 'laila').

  - variable_spec (str, required): A strings representing the parameter paths to be edited.

Returns: instance of the class CoreModel or ApsimModel

Example::

    ('[Grain].MaximumGrainsPerCob.FixedValue', '[Phenology].GrainFilling.Target.FixedValue')

  - values: values for each command (e.g., (721, 760)).

   .. method:: apsimNGpy.core.apsim.ApsimModel.update_cultivar(self, *, parameters: 'dict', simulations: 'Union[list, tuple]' = None, clear=False, **kwargs) (inherited)

      Update cultivar parameters

 Parameters
 ----------
``parameters`` (dict, required) dictionary of cultivar parameters to update.

``simulations``, optional
     List or tuples of simulation names to update if `None` update all simulations.

``clear`` (bool, optional)
     If `True` remove all existing parameters, by default `False`.

   .. method:: apsimNGpy.core.apsim.ApsimModel.recompile_edited_model(self, out_path: 'os.PathLike') (inherited)

      Args:
______________
``out_path``: os.PathLike object this method is called to convert the simulation object from ConverterReturnType to model like object

``return:`` self

   .. method:: apsimNGpy.core.apsim.ApsimModel.update_mgt_by_path(self, *, path: 'str', fmt='.', **kwargs) (inherited)

      Args:
_________________
``path``: complete node path to the script manager e.g. '.Simulations.Simulation.Field.Sow using a variable rule'

``fmt``: seperator for formatting the path e.g., ".". Other characters can be used with
 caution, e.g., / and clearly declared in fmt argument. If you want to use the forward slash, it will be '/Simulations/Simulation/Field/Sow using a variable rule', fmt = '/'

``kwargs``: Corresponding keyword arguments representing the paramters in the script manager and their values. Values is what you want
to change to; Example here ``Population`` =8.2, values should be entered with their corresponding data types e.g.,
 int, float, bool,str etc.

return: self

   .. method:: apsimNGpy.core.apsim.ApsimModel.replace_model_from(self, model, model_type: 'str', model_name: 'str' = None, target_model_name: 'str' = None, simulations: 'str' = None) (inherited)

      @deprecated and will be removed
function has not been maintained for a long time, use it at your own risk

Replace a model, e.g., a soil model with another soil model from another APSIM model.
The method assumes that the model to replace is already loaded in the current model and the same class as a source model.
e.g., a soil node to soil node, clock node to clock node, et.c

Args:
    ``model``: Path to the APSIM model file or a CoreModel instance.

    ``model_class`` (str): Class name (as string) of the model to replace (e.g., "Soil").

    ``model_name`` (str, optional): Name of the model instance to copy from the source model.
        If not provided, the first match is used.

    ``target_model_name`` (str, optional): Specific simulation name to target for replacement.
        Only used when replacing Simulation-level objects.

    ``simulations`` (str, optional): Simulation(s) to operate on. If None, applies to all.

Returns:
    self: To allow method chaining.

``Raises:``
    ``ValueError``: If ``model_class`` is "Simulations" which is not allowed for replacement.

   .. method:: apsimNGpy.core.apsim.ApsimModel.update_mgt(self, *, management: 'Union[dict, tuple]', simulations: '[list, tuple]' = <UserOptionMissing>, out: '[Path, str]' = None, reload: 'bool' = True, **kwargs) (inherited)

      Update management settings in the model. This method handles one management parameter at a time.

Parameters
----------
``management``: dict or tuple
    A dictionary or tuple of management parameters to update. The dictionary should have 'Name' as the key
    for the management script's name and corresponding values to update. Lists are not allowed as they are mutable
    and may cause issues with parallel processing. If a tuple is provided, it should be in the form (param_name, param_value).

``simulations``: list of str, optional
    List of simulation names to update. If `None`, updates all simulations. This is not recommended for large
    numbers of simulations as it may result in a high computational load.

``out``: str or pathlike, optional
    Path to save the edited model. If `None`, uses the default output path specified in `self.out_path` or
    `self.model_info.path`. No need to call `save_edited_file` after updating, as this method handles saving.

Returns
-------
self : CoreModel
    Returns the instance of the `CoreModel` class for method chaining.

Notes - Ensure that the ``management`` parameter is provided in the correct format to avoid errors. -
This method does not perform ``validation`` on the provided ``management`` dictionary beyond checking for key
existence. - If the specified management script or parameters do not exist, they will be ignored.

   .. method:: apsimNGpy.core.apsim.ApsimModel.preview_simulation(self) (inherited)

      Open the current simulation in the APSIM Next Gen GUI.

This first saves the in-memory simulation to ``self.path`` and then launches
the APSIM NG GUI (via: func:`get_apsim_bin_path`) so you can inspect the model
tree and make quick edits side-by-side.

Returns
-------
None
    This function is for its side effect (opening the GUI); it does not return a value.

Raises
------
FileNotFoundError
    If the file does not exist after ``save()``.
RuntimeError
    If the APSIM NG executable cannot be located or the GUI fails to start.

Notes
-----
**Important:** The file opened in the GUI is a *saved copy* of this Python object.
Changes made in the GUI are **not** propagated back to this instance. To continue
in Python with GUI edits, save in APSIM and re-load the file (e.g.,
``ApsimModel('gui_edited_file_path)').

Examples
--------
>>> model.preview_simulation()

   .. method:: apsimNGpy.core.apsim.ApsimModel.change_simulation_dates(self, start_date: 'str' = None, end_date: 'str' = None, simulations: 'Union[tuple, list]' = None) (inherited)

      Set simulation dates.

@deprecated and will be removed in future versions use: :func:`edit_method` isntead

Parameters
-----------------------

``start_date``: (str) optional
    Start date as string, by default ``None``.

``end_date``: str (str) optional.
    End date as string, by default ``None``.

``simulations`` (str), optional
    List of simulation names to update if ``None`` update all simulations.

.. note::

     one of the ``start_date`` or ``end_date`` parameters should at least not be None

raises assertion error if all dates are None

``return``: ``None``

Examples::


    >>> from apsimNGpy.core.base_data import load_default_simulations
    >>> model = load_default_simulations(crop='maize')
    >>> model.change_simulation_dates(start_date='2021-01-01', end_date='2021-01-12')
    >>> changed_dates = model.extract_dates #check if it was successful
    >>> print(changed_dates)
       {'Simulation': {'start': datetime.date(2021, 1, 1),
        'end': datetime.date(2021, 1, 12)}}

    .. tip::

        It is possible to target a specific simulation by specifying simulation name for this case the name is Simulations, so, it could appear as follows
         model.change_simulation_dates(start_date='2021-01-01', end_date='2021-01-12', simulation = 'Simulation')

   .. method:: apsimNGpy.core.apsim.ApsimModel.extract_start_end_years(self, simulations: 'str' = None) (inherited)

      Get simulation dates. deprecated

Parameters
----------
``simulations``: (str) optional
    List of simulation names to use if `None` get all simulations.

``Returns``
    Dictionary of simulation names with dates.

   .. method:: apsimNGpy.core.apsim.ApsimModel.replace_met_file(self, *, weather_file: 'Union[Path, str]', simulations=<UserOptionMissing>, **kwargs) -> "'Self'" (inherited)

      .. deprecated:: 0.**x**
   This helper will be removed in a future release. Prefer newer weather
   configuration utilities or set the ``FileName`` property on weather nodes
   directly.

Replace the ``FileName`` of every :class:`Models.Climate.Weather` node under one
or more simulations so they point to a new ``.met`` file.

This method traverses the APSIM NG model tree under each selected simulation and
updates the weather component(s) in-place. Version-aware traversal is used:

* If ``APSIM_VERSION_NO > BASE_RELEASE_NO`` **or**
  ``APSIM_VERSION_NO == GITHUB_RELEASE_NO``: use
  :func:`ModelTools.find_all_in_scope` to find
  :class:`Models.Climate.Weather` nodes.
* Otherwise: fall back to ``sim.FindAllDescendants[Models.Climate.Weather]()``.

Parameters
----------
weather_file : Union[pathlib.Path, str]
    Path to the ``.met`` file. May be absolute or relative to the current
    working directory. The path must exist at call time; otherwise a
    :class:`FileNotFoundError` is raised.
simulations : Any, optional
    Simulation selector forwarded to :meth:`find_simulations`. If left as
    ``MissingOption`` (default) (or if your implementation accepts ``None``),
    all simulations yielded by :meth:`find_simulations` are updated.
    Acceptable types depend on your :meth:`find_simulations` contract
    (e.g., iterable of names, single name, or sentinel).
**kwargs
    Ignored. Reserved for backward compatibility and future extensions.

Returns
-------
Self
    The current model/manager instance to support method chaining.

Raises
------
FileNotFoundError
    If ``weather_file`` does not exist.
Exception
    Any exception raised by :meth:`find_simulations` or underlying APSIM
    traversal utilities is propagated unchanged.

Side Effects
------------
Mutates the model by setting ``met.FileName = os.path.realpath(weather_file)``
for each matched :class:`Models.Climate.Weather` node.

Notes
-----
- **No-op safety:** If a simulation has no Weather nodes, that simulation
  is silently skipped.
- **Path normalization:** The stored path is the canonical real path
  (``os.path.realpath``).
- **Thread/process safety:** This operation mutates in-memory model state
  and is not inherently thread-safe. Coordinate external synchronization if
  calling concurrently.

Examples
--------
Update all simulations to use a local ``Ames.met``::

    model.replace_met_file(weather_file="data/weather/Ames.met")

Update only selected simulations::

    model.replace_met_file(
        weather_file=Path("~/wx/Boone.met").expanduser(),
        simulations=("Sim_A", "Sim_B")
    )

See Also
--------
find_simulations : Resolve and yield simulation objects by name/selector.
ModelTools.find_all_in_scope : Scope-aware traversal utility.
Models.Climate.Weather : APSIM NG weather component.

   .. method:: apsimNGpy.core.apsim.ApsimModel.get_weather_from_file(self, weather_file, simulations=None) -> "'self'" (inherited)

      Point targeted APSIM Weather nodes to a local ``.met`` file.

The function name mirrors the semantics of ``get_weather_from_web`` but sources the weather
from disk. If the provided path lacks the ``.met`` suffix, it is appended.
The file **must** exist on disk.

Parameters
----------
weather_file : str | Path
    Path (absolute or relative) to a ``.met`` file. If the suffix is missing,
    ``.met`` is appended. A ``FileNotFoundError`` is raised if the final path
    does not exist. The path is resolved to an absolute path to avoid ambiguity.
simulations : None | str | Iterable[str], optional
    Which simulations to update:
    - ``None`` (default): update **all** Weather nodes found under ``self.Simulations``.
    - ``str`` or iterable of names: only update Weather nodes within the named
      simulation(s). A ``ValueError`` is raised if a requested simulation has
      no Weather nodes.

Returns
-------
Self
    ``self`` (for method chaining).

Raises
------
FileNotFoundError
    If the resolved ``.met`` file does not exist.
ValueError
    If any requested simulation exists but contains no Weather nodes.

Side Effects
------------
Sets ``w.FileName`` for each targeted ``Models.Climate.Weather`` node to the
resolved path of ``weather_file``. The file is **not** copied; only the path
inside the APSIM document is changed.

Notes
-----
- APSIM resolves relative paths relative to the ``.apsimx`` file. Using an
  absolute path (the default here) reduces surprises across working directories.
- Replacement folders that contain Weather nodes are also updated when
  ``simulations`` is ``None`` (i.e., “update everything in scope”).

Examples
--------
Update all Weather nodes:

>>> model.get_weather_from_file("data/ames_2020.met")

Update only two simulations (suffix added automatically):

>>> model.get_weather_from_file("data/ames_2020", simulations=("SimA", "SimB"))# amke sure they exists

   .. method:: apsimNGpy.core.apsim.ApsimModel.get_weather_from_web(self, lonlat: 'tuple', start: 'int', end: 'int', simulations=<UserOptionMissing>, source='nasa', filename=None) (inherited)

      Replaces the weather (met) file in the model using weather data fetched from an online source. Internally, calls get_weather_from_file after downloading the weather

``lonlat``: ``tuple``
     A tuple containing the longitude and latitude coordinates.

``start``: int
      Start date for the weather data retrieval.

``end``: int
      End date for the weather data retrieval.

``simulations``: str | list[str] default is all or None list of simulations or a singular simulation
      name, where to place the weather data, defaults to None, implying ``all`` the available simulations

``source``: str default is 'nasa'
     Source of the weather data.

``filename``: str default is generated using the base name of the apsimx file in use, and the start and
        end years Name of the file to save the retrieved data. If None, a default name is generated.

``Returns: ``
 model object with the corresponding file replaced with the fetched weather data.

..code-block:: python

      from apsimNgpy.core.apsim import ApsimModel
      model = ApsimModel(model= "Maize")
      model.get_weather_from_web(lonlat = (-93.885490, 42.060650), start = 1990, end = 2001)

Changing weather data with non-matching start and end dates in the simulation will lead to RuntimeErrors.
To avoid this, first check the start and end date before proceeding as follows:

      >>> dt = model.inspect_model_parameters(model_class='Clock', model_name='Clock', simulations='Simulation')
      >>> start, end = dt['Start'].year, dt['End'].year
      # output: 1990, 2000

   .. method:: apsimNGpy.core.apsim.ApsimModel.show_met_file_in_simulation(self, simulations: 'list' = None) (inherited)

      Show weather file for all simulations

@deprecated: use inspect_model_parameters() instead

   .. method:: apsimNGpy.core.apsim.ApsimModel.change_report(self, *, command: 'str', report_name='Report', simulations=None, set_DayAfterLastOutput=None, **kwargs) (inherited)

      Set APSIM report _variables for specified simulations.

This function allows you to set the variable names for an APSIM report
in one or more simulations.

Parameters
----------
``command``: str
    The new report string that contains variable names.
``report_name``: str
    The name of the APSIM report to update defaults to Report.
``simulations``: list of str, optional
    A list of simulation names to update. If `None`, the function will
    update the report for all simulations.

Returns
-------
None

   .. method:: apsimNGpy.core.apsim.ApsimModel.extract_soil_physical(self, simulations: '[tuple, list]' = None) (inherited)

      Find physical soil

Parameters
----------
``simulation``, optional
    Simulation name, if `None` use the first simulation.
Returns
-------
    APSIM Models.Soils.Physical object

   .. method:: apsimNGpy.core.apsim.ApsimModel.extract_any_soil_physical(self, parameter, simulations: '[list, tuple]' = <UserOptionMissing>) (inherited)

      Extracts soil physical parameters in the simulation

Args::
    ``parameter`` (_string_): string e.g. DUL, SAT
    ``simulations`` (string, optional): Targeted simulation name. Defaults to None.
---------------------------------------------------------------------------
returns an array of the parameter values

   .. method:: apsimNGpy.core.apsim.ApsimModel.inspect_model(self, model_type: 'Union[str, Models]', fullpath=True, **kwargs) (inherited)

      Inspect the model types and returns the model paths or names.

When is it needed?
--------------------
 useful if you want to identify the paths or name of the model for further editing the model e.g., with the ``in edit_model`` method.

Parameters
--------------

model_class : type | str
    The APSIM model type to search for. You may pass either a class (e.g.,
    Models.Clock, Models.Manager) or a string. Strings can be short names
    (e.g., "Clock", "Manager") or fully qualified (e.g., "Models.Core.Simulation",
    "Models.Climate.Weather", "Models.Core.IPlant"). Please see from The list of classes
    or model types from the **Models** Namespace below. Red represents the modules, and this method
     will throw an error if only a module is supplied. The list constitutes the classes or
     model types under each module

    ``Models``:
      - Models.Clock
      - Models.Fertiliser
      - Models.Irrigation
      - Models.Manager
      - Models.Memo
      - Models.MicroClimate
      - Models.Operations
      - Models.Report
      - Models.Summary
    ``Models.Climate``:
      - Models.Climate.Weather
    ``Models.Core``:
      - Models.Core.Folder
      - Models.Core.Simulation
      - Models.Core.Simulations
      - Models.Core.Zone
    ``Models.Factorial``:
      - Models.Factorial.Experiment
      - Models.Factorial.Factors
      - Models.Factorial.Permutation
    ``Models.PMF``:
      - Models.PMF.Cultivar
      - Models.PMF.Plant
    ``Models.Soils``:
      - Models.Soils.Arbitrator.SoilArbitrator
      - Models.Soils.CERESSoilTemperature
      - Models.Soils.Chemical
      - Models.Soils.Nutrients.Nutrient
      - Models.Soils.Organic
      - Models.Soils.Physical
      - Models.Soils.Sample
      - Models.Soils.Soil
      - Models.Soils.SoilCrop
      - Models.Soils.Solute
      - Models.Soils.Water
    ``Models.Storage``:
      - Models.Storage.DataStore
    ``Models.Surface``:
      - Models.Surface.SurfaceOrganicMatter
    ``Models.WaterModel``:
      - Models.WaterModel.WaterBalance

fullpath : bool, optional (default: False)
    If False, return the model *name* only.
    If True, return the model’s *full path* relative to the Simulations root.

Returns
-------
list[str]
    A list of model names or full paths, depending on `fullpath`.

Examples::

     from apsimNGpy.core.apsim import ApsimModel
     from apsimNGpy.core.core import Models


load default ``maize`` module::

     model = ApsimModel('Maize')

Find the path to all the manager scripts in the simulation::

     model.inspect_model(Models.Manager, fullpath=True)
     [.Simulations.Simulation.Field.Sow using a variable rule', '.Simulations.Simulation.Field.Fertilise at
     sowing', '.Simulations.Simulation.Field.Harvest']

Inspect the full path of the Clock Model::

     model.inspect_model(Models.Clock) # gets the path to the Clock models
     ['.Simulations.Simulation.Clock']

Inspect the full path to the crop plants in the simulation::

     model.inspect_model(Models.Core.IPlant) # gets the path to the crop model
     ['.Simulations.Simulation.Field.Maize']

Or use the full string path as follows::

     model.inspect_model(Models.Core.IPlant, fullpath=False) # gets you the name of the crop Models
     ['Maize']
Get the full path to the fertilizer model::

     model.inspect_model(Models.Fertiliser, fullpath=True)
     ['.Simulations.Simulation.Field.Fertiliser']

The models from APSIM Models namespace are abstracted to use strings. All you need is to specify the name or the full path to the model enclosed in a stirng as follows::

     model.inspect_model('Clock') # get the path to the clock model
     ['.Simulations.Simulation.Clock']

Alternatively, you can do the following::

     model.inspect_model('Models.Clock')
     ['.Simulations.Simulation.Clock']

Repeat inspection of the plant model while using a ``string``::

     model.inspect_model('IPlant')
     ['.Simulations.Simulation.Field.Maize']

Inspect using the full model namespace path::

     model.inspect_model('Models.Core.IPlant')

What about the weather model?::

     model.inspect_model('Weather') # inspects the weather module
     ['.Simulations.Simulation.Weather']

Alternative::

     # or inspect using full model namespace path
     model.inspect_model('Models.Climate.Weather')
     ['.Simulations.Simulation.Weather']

Try finding the path to the cultivar model::

     model.inspect_model('Cultivar', fullpath=False) # list all available cultivar names
     ['Hycorn_53', 'Pioneer_33M54', 'Pioneer_38H20','Pioneer_34K77', 'Pioneer_39V43','Atrium', 'Laila', 'GH_5019WX']

# we can get only the names of the cultivar models using the full string path::

     model.inspect_model('Models.PMF.Cultivar', fullpath = False)
     ['Hycorn_53','Pioneer_33M54', 'Pioneer_38H20','Pioneer_34K77', 'Pioneer_39V43','Atrium', 'Laila', 'GH_5019WX']

.. tip::

    Models can be inspected either by importing the Models namespace or by using string paths. The most reliable
     approach is to provide the full model path—either as a string or as the ``Models`` object.

    However, remembering full paths can be tedious, so allowing partial model names or references can significantly
     save time during development and exploration.


.. note::

    - You do not need to import `Models` if you pass a string; both short and
      fully qualified names are supported.
    - “Full path” is the APSIM tree path **relative to the Simulations node**
      (be mindful of the difference between *Simulations* (root) and an individual
      *Simulation*).

   .. method:: apsimNGpy.core.apsim.ApsimModel.replace_soils_values_by_path(self, node_path: 'str', indices: 'list' = None, **kwargs) (inherited)

      set the new values of the specified soil object by path. only layers parameters are supported.

Unfortunately, it handles one soil child at a time e.g., ``Physical`` at a go

Args:

``node_path`` (str, required): complete path to the soil child of the Simulations e.g.,Simulations.Simulation.Field.Soil.Organic.
 Use`copy path to node function in the GUI to get the real path of the soil node.

``indices`` (list, optional): defaults to none but could be the position of the replacement values for arrays

``kwargs`` (key word arguments): This carries the parameter and the values e.g., BD = 1.23 or BD = [1.23, 1.75]
 if the child is ``Physical``, or ``Carbon`` if the child is ``Organic``

 ``raises``
 ``ValueError`` if none of the key word arguments, representing the paramters are specified

 returns:
    - ``apsimNGpy.core.CoreModel`` object and if the path specified does not translate to the child object in
 the simulation

 Example::

      from apsimNGpy.core.base_data import load_default_simulations
      model = load_default_simulations(crop ='Maize', simulations_object=False) # initiate model.
      model = CoreModel(model) # ``replace`` with your intended file path
      model.replace_soils_values_by_path(node_path='.Simulations.Simulation.Field.Soil.Organic', indices=[0], Carbon =1.3)
      sv= model.get_soil_values_by_path('.Simulations.Simulation.Field.Soil.Organic', 'Carbon')
      output # {'Carbon': [1.3, 0.96, 0.6, 0.3, 0.18, 0.12, 0.12]}

   .. method:: apsimNGpy.core.apsim.ApsimModel.replace_soil_property_values(self, *, parameter: 'str', param_values: 'list', soil_child: 'str', simulations: 'list' = <UserOptionMissing>, indices: 'list' = None, crop=None, **kwargs) (inherited)

      Replaces values in any soil property array. The soil property array.

``parameter``: str: parameter name e.g., NO3, 'BD'

``param_values``: list or tuple: values of the specified soil property name to replace

``soil_child``: str: sub child of the soil component e.g., organic, physical etc.

``simulations``: list: list of simulations to where the child is found if
  not found, all current simulations will receive the new values, thus defaults to None

``indices``: list. Positions in the array which will be replaced. Please note that unlike C#, python satrt counting from 0

``crop`` (str, optional): string for soil water replacement. Default is None

   .. method:: apsimNGpy.core.apsim.ApsimModel.clean_up(self, db=True, verbose=False, coerce=True, csv=True) (inherited)

      Clears the file cloned the datastore and associated csv files are not deleted if db is set to False defaults to True.

Returns:
   >>None: This method does not return a value.

.. caution::

   Please proceed with caution, we assume that if you want to clear the model objects, then you don't need them,
   but by making copy compulsory, then, we are clearing the edited files

   .. method:: apsimNGpy.core.apsim.ApsimModel.create_experiment(self, permutation: 'bool' = True, base_name: 'str' = None, **kwargs) (inherited)

      Initialize an ``ExperimentManager`` instance, adding the necessary models and factors.

Args:

    ``kwargs``: Additional parameters for CoreModel.

    ``permutation`` (bool). If True, the experiment uses a permutation node to run unique combinations of the specified
    factors for the simulation. For example, if planting population and nitrogen fertilizers are provided,
    each combination of planting population level and fertilizer amount is run as an individual treatment.

   ``base_name`` (str, optional): The name of the base simulation to be moved into the experiment setup. if not
    provided, it is expected to be Simulation as the default.

.. warning::

    ``base_name`` is optional but the experiment may not be created if there are more than one base simulations. Therefore, an error is likely.

   .. method:: apsimNGpy.core.apsim.ApsimModel.refresh_model(self) (inherited)

      for methods that will alter the simulation objects and need refreshing the second time we call
@return: self for method chaining

   .. method:: apsimNGpy.core.apsim.ApsimModel.add_factor(self, specification: 'str', factor_name: 'str' = None, **kwargs) (inherited)

      Adds a factor to the created experiment. Thus, this method only works on factorial experiments

It could raise a value error if the experiment is not yet created.

Under some circumstances, experiment will be created automatically as a permutation experiment.

Parameters:
----------

``specification``: *(str), required*
A specification can be:
        - 1. multiple values or categories e.g., "[Sow using a variable rule].Script.Population =4, 66, 9, 10"
        - 2. Range of values e.g, "[Fertilise at sowing].Script.Amount = 0 to 200 step 20",

``factor_name``: *(str), required*
- expected to be the user-desired name of the factor being specified e.g., population

Example::

    from apsimNGpy.core import base_data
    apsim = base_data.load_default_simulations(crop='Maize')
    apsim.create_experiment(permutation=False)
    apsim.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20", factor_name='Nitrogen')
    apsim.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2", factor_name='Population')
    apsim.run() # doctest: +SKIP

   .. method:: apsimNGpy.core.apsim.ApsimModel.add_fac(self, model_type, parameter, model_name, values, factor_name=None) (inherited)

      Add a factor to the initiated experiment. This should replace add_factor. which has less abstractionn @param
model_type: model_class from APSIM Models namespace @param parameter: name of the parameter to fill e.g CNR
@param model_name: name of the model @param values: values of the parameter, could be an iterable for case of
categorical variables or a string e.g, '0 to 100 step 10 same as [0, 10, 20, 30, ...].
@param factor_name: name to identify the factor in question
@return:

   .. method:: apsimNGpy.core.apsim.ApsimModel.set_continuous_factor(self, factor_path, lower_bound, upper_bound, interval, factor_name=None) (inherited)

      Wraps around `add_factor` to add a continuous factor, just for clarity

Args:
    ``factor_path``: (str): The path of the factor definition relative to its child node,
        e.g., `"[Fertilise at sowing].Script.Amount"`.

    ``factor_name``: (str): The name of the factor.

    ``lower_bound``: (int or float): The lower bound of the factor.

    ``upper_bound``: (int or float): The upper bound of the factor.

    ``interval``: (int or float): The distance between the factor levels.

``Returns``:
    ``ApsimModel`` or ``CoreModel``: An instance of `apsimNGpy.core.core.apsim.ApsimModel` or `CoreModel`.
Example::

    from apsimNGpy.core import base_data
    apsim = base_data.load_default_simulations(crop='Maize')
    apsim.create_experiment(permutation=False)
    apsim.set_continuous_factor(factor_path = "[Fertilise at sowing].Script.Amount", lower_bound=100, upper_bound=300, interval=10)

   .. method:: apsimNGpy.core.apsim.ApsimModel.set_categorical_factor(self, factor_path: 'str', categories: 'Union[list, tuple]', factor_name: 'str' = None) (inherited)

      wraps around ``add_factor()`` to add a continuous factor, just for clarity.

 parameters
 __________________________
``factor_path``: (str, required): path of the factor definition relative to its child node "[Fertilise at sowing].Script.Amount"

``factor_name``: (str) name of the factor.

``categories``: (tuple, list, required): multiple values of a factor

``returns``:
  ``ApsimModel`` or ``CoreModel``: An instance of ``apsimNGpy.core.core.apsim.ApsimModel`` or ``CoreModel``.

Example::

    from apsimNGpy.core import base_data
    apsim = base_data.load_default_simulations(crop='Maize')
    apsim.create_experiment(permutation=False)
    apsim.set_continuous_factor(factor_path = "[Fertilise at sowing].Script.Amount", lower_bound=100, upper_bound=300, interval=10)

   .. method:: apsimNGpy.core.apsim.ApsimModel.add_crop_replacements(self, _crop: 'str') (inherited)

      Adds a replacement folder as a child of the simulations.

Useful when you intend to edit cultivar **parameters**.

**Args:**
    ``_crop`` (*str*): Name of the crop to be added to the replacement folder.

``Returns:``
    - *ApsimModel*: An instance of `apsimNGpy.core.core.apsim.ApsimModel` or `CoreModel`.

``Raises:``
    - *ValueError*: If the specified crop is not found.

   .. method:: apsimNGpy.core.apsim.ApsimModel.get_model_paths(self, cultivar=False) -> 'list[str]' (inherited)

      Select out a few model types to use for building the APSIM file inspections

   .. method:: apsimNGpy.core.apsim.ApsimModel.inspect_file(self, *, cultivar=False, console=True, **kwargs) (inherited)

      Inspect the file by calling ``inspect_model()`` through ``get_model_paths.``
This method is important in inspecting the ``whole file`` and also getting the ``scripts paths``

cultivar: i (bool) includes cultivar paths

console: (bool) print to the console

   .. method:: apsimNGpy.core.apsim.ApsimModel.summarize_numeric(self, data_table: 'Union[str, tuple, list]' = None, columns: 'list' = None, percentiles=(0.25, 0.5, 0.75), round=2) -> 'pd.DataFrame' (inherited)

      Summarize numeric columns in a simulated pandas DataFrame. Useful when you want to quickly look at the simulated data

Parameters:

    -  data_table (list, tuple, str): The names of the data table attached to the simulations. defaults to all data tables.
    -  specific (list) columns to summarize.
    -  percentiles (tuple): Optional percentiles to include in the summary.
    -  round (int): number of decimal places for rounding off.

Returns:

    pd.DataFrame: A summary DataFrame with statistics for each numeric column.

   .. method:: apsimNGpy.core.apsim.ApsimModel.add_db_table(self, variable_spec: 'list' = None, set_event_names: 'list' = None, rename: 'str' = None, simulation_name: 'Union[str, list, tuple]' = <UserOptionMissing>) (inherited)

      Adds a new database table, which ``APSIM`` calls ``Report`` (Models.Report) to the ``Simulation`` under a Simulation Zone.

This is different from ``add_report_variable`` in that it creates a new, named report
table that collects data based on a given list of _variables and events. actu

:Args:
    ``variable_spec`` (list or str): A list of APSIM variable paths to include in the report table.
                                 If a string is passed, it will be converted to a list.
    ``set_event_names`` (list or str, optional): A list of APSIM events that trigger the recording of _variables.
                                             Defaults to ['[Clock].EndOfYear'] if not provided. other examples include '[Clock].StartOfYear', '[Clock].EndOfsimulation',
                                             '[crop_name].Harvesting' etc.,,
    ``rename`` (str): The name of the report table to be added. Defaults to 'my_table'.

    ``simulation_name`` (str,tuple, or list, Optional): if specified, the name of the simulation will be searched and will become the parent candidate for the report table.
                    If it is none, all Simulations in the file will be updated with the new db_table

``Raises``:
    ``ValueError``: If no variable_spec is provided.
    ``RuntimeError``: If no Zone is found in the current simulation scope.

: Example::

       from apsimNGpy import core
       model = core.base_data.load_default_simulations(crop = 'Maize')
       model.add_db_table(variable_spec=['[Clock].Today', '[Soil].Nutrient.TotalC[1]/1000 as SOC1'], rename='report2')
       model.add_db_table(variable_spec=['[Clock].Today', '[Soil].Nutrient.TotalC[1]/1000 as SOC1', '[Maize].Grain.Total.Wt*10 as Yield'], rename='report2', set_event_names=['[Maize].Harvesting','[Clock].EndOfYear' ])

   .. method:: apsimNGpy.core.apsim.ApsimModel.plot_mva(data=None, *, x=None, y=None, hue=None, size=None, style=None, units=None, weights=None, row=None, col=None, col_wrap=None, row_order=None, col_order=None, palette=None, hue_order=None, hue_norm=None, sizes=None, size_order=None, size_norm=None, markers=None, dashes=None, style_order=None, legend='auto', kind='scatter', height=5, aspect=1, facet_kws=None, **kwargs) (inherited)

      Plot a centered moving average (MVA) of `response` using seaborn.relplot.

        Enhancements over a direct relplot call:
          - Computes MVA with `mva(...)` and **plots the smoothed series**
          - Auto-assigns `hue` from `grouping` (supports multi-column grouping)
          - Optional overlay of the **raw** series for comparison
          - Preserves original row order and handles NaN groups
        
Figure-level interface for drawing relational plots onto a FacetGrid.

This function provides access to several different axes-level functions
that show the relationship between two variables with semantic mappings
of subsets. The `kind` parameter selects the underlying axes-level
function to use:

- :func:`scatterplot` (with `kind="scatter"`; the default)
- :func:`lineplot` (with `kind="line"`)

Extra keyword arguments are passed to the underlying function, so you
should refer to the documentation for each to see kind-specific options.

The relationship between `x` and `y` can be shown for different subsets
of the data using the `hue`, `size`, and `style` parameters. These
parameters control what visual semantics are used to identify the different
subsets. It is possible to show up to three dimensions independently by
using all three semantic types, but this style of plot can be hard to
interpret and is often ineffective. Using redundant semantics (i.e. both
`hue` and `style` for the same variable) can be helpful for making
graphics more accessible.

See the :ref:`tutorial <relational_tutorial>` for more information.

The default treatment of the `hue` (and to a lesser extent, `size`)
semantic, if present, depends on whether the variable is inferred to
represent "numeric" or "categorical" data. In particular, numeric variables
are represented with a sequential colormap by default, and the legend
entries show regular "ticks" with values that may or may not exist in the
data. This behavior can be controlled through various parameters, as
described and illustrated below.

After plotting, the :class:`FacetGrid` with the plot is returned and can
be used directly to tweak supporting plot details or add other layers.

Parameters
----------
data : :class:`pandas.DataFrame`, :class:`numpy.ndarray`, mapping, or sequence
    Input data structure. Either a long-form collection of vectors that can be
    assigned to named variables or a wide-form dataset that will be internally
    reshaped.
x, y : vectors or keys in ``data``
    Variables that specify positions on the x and y axes.
hue : vector or key in `data`
    Grouping variable that will produce elements with different colors.
    Can be either categorical or numeric, although color mapping will
    behave differently in latter case.
size : vector or key in `data`
    Grouping variable that will produce elements with different sizes.
    Can be either categorical or numeric, although size mapping will
    behave differently in latter case.
style : vector or key in `data`
    Grouping variable that will produce elements with different styles.
    Can have a numeric dtype but will always be treated as categorical.
units : vector or key in `data`
    Grouping variable identifying sampling units. When used, a separate
    line will be drawn for each unit with appropriate semantics, but no
    legend entry will be added. Useful for showing distribution of
    experimental replicates when exact identities are not needed.
weights : vector or key in `data`
    Data values or column used to compute weighted estimation.
    Note that use of weights currently limits the choice of statistics
    to a 'mean' estimator and 'ci' errorbar.
row, col : vectors or keys in ``data``
    Variables that define subsets to plot on different facets.    
col_wrap : int
    "Wrap" the column variable at this width, so that the column facets
    span multiple rows. Incompatible with a ``row`` facet.    
row_order, col_order : lists of strings
    Order to organize the rows and/or columns of the grid in, otherwise the
    orders are inferred from the data objects.
palette : string, list, dict, or :class:`matplotlib.colors.Colormap`
    Method for choosing the colors to use when mapping the ``hue`` semantic.
    String values are passed to :func:`color_palette`. List or dict values
    imply categorical mapping, while a colormap object implies numeric mapping.
hue_order : vector of strings
    Specify the order of processing and plotting for categorical levels of the
    ``hue`` semantic.
hue_norm : tuple or :class:`matplotlib.colors.Normalize`
    Either a pair of values that set the normalization range in data units
    or an object that will map from data units into a [0, 1] interval. Usage
    implies numeric mapping.
sizes : list, dict, or tuple
    An object that determines how sizes are chosen when `size` is used.
    List or dict arguments should provide a size for each unique data value,
    which forces a categorical interpretation. The argument may also be a
    min, max tuple.
size_order : list
    Specified order for appearance of the `size` variable levels,
    otherwise they are determined from the data. Not relevant when the
    `size` variable is numeric.
size_norm : tuple or Normalize object
    Normalization in data units for scaling plot objects when the
    `size` variable is numeric.
style_order : list
    Specified order for appearance of the `style` variable levels
    otherwise they are determined from the data. Not relevant when the
    `style` variable is numeric.
dashes : boolean, list, or dictionary
    Object determining how to draw the lines for different levels of the
    `style` variable. Setting to `True` will use default dash codes, or
    you can pass a list of dash codes or a dictionary mapping levels of the
    `style` variable to dash codes. Setting to `False` will use solid
    lines for all subsets. Dashes are specified as in matplotlib: a tuple
    of `(segment, gap)` lengths, or an empty string to draw a solid line.
markers : boolean, list, or dictionary
    Object determining how to draw the markers for different levels of the
    `style` variable. Setting to `True` will use default markers, or
    you can pass a list of markers or a dictionary mapping levels of the
    `style` variable to markers. Setting to `False` will draw
    marker-less lines.  Markers are specified as in matplotlib.
legend : "auto", "brief", "full", or False
    How to draw the legend. If "brief", numeric `hue` and `size`
    variables will be represented with a sample of evenly spaced values.
    If "full", every group will get an entry in the legend. If "auto",
    choose between brief or full representation based on number of levels.
    If `False`, no legend data is added and no legend is drawn.
kind : string
    Kind of plot to draw, corresponding to a seaborn relational plot.
    Options are `"scatter"` or `"line"`.
height : scalar
    Height (in inches) of each facet. See also: ``aspect``.    
aspect : scalar
    Aspect ratio of each facet, so that ``aspect * height`` gives the width
    of each facet in inches.    
facet_kws : dict
    Dictionary of other keyword arguments to pass to :class:`FacetGrid`.
kwargs : key, value pairings
    Other keyword arguments are passed through to the underlying plotting
    function.

Returns
-------
:class:`FacetGrid`
    An object managing one or more subplots that correspond to conditional data
    subsets with convenient methods for batch-setting of axes attributes.

Examples
--------

.. include:: ../docstrings/relplot.rst

   .. method:: apsimNGpy.core.apsim.ApsimModel.boxplot(data=None, index: 'Axes | None' = None, columns: 'Axes | None' = None, dtype: 'Dtype | None' = None, copy: 'bool | None' = None) -> 'None' (inherited)

      Plot a boxplot from the simulation results using ``pandas.DataFrame.boxplot`` 

    =======================================================================.
    

Two-dimensional, size-mutable, potentially heterogeneous tabular data.

Data structure also contains labeled axes (rows and columns).
Arithmetic operations align on both row and column labels. Can be
thought of as a dict-like container for Series objects. The primary
pandas data structure.

Parameters
----------
data : ndarray (structured or homogeneous), Iterable, dict, or DataFrame
    Dict can contain Series, arrays, constants, dataclass or list-like objects. If
    data is a dict, column order follows insertion-order. If a dict contains Series
    which have an index defined, it is aligned by its index. This alignment also
    occurs if data is a Series or a DataFrame itself. Alignment is done on
    Series/DataFrame inputs.

    If data is a list of dicts, column order follows insertion-order.

index : Index or array-like
    Index to use for resulting frame. Will default to RangeIndex if
    no indexing information part of input data and no index provided.
columns : Index or array-like
    Column labels to use for resulting frame when data does not have them,
    defaulting to RangeIndex(0, 1, 2, ..., n). If data contains column labels,
    will perform column selection instead.
dtype : dtype, default None
    Data type to force. Only a single dtype is allowed. If None, infer.
copy : bool or None, default None
    Copy data from inputs.
    For dict data, the default of None behaves like ``copy=True``.  For DataFrame
    or 2d ndarray input, the default of None behaves like ``copy=False``.
    If data is a dict containing one or more Series (possibly of different dtypes),
    ``copy=False`` will ensure that these inputs are not copied.

    .. versionchanged:: 1.3.0

See Also
--------
DataFrame.from_records : Constructor from tuples, also record arrays.
DataFrame.from_dict : From dicts of Series, arrays, or dicts.
read_csv : Read a comma-separated values (csv) file into DataFrame.
read_table : Read general delimited file into DataFrame.
read_clipboard : Read text from clipboard into DataFrame.

Notes
-----
Please reference the :ref:`User Guide <basics.dataframe>` for more information.

Examples
--------
Constructing DataFrame from a dictionary.

>>> d = {'col1': [1, 2], 'col2': [3, 4]}
>>> df = pd.DataFrame(data=d)
>>> df
   col1  col2
0     1     3
1     2     4

Notice that the inferred dtype is int64.

>>> df.dtypes
col1    int64
col2    int64
dtype: object

To enforce a single dtype:

>>> df = pd.DataFrame(data=d, dtype=np.int8)
>>> df.dtypes
col1    int8
col2    int8
dtype: object

Constructing DataFrame from a dictionary including Series:

>>> d = {'col1': [0, 1, 2, 3], 'col2': pd.Series([2, 3], index=[2, 3])}
>>> pd.DataFrame(data=d, index=[0, 1, 2, 3])
   col1  col2
0     0   NaN
1     1   NaN
2     2   2.0
3     3   3.0

Constructing DataFrame from numpy ndarray:

>>> df2 = pd.DataFrame(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
...                    columns=['a', 'b', 'c'])
>>> df2
   a  b  c
0  1  2  3
1  4  5  6
2  7  8  9

Constructing DataFrame from a numpy ndarray that has labeled columns:

>>> data = np.array([(1, 2, 3), (4, 5, 6), (7, 8, 9)],
...                 dtype=[("a", "i4"), ("b", "i4"), ("c", "i4")])
>>> df3 = pd.DataFrame(data, columns=['c', 'a'])
...
>>> df3
   c  a
0  3  1
1  6  4
2  9  7

Constructing DataFrame from dataclass:

>>> from dataclasses import make_dataclass
>>> Point = make_dataclass("Point", [("x", int), ("y", int)])
>>> pd.DataFrame([Point(0, 0), Point(0, 3), Point(2, 3)])
   x  y
0  0  0
1  0  3
2  2  3

Constructing DataFrame from Series/DataFrame:

>>> ser = pd.Series([1, 2, 3], index=["a", "b", "c"])
>>> df = pd.DataFrame(data=ser, index=["a", "c"])
>>> df
   0
a  1
c  3

>>> df1 = pd.DataFrame([1, 2, 3], index=["a", "b", "c"], columns=["x"])
>>> df2 = pd.DataFrame(data=df1, index=["a", "c"])
>>> df2
   x
a  1
c  3

   .. method:: apsimNGpy.core.apsim.ApsimModel.distribution(data=None, *, x=None, y=None, hue=None, weights=None, stat='count', bins='auto', binwidth=None, binrange=None, discrete=None, cumulative=False, common_bins=True, common_norm=True, multiple='layer', element='bars', fill=True, shrink=1, kde=False, kde_kws=None, line_kws=None, thresh=0, pthresh=None, pmax=None, cbar=False, cbar_ax=None, cbar_kws=None, palette=None, hue_order=None, hue_norm=None, color=None, log_scale=None, legend=True, ax=None, **kwargs) (inherited)

      Plot distribution for a numeric variable. It uses ``seaborn.histplot`` function. Please see their documentation below
        =========================================================================================================

        
Plot univariate or bivariate histograms to show distributions of datasets.

A histogram is a classic visualization tool that represents the distribution
of one or more variables by counting the number of observations that fall within
discrete bins.

This function can normalize the statistic computed within each bin to estimate
frequency, density or probability mass, and it can add a smooth curve obtained
using a kernel density estimate, similar to :func:`kdeplot`.

More information is provided in the :ref:`user guide <tutorial_hist>`.

Parameters
----------
data : :class:`pandas.DataFrame`, :class:`numpy.ndarray`, mapping, or sequence
    Input data structure. Either a long-form collection of vectors that can be
    assigned to named variables or a wide-form dataset that will be internally
    reshaped.
x, y : vectors or keys in ``data``
    Variables that specify positions on the x and y axes.
hue : vector or key in ``data``
    Semantic variable that is mapped to determine the color of plot elements.
weights : vector or key in ``data``
    If provided, weight the contribution of the corresponding data points
    towards the count in each bin by these factors.
stat : str
    Aggregate statistic to compute in each bin.
    
    - `count`: show the number of observations in each bin
    - `frequency`: show the number of observations divided by the bin width
    - `probability` or `proportion`: normalize such that bar heights sum to 1
    - `percent`: normalize such that bar heights sum to 100
    - `density`: normalize such that the total area of the histogram equals 1
bins : str, number, vector, or a pair of such values
    Generic bin parameter that can be the name of a reference rule,
    the number of bins, or the breaks of the bins.
    Passed to :func:`numpy.histogram_bin_edges`.
binwidth : number or pair of numbers
    Width of each bin, overrides ``bins`` but can be used with
    ``binrange``.
binrange : pair of numbers or a pair of pairs
    Lowest and highest value for bin edges; can be used either
    with ``bins`` or ``binwidth``. Defaults to data extremes.
discrete : bool
    If True, default to ``binwidth=1`` and draw the bars so that they are
    centered on their corresponding data points. This avoids "gaps" that may
    otherwise appear when using discrete (integer) data.
cumulative : bool
    If True, plot the cumulative counts as bins increase.
common_bins : bool
    If True, use the same bins when semantic variables produce multiple
    plots. If using a reference rule to determine the bins, it will be computed
    with the full dataset.
common_norm : bool
    If True and using a normalized statistic, the normalization will apply over
    the full dataset. Otherwise, normalize each histogram independently.
multiple : {"layer", "dodge", "stack", "fill"}
    Approach to resolving multiple elements when semantic mapping creates subsets.
    Only relevant with univariate data.
element : {"bars", "step", "poly"}
    Visual representation of the histogram statistic.
    Only relevant with univariate data.
fill : bool
    If True, fill in the space under the histogram.
    Only relevant with univariate data.
shrink : number
    Scale the width of each bar relative to the binwidth by this factor.
    Only relevant with univariate data.
kde : bool
    If True, compute a kernel density estimate to smooth the distribution
    and show on the plot as (one or more) line(s).
    Only relevant with univariate data.
kde_kws : dict
    Parameters that control the KDE computation, as in :func:`kdeplot`.
line_kws : dict
    Parameters that control the KDE visualization, passed to
    :meth:`matplotlib.axes.Axes.plot`.
thresh : number or None
    Cells with a statistic less than or equal to this value will be transparent.
    Only relevant with bivariate data.
pthresh : number or None
    Like ``thresh``, but a value in [0, 1] such that cells with aggregate counts
    (or other statistics, when used) up to this proportion of the total will be
    transparent.
pmax : number or None
    A value in [0, 1] that sets that saturation point for the colormap at a value
    such that cells below constitute this proportion of the total count (or
    other statistic, when used).
cbar : bool
    If True, add a colorbar to annotate the color mapping in a bivariate plot.
    Note: Does not currently support plots with a ``hue`` variable well.
cbar_ax : :class:`matplotlib.axes.Axes`
    Pre-existing axes for the colorbar.
cbar_kws : dict
    Additional parameters passed to :meth:`matplotlib.figure.Figure.colorbar`.
palette : string, list, dict, or :class:`matplotlib.colors.Colormap`
    Method for choosing the colors to use when mapping the ``hue`` semantic.
    String values are passed to :func:`color_palette`. List or dict values
    imply categorical mapping, while a colormap object implies numeric mapping.
hue_order : vector of strings
    Specify the order of processing and plotting for categorical levels of the
    ``hue`` semantic.
hue_norm : tuple or :class:`matplotlib.colors.Normalize`
    Either a pair of values that set the normalization range in data units
    or an object that will map from data units into a [0, 1] interval. Usage
    implies numeric mapping.
color : :mod:`matplotlib color <matplotlib.colors>`
    Single color specification for when hue mapping is not used. Otherwise, the
    plot will try to hook into the matplotlib property cycle.
log_scale : bool or number, or pair of bools or numbers
    Set axis scale(s) to log. A single value sets the data axis for any numeric
    axes in the plot. A pair of values sets each axis independently.
    Numeric values are interpreted as the desired base (default 10).
    When `None` or `False`, seaborn defers to the existing Axes scale.
legend : bool
    If False, suppress the legend for semantic variables.
ax : :class:`matplotlib.axes.Axes`
    Pre-existing axes for the plot. Otherwise, call :func:`matplotlib.pyplot.gca`
    internally.
kwargs
    Other keyword arguments are passed to one of the following matplotlib
    functions:

    - :meth:`matplotlib.axes.Axes.bar` (univariate, element="bars")
    - :meth:`matplotlib.axes.Axes.fill_between` (univariate, other element, fill=True)
    - :meth:`matplotlib.axes.Axes.plot` (univariate, other element, fill=False)
    - :meth:`matplotlib.axes.Axes.pcolormesh` (bivariate)

Returns
-------
:class:`matplotlib.axes.Axes`
    The matplotlib axes containing the plot.

See Also
--------
displot : Figure-level interface to distribution plot functions.
kdeplot : Plot univariate or bivariate distributions using kernel density estimation.
rugplot : Plot a tick at each observation value along the x and/or y axes.
ecdfplot : Plot empirical cumulative distribution functions.
jointplot : Draw a bivariate plot with univariate marginal distributions.

Notes
-----

The choice of bins for computing and plotting a histogram can exert
substantial influence on the insights that one is able to draw from the
visualization. If the bins are too large, they may erase important features.
On the other hand, bins that are too small may be dominated by random
variability, obscuring the shape of the true underlying distribution. The
default bin size is determined using a reference rule that depends on the
sample size and variance. This works well in many cases, (i.e., with
"well-behaved" data) but it fails in others. It is always a good to try
different bin sizes to be sure that you are not missing something important.
This function allows you to specify bins in several different ways, such as
by setting the total number of bins to use, the width of each bin, or the
specific locations where the bins should break.

Examples
--------

.. include:: ../docstrings/histplot.rst

   .. method:: apsimNGpy.core.apsim.ApsimModel.series_plot(data=None, *, x=None, y=None, hue=None, size=None, style=None, units=None, weights=None, palette=None, hue_order=None, hue_norm=None, sizes=None, size_order=None, size_norm=None, dashes=True, markers=None, style_order=None, estimator='mean', errorbar=('ci', 95), n_boot=1000, seed=None, orient='x', sort=True, err_style='band', err_kws=None, legend='auto', ci='deprecated', ax=None, **kwargs) (inherited)

      Just a wrapper for seaborn.lineplot that supports multiple y columns that could be provided as a list

        Examples::

           from apsimNGpy.core.apsim import ApsimModel
           model = ApsimModel(model= 'Maize')
           # run the results
           model.run(report_names='Report')
           model.series_plot(x='Maize.Grain.Size', y='Yield', table='Report')
           model.render_plot(show=True, ylabel = 'Maize yield', xlabel ='Maize grain size')

        Plot two variables::

           model.series_plot(x='Yield', y=['Maize.Grain.N', 'Maize.Grain.Size'], table= 'Report')

         see below or https://seaborn.pydata.org/generated/seaborn.lineplot.html 

        =============================================================================================================================================

        
Draw a line plot with possibility of several semantic groupings.

The relationship between `x` and `y` can be shown for different subsets
of the data using the `hue`, `size`, and `style` parameters. These
parameters control what visual semantics are used to identify the different
subsets. It is possible to show up to three dimensions independently by
using all three semantic types, but this style of plot can be hard to
interpret and is often ineffective. Using redundant semantics (i.e. both
`hue` and `style` for the same variable) can be helpful for making
graphics more accessible.

See the :ref:`tutorial <relational_tutorial>` for more information.

The default treatment of the `hue` (and to a lesser extent, `size`)
semantic, if present, depends on whether the variable is inferred to
represent "numeric" or "categorical" data. In particular, numeric variables
are represented with a sequential colormap by default, and the legend
entries show regular "ticks" with values that may or may not exist in the
data. This behavior can be controlled through various parameters, as
described and illustrated below.

By default, the plot aggregates over multiple `y` values at each value of
`x` and shows an estimate of the central tendency and a confidence
interval for that estimate.

Parameters
----------
data : :class:`pandas.DataFrame`, :class:`numpy.ndarray`, mapping, or sequence
    Input data structure. Either a long-form collection of vectors that can be
    assigned to named variables or a wide-form dataset that will be internally
    reshaped.
x, y : vectors or keys in ``data``
    Variables that specify positions on the x and y axes.
hue : vector or key in `data`
    Grouping variable that will produce lines with different colors.
    Can be either categorical or numeric, although color mapping will
    behave differently in latter case.
size : vector or key in `data`
    Grouping variable that will produce lines with different widths.
    Can be either categorical or numeric, although size mapping will
    behave differently in latter case.
style : vector or key in `data`
    Grouping variable that will produce lines with different dashes
    and/or markers. Can have a numeric dtype but will always be treated
    as categorical.
units : vector or key in `data`
    Grouping variable identifying sampling units. When used, a separate
    line will be drawn for each unit with appropriate semantics, but no
    legend entry will be added. Useful for showing distribution of
    experimental replicates when exact identities are not needed.
weights : vector or key in `data`
    Data values or column used to compute weighted estimation.
    Note that use of weights currently limits the choice of statistics
    to a 'mean' estimator and 'ci' errorbar.
palette : string, list, dict, or :class:`matplotlib.colors.Colormap`
    Method for choosing the colors to use when mapping the ``hue`` semantic.
    String values are passed to :func:`color_palette`. List or dict values
    imply categorical mapping, while a colormap object implies numeric mapping.
hue_order : vector of strings
    Specify the order of processing and plotting for categorical levels of the
    ``hue`` semantic.
hue_norm : tuple or :class:`matplotlib.colors.Normalize`
    Either a pair of values that set the normalization range in data units
    or an object that will map from data units into a [0, 1] interval. Usage
    implies numeric mapping.
sizes : list, dict, or tuple
    An object that determines how sizes are chosen when `size` is used.
    List or dict arguments should provide a size for each unique data value,
    which forces a categorical interpretation. The argument may also be a
    min, max tuple.
size_order : list
    Specified order for appearance of the `size` variable levels,
    otherwise they are determined from the data. Not relevant when the
    `size` variable is numeric.
size_norm : tuple or Normalize object
    Normalization in data units for scaling plot objects when the
    `size` variable is numeric.
dashes : boolean, list, or dictionary
    Object determining how to draw the lines for different levels of the
    `style` variable. Setting to `True` will use default dash codes, or
    you can pass a list of dash codes or a dictionary mapping levels of the
    `style` variable to dash codes. Setting to `False` will use solid
    lines for all subsets. Dashes are specified as in matplotlib: a tuple
    of `(segment, gap)` lengths, or an empty string to draw a solid line.
markers : boolean, list, or dictionary
    Object determining how to draw the markers for different levels of the
    `style` variable. Setting to `True` will use default markers, or
    you can pass a list of markers or a dictionary mapping levels of the
    `style` variable to markers. Setting to `False` will draw
    marker-less lines.  Markers are specified as in matplotlib.
style_order : list
    Specified order for appearance of the `style` variable levels
    otherwise they are determined from the data. Not relevant when the
    `style` variable is numeric.
estimator : name of pandas method or callable or None
    Method for aggregating across multiple observations of the `y`
    variable at the same `x` level. If `None`, all observations will
    be drawn.
errorbar : string, (string, number) tuple, or callable
    Name of errorbar method (either "ci", "pi", "se", or "sd"), or a tuple
    with a method name and a level parameter, or a function that maps from a
    vector to a (min, max) interval, or None to hide errorbar. See the
    :doc:`errorbar tutorial </tutorial/error_bars>` for more information.
n_boot : int
    Number of bootstraps to use for computing the confidence interval.
seed : int, numpy.random.Generator, or numpy.random.RandomState
    Seed or random number generator for reproducible bootstrapping.
orient : "x" or "y"
    Dimension along which the data are sorted / aggregated. Equivalently,
    the "independent variable" of the resulting function.
sort : boolean
    If True, the data will be sorted by the x and y variables, otherwise
    lines will connect points in the order they appear in the dataset.
err_style : "band" or "bars"
    Whether to draw the confidence intervals with translucent error bands
    or discrete error bars.
err_kws : dict of keyword arguments
    Additional parameters to control the aesthetics of the error bars. The
    kwargs are passed either to :meth:`matplotlib.axes.Axes.fill_between`
    or :meth:`matplotlib.axes.Axes.errorbar`, depending on `err_style`.
legend : "auto", "brief", "full", or False
    How to draw the legend. If "brief", numeric `hue` and `size`
    variables will be represented with a sample of evenly spaced values.
    If "full", every group will get an entry in the legend. If "auto",
    choose between brief or full representation based on number of levels.
    If `False`, no legend data is added and no legend is drawn.
ci : int or "sd" or None
    Size of the confidence interval to draw when aggregating.

    .. deprecated:: 0.12.0
        Use the new `errorbar` parameter for more flexibility.

ax : :class:`matplotlib.axes.Axes`
    Pre-existing axes for the plot. Otherwise, call :func:`matplotlib.pyplot.gca`
    internally.
kwargs : key, value mappings
    Other keyword arguments are passed down to
    :meth:`matplotlib.axes.Axes.plot`.

Returns
-------
:class:`matplotlib.axes.Axes`
    The matplotlib axes containing the plot.

See Also
--------
scatterplot : Plot data using points.
pointplot : Plot point estimates and CIs using markers and lines.

Examples
--------

.. include:: ../docstrings/lineplot.rst

   .. method:: apsimNGpy.core.apsim.ApsimModel.scatter_plot(data=None, *, x=None, y=None, hue=None, size=None, style=None, palette=None, hue_order=None, hue_norm=None, sizes=None, size_order=None, size_norm=None, markers=True, style_order=None, legend='auto', ax=None, **kwargs) (inherited)

      Plot scatter plot using seaborn with flexible aesthetic mappings.
        reference: https://seaborn.pydata.org/generated/seaborn.scatterplot.html. Check seaborn documentation below for more details 

        ================================================================================================================================

Draw a scatter plot with possibility of several semantic groupings.

The relationship between `x` and `y` can be shown for different subsets
of the data using the `hue`, `size`, and `style` parameters. These
parameters control what visual semantics are used to identify the different
subsets. It is possible to show up to three dimensions independently by
using all three semantic types, but this style of plot can be hard to
interpret and is often ineffective. Using redundant semantics (i.e. both
`hue` and `style` for the same variable) can be helpful for making
graphics more accessible.

See the :ref:`tutorial <relational_tutorial>` for more information.

The default treatment of the `hue` (and to a lesser extent, `size`)
semantic, if present, depends on whether the variable is inferred to
represent "numeric" or "categorical" data. In particular, numeric variables
are represented with a sequential colormap by default, and the legend
entries show regular "ticks" with values that may or may not exist in the
data. This behavior can be controlled through various parameters, as
described and illustrated below.

Parameters
----------
data : :class:`pandas.DataFrame`, :class:`numpy.ndarray`, mapping, or sequence
    Input data structure. Either a long-form collection of vectors that can be
    assigned to named variables or a wide-form dataset that will be internally
    reshaped.
x, y : vectors or keys in ``data``
    Variables that specify positions on the x and y axes.
hue : vector or key in `data`
    Grouping variable that will produce points with different colors.
    Can be either categorical or numeric, although color mapping will
    behave differently in latter case.
size : vector or key in `data`
    Grouping variable that will produce points with different sizes.
    Can be either categorical or numeric, although size mapping will
    behave differently in latter case.
style : vector or key in `data`
    Grouping variable that will produce points with different markers.
    Can have a numeric dtype but will always be treated as categorical.
palette : string, list, dict, or :class:`matplotlib.colors.Colormap`
    Method for choosing the colors to use when mapping the ``hue`` semantic.
    String values are passed to :func:`color_palette`. List or dict values
    imply categorical mapping, while a colormap object implies numeric mapping.
hue_order : vector of strings
    Specify the order of processing and plotting for categorical levels of the
    ``hue`` semantic.
hue_norm : tuple or :class:`matplotlib.colors.Normalize`
    Either a pair of values that set the normalization range in data units
    or an object that will map from data units into a [0, 1] interval. Usage
    implies numeric mapping.
sizes : list, dict, or tuple
    An object that determines how sizes are chosen when `size` is used.
    List or dict arguments should provide a size for each unique data value,
    which forces a categorical interpretation. The argument may also be a
    min, max tuple.
size_order : list
    Specified order for appearance of the `size` variable levels,
    otherwise they are determined from the data. Not relevant when the
    `size` variable is numeric.
size_norm : tuple or Normalize object
    Normalization in data units for scaling plot objects when the
    `size` variable is numeric.
markers : boolean, list, or dictionary
    Object determining how to draw the markers for different levels of the
    `style` variable. Setting to `True` will use default markers, or
    you can pass a list of markers or a dictionary mapping levels of the
    `style` variable to markers. Setting to `False` will draw
    marker-less lines.  Markers are specified as in matplotlib.
style_order : list
    Specified order for appearance of the `style` variable levels
    otherwise they are determined from the data. Not relevant when the
    `style` variable is numeric.
legend : "auto", "brief", "full", or False
    How to draw the legend. If "brief", numeric `hue` and `size`
    variables will be represented with a sample of evenly spaced values.
    If "full", every group will get an entry in the legend. If "auto",
    choose between brief or full representation based on number of levels.
    If `False`, no legend data is added and no legend is drawn.
ax : :class:`matplotlib.axes.Axes`
    Pre-existing axes for the plot. Otherwise, call :func:`matplotlib.pyplot.gca`
    internally.
kwargs : key, value mappings
    Other keyword arguments are passed down to
    :meth:`matplotlib.axes.Axes.scatter`.

Returns
-------
:class:`matplotlib.axes.Axes`
    The matplotlib axes containing the plot.

See Also
--------
lineplot : Plot data using lines.
stripplot : Plot a categorical scatter with jitter.
swarmplot : Plot a categorical scatter with non-overlapping points.

Examples
--------

.. include:: ../docstrings/scatterplot.rst

   .. method:: apsimNGpy.core.apsim.ApsimModel.cat_plot(data=None, *, x=None, y=None, hue=None, row=None, col=None, kind='strip', estimator='mean', errorbar=('ci', 95), n_boot=1000, seed=None, units=None, weights=None, order=None, hue_order=None, row_order=None, col_order=None, col_wrap=None, height=5, aspect=1, log_scale=None, native_scale=False, formatter=None, orient=None, color=None, palette=None, hue_norm=None, legend='auto', legend_out=True, sharex=True, sharey=True, margin_titles=False, facet_kws=None, ci=<deprecated>, **kwargs) (inherited)

      Wrapper for seaborn.catplot with all keyword arguments.
        reference https://seaborn.pydata.org/generated/seaborn.catplot.html or check seaborn documentation below

        =========================================================================================================

Figure-level interface for drawing categorical plots onto a FacetGrid.

This function provides access to several axes-level functions that
show the relationship between a numerical and one or more categorical
variables using one of several visual representations. The `kind`
parameter selects the underlying axes-level function to use.

Categorical scatterplots:

- :func:`stripplot` (with `kind="strip"`; the default)
- :func:`swarmplot` (with `kind="swarm"`)

Categorical distribution plots:

- :func:`boxplot` (with `kind="box"`)
- :func:`violinplot` (with `kind="violin"`)
- :func:`boxenplot` (with `kind="boxen"`)

Categorical estimate plots:

- :func:`pointplot` (with `kind="point"`)
- :func:`barplot` (with `kind="bar"`)
- :func:`countplot` (with `kind="count"`)

Extra keyword arguments are passed to the underlying function, so you
should refer to the documentation for each to see kind-specific options.

See the :ref:`tutorial <categorical_tutorial>` for more information.

.. note::
    By default, this function treats one of the variables as categorical
    and draws data at ordinal positions (0, 1, ... n) on the relevant axis.
    As of version 0.13.0, this can be disabled by setting `native_scale=True`.


After plotting, the :class:`FacetGrid` with the plot is returned and can
be used directly to tweak supporting plot details or add other layers.

Parameters
----------
data : DataFrame, Series, dict, array, or list of arrays
    Dataset for plotting. If `x` and `y` are absent, this is
    interpreted as wide-form. Otherwise it is expected to be long-form.    
x, y, hue : names of variables in `data` or vector data
    Inputs for plotting long-form data. See examples for interpretation.    
row, col : names of variables in `data` or vector data
    Categorical variables that will determine the faceting of the grid.
kind : str
    The kind of plot to draw, corresponds to the name of a categorical
    axes-level plotting function. Options are: "strip", "swarm", "box", "violin",
    "boxen", "point", "bar", or "count".
estimator : string or callable that maps vector -> scalar
    Statistical function to estimate within each categorical bin.
errorbar : string, (string, number) tuple, callable or None
    Name of errorbar method (either "ci", "pi", "se", or "sd"), or a tuple
    with a method name and a level parameter, or a function that maps from a
    vector to a (min, max) interval, or None to hide errorbar. See the
    :doc:`errorbar tutorial </tutorial/error_bars>` for more information.

    .. versionadded:: v0.12.0
n_boot : int
    Number of bootstrap samples used to compute confidence intervals.
seed : int, `numpy.random.Generator`, or `numpy.random.RandomState`
    Seed or random number generator for reproducible bootstrapping.
units : name of variable in `data` or vector data
    Identifier of sampling units; used by the errorbar function to
    perform a multilevel bootstrap and account for repeated measures
weights : name of variable in `data` or vector data
    Data values or column used to compute weighted statistics.
    Note that the use of weights may limit other statistical options.

    .. versionadded:: v0.13.1    
order, hue_order : lists of strings
    Order to plot the categorical levels in; otherwise the levels are
    inferred from the data objects.    
row_order, col_order : lists of strings
    Order to organize the rows and/or columns of the grid in; otherwise the
    orders are inferred from the data objects.
col_wrap : int
    "Wrap" the column variable at this width, so that the column facets
    span multiple rows. Incompatible with a ``row`` facet.    
height : scalar
    Height (in inches) of each facet. See also: ``aspect``.    
aspect : scalar
    Aspect ratio of each facet, so that ``aspect * height`` gives the width
    of each facet in inches.    
native_scale : bool
    When True, numeric or datetime values on the categorical axis will maintain
    their original scaling rather than being converted to fixed indices.

    .. versionadded:: v0.13.0    
formatter : callable
    Function for converting categorical data into strings. Affects both grouping
    and tick labels.

    .. versionadded:: v0.13.0    
orient : "v" | "h" | "x" | "y"
    Orientation of the plot (vertical or horizontal). This is usually
    inferred based on the type of the input variables, but it can be used
    to resolve ambiguity when both `x` and `y` are numeric or when
    plotting wide-form data.

    .. versionchanged:: v0.13.0
        Added 'x'/'y' as options, equivalent to 'v'/'h'.    
color : matplotlib color
    Single color for the elements in the plot.    
palette : palette name, list, or dict
    Colors to use for the different levels of the ``hue`` variable. Should
    be something that can be interpreted by :func:`color_palette`, or a
    dictionary mapping hue levels to matplotlib colors.    
hue_norm : tuple or :class:`matplotlib.colors.Normalize` object
    Normalization in data units for colormap applied to the `hue`
    variable when it is numeric. Not relevant if `hue` is categorical.

    .. versionadded:: v0.12.0    
legend : "auto", "brief", "full", or False
    How to draw the legend. If "brief", numeric `hue` and `size`
    variables will be represented with a sample of evenly spaced values.
    If "full", every group will get an entry in the legend. If "auto",
    choose between brief or full representation based on number of levels.
    If `False`, no legend data is added and no legend is drawn.

    .. versionadded:: v0.13.0    
legend_out : bool
    If ``True``, the figure size will be extended, and the legend will be
    drawn outside the plot on the center right.    
share{x,y} : bool, 'col', or 'row' optional
    If true, the facets will share y axes across columns and/or x axes
    across rows.    
margin_titles : bool
    If ``True``, the titles for the row variable are drawn to the right of
    the last column. This option is experimental and may not work in all
    cases.    
facet_kws : dict
    Dictionary of other keyword arguments to pass to :class:`FacetGrid`.
kwargs : key, value pairings
    Other keyword arguments are passed through to the underlying plotting
    function.

Returns
-------
:class:`FacetGrid`
    Returns the :class:`FacetGrid` object with the plot on it for further
    tweaking.

Examples
--------
.. include:: ../docstrings/catplot.rst

