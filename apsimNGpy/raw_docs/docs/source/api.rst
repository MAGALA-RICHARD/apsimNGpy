apsimNGpy: API Reference
========================

apsimNGpy.core.apsim
--------------------

Interface to APSIM simulation models using Python.NET
author: Richard Magala
email: magalarich20@gmail.com

Classes
^^^^^^^

.. py:class:: apsimNGpy.core.apsim.ApsimModel

   Main class for apsimNGpy modules.
   It inherits from the CoreModel class and therefore has access to a repertoire of methods from it.

   This implies that you can still run the model and modify parameters as needed.
   Example:
       >>> from apsimNGpy.core.apsim import ApsimModel
       >>> from pathlib import Path
       >>> model = ApsimModel('Maize', out_path=Path.home()/'apsim_model_example.apsimx')
       >>> model.run(report_name='Report') # report is the default, please replace it as needed

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.__init__(self, model: Union[os.PathLike, dict, str], out_path: Union[str, pathlib.Path] = None, set_wd=None, **kwargs)

   Initialize self.  See help(type(self)) for accurate signature.

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.get_soil_from_web(self, simulation_name: Union[str, tuple, NoneType] = None, *, lonlat: Optional[System.Tuple[Double,Double]] = None, soil_series: Optional[str] = None, thickness_sequence: Optional[Sequence[float]] = 'auto', thickness_value: int = None, max_depth: Optional[int] = 2400, n_layers: int = 10, thinnest_layer: int = 100, thickness_growth_rate: float = 1.5, edit_sections: Optional[Sequence[str]] = None, attach_missing_sections: bool = True, additional_plants: tuple = None, adjust_dul: bool = True)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.adjust_dul(self, simulations: Union[tuple, list] = None)

   - This method checks whether the soil ``SAT`` is above or below ``DUL`` and decreases ``DUL``  values accordingly

   - Need to call this method everytime ``SAT`` is changed, or ``DUL`` is changed accordingly.

   ``simulations``: str, name of the simulation where we want to adjust DUL and SAT according.

   ``returns``:

       model the object for method chaining

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.replace_downloaded_soils(self, soil_tables: Union[dict, list], simulation_names: Union[tuple, list], **kwargs)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.spin_up(self, report_name: str = 'Report', start=None, end=None, spin_var='Carbon', simulations=None)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.read_apsimx_data(self, table=None)

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

   .. py:property:: apsimNGpy.core.apsim.ApsimModel.simulations (inherited)

   Retrieve simulation nodes in the APSIMx `Model.Core.Simulations` object.

   We search all-Models.Core.Simulation in the scope of Model.Core.Simulations. Please note the difference
   Simulations is the whole json object Simulation is the child with the field zones, crops, soils and managers.

   Any structure of apsimx file can be handled.

   ..note::

        The simulations are c# referenced objects, and their manipulation maybe for advanced users only.

   .. py:property:: apsimNGpy.core.apsim.ApsimModel.simulation_names (inherited)

   @deprecated will be removed in future releases. Please use inspect_model function instead.

   retrieves the name of the simulations in the APSIMx file
   @return: list of simulation names

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.restart_model(self, model_info=None) (inherited)

   ``model_info``: A named tuple object returned by `load_apsim_model` from the `model_loader` module.

   Notes:
   - This parameter is crucial whenever we need to ``reinitialize`` the model, especially after updating management practices or editing the file.
   - In some cases, this method is executed automatically.
   - If ``model_info`` is not specified, the simulation will be reinitialized from `self`.

   This function is called by ``save_edited_file`` and ``update_mgt``.

   :return: self

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.save(self, file_name: 'Union[str, Path, None]' = None, reload=True) (inherited)

   Saves the current APSIM NG model (``Simulations``) to disk and refresh runtime state.

   This method writes the model to a file, using a version-aware strategy:

   After writing, the model is recompiled via :func:`recompile(self)` and the
   in-memory instance is refreshed using :meth:`restart_model`, ensuring the
   object graph reflects the just-saved state. This is now only impozed if the user specified `relaod = True`.

   Parameters
   ----------
   file_name : str or pathlib.Path, optional
       Output path for the saved model file. If omitted (``None``), the method
       uses the instance's existing ``path``. The resolved path is also
       written back to instance `path` attribute for consistency if reload is True.

   reload: bool Optional default is True
        resets the reference path to the one provided after serializing to disk. This implies that the instance `path` will be the provided `file_name`

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
   - If reload is True (default), recompiles the model and restarts the in-memory instance.

   Notes
   -----
   - *Path normalization:* The path is stringified via ``str(file_name)`` just in case it is a pathlib object.

   - *Reload semantics:* Post-save recompilation and restart ensure any code
     generation or cached reflection is refreshed to match the serialized model.

   Examples
   --------
   check the current path before saving the model
       >>> from apsimNGpy.core.apsim import ApsimModel
       >>> from pathlib import Path
       >>> model = ApsimModel("Maize", out_path='saved_maize.apsimx')
       >>> model.path
       scratch\saved_maize.apsimx

   Save to a new path and continue working with the refreshed instance
       >>> model.save(file_name='out_maize.apsimx', reload=True)
       # check the path
       >>> model.path
       'out_maize.apsimx'
       # possible to run again the refreshed model.
       >>> model.run()

   Save to a new path without refreshing the instance path
     >>> model = ApsimModel("Maize",  out_path='saved_maize.apsimx')
     >>> model.save(file_name='out_maize.apsimx', reload=False)
     # check the current reference path for the model.
      >>> model.path 'scratch\saved_maize.apsimx'
      # When reload is False, the original referenced path remains as shown above

   As shown above, everything is saved in the scratch folder; if
   the path is not abolutely provided, e.g., a relative path. If the path is not provided as shown below,
   the reference path is the current path for the isntance model.
      >>> model = ApsimModel("Maize",  out_path='saved_maize.apsimx')
      >>> model.path
      'scratch\saved_maize.apsimx'
      # save the model without providing the path.
      >>> model.save()# uses the default, in this case the defaul path is the existing path
      >>> model.path
      'scratch\saved_maize.apsimx'

   In the above case, both reload = `False` or `True`, will produce the same reference path for the live
   instance class.


   See Also
   --------
   recompile : Rebuild internal/compiled artifacts for the model.
   restart_model : Reload/refresh the model instance after recompilation.
   save_model_to_file : Legacy writer for older APSIM NG versions.

   .. py:property:: apsimNGpy.core.apsim.ApsimModel.results (inherited)

   Legacy method for retrieving simulation results.

   This method is implemented as a ``property`` to enable lazy loading—results are
   only loaded into memory when explicitly accessed. This design helps optimize
   ``memory`` usage, especially for ``large`` simulations.

   It must be called only after invoking ``run()``. If accessed before the simulation
   is run, it will raise an error.

   Notes
   -----
   - The ``run()`` method should be called with a valid ``report name`` or a list of
     report names.
   - If ``report_names`` is not provided (i.e., ``None``), the system will inspect
     the model and automatically detect all available report components. These
     reports will then be used to collect the data.
   - If multiple report names are used, their corresponding data tables will be
     concatenated along the rows.

   Returns
   -------
   pd.DataFrame
       A DataFrame containing the simulation output results.

   Examples
   --------
   >>> from apsimNGpy.core.apsim import ApsimModel
   # create an instance of ApsimModel class
   >>> model = ApsimModel("Maize", out_path="my_maize_model.apsimx")
   # run the simulation
   >>> model.run()
   # get the results
   >>> df = model.results
   # do something with the results e.g. get the mean of numeric columns
   >>> df.mean(numeric_only=True)
   Out[12]:
   CheckpointID                     1.000000
   SimulationID                     1.000000
   Maize.AboveGround.Wt          1225.099950
   Maize.AboveGround.N             12.381196
   Yield                         5636.529504
   Maize.Grain.Wt                 563.652950
   Maize.Grain.Size                 0.284941
   Maize.Grain.NumberFunction    1986.770519
   Maize.Grain.Total.Wt           563.652950
   Maize.Grain.N                    7.459296
   Maize.Total.Wt                1340.837427

   If there are more than one database tables or `reports` as called in APSIM,
   results are concatenated along the axis 0, implying along rows.
   The example below mimics this scenario.

   >>> model.add_db_table(
   ...     variable_spec=['[Clock].Today.Year as year',
   ...                    'sum([Soil].Nutrient.TotalC)/1000 from 01-jan to [clock].Today as soc'],
   ...     rename='soc'
   ... )
   # inspect the reports
   >>> model.inspect_model('Models.Report', fullpath=False)
   ['Report', 'soc']
   >>> model.run()
   >>> model.results
       CheckpointID  SimulationID   Zone  ... source_table    year        soc
   0              1             1  Field  ...       Report     NaN        NaN
   1              1             1  Field  ...       Report     NaN        NaN
   2              1             1  Field  ...       Report     NaN        NaN
   3              1             1  Field  ...       Report     NaN        NaN
   4              1             1  Field  ...       Report     NaN        NaN
   5              1             1  Field  ...       Report     NaN        NaN
   6              1             1  Field  ...       Report     NaN        NaN
   7              1             1  Field  ...       Report     NaN        NaN
   8              1             1  Field  ...       Report     NaN        NaN
   9              1             1  Field  ...       Report     NaN        NaN
   10             1             1  Field  ...          soc  1990.0  77.831512
   11             1             1  Field  ...          soc  1991.0  78.501766
   12             1             1  Field  ...          soc  1992.0  78.916339
   13             1             1  Field  ...          soc  1993.0  78.707094
   14             1             1  Field  ...          soc  1994.0  78.191686
   15             1             1  Field  ...          soc  1995.0  78.573085
   16             1             1  Field  ...          soc  1996.0  78.724598
   17             1             1  Field  ...          soc  1997.0  79.043935
   18             1             1  Field  ...          soc  1998.0  78.343111
   19             1             1  Field  ...          soc  1999.0  78.872767
   20             1             1  Field  ...          soc  2000.0  79.916413
   [21 rows x 17 columns]

   By default all the tables are returned and the column ``source_table`` tells us
   the source table for each row. Since ``results`` is a property attribute,
   which does not take in any argument, we can only decide this when calling the
   ``run`` method as shown below.

   >>> model.run(report_name='soc')
   >>> model.results
       CheckpointID  SimulationID   Zone    year        soc source_table
   0              1             1  Field  1990.0  77.831512          soc
   1              1             1  Field  1991.0  78.501766          soc
   2              1             1  Field  1992.0  78.916339          soc
   3              1             1  Field  1993.0  78.707094          soc
   4              1             1  Field  1994.0  78.191686          soc
   5              1             1  Field  1995.0  78.573085          soc
   6              1             1  Field  1996.0  78.724598          soc
   7              1             1  Field  1997.0  79.043935          soc
   8              1             1  Field  1998.0  78.343111          soc
   9              1             1  Field  1999.0  78.872767          soc
   10             1             1  Field  2000.0  79.916413          soc

   The above example has dataset only from one database table specified at run time.

   See also
   --------
   `get_simulated_output`

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.get_simulated_output(self, report_names: 'Union[str, list]', axis=0, **kwargs) -> 'pd.DataFrame' (inherited)

   Reads report data from CSV files generated by the simulation.

   Parameters:
   -----------
   ``report_names``: Union[str, list]
       Name or list names of report tables to read. These should match the
       report names in the simulation output.

   ``axis`` int, Optional. Default to 0
       concatenation axis numbers for multiple reports or database tables. if axis is 0, source_table column is populated to show source of the data for each row

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
   Examples
   --------
   >>> from apsimNGpy.core.apsim import ApsimModel
   >>> model = ApsimModel(model='Maize')  # replace with your path to the apsim template model
   >>> model.run()  # if we are going to use get_simulated_output, no need to provide the report name in ``run()`` method
   >>> df = model.get_simulated_output(report_names="Report")
       SimulationName  SimulationID  CheckpointID  ...  Maize.Total.Wt     Yield   Zone
   0       Simulation             1             1  ...        1728.427  8469.616  Field
   1       Simulation             1             1  ...         920.854  4668.505  Field
   2       Simulation             1             1  ...         204.118   555.047  Field
   3       Simulation             1             1  ...         869.180  3504.000  Field
   4       Simulation             1             1  ...        1665.475  7820.075  Field
   5       Simulation             1             1  ...        2124.740  8823.517  Field
   6       Simulation             1             1  ...        1235.469  3587.101  Field
   7       Simulation             1             1  ...         951.808  2939.152  Field
   8       Simulation             1             1  ...        1986.968  8379.435  Field
   9       Simulation             1             1  ...        1689.966  7370.301  Field
   [10 rows x 16 columns]

   This method also handles more than one reports as shown below.

   >>> model.add_db_table(
   ...     variable_spec=[
   ...         '[Clock].Today.Year as year',
   ...         'sum([Soil].Nutrient.TotalC)/1000 from 01-jan to [clock].Today as soc'
   ...     ],
   ...     rename='soc'
   ... )
   # inspect the reports
   >>> model.inspect_model('Models.Report', fullpath=False)
   ['Report', 'soc']
   >>> model.run()
   >>> model.get_simulated_output(["soc", "Report"], axis=0)
       CheckpointID  SimulationID  ...  Maize.Grain.N  Maize.Total.Wt
   0              1             1  ...            NaN             NaN
   1              1             1  ...            NaN             NaN
   2              1             1  ...            NaN             NaN
   3              1             1  ...            NaN             NaN
   4              1             1  ...            NaN             NaN
   5              1             1  ...            NaN             NaN
   6              1             1  ...            NaN             NaN
   7              1             1  ...            NaN             NaN
   8              1             1  ...            NaN             NaN
   9              1             1  ...            NaN             NaN
   10             1             1  ...            NaN             NaN
   11             1             1  ...      11.178291     1728.427114
   12             1             1  ...       6.226327      922.393712
   13             1             1  ...       0.752357      204.108770
   14             1             1  ...       4.886844      869.242545
   15             1             1  ...      10.463854     1665.483701
   16             1             1  ...      11.253916     2124.739830
   17             1             1  ...       5.044417     1261.674967
   18             1             1  ...       3.955080      951.303260
   19             1             1  ...      11.080878     1987.106980
   20             1             1  ...       9.751001     1693.893386
   [21 rows x 17 columns]

   >>> model.get_simulated_output(['soc', 'Report'], axis=1)
       CheckpointID  SimulationID  ...  Maize.Grain.N  Maize.Total.Wt
   0              1             1  ...      11.178291     1728.427114
   1              1             1  ...       6.226327      922.393712
   2              1             1  ...       0.752357      204.108770
   3              1             1  ...       4.886844      869.242545
   4              1             1  ...      10.463854     1665.483701
   5              1             1  ...      11.253916     2124.739830
   6              1             1  ...       5.044417     1261.674967
   7              1             1  ...       3.955080      951.303260
   8              1             1  ...      11.080878     1987.106980
   9              1             1  ...       9.751001     1693.893386
   10             1             1  ...            NaN             NaN
   [11 rows x 19 columns]

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.run(self, report_name: 'Union[tuple, list, str]' = None, simulations: 'Union[tuple, list]' = None, clean_up: 'bool' = True, verbose: 'bool' = False, **kwargs) -> "'CoreModel'" (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.rename_model(self, model_type, *, old_name, new_name) (inherited)

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

   .. tip::

        This method uses ``get_or_check_model`` with action='get' to locate the model,
        and then updates the model's `Name` attribute. The model is serialized using the `save()`
        immediately after to apply and enfoce the change.

    Examples
    ---------
       >>> from apsimNGpy.core.apsim import ApsimModel
       >>> model = ApsimModel(model = 'Maize', out_path='my_maize.apsimx')
       >>> model.rename_model(model_type="Models.Core.Simulation", old_name ='Simulation', new_name='my_simulation')
       # check if it has been successfully renamed
       >>> model.inspect_model(model_type='Models.Core.Simulation', fullpath = False)
        ['my_simulation']
       # The alternative is to use model.inspect_file to see your changes
       >>> model.inspect_file()
       └── Simulations: .Simulations
        ├── DataStore: .Simulations.DataStore
        └── my_simulation: .Simulations.my_simulation
            ├── Clock: .Simulations.my_simulation.Clock
            ├── Field: .Simulations.my_simulation.Field
            │   ├── Fertilise at sowing: .Simulations.my_simulation.Field.Fertilise at sowing
            │   ├── Fertiliser: .Simulations.my_simulation.Field.Fertiliser
            │   ├── Harvest: .Simulations.my_simulation.Field.Harvest
            │   ├── Maize: .Simulations.my_simulation.Field.Maize
            │   ├── Report: .Simulations.my_simulation.Field.Report
            │   ├── Soil: .Simulations.my_simulation.Field.Soil
            │   │   ├── Chemical: .Simulations.my_simulation.Field.Soil.Chemical
            │   │   ├── NH4: .Simulations.my_simulation.Field.Soil.NH4
            │   │   ├── NO3: .Simulations.my_simulation.Field.Soil.NO3
            │   │   ├── Organic: .Simulations.my_simulation.Field.Soil.Organic
            │   │   ├── Physical: .Simulations.my_simulation.Field.Soil.Physical
            │   │   │   └── MaizeSoil: .Simulations.my_simulation.Field.Soil.Physical.MaizeSoil
            │   │   ├── Urea: .Simulations.my_simulation.Field.Soil.Urea
            │   │   └── Water: .Simulations.my_simulation.Field.Soil.Water
            │   ├── Sow using a variable rule: .Simulations.my_simulation.Field.Sow using a variable rule
            │   └── SurfaceOrganicMatter: .Simulations.my_simulation.Field.SurfaceOrganicMatter
            ├── Graph: .Simulations.my_simulation.Graph
            │   └── Series: .Simulations.my_simulation.Graph.Series
            ├── MicroClimate: .Simulations.my_simulation.MicroClimate
            ├── SoilArbitrator: .Simulations.my_simulation.SoilArbitrator
            ├── Summary: .Simulations.my_simulation.Summary
            └── Weather: .Simulations.my_simulation.Weather

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.clone_model(self, model_type, model_name, adoptive_parent_type, rename=None, adoptive_parent_name=None) (inherited)

   Clone an existing ``model`` and move it to a specified parent within the simulation structure.
   The function modifies the simulation structure by adding the cloned model to the designated parent.

   This function is useful when a model instance needs to be duplicated and repositioned in the `APSIM` simulation
   hierarchy without manually redefining its structure.

   Parameters:
   ----------
   model_type: Models
       The type of the model to be cloned, e.g., `Models.Simulation` or `Models.Clock`.
   model_name: str
       The unique identification name of the model instance to be cloned, e.g., `"clock1"`.
   adoptive_parent_type: Models
       The type of the new parent model where the cloned model will be placed.
   rename: str, optional
       The new name for the cloned model. If not provided, the clone will be renamed using
       the original name with a `_clone` suffix.
   adoptive_parent_name: str, optional
       The name of the parent model where the cloned model should be moved. If not provided,
       the model will be placed under the default parent of the specified type.
   in_place: bool, optional
       If ``True``, the cloned model remains in the same location but is duplicated. Defaults to ``False``.

   Returns:
   -------
   None

   Example:
   -------
    Create a cloned version of `"clock1"` and place it under `"Simulation"` with the new name `"new_clock`:

       >>> from apsimNGpy.core.apsim import ApsimModel
       >>> model = ApsimModel('Maize', out_path='my_maize.apsimx')
       >>> model.clone_model(model_type='Models.Core.Simulation', model_name="Simulation",
       ... rename="Sim2", adoptive_parent_type = 'Models.Core.Simulations',
       ... adoptive_parent_name='Simulations')
       >>> model.inspect_file()
       └── Simulations: .Simulations
           ├── DataStore: .Simulations.DataStore
           ├── Sim2: .Simulations.Sim2
           │   ├── Clock: .Simulations.Sim2.Clock
           │   ├── Field: .Simulations.Sim2.Field
           │   │   ├── Fertilise at sowing: .Simulations.Sim2.Field.Fertilise at sowing
           │   │   ├── Fertiliser: .Simulations.Sim2.Field.Fertiliser
           │   │   ├── Harvest: .Simulations.Sim2.Field.Harvest
           │   │   ├── Maize: .Simulations.Sim2.Field.Maize
           │   │   ├── Report: .Simulations.Sim2.Field.Report
           │   │   ├── Soil: .Simulations.Sim2.Field.Soil
           │   │   │   ├── Chemical: .Simulations.Sim2.Field.Soil.Chemical
           │   │   │   ├── NH4: .Simulations.Sim2.Field.Soil.NH4
           │   │   │   ├── NO3: .Simulations.Sim2.Field.Soil.NO3
           │   │   │   ├── Organic: .Simulations.Sim2.Field.Soil.Organic
           │   │   │   ├── Physical: .Simulations.Sim2.Field.Soil.Physical
           │   │   │   │   └── MaizeSoil: .Simulations.Sim2.Field.Soil.Physical.MaizeSoil
           │   │   │   ├── Urea: .Simulations.Sim2.Field.Soil.Urea
           │   │   │   └── Water: .Simulations.Sim2.Field.Soil.Water
           │   │   ├── Sow using a variable rule: .Simulations.Sim2.Field.Sow using a variable rule
           │   │   ├── SurfaceOrganicMatter: .Simulations.Sim2.Field.SurfaceOrganicMatter
           │   │   └── soc_table: .Simulations.Sim2.Field.soc_table
           │   ├── Graph: .Simulations.Sim2.Graph
           │   │   └── Series: .Simulations.Sim2.Graph.Series
           │   ├── MicroClimate: .Simulations.Sim2.MicroClimate
           │   ├── SoilArbitrator: .Simulations.Sim2.SoilArbitrator
           │   ├── Summary: .Simulations.Sim2.Summary
           │   └── Weather: .Simulations.Sim2.Weather
           └── Simulation: .Simulations.Simulation
               ├── Clock: .Simulations.Simulation.Clock
               ├── Field: .Simulations.Simulation.Field
               │   ├── Fertilise at sowing: .Simulations.Simulation.Field.Fertilise at sowing
               │   ├── Fertiliser: .Simulations.Simulation.Field.Fertiliser
               │   ├── Harvest: .Simulations.Simulation.Field.Harvest
               │   ├── Maize: .Simulations.Simulation.Field.Maize
               │   ├── Report: .Simulations.Simulation.Field.Report
               │   ├── Soil: .Simulations.Simulation.Field.Soil
               │   │   ├── Chemical: .Simulations.Simulation.Field.Soil.Chemical
               │   │   ├── NH4: .Simulations.Simulation.Field.Soil.NH4
               │   │   ├── NO3: .Simulations.Simulation.Field.Soil.NO3
               │   │   ├── Organic: .Simulations.Simulation.Field.Soil.Organic
               │   │   ├── Physical: .Simulations.Simulation.Field.Soil.Physical
               │   │   │   └── MaizeSoil: .Simulations.Simulation.Field.Soil.Physical.MaizeSoil
               │   │   ├── Urea: .Simulations.Simulation.Field.Soil.Urea
               │   │   └── Water: .Simulations.Simulation.Field.Soil.Water
               │   ├── Sow using a variable rule: .Simulations.Simulation.Field.Sow using a variable rule
               │   ├── SurfaceOrganicMatter: .Simulations.Simulation.Field.SurfaceOrganicMatter
               │   └── soc_table: .Simulations.Simulation.Field.soc_table
               ├── Graph: .Simulations.Simulation.Graph
               │   └── Series: .Simulations.Simulation.Graph.Series
               ├── MicroClimate: .Simulations.Simulation.MicroClimate
               ├── SoilArbitrator: .Simulations.Simulation.SoilArbitrator
               ├── Summary: .Simulations.Simulation.Summary
               └── Weather: .Simulations.Simulation.Weather

   .. py:staticmethod:: apsimNGpy.core.apsim.ApsimModel.find_model(model_name: 'str') (inherited)

   Find a model from the Models namespace and return its path.

   Parameters:
   -----------
   model_name: (str)
     The name of the model to find.
   model_namespace: (object, optional):
      The root namespace (defaults to Models).
   path: (str, optional)
      The accumulated path to the model.

   Returns:
       str: The full path to the model if found, otherwise None.

   Example:
   --------
        >>> from apsimNGpy import core  # doctest:
        >>> model =core.apsim.ApsimModel(model = "Maize", out_path ='my_maize.apsimx')
        >>> model.find_model("Weather")  # doctest: +SKIP
        'Models.Climate.Weather'
        >>> model.find_model("Clock")  # doctest: +SKIP
        'Models.Clock'

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.add_model(self, model_type, adoptive_parent, rename=None, adoptive_parent_name=None, verbose=False, source='Models', source_model_name=None, override=True, **kwargs) (inherited)

   Adds a model to the Models Simulations namespace.

   Some models are restricted to specific parent models, meaning they can only be added to compatible models.
   For example, a Clock model cannot be added to a Soil model.

   Parameters:
   -----------
   model_class: (str or Models object)
      The type of model to add, e.g., `Models.Clock` or just `"Clock"`. if the APSIM Models namespace is exposed to the current script, then model_class can be Models.Clock without strings quotes

   rename (str):
     The new name for the model.

   adoptive_parent: (Models object)
       The target parent where the model will be added or moved e.g `Models.Clock` or `Clock` as string all are valid

   adoptive_parent_name: (Models object, optional)
       Specifies the parent name for precise location. e.g., `Models.Core.Simulation` or ``Simulations`` all are valid

   source: Models, str, CoreModel, ApsimModel object: defaults to Models namespace.
      The source can be an existing Models or string name to point to one of the
      default model examples, which we can extract the model from

   override: bool, optional defaults to `True`.
       When `True` (recommended), it deletes
       any model with the same name and type at the suggested parent location before adding the new model
       if ``False`` and proposed model to be added exists at the parent location;
       `APSIM` automatically generates a new name for the newly added model. This is not recommended.
   Returns:
       None:

   `Models` are modified in place, so models retains the same reference.

   .. caution::
       Added models from ``Models namespace`` are initially empty. Additional configuration is required to set parameters.
       For example, after adding a Clock module, you must set the start and end dates.

   Example
   -------------

   >>> from apsimNGpy import core
   >>> from apsimNGpy.core.core import Models
   >>> model = core.apsim.ApsimModel("Maize")
   >>> model.remove_model(Models.Clock)  # first delete the model
   >>> model.add_model(Models.Clock, adoptive_parent=Models.Core.Simulation, rename='Clock_replaced', verbose=False)

   >>> model.add_model(model_class=Models.Core.Simulation, adoptive_parent=Models.Core.Simulations, rename='Iowa')

   >>> model.preview_simulation()  # doctest: +SKIP

   >>> model.add_model(
   ... Models.Core.Simulation,
   ... adoptive_parent='Simulations',
   ... rename='soybean_replaced',
   ... source='Soybean')  # basically adding another simulation from soybean to the maize simulation

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.detect_model_type(self, model_instance: 'Union[str, Models]') (inherited)

   Detects the model type from a given APSIM model instance or path string.

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.edit_model_by_path(self, path: 'str', **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.edit_model(self, model_type: 'str', model_name: 'str', simulations: 'Union[str, list]' = 'all', verbose=False, **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.add_report_variable(self, variable_spec: 'Union[list, str, tuple]', report_name: 'str' = None, set_event_names: 'Union[str, list]' = None) (inherited)

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
       # isnepct the report
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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.remove_report_variable(self, variable_spec: 'Union[list, tuple, str]', report_name: 'str | None' = None) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.remove_model(self, model_class: 'Models', model_name: 'str' = None) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.move_model(self, model_type: 'Models', new_parent_type: 'Models', model_name: 'str' = None, new_parent_name: 'str' = None, verbose: 'bool' = False, simulations: 'Union[str, list]' = None) (inherited)

   Args:

   - ``model_class`` (Models): type of model tied to Models Namespace

   - ``new_parent_type``: new model parent type (Models)

   - ``model_name``:name of the model e.g., Clock, or Clock2, whatever name that was given to the model

   -  ``new_parent_name``: what is the new parent names =Field2, this field is optional but important if you have nested simulations

   Returns:

     returns instance of apsimNGpy.core.core.apsim.ApsimModel or apsimNGpy.core.core.apsim.CoreModel

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.replicate_file(self, k: 'int', path: 'os.PathLike' = None, suffix: 'str' = 'replica') (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.get_crop_replacement(self, Crop) (inherited)

   :param Crop: crop to get the replacement
   :return: System.Collections.Generic.IEnumerable APSIM plant object

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.inspect_model_parameters(self, model_type: 'Union[Models, str]', model_name: 'str', simulations: 'Union[str, list]' = <UserOptionMissing>, parameters: 'Union[list, set, tuple, str]' = 'all', **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.inspect_model_parameters_by_path(self, path, *, parameters: 'Union[list, set, tuple, str]' = None) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.edit_cultivar(self, *, CultivarName: 'str', commands: 'str', values: 'Any', **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.update_cultivar(self, *, parameters: 'dict', simulations: 'Union[list, tuple]' = None, clear=False, **kwargs) (inherited)

   Update cultivar parameters

    Parameters
    ----------
   ``parameters`` (dict, required) dictionary of cultivar parameters to update.

   ``simulations``, optional
        List or tuples of simulation names to update if `None` update all simulations.

   ``clear`` (bool, optional)
        If `True` remove all existing parameters, by default `False`.

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.recompile_edited_model(self, out_path: 'os.PathLike') (inherited)

   Args:
   ______________
   ``out_path``: os.PathLike object this method is called to convert the simulation object from ConverterReturnType to model like object

   ``return:`` self

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.update_mgt_by_path(self, *, path: 'str', fmt='.', **kwargs) (inherited)

   Args:
   _________________
   ``path``: complete node path to the script manager e.g. '.Simulations.Simulation.Field.Sow using a variable rule'

   ``fmt``: seperator for formatting the path e.g., ".". Other characters can be used with
    caution, e.g., / and clearly declared in fmt argument. If you want to use the forward slash, it will be '/Simulations/Simulation/Field/Sow using a variable rule', fmt = '/'

   ``kwargs``: Corresponding keyword arguments representing the paramters in the script manager and their values. Values is what you want
   to change to; Example here ``Population`` =8.2, values should be entered with their corresponding data types e.g.,
    int, float, bool,str etc.

   return: self

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.replace_model_from(self, model, model_type: 'str', model_name: 'str' = None, target_model_name: 'str' = None, simulations: 'str' = None) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.update_mgt(self, *, management: 'Union[dict, tuple]', simulations: '[list, tuple]' = <UserOptionMissing>, out: '[Path, str]' = None, reload: 'bool' = True, **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.preview_simulation(self) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.change_simulation_dates(self, start_date: 'str' = None, end_date: 'str' = None, simulations: 'Union[tuple, list]' = None) (inherited)

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

   .. py:property:: apsimNGpy.core.apsim.ApsimModel.extract_dates (inherited)

   Get simulation dates in the model.

   @deprecated

   Parameters
   ----------
   ``simulations``, optional
       List of simulation names to get, if ``None`` get all simulations.

   ``Returns``
       ``Dictionary`` of simulation names with dates
   # Example

       >>> from apsimNGpy.core.base_data import load_default_simulations
       >>> model = load_default_simulations(crop='maize')
       >>> changed_dates = model.extract_dates
       >>> print(changed_dates)

          {'Simulation': {'start': datetime.date(2021, 1, 1),
           'end': datetime.date(2021, 1, 12)}}

       .. note::

           It is possible to target a specific simulation by specifying simulation name for this case the name is Simulations,
            so, it could appear as follows;

        >>>model.change_simulation_dates(start_date='2021-01-01', end_date='2021-01-12', simulation = 'Simulation')

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.extract_start_end_years(self, simulations: 'str' = None) (inherited)

   Get simulation dates. deprecated

   Parameters
   ----------
   ``simulations``: (str) optional
       List of simulation names to use if `None` get all simulations.

   ``Returns``
       Dictionary of simulation names with dates.

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.replace_met_file(self, *, weather_file: 'Union[Path, str]', simulations=<UserOptionMissing>, **kwargs) -> "'Self'" (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.get_weather_from_file(self, weather_file, simulations=None) -> "'self'" (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.get_weather_from_web(self, lonlat: 'tuple', start: 'int', end: 'int', simulations=<UserOptionMissing>, source='nasa', filename=None) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.show_met_file_in_simulation(self, simulations: 'list' = None) (inherited)

   Show weather file for all simulations

   @deprecated: use inspect_model_parameters() instead

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.change_report(self, *, command: 'str', report_name='Report', simulations=None, set_DayAfterLastOutput=None, **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.extract_soil_physical(self, simulations: '[tuple, list]' = None) (inherited)

   Find physical soil

   Parameters
   ----------
   ``simulation``, optional
       Simulation name, if `None` use the first simulation.
   Returns
   -------
       APSIM Models.Soils.Physical object

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.extract_any_soil_physical(self, parameter, simulations: '[list, tuple]' = <UserOptionMissing>) (inherited)

   Extracts soil physical parameters in the simulation

   Args::
       ``parameter`` (_string_): string e.g. DUL, SAT
       ``simulations`` (string, optional): Targeted simulation name. Defaults to None.
   ---------------------------------------------------------------------------
   returns an array of the parameter values

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.inspect_model(self, model_type: 'Union[str, Models]', fullpath=True, **kwargs) (inherited)

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

   .. py:property:: apsimNGpy.core.apsim.ApsimModel.configs (inherited)

   records activities or modifications to the model including changes to the file

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.replace_soils_values_by_path(self, node_path: 'str', indices: 'list' = None, **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.replace_soil_property_values(self, *, parameter: 'str', param_values: 'list', soil_child: 'str', simulations: 'list' = <UserOptionMissing>, indices: 'list' = None, crop=None, **kwargs) (inherited)

   Replaces values in any soil property array. The soil property array.

   ``parameter``: str: parameter name e.g., NO3, 'BD'

   ``param_values``: list or tuple: values of the specified soil property name to replace

   ``soil_child``: str: sub child of the soil component e.g., organic, physical etc.

   ``simulations``: list: list of simulations to where the child is found if
     not found, all current simulations will receive the new values, thus defaults to None

   ``indices``: list. Positions in the array which will be replaced. Please note that unlike C#, python satrt counting from 0

   ``crop`` (str, optional): string for soil water replacement. Default is None

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.clean_up(self, db=True, verbose=False, coerce=True, csv=True) (inherited)

   Clears the file cloned the datastore and associated csv files are not deleted if db is set to False defaults to True.

   Returns:
      >>None: This method does not return a value.

   .. caution::

      Please proceed with caution, we assume that if you want to clear the model objects, then you don't need them,
      but by making copy compulsory, then, we are clearing the edited files

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.create_experiment(self, permutation: 'bool' = True, base_name: 'str' = None, **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.refresh_model(self) (inherited)

   for methods that will alter the simulation objects and need refreshing the second time we call
   @return: self for method chaining

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.add_factor(self, specification: 'str', factor_name: 'str' = None, **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.add_fac(self, model_type, parameter, model_name, values, factor_name=None) (inherited)

   Add a factor to the initiated experiment. This should replace add_factor. which has less abstractionn @param
   model_type: model_class from APSIM Models namespace @param parameter: name of the parameter to fill e.g CNR
   @param model_name: name of the model @param values: values of the parameter, could be an iterable for case of
   categorical variables or a string e.g, '0 to 100 step 10 same as [0, 10, 20, 30, ...].
   @param factor_name: name to identify the factor in question
   @return:

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.set_continuous_factor(self, factor_path, lower_bound, upper_bound, interval, factor_name=None) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.set_categorical_factor(self, factor_path: 'str', categories: 'Union[list, tuple]', factor_name: 'str' = None) (inherited)

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

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.add_crop_replacements(self, _crop: 'str') (inherited)

   Adds a replacement folder as a child of the simulations.

   Useful when you intend to edit cultivar **parameters**.

   **Args:**
       ``_crop`` (*str*): Name of the crop to be added to the replacement folder.

   ``Returns:``
       - *ApsimModel*: An instance of `apsimNGpy.core.core.apsim.ApsimModel` or `CoreModel`.

   ``Raises:``
       - *ValueError*: If the specified crop is not found.

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.get_model_paths(self, cultivar=False) -> 'list[str]' (inherited)

   Select out a few model types to use for building the APSIM file inspections

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.inspect_file(self, *, cultivar=False, console=True, **kwargs) (inherited)

   Inspect the file by calling ``inspect_model()`` through ``get_model_paths.``
   This method is important in inspecting the ``whole file`` and also getting the ``scripts paths``

   cultivar: i (bool) includes cultivar paths

   console: (bool) print to the console

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.summarize_numeric(self, data_table: 'Union[str, tuple, list]' = None, columns: 'list' = None, percentiles=(0.25, 0.5, 0.75), round=2) -> 'pd.DataFrame' (inherited)

   Summarize numeric columns in a simulated pandas DataFrame. Useful when you want to quickly look at the simulated data

   Parameters:

       -  data_table (list, tuple, str): The names of the data table attached to the simulations. defaults to all data tables.
       -  specific (list) columns to summarize.
       -  percentiles (tuple): Optional percentiles to include in the summary.
       -  round (int): number of decimal places for rounding off.

   Returns:

       pd.DataFrame: A summary DataFrame with statistics for each numeric column.

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.add_db_table(self, variable_spec: 'list' = None, set_event_names: 'list' = None, rename: 'str' = None, simulation_name: 'Union[str, list, tuple]' = <UserOptionMissing>) (inherited)

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

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.Datastore (inherited)

   Default: ``<member 'Datastore' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.End (inherited)

   Default: ``<member 'End' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.Models (inherited)

   Default: ``<member 'Models' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.Simulations (inherited)

   Default: ``<member 'Simulations' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.Start (inherited)

   Default: ``<member 'Start' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.base_name (inherited)

   Default: ``<member 'base_name' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.copy (inherited)

   Default: ``<member 'copy' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.datastore (inherited)

   Default: ``<member 'datastore' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.experiment (inherited)

   Default: ``<member 'experiment' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.experiment_created (inherited)

   Default: ``<member 'experiment_created' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.factor_names (inherited)

   Default: ``<member 'factor_names' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.factors (inherited)

   Default: ``<member 'factors' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.model (inherited)

   Default: ``<member 'model' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.model_info (inherited)

   Default: ``<member 'model_info' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.others (inherited)

   Default: ``<member 'others' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.out (inherited)

   Default: ``<member 'out' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.out_path (inherited)

   Default: ``<member 'out_path' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.path (inherited)

   Default: ``<member 'path' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.permutation (inherited)

   Default: ``<member 'permutation' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.ran_ok (inherited)

   Default: ``<member 'ran_ok' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.report_names (inherited)

   Default: ``<member 'report_names' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.run_method (inherited)

   Default: ``<member 'run_method' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.set_wd (inherited)

   Default: ``<member 'set_wd' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.wk_info (inherited)

   Default: ``<member 'wk_info' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.apsim.ApsimModel.work_space (inherited)

   Default: ``<member 'work_space' of 'CoreModel' objects>``

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.plot_mva(self, table: pandas.core.frame.DataFrame, time_col: Hashable, response: Hashable, *, window: int = 5, min_period: int = 1, grouping: Union[Hashable, collections.abc.Sequence[Hashable], NoneType] = None, preserve_start: bool = True, kind: str = 'line', estimator='mean', plot_raw: bool = False, raw_alpha: float = 0.35, raw_linewidth: float = 1.0, auto_datetime: bool = False, ylabel: Optional[str] = None, return_data: bool = False, **kwargs) -> seaborn.axisgrid.FacetGrid | tuple[seaborn.axisgrid.FacetGrid, pandas.core.frame.DataFrame] (inherited)

   Plot a centered moving-average (MVA) of a response using ``seaborn.relplot``.

   Enhancements over a direct ``relplot`` call:
   - Computes and plots a smoothed series via :func:`apsimNGpy.stats.data_insights.mva`.
   - Supports multi-column grouping; will auto-construct a composite hue if needed.
   - Optional overlay of the raw (unsmoothed) series for comparison.
   - Stable (mergesort) time ordering.

   Parameters
   ----------
   table : pandas.DataFrame or str
       Data source or table name; if ``None``, use :pyattr:`results`.
   time_col : hashable
       Time (x-axis) column.
   response : hashable
       Response (y) column to smooth.
   window : int, default=5
       MVA window size.
   min_period : int, default=1
       Minimum periods for the rolling mean.
   grouping : hashable or sequence of hashable, optional
       One or more grouping columns.
   preserve_start : bool, default=True
       Preserve initial values when centering.
   kind : {"line","scatter"}, default="line"
       Passed to ``sns.relplot``.
   estimator : str or None, default="mean"
       Passed to ``sns.relplot`` (set to ``None`` to plot raw observations).
   plot_raw : bool, default=False
       Overlay the raw series on each facet.
   raw_alpha : float, default=0.35
       Alpha for the raw overlay.
   raw_linewidth : float, default=1.0
       Line width for the raw overlay.
   auto_datetime : bool, default=False
       Attempt to convert ``time_col`` to datetime.
   ylabel : str, optional
       Custom y-axis label; default is generated from window/response.
   return_data : bool, default=False
       If ``True``, return ``(FacetGrid, smoothed_df)``.

   Returns
   -------
   seaborn.FacetGrid
       The relplot grid, or ``(grid, smoothed_df)`` if ``return_data=True``.

   Notes
   -----
      This function calls :func:`seaborn.relplot` and accepts its keyword arguments
      via ``**kwargs``. See link below for details:

   https://seaborn.pydata.org/generated/seaborn/relplot.html

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.boxplot(self, column, *, table=None, by=None, figsize=(10, 8), grid=False, **kwargs) (inherited)

   Plot a boxplot from simulation results using ``pandas.DataFrame.boxplot``.

   Parameters
   ----------
   column : str
       Column to plot.
   table : str or pandas.DataFrame, optional
       Table name or DataFrame; if omitted, use :pyattr:`results`.
   by : str, optional
       Grouping column.
   figsize : tuple, default=(10, 8)
   grid : bool, default=False
   **kwargs
       Forwarded to :meth:`pandas.DataFrame.boxplot`.

   Returns
   -------
   matplotlib.axes.Axes

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.distribution(self, x, *, table=None, **kwargs) (inherited)

   Plot a uni-variate distribution/histogram using :func:`seaborn.histplot`.

   Parameters
   ----------
   x : str
       Numeric column to plot.
   table : str or pandas.DataFrame, optional
       Table name or DataFrame; if omitted, use :pyattr:`results`.
   **kwargs
       Forwarded to :func:`seaborn.histplot`.

   Raises
   ------
   ValueError
       If ``x`` is a string-typed column.

   Notes
   -----
   This function calls :func:`seaborn.histplot` and accepts its keyword arguments
   via ``**kwargs``. See link below for details:

   https://seaborn.pydata.org/generated/seaborn/histplot.html 


   =================================================================

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.series_plot(self, table=None, *, x: str = None, y: Union[str, list] = None, hue=None, size=None, style=None, units=None, weights=None, palette=None, hue_order=None, hue_norm=None, sizes=None, size_order=None, size_norm=None, dashes=True, markers=None, style_order=None, estimator='mean', errorbar=('ci', 95), n_boot=1000, seed=None, orient='x', sort=True, err_style='band', err_kws=None, legend='auto', ci='deprecated', ax=None, **kwargs) (inherited)

   Just a wrapper for seaborn.lineplot that supports multiple y columns that could be provided as a list

    table : str | [str] |None | None| pandas.DataFrame, optional. Default is None
       If the table names are provided, results are collected from the simulated data, using that table names.
       If None, results will be all the table names inside concatenated along the axis 0 (not recommended)

    If ``y`` is a list of columns, the data are melted into long form and
   the different series are colored by variable name.

   **Kwargs
       Additional keyword args and all other arguments are for Seaborn.lineplot.
       See the reference below for all the kwargs.

   reference; https://seaborn.pydata.org/generated/seaborn.lineplot.html

   Examples
   --------
   >>> model.series_plot(x='Year', y='Yield', table='Report')  # doctest: +SKIP
   >>> model.series_plot(x='Year', y=['SOC1', 'SOC2'], table='Report')  # doctest: +SKIP

   Examples:
   ------------

      >>>from apsimNGpy.core.apsim import ApsimModel
      >>> model = ApsimModel(model= 'Maize')
      # run the results
      >>> model.run(report_names='Report')
      >>>model.series_plot(x='Maize.Grain.Size', y='Yield', table='Report')
      >>>model.render_plot(show=True, ylabel = 'Maize yield', xlabel ='Maize grain size')

   Plot two variables:

      >>>model.series_plot(x='Yield', y=['Maize.Grain.N', 'Maize.Grain.Size'], table= 'Report')

   Notes
   -----
   This function calls :func:`seaborn.lineplot` and accepts its keyword arguments
   via ``**kwargs``. See link below for detailed explanations:

   https://seaborn.pydata.org/generated/seaborn/lineplot.html 

   =============================================================================================================================================

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.scatter_plot(self, table=None, *, x=None, y=None, hue=None, size=None, style=None, palette=None, hue_order=None, hue_norm=None, sizes=None, size_order=None, size_norm=None, markers=True, style_order=None, legend='auto', ax=None, **kwargs) (inherited)

   Scatter plot using :func:`seaborn.scatterplot` with flexible aesthetic mappings.

   Parameters
   ----------
   table : str | [str] |None | None| pandas.DataFrame, optional. Default is None
       If the table names are provided, results are collected from the simulated data, using that table names.
       If None, results will be all the table names inside concatenated along the axis 0 (not recommended)
   x, y, hue, size, style, palette, hue_order, hue_norm, sizes, size_order, size_norm, markers, style_order, legend, ax
       Passed through to :func:`seaborn.scatterplot`.
   **Kwargs
       Additional keyword args for Seaborn.
   See the reference below for all the kwargs.
   reference; https://seaborn.pydata.org/generated/seaborn.scatterplot.html 

   ================================================================================================================================

   .. py:method:: apsimNGpy.core.apsim.ApsimModel.cat_plot(self, table=None, *, x=None, y=None, hue=None, row=None, col=None, kind='strip', estimator='mean', errorbar=('ci', 95), n_boot=1000, seed=None, units=None, weights=None, order=None, hue_order=None, row_order=None, col_order=None, col_wrap=None, height=5, aspect=1, log_scale=None, native_scale=False, formatter=None, orient=None, color=None, palette=None, hue_norm=None, legend='auto', legend_out=True, sharex=True, sharey=True, margin_titles=False, facet_kws=None, **kwargs) (inherited)

    Categorical plot wrapper over :func:`seaborn.catplot`.

   Parameters
   ----------
   table : str or pandas.DataFrame, optional
   x, y, hue, row, col, kind, estimator, errorbar, n_boot, seed, units, weights, order,
   hue_order, row_order, col_order, col_wrap, height, aspect, log_scale, native_scale, formatter,
   orient, color, palette, hue_norm, legend, legend_out, sharex, sharey, margin_titles, facet_kws
       Passed through to :func:`seaborn.catplot`.
   **kwargs
       Additional keyword args for Seaborn.

   Returns
   -------
   seaborn.axisgrid.FacetGrid

   reference https://seaborn.pydata.org/generated/seaborn.catplot.html

   =========================================================================================================

apsimNGpy.core.config
---------------------

Functions
^^^^^^^^^

.. py:function:: apsimNGpy.core.config.any_bin_path_from_env() -> pathlib.Path

   Finalize resolving the real APSIM bin path or raise a clear error.

   APSIM bin path expected in environment variables:keys include:

           APSIM_BIN_PATH / APSIM_PATH / APSIM/ Models

.. py:function:: apsimNGpy.core.config.get_bin_use_history()

   shows the bins that have been used only those still available on the computer as valid paths are shown.

   @return: list[paths]

.. py:function:: apsimNGpy.core.config.list_drives()

   for windows-only
   @return: list of available drives on windows pc

.. py:function:: apsimNGpy.core.config.scan_drive_for_bin()

   This function uses scan_dir_for_bin to scan all drive directories.
   for Windows only

.. py:function:: apsimNGpy.core.config.set_apsim_bin_path(path: Union[str, pathlib.Path], raise_errors: bool = True, verbose: bool = False) -> bool

   Validate and persist the APSIM binary folder path.

   The provided `path` should point to (or contain) the APSIM `bin` directory that
   includes the required binaries:

     - Windows: Models.dll AND Models.exe
     - macOS/Linux: Models.dll AND Models (unix executable)

   If `path` is a parent directory, the function will search recursively to locate
   a matching `bin` directory. The first match is used.

   Returns
   -------
   bool
       True if the configuration was updated (or already valid and set to the same
       resolved path), False if validation failed and `raise_errors=False`.

   Raises
   ------
   ValueError
       If no valid APSIM binary directory is found and `raise_errors=True`.

   Examples
   --------
   >>> from apsimNGpy.core import config
   >>> # Check the current path
   >>> current = config.get_apsim_bin_path()
   >>> # Set the desired path (either the bin folder or a parent)
   >>> config.set_apsim_bin_path('/path/to/APSIM/2025/bin', verbose=True)

.. py:function:: apsimNGpy.core.config.stamp_name_with_version(file_name)

   we stamp every file name with the version, which allows the user to open it in the appropriate version it was created
   @param file_name: path to the would be.apsimx file
   @return: path to the stamped file

apsimNGpy.core.experimentmanager
--------------------------------

Classes
^^^^^^^

.. py:class:: apsimNGpy.core.experimentmanager.ExperimentManager

   Main class for apsimNGpy modules.
   It inherits from the CoreModel class and therefore has access to a repertoire of methods from it.

   This implies that you can still run the model and modify parameters as needed.
   Example:
       >>> from apsimNGpy.core.apsim import ApsimModel
       >>> from pathlib import Path
       >>> model = ApsimModel('Maize', out_path=Path.home()/'apsim_model_example.apsimx')
       >>> model.run(report_name='Report') # report is the default, please replace it as needed

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.__init__(self, model, out_path=None)

   Initialize self.  See help(type(self)) for accurate signature.

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.init_experiment(self, permutation=True)

   Initializes the factorial experiment structure inside the APSIM file.

   Args:
       permutation (bool): If True, enables permutation mode; otherwise, uses standard factor crossing.

   Side Effects:
       Replaces any existing ExperimentManager node with a new configuration.
       Clones the base simulation and adds it under the experiment.

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.add_factor(self, specification: str, factor_name: str = None, **kwargs)

   Adds a new factor to the experiment based on an APSIM script specification.

   Args:
       specification (str): A script-like APSIM expression that defines the parameter variation.
       factor_name (str, optional): A unique name for the factor; auto-generated if not provided.
       **kwargs: Optional metadata or configuration (not yet used internally).

   Raises:
       ValueError: If a Script-based specification references a non-existent or unlinked manager script.

   Side Effects:
       Inserts the factor into the appropriate parent node (Permutation or Factors).
       If a factor at the same index already exists, it is safely deleted before inserting the new one.

   .. py:property:: apsimNGpy.core.experimentmanager.ExperimentManager.n_factors

   Returns:
       int: The total number of active factor specifications currently added to the experiment.

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.finalize(self)

   "
   Finalizes the experiment setup by re-creating the internal APSIM factor nodes from specs.

   This method is designed as a guard against unintended modifications and ensures that all
   factor definitions are fully resolved and written before saving.

   Side Effects:
       Clears existing children from the parent factor node.
       Re-creates and attaches each factor as a new node.
       Triggers model saving.

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.get_soil_from_web(self, simulation_name: Union[str, tuple, NoneType] = None, *, lonlat: Optional[System.Tuple[Double,Double]] = None, soil_series: Optional[str] = None, thickness_sequence: Optional[Sequence[float]] = 'auto', thickness_value: int = None, max_depth: Optional[int] = 2400, n_layers: int = 10, thinnest_layer: int = 100, thickness_growth_rate: float = 1.5, edit_sections: Optional[Sequence[str]] = None, attach_missing_sections: bool = True, additional_plants: tuple = None, adjust_dul: bool = True) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.adjust_dul(self, simulations: Union[tuple, list] = None) (inherited)

   - This method checks whether the soil ``SAT`` is above or below ``DUL`` and decreases ``DUL``  values accordingly

   - Need to call this method everytime ``SAT`` is changed, or ``DUL`` is changed accordingly.

   ``simulations``: str, name of the simulation where we want to adjust DUL and SAT according.

   ``returns``:

       model the object for method chaining

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.replace_downloaded_soils(self, soil_tables: Union[dict, list], simulation_names: Union[tuple, list], **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.spin_up(self, report_name: str = 'Report', start=None, end=None, spin_var='Carbon', simulations=None) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.read_apsimx_data(self, table=None) (inherited)

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

   .. py:property:: apsimNGpy.core.experimentmanager.ExperimentManager.simulations (inherited)

   Retrieve simulation nodes in the APSIMx `Model.Core.Simulations` object.

   We search all-Models.Core.Simulation in the scope of Model.Core.Simulations. Please note the difference
   Simulations is the whole json object Simulation is the child with the field zones, crops, soils and managers.

   Any structure of apsimx file can be handled.

   ..note::

        The simulations are c# referenced objects, and their manipulation maybe for advanced users only.

   .. py:property:: apsimNGpy.core.experimentmanager.ExperimentManager.simulation_names (inherited)

   @deprecated will be removed in future releases. Please use inspect_model function instead.

   retrieves the name of the simulations in the APSIMx file
   @return: list of simulation names

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.restart_model(self, model_info=None) (inherited)

   ``model_info``: A named tuple object returned by `load_apsim_model` from the `model_loader` module.

   Notes:
   - This parameter is crucial whenever we need to ``reinitialize`` the model, especially after updating management practices or editing the file.
   - In some cases, this method is executed automatically.
   - If ``model_info`` is not specified, the simulation will be reinitialized from `self`.

   This function is called by ``save_edited_file`` and ``update_mgt``.

   :return: self

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.save(self, file_name: 'Union[str, Path, None]' = None, reload=True) (inherited)

   Saves the current APSIM NG model (``Simulations``) to disk and refresh runtime state.

   This method writes the model to a file, using a version-aware strategy:

   After writing, the model is recompiled via :func:`recompile(self)` and the
   in-memory instance is refreshed using :meth:`restart_model`, ensuring the
   object graph reflects the just-saved state. This is now only impozed if the user specified `relaod = True`.

   Parameters
   ----------
   file_name : str or pathlib.Path, optional
       Output path for the saved model file. If omitted (``None``), the method
       uses the instance's existing ``path``. The resolved path is also
       written back to instance `path` attribute for consistency if reload is True.

   reload: bool Optional default is True
        resets the reference path to the one provided after serializing to disk. This implies that the instance `path` will be the provided `file_name`

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
   - If reload is True (default), recompiles the model and restarts the in-memory instance.

   Notes
   -----
   - *Path normalization:* The path is stringified via ``str(file_name)`` just in case it is a pathlib object.

   - *Reload semantics:* Post-save recompilation and restart ensure any code
     generation or cached reflection is refreshed to match the serialized model.

   Examples
   --------
   check the current path before saving the model
       >>> from apsimNGpy.core.apsim import ApsimModel
       >>> from pathlib import Path
       >>> model = ApsimModel("Maize", out_path='saved_maize.apsimx')
       >>> model.path
       scratch\saved_maize.apsimx

   Save to a new path and continue working with the refreshed instance
       >>> model.save(file_name='out_maize.apsimx', reload=True)
       # check the path
       >>> model.path
       'out_maize.apsimx'
       # possible to run again the refreshed model.
       >>> model.run()

   Save to a new path without refreshing the instance path
     >>> model = ApsimModel("Maize",  out_path='saved_maize.apsimx')
     >>> model.save(file_name='out_maize.apsimx', reload=False)
     # check the current reference path for the model.
      >>> model.path 'scratch\saved_maize.apsimx'
      # When reload is False, the original referenced path remains as shown above

   As shown above, everything is saved in the scratch folder; if
   the path is not abolutely provided, e.g., a relative path. If the path is not provided as shown below,
   the reference path is the current path for the isntance model.
      >>> model = ApsimModel("Maize",  out_path='saved_maize.apsimx')
      >>> model.path
      'scratch\saved_maize.apsimx'
      # save the model without providing the path.
      >>> model.save()# uses the default, in this case the defaul path is the existing path
      >>> model.path
      'scratch\saved_maize.apsimx'

   In the above case, both reload = `False` or `True`, will produce the same reference path for the live
   instance class.


   See Also
   --------
   recompile : Rebuild internal/compiled artifacts for the model.
   restart_model : Reload/refresh the model instance after recompilation.
   save_model_to_file : Legacy writer for older APSIM NG versions.

   .. py:property:: apsimNGpy.core.experimentmanager.ExperimentManager.results (inherited)

   Legacy method for retrieving simulation results.

   This method is implemented as a ``property`` to enable lazy loading—results are
   only loaded into memory when explicitly accessed. This design helps optimize
   ``memory`` usage, especially for ``large`` simulations.

   It must be called only after invoking ``run()``. If accessed before the simulation
   is run, it will raise an error.

   Notes
   -----
   - The ``run()`` method should be called with a valid ``report name`` or a list of
     report names.
   - If ``report_names`` is not provided (i.e., ``None``), the system will inspect
     the model and automatically detect all available report components. These
     reports will then be used to collect the data.
   - If multiple report names are used, their corresponding data tables will be
     concatenated along the rows.

   Returns
   -------
   pd.DataFrame
       A DataFrame containing the simulation output results.

   Examples
   --------
   >>> from apsimNGpy.core.apsim import ApsimModel
   # create an instance of ApsimModel class
   >>> model = ApsimModel("Maize", out_path="my_maize_model.apsimx")
   # run the simulation
   >>> model.run()
   # get the results
   >>> df = model.results
   # do something with the results e.g. get the mean of numeric columns
   >>> df.mean(numeric_only=True)
   Out[12]:
   CheckpointID                     1.000000
   SimulationID                     1.000000
   Maize.AboveGround.Wt          1225.099950
   Maize.AboveGround.N             12.381196
   Yield                         5636.529504
   Maize.Grain.Wt                 563.652950
   Maize.Grain.Size                 0.284941
   Maize.Grain.NumberFunction    1986.770519
   Maize.Grain.Total.Wt           563.652950
   Maize.Grain.N                    7.459296
   Maize.Total.Wt                1340.837427

   If there are more than one database tables or `reports` as called in APSIM,
   results are concatenated along the axis 0, implying along rows.
   The example below mimics this scenario.

   >>> model.add_db_table(
   ...     variable_spec=['[Clock].Today.Year as year',
   ...                    'sum([Soil].Nutrient.TotalC)/1000 from 01-jan to [clock].Today as soc'],
   ...     rename='soc'
   ... )
   # inspect the reports
   >>> model.inspect_model('Models.Report', fullpath=False)
   ['Report', 'soc']
   >>> model.run()
   >>> model.results
       CheckpointID  SimulationID   Zone  ... source_table    year        soc
   0              1             1  Field  ...       Report     NaN        NaN
   1              1             1  Field  ...       Report     NaN        NaN
   2              1             1  Field  ...       Report     NaN        NaN
   3              1             1  Field  ...       Report     NaN        NaN
   4              1             1  Field  ...       Report     NaN        NaN
   5              1             1  Field  ...       Report     NaN        NaN
   6              1             1  Field  ...       Report     NaN        NaN
   7              1             1  Field  ...       Report     NaN        NaN
   8              1             1  Field  ...       Report     NaN        NaN
   9              1             1  Field  ...       Report     NaN        NaN
   10             1             1  Field  ...          soc  1990.0  77.831512
   11             1             1  Field  ...          soc  1991.0  78.501766
   12             1             1  Field  ...          soc  1992.0  78.916339
   13             1             1  Field  ...          soc  1993.0  78.707094
   14             1             1  Field  ...          soc  1994.0  78.191686
   15             1             1  Field  ...          soc  1995.0  78.573085
   16             1             1  Field  ...          soc  1996.0  78.724598
   17             1             1  Field  ...          soc  1997.0  79.043935
   18             1             1  Field  ...          soc  1998.0  78.343111
   19             1             1  Field  ...          soc  1999.0  78.872767
   20             1             1  Field  ...          soc  2000.0  79.916413
   [21 rows x 17 columns]

   By default all the tables are returned and the column ``source_table`` tells us
   the source table for each row. Since ``results`` is a property attribute,
   which does not take in any argument, we can only decide this when calling the
   ``run`` method as shown below.

   >>> model.run(report_name='soc')
   >>> model.results
       CheckpointID  SimulationID   Zone    year        soc source_table
   0              1             1  Field  1990.0  77.831512          soc
   1              1             1  Field  1991.0  78.501766          soc
   2              1             1  Field  1992.0  78.916339          soc
   3              1             1  Field  1993.0  78.707094          soc
   4              1             1  Field  1994.0  78.191686          soc
   5              1             1  Field  1995.0  78.573085          soc
   6              1             1  Field  1996.0  78.724598          soc
   7              1             1  Field  1997.0  79.043935          soc
   8              1             1  Field  1998.0  78.343111          soc
   9              1             1  Field  1999.0  78.872767          soc
   10             1             1  Field  2000.0  79.916413          soc

   The above example has dataset only from one database table specified at run time.

   See also
   --------
   `get_simulated_output`

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.get_simulated_output(self, report_names: 'Union[str, list]', axis=0, **kwargs) -> 'pd.DataFrame' (inherited)

   Reads report data from CSV files generated by the simulation.

   Parameters:
   -----------
   ``report_names``: Union[str, list]
       Name or list names of report tables to read. These should match the
       report names in the simulation output.

   ``axis`` int, Optional. Default to 0
       concatenation axis numbers for multiple reports or database tables. if axis is 0, source_table column is populated to show source of the data for each row

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
   Examples
   --------
   >>> from apsimNGpy.core.apsim import ApsimModel
   >>> model = ApsimModel(model='Maize')  # replace with your path to the apsim template model
   >>> model.run()  # if we are going to use get_simulated_output, no need to provide the report name in ``run()`` method
   >>> df = model.get_simulated_output(report_names="Report")
       SimulationName  SimulationID  CheckpointID  ...  Maize.Total.Wt     Yield   Zone
   0       Simulation             1             1  ...        1728.427  8469.616  Field
   1       Simulation             1             1  ...         920.854  4668.505  Field
   2       Simulation             1             1  ...         204.118   555.047  Field
   3       Simulation             1             1  ...         869.180  3504.000  Field
   4       Simulation             1             1  ...        1665.475  7820.075  Field
   5       Simulation             1             1  ...        2124.740  8823.517  Field
   6       Simulation             1             1  ...        1235.469  3587.101  Field
   7       Simulation             1             1  ...         951.808  2939.152  Field
   8       Simulation             1             1  ...        1986.968  8379.435  Field
   9       Simulation             1             1  ...        1689.966  7370.301  Field
   [10 rows x 16 columns]

   This method also handles more than one reports as shown below.

   >>> model.add_db_table(
   ...     variable_spec=[
   ...         '[Clock].Today.Year as year',
   ...         'sum([Soil].Nutrient.TotalC)/1000 from 01-jan to [clock].Today as soc'
   ...     ],
   ...     rename='soc'
   ... )
   # inspect the reports
   >>> model.inspect_model('Models.Report', fullpath=False)
   ['Report', 'soc']
   >>> model.run()
   >>> model.get_simulated_output(["soc", "Report"], axis=0)
       CheckpointID  SimulationID  ...  Maize.Grain.N  Maize.Total.Wt
   0              1             1  ...            NaN             NaN
   1              1             1  ...            NaN             NaN
   2              1             1  ...            NaN             NaN
   3              1             1  ...            NaN             NaN
   4              1             1  ...            NaN             NaN
   5              1             1  ...            NaN             NaN
   6              1             1  ...            NaN             NaN
   7              1             1  ...            NaN             NaN
   8              1             1  ...            NaN             NaN
   9              1             1  ...            NaN             NaN
   10             1             1  ...            NaN             NaN
   11             1             1  ...      11.178291     1728.427114
   12             1             1  ...       6.226327      922.393712
   13             1             1  ...       0.752357      204.108770
   14             1             1  ...       4.886844      869.242545
   15             1             1  ...      10.463854     1665.483701
   16             1             1  ...      11.253916     2124.739830
   17             1             1  ...       5.044417     1261.674967
   18             1             1  ...       3.955080      951.303260
   19             1             1  ...      11.080878     1987.106980
   20             1             1  ...       9.751001     1693.893386
   [21 rows x 17 columns]

   >>> model.get_simulated_output(['soc', 'Report'], axis=1)
       CheckpointID  SimulationID  ...  Maize.Grain.N  Maize.Total.Wt
   0              1             1  ...      11.178291     1728.427114
   1              1             1  ...       6.226327      922.393712
   2              1             1  ...       0.752357      204.108770
   3              1             1  ...       4.886844      869.242545
   4              1             1  ...      10.463854     1665.483701
   5              1             1  ...      11.253916     2124.739830
   6              1             1  ...       5.044417     1261.674967
   7              1             1  ...       3.955080      951.303260
   8              1             1  ...      11.080878     1987.106980
   9              1             1  ...       9.751001     1693.893386
   10             1             1  ...            NaN             NaN
   [11 rows x 19 columns]

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.run(self, report_name: 'Union[tuple, list, str]' = None, simulations: 'Union[tuple, list]' = None, clean_up: 'bool' = True, verbose: 'bool' = False, **kwargs) -> "'CoreModel'" (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.rename_model(self, model_type, *, old_name, new_name) (inherited)

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

   .. tip::

        This method uses ``get_or_check_model`` with action='get' to locate the model,
        and then updates the model's `Name` attribute. The model is serialized using the `save()`
        immediately after to apply and enfoce the change.

    Examples
    ---------
       >>> from apsimNGpy.core.apsim import ApsimModel
       >>> model = ApsimModel(model = 'Maize', out_path='my_maize.apsimx')
       >>> model.rename_model(model_type="Models.Core.Simulation", old_name ='Simulation', new_name='my_simulation')
       # check if it has been successfully renamed
       >>> model.inspect_model(model_type='Models.Core.Simulation', fullpath = False)
        ['my_simulation']
       # The alternative is to use model.inspect_file to see your changes
       >>> model.inspect_file()
       └── Simulations: .Simulations
        ├── DataStore: .Simulations.DataStore
        └── my_simulation: .Simulations.my_simulation
            ├── Clock: .Simulations.my_simulation.Clock
            ├── Field: .Simulations.my_simulation.Field
            │   ├── Fertilise at sowing: .Simulations.my_simulation.Field.Fertilise at sowing
            │   ├── Fertiliser: .Simulations.my_simulation.Field.Fertiliser
            │   ├── Harvest: .Simulations.my_simulation.Field.Harvest
            │   ├── Maize: .Simulations.my_simulation.Field.Maize
            │   ├── Report: .Simulations.my_simulation.Field.Report
            │   ├── Soil: .Simulations.my_simulation.Field.Soil
            │   │   ├── Chemical: .Simulations.my_simulation.Field.Soil.Chemical
            │   │   ├── NH4: .Simulations.my_simulation.Field.Soil.NH4
            │   │   ├── NO3: .Simulations.my_simulation.Field.Soil.NO3
            │   │   ├── Organic: .Simulations.my_simulation.Field.Soil.Organic
            │   │   ├── Physical: .Simulations.my_simulation.Field.Soil.Physical
            │   │   │   └── MaizeSoil: .Simulations.my_simulation.Field.Soil.Physical.MaizeSoil
            │   │   ├── Urea: .Simulations.my_simulation.Field.Soil.Urea
            │   │   └── Water: .Simulations.my_simulation.Field.Soil.Water
            │   ├── Sow using a variable rule: .Simulations.my_simulation.Field.Sow using a variable rule
            │   └── SurfaceOrganicMatter: .Simulations.my_simulation.Field.SurfaceOrganicMatter
            ├── Graph: .Simulations.my_simulation.Graph
            │   └── Series: .Simulations.my_simulation.Graph.Series
            ├── MicroClimate: .Simulations.my_simulation.MicroClimate
            ├── SoilArbitrator: .Simulations.my_simulation.SoilArbitrator
            ├── Summary: .Simulations.my_simulation.Summary
            └── Weather: .Simulations.my_simulation.Weather

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.clone_model(self, model_type, model_name, adoptive_parent_type, rename=None, adoptive_parent_name=None) (inherited)

   Clone an existing ``model`` and move it to a specified parent within the simulation structure.
   The function modifies the simulation structure by adding the cloned model to the designated parent.

   This function is useful when a model instance needs to be duplicated and repositioned in the `APSIM` simulation
   hierarchy without manually redefining its structure.

   Parameters:
   ----------
   model_type: Models
       The type of the model to be cloned, e.g., `Models.Simulation` or `Models.Clock`.
   model_name: str
       The unique identification name of the model instance to be cloned, e.g., `"clock1"`.
   adoptive_parent_type: Models
       The type of the new parent model where the cloned model will be placed.
   rename: str, optional
       The new name for the cloned model. If not provided, the clone will be renamed using
       the original name with a `_clone` suffix.
   adoptive_parent_name: str, optional
       The name of the parent model where the cloned model should be moved. If not provided,
       the model will be placed under the default parent of the specified type.
   in_place: bool, optional
       If ``True``, the cloned model remains in the same location but is duplicated. Defaults to ``False``.

   Returns:
   -------
   None

   Example:
   -------
    Create a cloned version of `"clock1"` and place it under `"Simulation"` with the new name `"new_clock`:

       >>> from apsimNGpy.core.apsim import ApsimModel
       >>> model = ApsimModel('Maize', out_path='my_maize.apsimx')
       >>> model.clone_model(model_type='Models.Core.Simulation', model_name="Simulation",
       ... rename="Sim2", adoptive_parent_type = 'Models.Core.Simulations',
       ... adoptive_parent_name='Simulations')
       >>> model.inspect_file()
       └── Simulations: .Simulations
           ├── DataStore: .Simulations.DataStore
           ├── Sim2: .Simulations.Sim2
           │   ├── Clock: .Simulations.Sim2.Clock
           │   ├── Field: .Simulations.Sim2.Field
           │   │   ├── Fertilise at sowing: .Simulations.Sim2.Field.Fertilise at sowing
           │   │   ├── Fertiliser: .Simulations.Sim2.Field.Fertiliser
           │   │   ├── Harvest: .Simulations.Sim2.Field.Harvest
           │   │   ├── Maize: .Simulations.Sim2.Field.Maize
           │   │   ├── Report: .Simulations.Sim2.Field.Report
           │   │   ├── Soil: .Simulations.Sim2.Field.Soil
           │   │   │   ├── Chemical: .Simulations.Sim2.Field.Soil.Chemical
           │   │   │   ├── NH4: .Simulations.Sim2.Field.Soil.NH4
           │   │   │   ├── NO3: .Simulations.Sim2.Field.Soil.NO3
           │   │   │   ├── Organic: .Simulations.Sim2.Field.Soil.Organic
           │   │   │   ├── Physical: .Simulations.Sim2.Field.Soil.Physical
           │   │   │   │   └── MaizeSoil: .Simulations.Sim2.Field.Soil.Physical.MaizeSoil
           │   │   │   ├── Urea: .Simulations.Sim2.Field.Soil.Urea
           │   │   │   └── Water: .Simulations.Sim2.Field.Soil.Water
           │   │   ├── Sow using a variable rule: .Simulations.Sim2.Field.Sow using a variable rule
           │   │   ├── SurfaceOrganicMatter: .Simulations.Sim2.Field.SurfaceOrganicMatter
           │   │   └── soc_table: .Simulations.Sim2.Field.soc_table
           │   ├── Graph: .Simulations.Sim2.Graph
           │   │   └── Series: .Simulations.Sim2.Graph.Series
           │   ├── MicroClimate: .Simulations.Sim2.MicroClimate
           │   ├── SoilArbitrator: .Simulations.Sim2.SoilArbitrator
           │   ├── Summary: .Simulations.Sim2.Summary
           │   └── Weather: .Simulations.Sim2.Weather
           └── Simulation: .Simulations.Simulation
               ├── Clock: .Simulations.Simulation.Clock
               ├── Field: .Simulations.Simulation.Field
               │   ├── Fertilise at sowing: .Simulations.Simulation.Field.Fertilise at sowing
               │   ├── Fertiliser: .Simulations.Simulation.Field.Fertiliser
               │   ├── Harvest: .Simulations.Simulation.Field.Harvest
               │   ├── Maize: .Simulations.Simulation.Field.Maize
               │   ├── Report: .Simulations.Simulation.Field.Report
               │   ├── Soil: .Simulations.Simulation.Field.Soil
               │   │   ├── Chemical: .Simulations.Simulation.Field.Soil.Chemical
               │   │   ├── NH4: .Simulations.Simulation.Field.Soil.NH4
               │   │   ├── NO3: .Simulations.Simulation.Field.Soil.NO3
               │   │   ├── Organic: .Simulations.Simulation.Field.Soil.Organic
               │   │   ├── Physical: .Simulations.Simulation.Field.Soil.Physical
               │   │   │   └── MaizeSoil: .Simulations.Simulation.Field.Soil.Physical.MaizeSoil
               │   │   ├── Urea: .Simulations.Simulation.Field.Soil.Urea
               │   │   └── Water: .Simulations.Simulation.Field.Soil.Water
               │   ├── Sow using a variable rule: .Simulations.Simulation.Field.Sow using a variable rule
               │   ├── SurfaceOrganicMatter: .Simulations.Simulation.Field.SurfaceOrganicMatter
               │   └── soc_table: .Simulations.Simulation.Field.soc_table
               ├── Graph: .Simulations.Simulation.Graph
               │   └── Series: .Simulations.Simulation.Graph.Series
               ├── MicroClimate: .Simulations.Simulation.MicroClimate
               ├── SoilArbitrator: .Simulations.Simulation.SoilArbitrator
               ├── Summary: .Simulations.Simulation.Summary
               └── Weather: .Simulations.Simulation.Weather

   .. py:staticmethod:: apsimNGpy.core.experimentmanager.ExperimentManager.find_model(model_name: 'str') (inherited)

   Find a model from the Models namespace and return its path.

   Parameters:
   -----------
   model_name: (str)
     The name of the model to find.
   model_namespace: (object, optional):
      The root namespace (defaults to Models).
   path: (str, optional)
      The accumulated path to the model.

   Returns:
       str: The full path to the model if found, otherwise None.

   Example:
   --------
        >>> from apsimNGpy import core  # doctest:
        >>> model =core.apsim.ApsimModel(model = "Maize", out_path ='my_maize.apsimx')
        >>> model.find_model("Weather")  # doctest: +SKIP
        'Models.Climate.Weather'
        >>> model.find_model("Clock")  # doctest: +SKIP
        'Models.Clock'

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.add_model(self, model_type, adoptive_parent, rename=None, adoptive_parent_name=None, verbose=False, source='Models', source_model_name=None, override=True, **kwargs) (inherited)

   Adds a model to the Models Simulations namespace.

   Some models are restricted to specific parent models, meaning they can only be added to compatible models.
   For example, a Clock model cannot be added to a Soil model.

   Parameters:
   -----------
   model_class: (str or Models object)
      The type of model to add, e.g., `Models.Clock` or just `"Clock"`. if the APSIM Models namespace is exposed to the current script, then model_class can be Models.Clock without strings quotes

   rename (str):
     The new name for the model.

   adoptive_parent: (Models object)
       The target parent where the model will be added or moved e.g `Models.Clock` or `Clock` as string all are valid

   adoptive_parent_name: (Models object, optional)
       Specifies the parent name for precise location. e.g., `Models.Core.Simulation` or ``Simulations`` all are valid

   source: Models, str, CoreModel, ApsimModel object: defaults to Models namespace.
      The source can be an existing Models or string name to point to one of the
      default model examples, which we can extract the model from

   override: bool, optional defaults to `True`.
       When `True` (recommended), it deletes
       any model with the same name and type at the suggested parent location before adding the new model
       if ``False`` and proposed model to be added exists at the parent location;
       `APSIM` automatically generates a new name for the newly added model. This is not recommended.
   Returns:
       None:

   `Models` are modified in place, so models retains the same reference.

   .. caution::
       Added models from ``Models namespace`` are initially empty. Additional configuration is required to set parameters.
       For example, after adding a Clock module, you must set the start and end dates.

   Example
   -------------

   >>> from apsimNGpy import core
   >>> from apsimNGpy.core.core import Models
   >>> model = core.apsim.ApsimModel("Maize")
   >>> model.remove_model(Models.Clock)  # first delete the model
   >>> model.add_model(Models.Clock, adoptive_parent=Models.Core.Simulation, rename='Clock_replaced', verbose=False)

   >>> model.add_model(model_class=Models.Core.Simulation, adoptive_parent=Models.Core.Simulations, rename='Iowa')

   >>> model.preview_simulation()  # doctest: +SKIP

   >>> model.add_model(
   ... Models.Core.Simulation,
   ... adoptive_parent='Simulations',
   ... rename='soybean_replaced',
   ... source='Soybean')  # basically adding another simulation from soybean to the maize simulation

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.detect_model_type(self, model_instance: 'Union[str, Models]') (inherited)

   Detects the model type from a given APSIM model instance or path string.

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.edit_model_by_path(self, path: 'str', **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.edit_model(self, model_type: 'str', model_name: 'str', simulations: 'Union[str, list]' = 'all', verbose=False, **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.add_report_variable(self, variable_spec: 'Union[list, str, tuple]', report_name: 'str' = None, set_event_names: 'Union[str, list]' = None) (inherited)

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
       # isnepct the report
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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.remove_report_variable(self, variable_spec: 'Union[list, tuple, str]', report_name: 'str | None' = None) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.remove_model(self, model_class: 'Models', model_name: 'str' = None) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.move_model(self, model_type: 'Models', new_parent_type: 'Models', model_name: 'str' = None, new_parent_name: 'str' = None, verbose: 'bool' = False, simulations: 'Union[str, list]' = None) (inherited)

   Args:

   - ``model_class`` (Models): type of model tied to Models Namespace

   - ``new_parent_type``: new model parent type (Models)

   - ``model_name``:name of the model e.g., Clock, or Clock2, whatever name that was given to the model

   -  ``new_parent_name``: what is the new parent names =Field2, this field is optional but important if you have nested simulations

   Returns:

     returns instance of apsimNGpy.core.core.apsim.ApsimModel or apsimNGpy.core.core.apsim.CoreModel

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.replicate_file(self, k: 'int', path: 'os.PathLike' = None, suffix: 'str' = 'replica') (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.get_crop_replacement(self, Crop) (inherited)

   :param Crop: crop to get the replacement
   :return: System.Collections.Generic.IEnumerable APSIM plant object

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.inspect_model_parameters(self, model_type: 'Union[Models, str]', model_name: 'str', simulations: 'Union[str, list]' = <UserOptionMissing>, parameters: 'Union[list, set, tuple, str]' = 'all', **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.inspect_model_parameters_by_path(self, path, *, parameters: 'Union[list, set, tuple, str]' = None) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.edit_cultivar(self, *, CultivarName: 'str', commands: 'str', values: 'Any', **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.update_cultivar(self, *, parameters: 'dict', simulations: 'Union[list, tuple]' = None, clear=False, **kwargs) (inherited)

   Update cultivar parameters

    Parameters
    ----------
   ``parameters`` (dict, required) dictionary of cultivar parameters to update.

   ``simulations``, optional
        List or tuples of simulation names to update if `None` update all simulations.

   ``clear`` (bool, optional)
        If `True` remove all existing parameters, by default `False`.

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.recompile_edited_model(self, out_path: 'os.PathLike') (inherited)

   Args:
   ______________
   ``out_path``: os.PathLike object this method is called to convert the simulation object from ConverterReturnType to model like object

   ``return:`` self

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.update_mgt_by_path(self, *, path: 'str', fmt='.', **kwargs) (inherited)

   Args:
   _________________
   ``path``: complete node path to the script manager e.g. '.Simulations.Simulation.Field.Sow using a variable rule'

   ``fmt``: seperator for formatting the path e.g., ".". Other characters can be used with
    caution, e.g., / and clearly declared in fmt argument. If you want to use the forward slash, it will be '/Simulations/Simulation/Field/Sow using a variable rule', fmt = '/'

   ``kwargs``: Corresponding keyword arguments representing the paramters in the script manager and their values. Values is what you want
   to change to; Example here ``Population`` =8.2, values should be entered with their corresponding data types e.g.,
    int, float, bool,str etc.

   return: self

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.replace_model_from(self, model, model_type: 'str', model_name: 'str' = None, target_model_name: 'str' = None, simulations: 'str' = None) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.update_mgt(self, *, management: 'Union[dict, tuple]', simulations: '[list, tuple]' = <UserOptionMissing>, out: '[Path, str]' = None, reload: 'bool' = True, **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.preview_simulation(self) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.change_simulation_dates(self, start_date: 'str' = None, end_date: 'str' = None, simulations: 'Union[tuple, list]' = None) (inherited)

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

   .. py:property:: apsimNGpy.core.experimentmanager.ExperimentManager.extract_dates (inherited)

   Get simulation dates in the model.

   @deprecated

   Parameters
   ----------
   ``simulations``, optional
       List of simulation names to get, if ``None`` get all simulations.

   ``Returns``
       ``Dictionary`` of simulation names with dates
   # Example

       >>> from apsimNGpy.core.base_data import load_default_simulations
       >>> model = load_default_simulations(crop='maize')
       >>> changed_dates = model.extract_dates
       >>> print(changed_dates)

          {'Simulation': {'start': datetime.date(2021, 1, 1),
           'end': datetime.date(2021, 1, 12)}}

       .. note::

           It is possible to target a specific simulation by specifying simulation name for this case the name is Simulations,
            so, it could appear as follows;

        >>>model.change_simulation_dates(start_date='2021-01-01', end_date='2021-01-12', simulation = 'Simulation')

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.extract_start_end_years(self, simulations: 'str' = None) (inherited)

   Get simulation dates. deprecated

   Parameters
   ----------
   ``simulations``: (str) optional
       List of simulation names to use if `None` get all simulations.

   ``Returns``
       Dictionary of simulation names with dates.

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.replace_met_file(self, *, weather_file: 'Union[Path, str]', simulations=<UserOptionMissing>, **kwargs) -> "'Self'" (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.get_weather_from_file(self, weather_file, simulations=None) -> "'self'" (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.get_weather_from_web(self, lonlat: 'tuple', start: 'int', end: 'int', simulations=<UserOptionMissing>, source='nasa', filename=None) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.show_met_file_in_simulation(self, simulations: 'list' = None) (inherited)

   Show weather file for all simulations

   @deprecated: use inspect_model_parameters() instead

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.change_report(self, *, command: 'str', report_name='Report', simulations=None, set_DayAfterLastOutput=None, **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.extract_soil_physical(self, simulations: '[tuple, list]' = None) (inherited)

   Find physical soil

   Parameters
   ----------
   ``simulation``, optional
       Simulation name, if `None` use the first simulation.
   Returns
   -------
       APSIM Models.Soils.Physical object

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.extract_any_soil_physical(self, parameter, simulations: '[list, tuple]' = <UserOptionMissing>) (inherited)

   Extracts soil physical parameters in the simulation

   Args::
       ``parameter`` (_string_): string e.g. DUL, SAT
       ``simulations`` (string, optional): Targeted simulation name. Defaults to None.
   ---------------------------------------------------------------------------
   returns an array of the parameter values

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.inspect_model(self, model_type: 'Union[str, Models]', fullpath=True, **kwargs) (inherited)

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

   .. py:property:: apsimNGpy.core.experimentmanager.ExperimentManager.configs (inherited)

   records activities or modifications to the model including changes to the file

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.replace_soils_values_by_path(self, node_path: 'str', indices: 'list' = None, **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.replace_soil_property_values(self, *, parameter: 'str', param_values: 'list', soil_child: 'str', simulations: 'list' = <UserOptionMissing>, indices: 'list' = None, crop=None, **kwargs) (inherited)

   Replaces values in any soil property array. The soil property array.

   ``parameter``: str: parameter name e.g., NO3, 'BD'

   ``param_values``: list or tuple: values of the specified soil property name to replace

   ``soil_child``: str: sub child of the soil component e.g., organic, physical etc.

   ``simulations``: list: list of simulations to where the child is found if
     not found, all current simulations will receive the new values, thus defaults to None

   ``indices``: list. Positions in the array which will be replaced. Please note that unlike C#, python satrt counting from 0

   ``crop`` (str, optional): string for soil water replacement. Default is None

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.clean_up(self, db=True, verbose=False, coerce=True, csv=True) (inherited)

   Clears the file cloned the datastore and associated csv files are not deleted if db is set to False defaults to True.

   Returns:
      >>None: This method does not return a value.

   .. caution::

      Please proceed with caution, we assume that if you want to clear the model objects, then you don't need them,
      but by making copy compulsory, then, we are clearing the edited files

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.create_experiment(self, permutation: 'bool' = True, base_name: 'str' = None, **kwargs) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.refresh_model(self) (inherited)

   for methods that will alter the simulation objects and need refreshing the second time we call
   @return: self for method chaining

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.add_fac(self, model_type, parameter, model_name, values, factor_name=None) (inherited)

   Add a factor to the initiated experiment. This should replace add_factor. which has less abstractionn @param
   model_type: model_class from APSIM Models namespace @param parameter: name of the parameter to fill e.g CNR
   @param model_name: name of the model @param values: values of the parameter, could be an iterable for case of
   categorical variables or a string e.g, '0 to 100 step 10 same as [0, 10, 20, 30, ...].
   @param factor_name: name to identify the factor in question
   @return:

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.set_continuous_factor(self, factor_path, lower_bound, upper_bound, interval, factor_name=None) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.set_categorical_factor(self, factor_path: 'str', categories: 'Union[list, tuple]', factor_name: 'str' = None) (inherited)

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

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.add_crop_replacements(self, _crop: 'str') (inherited)

   Adds a replacement folder as a child of the simulations.

   Useful when you intend to edit cultivar **parameters**.

   **Args:**
       ``_crop`` (*str*): Name of the crop to be added to the replacement folder.

   ``Returns:``
       - *ApsimModel*: An instance of `apsimNGpy.core.core.apsim.ApsimModel` or `CoreModel`.

   ``Raises:``
       - *ValueError*: If the specified crop is not found.

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.get_model_paths(self, cultivar=False) -> 'list[str]' (inherited)

   Select out a few model types to use for building the APSIM file inspections

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.inspect_file(self, *, cultivar=False, console=True, **kwargs) (inherited)

   Inspect the file by calling ``inspect_model()`` through ``get_model_paths.``
   This method is important in inspecting the ``whole file`` and also getting the ``scripts paths``

   cultivar: i (bool) includes cultivar paths

   console: (bool) print to the console

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.summarize_numeric(self, data_table: 'Union[str, tuple, list]' = None, columns: 'list' = None, percentiles=(0.25, 0.5, 0.75), round=2) -> 'pd.DataFrame' (inherited)

   Summarize numeric columns in a simulated pandas DataFrame. Useful when you want to quickly look at the simulated data

   Parameters:

       -  data_table (list, tuple, str): The names of the data table attached to the simulations. defaults to all data tables.
       -  specific (list) columns to summarize.
       -  percentiles (tuple): Optional percentiles to include in the summary.
       -  round (int): number of decimal places for rounding off.

   Returns:

       pd.DataFrame: A summary DataFrame with statistics for each numeric column.

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.add_db_table(self, variable_spec: 'list' = None, set_event_names: 'list' = None, rename: 'str' = None, simulation_name: 'Union[str, list, tuple]' = <UserOptionMissing>) (inherited)

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

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.Datastore (inherited)

   Default: ``<member 'Datastore' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.End (inherited)

   Default: ``<member 'End' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.Models (inherited)

   Default: ``<member 'Models' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.Simulations (inherited)

   Default: ``<member 'Simulations' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.Start (inherited)

   Default: ``<member 'Start' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.base_name (inherited)

   Default: ``<member 'base_name' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.copy (inherited)

   Default: ``<member 'copy' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.datastore (inherited)

   Default: ``<member 'datastore' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.experiment (inherited)

   Default: ``<member 'experiment' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.experiment_created (inherited)

   Default: ``<member 'experiment_created' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.factor_names (inherited)

   Default: ``<member 'factor_names' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.factors (inherited)

   Default: ``<member 'factors' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.model (inherited)

   Default: ``<member 'model' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.model_info (inherited)

   Default: ``<member 'model_info' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.others (inherited)

   Default: ``<member 'others' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.out (inherited)

   Default: ``<member 'out' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.out_path (inherited)

   Default: ``<member 'out_path' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.path (inherited)

   Default: ``<member 'path' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.permutation (inherited)

   Default: ``<member 'permutation' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.ran_ok (inherited)

   Default: ``<member 'ran_ok' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.report_names (inherited)

   Default: ``<member 'report_names' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.run_method (inherited)

   Default: ``<member 'run_method' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.set_wd (inherited)

   Default: ``<member 'set_wd' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.wk_info (inherited)

   Default: ``<member 'wk_info' of 'CoreModel' objects>``

   .. py:attribute:: apsimNGpy.core.experimentmanager.ExperimentManager.work_space (inherited)

   Default: ``<member 'work_space' of 'CoreModel' objects>``

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.plot_mva(self, table: pandas.core.frame.DataFrame, time_col: Hashable, response: Hashable, *, window: int = 5, min_period: int = 1, grouping: Union[Hashable, collections.abc.Sequence[Hashable], NoneType] = None, preserve_start: bool = True, kind: str = 'line', estimator='mean', plot_raw: bool = False, raw_alpha: float = 0.35, raw_linewidth: float = 1.0, auto_datetime: bool = False, ylabel: Optional[str] = None, return_data: bool = False, **kwargs) -> seaborn.axisgrid.FacetGrid | tuple[seaborn.axisgrid.FacetGrid, pandas.core.frame.DataFrame] (inherited)

   Plot a centered moving-average (MVA) of a response using ``seaborn.relplot``.

   Enhancements over a direct ``relplot`` call:
   - Computes and plots a smoothed series via :func:`apsimNGpy.stats.data_insights.mva`.
   - Supports multi-column grouping; will auto-construct a composite hue if needed.
   - Optional overlay of the raw (unsmoothed) series for comparison.
   - Stable (mergesort) time ordering.

   Parameters
   ----------
   table : pandas.DataFrame or str
       Data source or table name; if ``None``, use :pyattr:`results`.
   time_col : hashable
       Time (x-axis) column.
   response : hashable
       Response (y) column to smooth.
   window : int, default=5
       MVA window size.
   min_period : int, default=1
       Minimum periods for the rolling mean.
   grouping : hashable or sequence of hashable, optional
       One or more grouping columns.
   preserve_start : bool, default=True
       Preserve initial values when centering.
   kind : {"line","scatter"}, default="line"
       Passed to ``sns.relplot``.
   estimator : str or None, default="mean"
       Passed to ``sns.relplot`` (set to ``None`` to plot raw observations).
   plot_raw : bool, default=False
       Overlay the raw series on each facet.
   raw_alpha : float, default=0.35
       Alpha for the raw overlay.
   raw_linewidth : float, default=1.0
       Line width for the raw overlay.
   auto_datetime : bool, default=False
       Attempt to convert ``time_col`` to datetime.
   ylabel : str, optional
       Custom y-axis label; default is generated from window/response.
   return_data : bool, default=False
       If ``True``, return ``(FacetGrid, smoothed_df)``.

   Returns
   -------
   seaborn.FacetGrid
       The relplot grid, or ``(grid, smoothed_df)`` if ``return_data=True``.

   Notes
   -----
      This function calls :func:`seaborn.relplot` and accepts its keyword arguments
      via ``**kwargs``. See link below for details:

   https://seaborn.pydata.org/generated/seaborn/relplot.html

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.boxplot(self, column, *, table=None, by=None, figsize=(10, 8), grid=False, **kwargs) (inherited)

   Plot a boxplot from simulation results using ``pandas.DataFrame.boxplot``.

   Parameters
   ----------
   column : str
       Column to plot.
   table : str or pandas.DataFrame, optional
       Table name or DataFrame; if omitted, use :pyattr:`results`.
   by : str, optional
       Grouping column.
   figsize : tuple, default=(10, 8)
   grid : bool, default=False
   **kwargs
       Forwarded to :meth:`pandas.DataFrame.boxplot`.

   Returns
   -------
   matplotlib.axes.Axes

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.distribution(self, x, *, table=None, **kwargs) (inherited)

   Plot a uni-variate distribution/histogram using :func:`seaborn.histplot`.

   Parameters
   ----------
   x : str
       Numeric column to plot.
   table : str or pandas.DataFrame, optional
       Table name or DataFrame; if omitted, use :pyattr:`results`.
   **kwargs
       Forwarded to :func:`seaborn.histplot`.

   Raises
   ------
   ValueError
       If ``x`` is a string-typed column.

   Notes
   -----
   This function calls :func:`seaborn.histplot` and accepts its keyword arguments
   via ``**kwargs``. See link below for details:

   https://seaborn.pydata.org/generated/seaborn/histplot.html 


   =================================================================

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.series_plot(self, table=None, *, x: str = None, y: Union[str, list] = None, hue=None, size=None, style=None, units=None, weights=None, palette=None, hue_order=None, hue_norm=None, sizes=None, size_order=None, size_norm=None, dashes=True, markers=None, style_order=None, estimator='mean', errorbar=('ci', 95), n_boot=1000, seed=None, orient='x', sort=True, err_style='band', err_kws=None, legend='auto', ci='deprecated', ax=None, **kwargs) (inherited)

   Just a wrapper for seaborn.lineplot that supports multiple y columns that could be provided as a list

    table : str | [str] |None | None| pandas.DataFrame, optional. Default is None
       If the table names are provided, results are collected from the simulated data, using that table names.
       If None, results will be all the table names inside concatenated along the axis 0 (not recommended)

    If ``y`` is a list of columns, the data are melted into long form and
   the different series are colored by variable name.

   **Kwargs
       Additional keyword args and all other arguments are for Seaborn.lineplot.
       See the reference below for all the kwargs.

   reference; https://seaborn.pydata.org/generated/seaborn.lineplot.html

   Examples
   --------
   >>> model.series_plot(x='Year', y='Yield', table='Report')  # doctest: +SKIP
   >>> model.series_plot(x='Year', y=['SOC1', 'SOC2'], table='Report')  # doctest: +SKIP

   Examples:
   ------------

      >>>from apsimNGpy.core.apsim import ApsimModel
      >>> model = ApsimModel(model= 'Maize')
      # run the results
      >>> model.run(report_names='Report')
      >>>model.series_plot(x='Maize.Grain.Size', y='Yield', table='Report')
      >>>model.render_plot(show=True, ylabel = 'Maize yield', xlabel ='Maize grain size')

   Plot two variables:

      >>>model.series_plot(x='Yield', y=['Maize.Grain.N', 'Maize.Grain.Size'], table= 'Report')

   Notes
   -----
   This function calls :func:`seaborn.lineplot` and accepts its keyword arguments
   via ``**kwargs``. See link below for detailed explanations:

   https://seaborn.pydata.org/generated/seaborn/lineplot.html 

   =============================================================================================================================================

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.scatter_plot(self, table=None, *, x=None, y=None, hue=None, size=None, style=None, palette=None, hue_order=None, hue_norm=None, sizes=None, size_order=None, size_norm=None, markers=True, style_order=None, legend='auto', ax=None, **kwargs) (inherited)

   Scatter plot using :func:`seaborn.scatterplot` with flexible aesthetic mappings.

   Parameters
   ----------
   table : str | [str] |None | None| pandas.DataFrame, optional. Default is None
       If the table names are provided, results are collected from the simulated data, using that table names.
       If None, results will be all the table names inside concatenated along the axis 0 (not recommended)
   x, y, hue, size, style, palette, hue_order, hue_norm, sizes, size_order, size_norm, markers, style_order, legend, ax
       Passed through to :func:`seaborn.scatterplot`.
   **Kwargs
       Additional keyword args for Seaborn.
   See the reference below for all the kwargs.
   reference; https://seaborn.pydata.org/generated/seaborn.scatterplot.html 

   ================================================================================================================================

   .. py:method:: apsimNGpy.core.experimentmanager.ExperimentManager.cat_plot(self, table=None, *, x=None, y=None, hue=None, row=None, col=None, kind='strip', estimator='mean', errorbar=('ci', 95), n_boot=1000, seed=None, units=None, weights=None, order=None, hue_order=None, row_order=None, col_order=None, col_wrap=None, height=5, aspect=1, log_scale=None, native_scale=False, formatter=None, orient=None, color=None, palette=None, hue_norm=None, legend='auto', legend_out=True, sharex=True, sharey=True, margin_titles=False, facet_kws=None, **kwargs) (inherited)

    Categorical plot wrapper over :func:`seaborn.catplot`.

   Parameters
   ----------
   table : str or pandas.DataFrame, optional
   x, y, hue, row, col, kind, estimator, errorbar, n_boot, seed, units, weights, order,
   hue_order, row_order, col_order, col_wrap, height, aspect, log_scale, native_scale, formatter,
   orient, color, palette, hue_norm, legend, legend_out, sharex, sharey, margin_titles, facet_kws
       Passed through to :func:`seaborn.catplot`.
   **kwargs
       Additional keyword args for Seaborn.

   Returns
   -------
   seaborn.axisgrid.FacetGrid

   reference https://seaborn.pydata.org/generated/seaborn.catplot.html

   =========================================================================================================

apsimNGpy.core.mult_cores
-------------------------

Functions
^^^^^^^^^

.. py:function:: apsimNGpy.core.mult_cores.is_my_iterable(value)

   Check if a value is an iterable, but not a string.

.. py:function:: apsimNGpy.core.mult_cores.simulation_exists(db_path: str, table_name: str, simulation_id: int) -> bool

   Check if a simulation_id exists in the specified table.

   Args:
       db_path (str): Path to the SQLite database file.
       table_name (str): Name of the table to query.
       simulation_id (int): ID of the simulation to check.

   Returns:
       bool: True if exists, False otherwise.

Classes
^^^^^^^

.. py:class:: apsimNGpy.core.mult_cores.MultiCoreManager

   MultiCoreManager(db_path: Union[str, pathlib.Path, NoneType] = (None,), agg_func: Optional[str] = None, ran_ok: bool = False, incomplete_jobs: list = <factory>)

   .. py:method:: apsimNGpy.core.mult_cores.MultiCoreManager.__init__(self, db_path: Union[str, pathlib.Path, NoneType] = (None,), agg_func: Optional[str] = None, ran_ok: bool = False, incomplete_jobs: list = <factory>) -> None

   Initialize self.  See help(type(self)) for accurate signature.

   .. py:attribute:: apsimNGpy.core.mult_cores.MultiCoreManager.tag

   Default: ``'multi-core'``

   .. py:attribute:: apsimNGpy.core.mult_cores.MultiCoreManager.default_db

   Default: ``'manager_datastorage.db'``

   .. py:method:: apsimNGpy.core.mult_cores.MultiCoreManager.insert_data(self, results, table)

   Insert results into the specified table
   results: (Pd.DataFrame, dict) The results that will be inserted into the table
   table: str (name of the table to insert)

   .. py:property:: apsimNGpy.core.mult_cores.MultiCoreManager.tables

   Summarizes all the tables that have been created from the simulations

   .. py:method:: apsimNGpy.core.mult_cores.MultiCoreManager.run_parallel(self, model)

   This is the worker for each simulation.

   The function performs two things; runs the simulation and then inserts the simulated data into a specified
   database.

   :param model: str, dict, or Path object related .apsimx json file

   returns None

   .. py:method:: apsimNGpy.core.mult_cores.MultiCoreManager.get_simulated_output(self, axis=0)

   Get simulated output from the API

   :param axis: if axis =0, concatenation is along the ``rows`` and if it is 1 concatenation is along the ``columns``

   .. py:property:: apsimNGpy.core.mult_cores.MultiCoreManager.results

   property methods for getting simulated output

   .. py:method:: apsimNGpy.core.mult_cores.MultiCoreManager.clear_db(self)

   Clears the database before any simulations.

   First attempt a complete ``deletion`` of the database if that fails, existing tables are all deleted

   .. py:method:: apsimNGpy.core.mult_cores.MultiCoreManager.clear_scratch(self)

   clears the scratch directory where apsim files are cloned before being loaded. should be called after all simulations are completed

   .. py:method:: apsimNGpy.core.mult_cores.MultiCoreManager.clean_up_data(self)

   Clears the data associated with each job. Please call this method after run_all_jobs is complete

   .. py:method:: apsimNGpy.core.mult_cores.MultiCoreManager.save_tosql(self, db_name: Union[str, pathlib.Path], *, table_name: str = 'aggregated_tables', if_exists: Literal['fail', 'replace', 'append'] = 'fail') -> None

   Persist simulation results to a SQLite database table.

   This method writes `self.results` (a pandas DataFrame) to the given SQLite
   database. It is designed to be robust in workflows where some simulations
   may fail: any successfully simulated rows present in `self.results` are
   still saved. This is useful when an ephemeral/temporary database was used
   during simulation and you need a durable copy.

   Parameters
   ----------
   db_name : str | pathlib.Path
       Target database file. If a name without extension is provided, a
       ``.db`` suffix is appended. If a relative path is given, it resolves
       against the current working directory.
   table_name : str, optional
       Name of the destination table. Defaults to ``"Report"``.
   if_exists: {"fail", "replace", "append"}, optional.
       Write mode passed through to pandas:
       - ``"fail"``: raise if the table already exists.
       - ``"replace"``: drop the table, create a new one, then insert.
       - ``"append"``: insert rows into existing table (default).
       (defaults to fail if table exists, more secure for the users to know
    what they are doing)

   Raises
   ------
   ValueError
       If `self.results` is missing or empty.
   TypeError
       If `self.results` is not a pandas DataFrame.
   RuntimeError
       If the underlying database writes fails.

   Notes
   -----
   - Ensure that `self.results` contain only the rows you intend to persist with.
     If you maintain a separate collection of failed/incomplete jobs, they
     should not be included in `self.results`.
   - This method does not mutate `self.results`.

   Examples
   --------
   >>> mgr.results.head()
      sim_id  yield  n2o
   0       1   10.2  0.8
   >>> mgr.save("outputs/simulations.db")

   .. py:method:: apsimNGpy.core.mult_cores.MultiCoreManager.save_tocsv(self, path_or_buf, **kwargs)

   Persist simulation results to a SQLite database table.

           This method writes `self.results` (a pandas DataFrame) to the given csv file. It is designed to be robust in workflows where some simulations
           may fail: any successfully simulated rows present in `self.results` are
           still saved. This is useful when an ephemeral/temporary database was used
           during simulation and you need a durable copy
   .

   Write object to a comma-separated values (csv) file.

   Parameters
   ----------
   path_or_buf : str, path object, file-like object, or None, default None
       String, path object (implementing os.PathLike[str]), or file-like
       object implementing a write() function. If None, the result is
       returned as a string. If a non-binary file object is passed, it should
       be opened with `newline=''`, disabling universal newlines. If a binary
       file object is passed, `mode` might need to contain a `'b'`.
   sep : str, default ','
       String of length 1. Field delimiter for the output file.
   na_rep : str, default ''
       Missing data representation.
   float_format : str, Callable, default None
       Format string for floating point numbers. If a Callable is given, it takes
       precedence over other numeric formatting parameters, like decimal.
   columns : sequence, optional
       Columns to write.
   header : bool or list of str, default True
       Write out the column names. If a list of strings is given it is
       assumed to be aliases for the column names.
   index : bool, default True
       Write row names (index).
   index_label : str or sequence, or False, default None
       Column label for index column(s) if desired. If None is given, and
       `header` and `index` are True, then the index names are used. A
       sequence should be given if the object uses MultiIndex. If
       False do not print fields for index names. Use index_label=False
       for easier importing in R.
   mode : {'w', 'x', 'a'}, default 'w'
       Forwarded to either `open(mode=)` or `fsspec.open(mode=)` to control
       the file opening. Typical values include:

       - 'w', truncate the file first.
       - 'x', exclusive creation, failing if the file already exists.
       - 'a', append to the end of file if it exists.

   encoding : str, optional
       A string representing the encoding to use in the output file,
       defaults to 'utf-8'. `encoding` is not supported if `path_or_buf`
       is a non-binary file object.
   compression : str or dict, default 'infer'
       For on-the-fly compression of the output data. If 'infer' and 'path_or_buf' is
       path-like, then detect compression from the following extensions: '.gz',
       '.bz2', '.zip', '.xz', '.zst', '.tar', '.tar.gz', '.tar.xz' or '.tar.bz2'
       (otherwise no compression).
       Set to ``None`` for no compression.
       Can also be a dict with key ``'method'`` set
       to one of {``'zip'``, ``'gzip'``, ``'bz2'``, ``'zstd'``, ``'xz'``, ``'tar'``} and
       other key-value pairs are forwarded to
       ``zipfile.ZipFile``, ``gzip.GzipFile``,
       ``bz2.BZ2File``, ``zstandard.ZstdCompressor``, ``lzma.LZMAFile`` or
       ``tarfile.TarFile``, respectively.
       As an example, the following could be passed for faster compression and to create
       a reproducible gzip archive:
       ``compression={'method': 'gzip', 'compresslevel': 1, 'mtime': 1}``.

       .. versionadded:: 1.5.0
           Added support for `.tar` files.

          May be a dict with key 'method' as compression mode
          and other entries as additional compression options if
          compression mode is 'zip'.

          Passing compression options as keys in dict is
          supported for compression modes 'gzip', 'bz2', 'zstd', and 'zip'.
   quoting : optional constant from csv module
       Defaults to csv.QUOTE_MINIMAL. If you have set a `float_format`
       then floats are converted to strings and thus csv.QUOTE_NONNUMERIC
       will treat them as non-numeric.
   quotechar : str, default '\"'
       String of length 1. Character used to quote fields.
   lineterminator : str, optional
       The newline character or character sequence to use in the output
       file. Defaults to `os.linesep`, which depends on the OS in which
       this method is called ('\\n' for linux, '\\r\\n' for Windows, i.e.).

       .. versionchanged:: 1.5.0

           Previously was line_terminator, changed for consistency with
           read_csv and the standard library 'csv' module.

   chunksize : int or None
       Rows to write at a time.
   date_format : str, default None
       Format string for datetime objects.
   doublequote : bool, default True
       Control quoting of `quotechar` inside a field.
   escapechar : str, default None
       String of length 1. Character used to escape `sep` and `quotechar`
       when appropriate.
   decimal : str, default '.'
       Character recognized as decimal separator. E.g. use ',' for
       European data.
   errors : str, default 'strict'
       Specifies how encoding and decoding errors are to be handled.
       See the errors argument for :func:`open` for a full list
       of options.

   storage_options : dict, optional
       Extra options that make sense for a particular storage connection, e.g.
       host, port, username, password, etc. For HTTP(S) URLs the key-value pairs
       are forwarded to ``urllib.request.Request`` as header options. For other
       URLs (e.g. starting with "s3://", and "gcs://") the key-value pairs are
       forwarded to ``fsspec.open``. Please see ``fsspec`` and ``urllib`` for more
       details, and for more examples on storage options refer `here
       <https://pandas.pydata.org/docs/user_guide/io.html?
       highlight=storage_options#reading-writing-remote-files>`_.

   Returns
   -------
   None or str
       If path_or_buf is None, returns the resulting csv format as a
       string. Otherwise returns None.

   See Also
   --------
   read_csv : Load a CSV file into a DataFrame.
   to_excel : Write DataFrame to an Excel file.

   Examples
   --------
   Create 'out.csv' containing 'df' without indices

   >>> df = pd.DataFrame({'name': ['Raphael', 'Donatello'],
   ...                    'mask': ['red', 'purple'],
   ...                    'weapon': ['sai', 'bo staff']})
   >>> df.to_csv('out.csv', index=False)  # doctest: +SKIP

   Create 'out.zip' containing 'out.csv'

   >>> df.to_csv(index=False)
   'name,mask,weapon\nRaphael,red,sai\nDonatello,purple,bo staff\n'
   >>> compression_opts = dict(method='zip',
   ...                         archive_name='out.csv')  # doctest: +SKIP
   >>> df.to_csv('out.zip', index=False,
   ...           compression=compression_opts)  # doctest: +SKIP

   To write a csv file to a new folder or nested folder you will first
   need to create it using either Pathlib or os:

   >>> from pathlib import Path  # doctest: +SKIP
   >>> filepath = Path('folder/subfolder/out.csv')  # doctest: +SKIP
   >>> filepath.parent.mkdir(parents=True, exist_ok=True)  # doctest: +SKIP
   >>> df.to_csv(filepath)  # doctest: +SKIP

   >>> import os  # doctest: +SKIP
   >>> os.makedirs('folder/subfolder', exist_ok=True)  # doctest: +SKIP
   >>> df.to_csv('folder/subfolder/out.csv')  # doctest: +SKIP

   .. py:method:: apsimNGpy.core.mult_cores.MultiCoreManager.run_all_jobs(self, jobs, *, n_cores=17, threads=False, clear_db=True, **kwargs)

   runs all provided jobs using ``processes`` or ``threads`` specified

   ``threads (bool)``: threads or processes

   ``jobs (iterable[simulations paths]``: jobs to run

   ``n_cores (int)``: number of cores to use

   ``clear_db (bool)``: clear the database existing data if any. defaults to True

   ``kwargs``:
     retry_rate (int, optional): how many times to retry jobs before giving up

   :return: None

   .. py:attribute:: apsimNGpy.core.mult_cores.MultiCoreManager.agg_func

   Default: ``<member 'agg_func' of 'MultiCoreManager' objects>``

   .. py:attribute:: apsimNGpy.core.mult_cores.MultiCoreManager.db_path

   Default: ``<member 'db_path' of 'MultiCoreManager' objects>``

   .. py:attribute:: apsimNGpy.core.mult_cores.MultiCoreManager.incomplete_jobs

   Default: ``<member 'incomplete_jobs' of 'MultiCoreManager' objects>``

   .. py:attribute:: apsimNGpy.core.mult_cores.MultiCoreManager.ran_ok

   Default: ``<member 'ran_ok' of 'MultiCoreManager' objects>``

apsimNGpy.core.pythonet_config
------------------------------

Module attributes
^^^^^^^^^^^^^^^^^^

.. py:attribute:: apsimNGpy.core.pythonet_config.CI

   Default value: ``ConfigRuntimeInfo(clr_loaded=True, bin_path=WindowsPath('D:/My_BOX/Box/PhD thes…``

Functions
^^^^^^^^^

.. py:function:: apsimNGpy.core.pythonet_config.get_apsim_file_reader(method: str = 'string')

   Return an APSIM file reader callable based on the requested method.

   This helper selects the appropriate APSIM NG ``FileFormat`` implementation,
   accounting for runtime changes in the file format (via
   :func:`is_file_format_modified`) and whether the managed type is available
   under ``Models.Core.ApsimFile.FileFormat`` or ``APSIM.Core.FileFormat``.
   It then returns the corresponding static method to read an APSIM file
   either **from a string** or **from a file path**.

   Parameters
   ----------
   method: {"string", "file"}, optional
       Which reader to return:
       - ``"string"`` >>> returns ``FileFormat.ReadFromString``.
       - ``"file"``   >>> returns ``FileFormat.ReadFromFile``.
       Defaults to ``"string"``.

   Returns
   -------
   Callable
       A .NET static method (callable from Python) that performs the read:
       either ``ReadFromString(text: str)`` or ``ReadFromFile(path: str)``.

   Raises
   ------
   NotImplementedError
       If ``method`` is not one of ``"string"`` or ``"file"``.
   AttributeError
       If the underlying APSIM ``FileFormat`` type does not expose the
       expected reader method (environment/binaries misconfigured).

   Notes
   -----
   - When : func:`is_file_format_modified` returns ``bool``.If False, then
     ``Models.Core.ApsimFile.FileFormat`` is unavailable, the function falls
     back to ``APSIM.Core.FileFormat``.
   - The returned callable is a .NET method; typical usage is
     ``reader = get_apsim_file_reader("file"); model = reader(path)``.

   Examples
   --------
   Read from a file path:

   >>> reader = get_apsim_file_reader("file")      # doctest: +SKIP
   >>> sims = reader("/path/to/model.apsimx")      # doctest: +SKIP

   Read from a string (APSXML/JSON depending on APSIM NG):

   >>> text = "...apsimx content..."               # doctest: +SKIP
   >>> reader = get_apsim_file_reader("string")    # doctest: +SKIP
   >>> sims = reader(text)                         # doctest: +SKIP

.. py:function:: apsimNGpy.core.pythonet_config.get_apsim_version(bin_path: Union[str, pathlib.Path] = WindowsPath('D:/My_BOX/Box/PhD thesis/Objective two/morrow plots 20250821/APSIM2025.8.7844.0/bin'), release_number: bool = False) -> Optional[str]

   Return the APSIM version string detected from the installed binaries.

   The function initializes pythonnet for the given APSIM binaries path (via
   ``load_pythonnet(bin_path)``), then loads ``Models.dll`` and reads its
   assembly version. By default, the returned string is prefixed with ``"APSIM"``;
   set ``release_number=True`` to get the raw semantic version.

   Parameters
   ----------
   bin_path : str or pathlib.Path, optional
       Filesystem path to the APSIM **binaries** directory that contains
       ``Models.dll``. Defaults to ``APSIM_BIN_PATH``.
   release_number : bool, optional
       If ``True``, returns only the assembly version (e.g., ``"2024.6.123"``).
       If ``False`` (default), prefix with ``"APSIM"`` (e.g., ``"APSIM 2024.6.123"``).

   Returns
   -------
   str or None
       The version string if detected successfully; otherwise ``None`` when
       required system modules are unavailable (e.g., if the binaries path is
       not correctly configured).

   Raises
   ------
   ApsimBinPathConfigError
       If pythonnet/CLR is not initialized for the provided ``bin_path`` (i.e.,
       APSIM binaries path has not been set up).

   Notes
   -----
   - This call requires a valid APSIM NG binaries folder and a loadable
     ``Models.dll`` at ``bin_path/Models.dll``.
   - ``load_pythonnet`` must succeed so that the CLR is available; otherwise
     the version cannot be queried.

   Examples
   --------
   >>> get_apsim_version("/opt/apsim/bin")           # doctest: +SKIP
   'APSIM2024.6.123'
   >>> get_apsim_version("/opt/apsim/bin", True)     # doctest: +SKIP
   '2024.6.123'

   See Also
   --------
   load_pythonnet : Initialize pythonnet/CLR for APSIM binaries.

.. py:function:: apsimNGpy.core.pythonet_config.is_file_format_modified(bin_path: Union[str, pathlib.Path] = WindowsPath('D:/My_BOX/Box/PhD thesis/Objective two/morrow plots 20250821/APSIM2025.8.7844.0/bin')) -> bool

   Checks if the APSIM.CORE.dll is present in the bin path. Normally, the new APSIM version has this dll
   @return: bool

Classes
^^^^^^^

.. py:class:: apsimNGpy.core.pythonet_config.ConfigRuntimeInfo

   ConfigRuntimeInfo(clr_loaded: bool, bin_path: Union[pathlib.Path, str], file_format_modified: bool = True)

   .. py:method:: apsimNGpy.core.pythonet_config.ConfigRuntimeInfo.__init__(self, clr_loaded: bool, bin_path: Union[pathlib.Path, str], file_format_modified: bool = True) -> None

   Initialize self.  See help(type(self)) for accurate signature.

   .. py:attribute:: apsimNGpy.core.pythonet_config.ConfigRuntimeInfo.file_format_modified

   Default: ``True``

apsimNGpy.core_utils.database_utils
-----------------------------------

Interface to APSIM simulation models using Python.NET 

Module attributes
^^^^^^^^^^^^^^^^^^

.. py:attribute:: apsimNGpy.core_utils.database_utils.T

   Default value: ``~T``

Functions
^^^^^^^^^

.. py:function:: apsimNGpy.core_utils.database_utils.chunker(data: 'Iterable[T]', *, chunk_size: 'Optional[int]' = None, n_chunks: 'Optional[int]' = None, pad: 'bool' = False, fillvalue: 'Optional[T]' = None) -> 'Iterator[List[T]]'

   Yield chunks from `data`.

   Choose exactly one of:
     - `chunk_size`: yield consecutive chunks of length `chunk_size`
       (last chunk may be shorter unless `pad=True`)
     - `n_chunks`: split data into `n_chunks` nearly equal parts
       (sizes differ by at most 1)

   Args
   ----
   data : Iterable[T]
       The input data (list, generator, etc.)
   chunk_size : int, optional
       Fixed size for each chunk (>=1).
   n_chunks : int, optional
       Number of chunks to create (>=1). Uses nearly equal sizes.
   pad : bool, default False
       If True and using `chunk_size`, pad the last chunk to length `chunk_size`.
   fill value : T, optional
       Value to use when padding.

   Yields
   ------
   List[T]
       Chunks of the input data.

   Raises
   ------
   ValueError
       If neither or both of `chunk_size` and `n_chunks` are provided,
       or if provided values are invalid.

.. py:function:: apsimNGpy.core_utils.database_utils.clear_all_tables(db)

   Deletes all rows from all user-defined tables in the given SQLite database.

   ``db``: Path to the SQLite database file.

   ``return``: None

.. py:function:: apsimNGpy.core_utils.database_utils.clear_table(db, table_name)

   ``db``: path to db.

   ``table_name``: name of the table to clear.

   ``return``: None

.. py:function:: apsimNGpy.core_utils.database_utils.dataview_to_dataframe(_model, reports)

   Convert .NET System.Data.DataView to Pandas DataFrame.
   report (str, list, tuple) of the report to be displayed. these should be in the simulations
   :param apsimng model: CoreModel object or instance
   :return: Pandas DataFrame

.. py:function:: apsimNGpy.core_utils.database_utils.delete_all_tables(db: 'str') -> 'None'

   Deletes all tables in the specified SQLite database.

   ⚠️ Proceed with caution: this operation is irreversible.

   Args:
       db (str): Path to the SQLite database file.

.. py:function:: apsimNGpy.core_utils.database_utils.delete_table(db, table_name)

   deletes the table in a database.

   ⚠️ Proceed with caution: this operation is irreversible.

.. py:function:: apsimNGpy.core_utils.database_utils.get_db_table_names(d_b)

   ``d_b``: database name or path.

   ``return:`` all names ``SQL`` database table ``names`` existing within the database

.. py:function:: apsimNGpy.core_utils.database_utils.read_db_table(db, report_name)

   Connects to a specified database, retrieves the entire contents of a specified table,
   and returns the results as a Pandas DataFrame.

   Args:
       ``db`` (str): The database file path or identifier to connect to.

       ``report_name`` (str): name of the database table: The name of the table in the database from which to retrieve data.

   Returns:
       ``pandas.DataFrame``: A DataFrame containing all the records from the specified table.

   The function establishes a connection to the specified SQLite database, constructs and executes a SQL query
   to select all records from the specified table, fetches the results into a DataFrame, then closes the database connection.

   Examples:
       # Define the database and the table name

       >>> database_path = 'your_database.sqlite'
       >>> table_name = 'your_table'

       # Get the table data as a DataFrame

       >>> ddf = read_db_table(database_path, table_name)

       # Work with the DataFrame
       >>> print(ddf)

   Note:
       - Ensure that the database path and table name are correct.
       - The function uses 'sqlite3' for connecting to the database; make sure it is appropriate for your database.
       - This function retrieves all records from the specified table. Use with caution if the table is very large.

.. py:function:: apsimNGpy.core_utils.database_utils.read_with_query(db, query)

   Executes an SQL query on a specified database and returns the result as a Pandas DataFrame.

   Args:
   ``db`` (str): The database file path or identifier to connect to.

   ``query`` (str): The SQL query string to be executed. The query should be a valid SQL SELECT statement.

   ``Returns:``
   ``pandas.DataFrame``: A DataFrame containing the results of the SQL query.

   The function opens a connection to the specified SQLite database, executes the given SQL query,
   fetches the results into a DataFrame, then closes the database connection.

   Example:
       # Define the database and the query

       >>> database_path = 'your_database.sqlite'
       >>> sql_query = 'SELECT * FROM your_table WHERE condition = values'

       # Get the query result as a DataFrame

       >>>df = read_with_query(database_path, sql_query)

       # Work with the DataFrame
       >>> print(df)

   Note: Ensure that the database path and the query are correct and that the query is a proper SQL SELECT statement.
   The function uses ``sqlite3`` for connecting to the database; make sure it is appropriate for your database.

.. py:function:: apsimNGpy.core_utils.database_utils.write_results_to_sql(db_path: 'Union[str, Path]', table: 'str' = 'Report', *, if_exists: "Literal['fail', 'replace', 'append']" = 'append', insert_fn: 'InsertFn | None' = None, ensure_parent: 'bool' = True) -> 'Callable'

   Decorator factory: collect the wrapped function's returned data and insert it or saves it into SQLite database.

   After the wrapped function executes, its return value is normalized to a list of
   `(table, DataFrame)` pairs via `_normalize_result` and inserted into `db_path` using
   either the provided `insert_fn` or the default `_default_insert_fn` (which relies on
   `pandas.DataFrame.to_sql` + SQLAlchemy). The original return value is passed through
   unchanged to the caller.

   Accepted return shapes
   ----------------------
   - `pd.DataFrame`                          -> appended to `table`
   - `(table_name: str, df: pd.DataFrame)`   -> appended to `table_name`
   - `list[pd.DataFrame]`                    -> each appended to `table`
   - `list[(table_name, df)]`                -> routed per pair
   - `{"data": <df|list[dict]|dict-of-cols>, "table": "MyTable"}` -> to "MyTable"
   - `{"TblA": df_or_records, "TblB": df2}`  -> multiple tables
   - `list[dict]` or `dict-of-columns`       -> coerced to DataFrame -> appended to `table`
   - `None`                                  -> no-op

   Parameters
   ----------
   db_path : str | pathlib.Path
       Destination SQLite file. A `.db` suffix is enforced if missing. If `ensure_parent`
       is True, parent directories are created.
   table : str, default "Report"
       Default table name when the return shape does not carry one.
   if_exists: {"fail", "replace", "append"}, default "append"
       Passed to `to_sql` by the inserter. See panda docs for semantics.
   insert_fn : callable, optional
       Custom inserter `(db_path, df, table, if_exists) -> None`. Use this to:
       - reuse a single connection/transaction across multiple tables,
       - enable SQLite WAL mode and retry on lock,
       - control dtype mapping or target a different DBMS.
   ensure_parent : bool, default True
       If True, create missing parent directories for `db_path`.

   Returns
   -------
   Callable
       A decorator that, when applied to a function, performs the persistence step
       after the function returns and then yields the original result.

   Raises
   ------
   TypeError
       If the wrapped function's result cannot be normalized by `_normalize_result`.
   RuntimeError
       If any insert operation fails (original exception is chained as `__cause__`).
   OSError
       On path or filesystem errors when creating the database directory/file.

   Side Effects
   ------------
   - Creates parent directories for `db_path` (when `ensure_parent=True`).
   - Creates/opens the SQLite database and writes one or more tables.
   - **Skips empty frames**: pairs where `df` is `None` or `df.empty` are ignored.
   - May DROP + CREATE the table when `if_exists="replace"`.

   Cautions
   --------
   - **SQLite concurrency: ** Concurrent writers can trigger "database is locked".
     Consider a custom `insert_fn` enabling WAL mode, retries, and transactional
     batching for robustness.
   - **Table name safety: ** Avoid propagating untrusted table names; identifier quoting
     is driver-dependent.
   - **Schema drift:** `to_sql` infers SQL schema from the DataFrame's dtypes each call.
     Ensure stable dtypes or manage schema explicitly in your `insert_fn`.
   - **Timezones: ** Pandas may localize/naivify datetime on writing; verify round-trips
     if timezone fidelity matters.
   - **Performance: ** Creating a new engine/connection per insert is simple but not optimal.
     For high-volume pipelines, supply an `insert_fn` that reuses a connection and commits
     once per batch.

   Design rationale
   ----------------
   Separates computation from persistence. The decorator is explicit about *where* data
   goes (db path, table names) and flexible about *what* callers return, reducing boilerplate
   in the business logic while still allowing power users to override insertion strategy.

   Examples
   --------
   Basic usage, single table with default appends::

       @collect_returned_results("outputs/results.db", table="Report")
       def run_analysis(...):
           return df  # a DataFrame

   Multiple tables using a mapping shape::

       @collect_returned_results("outputs/results.db")
       def summarize(...):
           return {"Summary": df1, "Metrics": df2}

   Custom inserter enabling WAL mode and a single transaction::

       def wal_insert(db, df, table, if_exists):
           import sqlite3
           con = sqlite3.connect(db, isolation_level="DEFERRED")
           try:
               con.execute("PRAGMA journal_mode=WAL;")
               df.to_sql(table, con, if_exists=if_exists, index=False)
               con.commit()
           finally:
               con.close()
   Examples:

   >>> from pandas import DataFrame
   >>> from apsimNGpy.core_utils.database_utils import write_results_to_sql, read_db_table
   >>> @write_results_to_sql(db_path="db.db", table="Report", if_exists="replace")
   ... def get_report():
   ...     # Return a DataFrame to be written to SQLite
   ...     return DataFrame({"x": [2], "y": [4]})

   >>> _ = get_report()  # executes and writes to db.db::Report
   >>> db = read_db_table("db.db", report_name="Report")
   >>> print(db.to_string(index=False))
    x  y
    2  4

apsimNGpy.exceptions
--------------------

Classes
^^^^^^^

.. py:class:: apsimNGpy.exceptions.ApsimBinPathConfigError

   Raised when the APSIM bin path is misconfigured or incomplete.

   .. py:method:: apsimNGpy.exceptions.ApsimBinPathConfigError.with_traceback() (inherited)

   Exception.with_traceback(tb) --
   set self.__traceback__ to tb and return self.

   .. py:method:: apsimNGpy.exceptions.ApsimBinPathConfigError.add_note() (inherited)

   Exception.add_note(note) --
   add a note to the exception

   .. py:attribute:: apsimNGpy.exceptions.ApsimBinPathConfigError.args (inherited)

   Default: ``<attribute 'args' of 'BaseException' objects>``

.. py:class:: apsimNGpy.exceptions.ApsimNGpyError

   Base class for all apsimNGpy-related exceptions. These errors are more descriptive than just rising a value error

   .. py:method:: apsimNGpy.exceptions.ApsimNGpyError.with_traceback() (inherited)

   Exception.with_traceback(tb) --
   set self.__traceback__ to tb and return self.

   .. py:method:: apsimNGpy.exceptions.ApsimNGpyError.add_note() (inherited)

   Exception.add_note(note) --
   add a note to the exception

   .. py:attribute:: apsimNGpy.exceptions.ApsimNGpyError.args (inherited)

   Default: ``<attribute 'args' of 'BaseException' objects>``

.. py:class:: apsimNGpy.exceptions.ApsimNotFoundError

   Raised when the APSIM executable or directory is not found.

   .. py:method:: apsimNGpy.exceptions.ApsimNotFoundError.with_traceback() (inherited)

   Exception.with_traceback(tb) --
   set self.__traceback__ to tb and return self.

   .. py:method:: apsimNGpy.exceptions.ApsimNotFoundError.add_note() (inherited)

   Exception.add_note(note) --
   add a note to the exception

   .. py:attribute:: apsimNGpy.exceptions.ApsimNotFoundError.args (inherited)

   Default: ``<attribute 'args' of 'BaseException' objects>``

.. py:class:: apsimNGpy.exceptions.ApsimRuntimeError

   occurs when an error occurs during running APSIM models with Models.exe or Models on Mac and linnux

   .. py:method:: apsimNGpy.exceptions.ApsimRuntimeError.with_traceback() (inherited)

   Exception.with_traceback(tb) --
   set self.__traceback__ to tb and return self.

   .. py:method:: apsimNGpy.exceptions.ApsimRuntimeError.add_note() (inherited)

   Exception.add_note(note) --
   add a note to the exception

   .. py:attribute:: apsimNGpy.exceptions.ApsimRuntimeError.args (inherited)

   Default: ``<attribute 'args' of 'BaseException' objects>``

.. py:class:: apsimNGpy.exceptions.CastCompilationError

   Raised when the C# cast helper DLL fails to compile.

   .. py:method:: apsimNGpy.exceptions.CastCompilationError.with_traceback() (inherited)

   Exception.with_traceback(tb) --
   set self.__traceback__ to tb and return self.

   .. py:method:: apsimNGpy.exceptions.CastCompilationError.add_note() (inherited)

   Exception.add_note(note) --
   add a note to the exception

   .. py:attribute:: apsimNGpy.exceptions.CastCompilationError.args (inherited)

   Default: ``<attribute 'args' of 'BaseException' objects>``

.. py:class:: apsimNGpy.exceptions.EmptyDateFrameError

   Raised when a DataFrame is unexpectedly empty.

   .. py:method:: apsimNGpy.exceptions.EmptyDateFrameError.with_traceback() (inherited)

   Exception.with_traceback(tb) --
   set self.__traceback__ to tb and return self.

   .. py:method:: apsimNGpy.exceptions.EmptyDateFrameError.add_note() (inherited)

   Exception.add_note(note) --
   add a note to the exception

   .. py:attribute:: apsimNGpy.exceptions.EmptyDateFrameError.args (inherited)

   Default: ``<attribute 'args' of 'BaseException' objects>``

.. py:class:: apsimNGpy.exceptions.ForgotToRunError

   Raised when a required APSIM model run was skipped or forgotten.

   .. py:method:: apsimNGpy.exceptions.ForgotToRunError.with_traceback() (inherited)

   Exception.with_traceback(tb) --
   set self.__traceback__ to tb and return self.

   .. py:method:: apsimNGpy.exceptions.ForgotToRunError.add_note() (inherited)

   Exception.add_note(note) --
   add a note to the exception

   .. py:attribute:: apsimNGpy.exceptions.ForgotToRunError.args (inherited)

   Default: ``<attribute 'args' of 'BaseException' objects>``

.. py:class:: apsimNGpy.exceptions.InvalidInputErrors

   Raised when the input provided is invalid or improperly formatted.

   .. py:method:: apsimNGpy.exceptions.InvalidInputErrors.with_traceback() (inherited)

   Exception.with_traceback(tb) --
   set self.__traceback__ to tb and return self.

   .. py:method:: apsimNGpy.exceptions.InvalidInputErrors.add_note() (inherited)

   Exception.add_note(note) --
   add a note to the exception

   .. py:attribute:: apsimNGpy.exceptions.InvalidInputErrors.args (inherited)

   Default: ``<attribute 'args' of 'BaseException' objects>``

.. py:class:: apsimNGpy.exceptions.ModelNotFoundError

   Raised when a specified model  cannot be found.

   .. py:method:: apsimNGpy.exceptions.ModelNotFoundError.with_traceback() (inherited)

   Exception.with_traceback(tb) --
   set self.__traceback__ to tb and return self.

   .. py:method:: apsimNGpy.exceptions.ModelNotFoundError.add_note() (inherited)

   Exception.add_note(note) --
   add a note to the exception

   .. py:attribute:: apsimNGpy.exceptions.ModelNotFoundError.args (inherited)

   Default: ``<attribute 'args' of 'BaseException' objects>``

.. py:class:: apsimNGpy.exceptions.NodeNotFoundError

   Raised when a specified model node cannot be found.

   .. py:method:: apsimNGpy.exceptions.NodeNotFoundError.with_traceback() (inherited)

   Exception.with_traceback(tb) --
   set self.__traceback__ to tb and return self.

   .. py:method:: apsimNGpy.exceptions.NodeNotFoundError.add_note() (inherited)

   Exception.add_note(note) --
   add a note to the exception

   .. py:attribute:: apsimNGpy.exceptions.NodeNotFoundError.args (inherited)

   Default: ``<attribute 'args' of 'BaseException' objects>``

.. py:class:: apsimNGpy.exceptions.TableNotFoundError

   the table was not found error.

   .. py:method:: apsimNGpy.exceptions.TableNotFoundError.with_traceback() (inherited)

   Exception.with_traceback(tb) --
   set self.__traceback__ to tb and return self.

   .. py:method:: apsimNGpy.exceptions.TableNotFoundError.add_note() (inherited)

   Exception.add_note(note) --
   add a note to the exception

   .. py:attribute:: apsimNGpy.exceptions.TableNotFoundError.args (inherited)

   Default: ``<attribute 'args' of 'BaseException' objects>``

apsimNGpy.optimizer.moo
-----------------------

Classes
^^^^^^^

.. py:class:: apsimNGpy.optimizer.moo.MultiObjectiveProblem

   Helper class that provides a standard way to create an ABC using
   inheritance.

   .. py:method:: apsimNGpy.optimizer.moo.MultiObjectiveProblem.__init__(self, apsim_model: apsimNGpy.core.cal.OptimizationBase, objectives: list, *, decision_vars: list = None, cache_size=100)

   Parameters
   ----------
   apsim_runner : apsimNGpy.core.cal.OptimizationBase
       Instance to run APSIM simulations.
   objectives : list of callable
       List of functions that take simulation output (DataFrame) and return scalar objective values.
   decision_vars : list of dict, optional
       Each dict must have: 'path', 'bounds', 'v_type', 'kwargs'.

   .. py:method:: apsimNGpy.optimizer.moo.MultiObjectiveProblem.optimization_type(self)

   Must be implemented as a property in subclass

   .. py:method:: apsimNGpy.optimizer.moo.MultiObjectiveProblem.is_mixed_type_vars(self)

   Detect if decision vars contain types other than float or int.

   .. py:method:: apsimNGpy.optimizer.moo.MultiObjectiveProblem.add_control(self, path: str, *, bounds, v_type, q=None, start_value=None, categories=None, **kwargs) (inherited)

   Adds a single APSIM parameter to be optimized.

   Parameters
   ----------
   path : str
       APSIM component path.

    v_type : type
       The Python type of the variable. Should be either `int` or `float` for continous variable problem or
       'uniform', 'choice',  'grid',   'categorical',   'qrandint',  'quniform' for mixed variable problem

   start_value : any (type determined by the variable type.
       The initial value to use for the parameter in optimization routines. Only required for single objective optimizations

   bounds : tuple of (float, float), optional
       Lower and upper bounds for the parameter (used in bounded optimization).
       Must be a tuple like (min, max). If None, the variable is considered unbounded or categorical or the algorithm to be used do not support bounds

   kwargs: dict
       One of the key-value pairs must contain a value of '?', indicating the parameter to be filled during optimization.
       Keyword arguments are used because most APSIM models have unique parameter structures, and this approach allows
       flexible specification of model-specific parameters. It is also possible to pass other parameters associated with the model in question to be changed on the fly.


   Returns
   -------
   self : object
       Returns self to support method chaining.

   .. warning::

       Raises a ``ValueError``
           If the provided arguments do not pass validation via `_evaluate_args`.


   .. Note::

       - This method is typically used before running optimization to define which
         parameters should be tuned.

   Example:

   .. code-block:: python

            from apsimNGpy.core.apsim import ApsimModel
            from apsimNGpy.core.optimizer import MultiObjectiveProblem
            runner = ApsimModel("Maize")

           _vars = [
           {'path': '.Simulations.Simulation.Field.Fertilise at sowing', 'Amount': "?", "bounds": [50, 300],
            "v_type": "float"},
           {'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': "?", 'v_type': 'float',
            'bounds': [4, 14]}
            ]
           problem = MultiObjectiveProblem(runner, objectives=objectives, decision_vars=_vars)
           # or
           problem = MultiObjectiveProblem(runner, objectives=objectives, None)
           problem.add_control(
               **{'path': '.Simulations.Simulation.Field.Fertilise at sowing', 'Amount': "?", "bounds": [50, 300],
                  "v_type": "float"})
           problem.add_control(
               **{'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': "?", 'v_type': 'float',
                  'bounds': [4, 14]})

apsimNGpy.optimizer.single
--------------------------

Classes
^^^^^^^

.. py:class:: apsimNGpy.optimizer.single.ContinuousVariable

   Defines an optimization problem for continuous variables in APSIM simulations.

   This class enables the user to configure and solve optimization problems involving continuous
   control variables in APSIM models. It provides methods for setting up control variables,
   applying bounds and starting values, inserting variable values into APSIM model configurations,
   and running optimization routines using local solvers or differential evolution.

   Inherits from:
       AbstractProblem: A base class providing caching and model-editing functionality.

   Parameters:
       ``model (str):`` The name or path of the APSIM template file.
       .
       ``simulation (str or list, optional)``: The name(s) of the APSIM simulation(s) to target.
                                           Defaults to all simulations.

       ``decision_vars`` (list, optional): A list of VarDesc instances defining variable metadata.

       ``labels (list, optional)``: Variable labels for display and results tracking.

       ``cache_size (int):`` Maximum number of results to store in the evaluation cache.

   Attributes:
       ``model (str):`` The APSIM model template file name.

       ``simulation (str):`` Target simulation(s).

       ``decision_vars (list):`` Defined control variables.

       ``decission_vars (list):`` List of VarDesc instances for optimization.

       ``labels (list): Labels`` for variables.

       ``pbar (tqdm):`` Progress bar instance.

       ```cache (bool):`` Whether to cache evaluation results.

       ```cache_size (int):`` Size of the local cache.

   Methods:
       ``add_control(...):`` Add a new control variable to the optimization problem.

       ``bounds:`` Return the bounds for all control variables as a tuple.

       ``starting_values():`` Return the initial values for all control variables.

       ``minimize_with_local_solver(...):`` Optimize using `scipy.optimize.minimize`.

       ``optimize_with_differential_evolution(...):`` Optimize using `scipy.optimize.differential_evolution`.


   Example:
       >>> class Problem(ContVarProblem):
       ...     def evaluate(self, x):
       ...         return -self.run(verbose=False).results.Yield.mean()

       >>> problem = Problem(model="Maize", simulation="Sim")
       >>> problem.add_control("Manager", "Sow using a rule", "Population", int, 5, bounds=[2, 15])
       >>> result = problem.minimize_with_local_solver(method='Powell')
       >>> print(result.x_vars)

   .. py:method:: apsimNGpy.optimizer.single.ContinuousVariable.__init__(self, apsim_model: 'apsimNGpy.core.apsim.ApsimModel', max_cache_size: int = 400, objectives: list = None, decision_vars: list = None)

   Initialize self.  See help(type(self)) for accurate signature.

   .. py:method:: apsimNGpy.optimizer.single.ContinuousVariable.minimize_with_a_local_solver(self, **kwargs)

   Run a local optimization solver using `scipy.optimize.minimize`.

   This method wraps ``scipy.optimize.minimize`` to solve APSIM optimization problems
   defined using APSIM control variables and variable encodings. It tracks optimization progress via a progress bar,
   and decodes results into user-friendly labeled dictionaries.

   Optimization methods avail
   able in `scipy.optimize.minimize` include:

   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | Method           | Type                   | Gradient Required | Handles Bounds | Handles Constraints | Notes                                        |
   +==================+========================+===================+================+=====================+==============================================+
   | Nelder-Mead      | Local (Derivative-free)| No                | No             | No                  | Simplex algorithm                            |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | Powell           | Local (Derivative-free)| No                | Yes            | No                  | Direction set method                         |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | CG               | Local (Gradient-based) | Yes               | No             | No                  | Conjugate Gradient                           |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | BFGS             | Local (Gradient-based) | Yes               | No             | No                  | Quasi-Newton                                 |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | Newton-CG        | Local (Gradient-based) | Yes               | No             | No                  | Newton's method                              |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | L-BFGS-B         | Local (Gradient-based) | Yes               | Yes            | No                  | Limited memory BFGS                          |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | TNC              | Local (Gradient-based) | Yes               | Yes            | No                  | Truncated Newton                             |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | COBYLA           | Local (Derivative-free)| No                | No             | Yes                 | Constrained optimization by linear approx.   |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | SLSQP            | Local (Gradient-based) | Yes               | Yes            | Yes                 | Sequential Least Squares Programming         |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | trust-constr     | Local (Gradient-based) | Yes               | Yes            | Yes                 | Trust-region constrained                     |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | dogleg           | Local (Gradient-based) | Yes               | No             | No                  | Requires Hessian                             |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | trust-ncg        | Local (Gradient-based) | Yes               | No             | No                  | Newton-CG trust region                       |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | trust-exact      | Local (Gradient-based) | Yes               | No             | No                  | Trust-region, exact Hessian                  |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | trust-krylov     | Local (Gradient-based) | Yes               | No             | No                  | Trust-region, Hessian-free                   |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+

   Reference:

   https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html#scipy.optimize.minimize.

   Parameters::

   **kwargs:

       Arbitrary keyword arguments passed to `scipy.optimize.minimize`, such as:

       - ``method (str)``: The optimization method to use.

       - ``options (dict)``: Solver-specific options like `disp`, `maxiter`, `gtol`, etc.

       - ``bounds (list of tuple)``: Variable bounds; defaults to self.bounds if not provided.

       - ``x0 (list):`` Optional starting guess (will override default provided values with ``add_control_var`` starting values).

   Returns:
       result (OptimizeResult):
           The optimization result object with the following additional field:
           - result.x_vars (dict): A dictionary of variable labels and optimized values.

   Example::

     from apsimNGpy.optimizer.single import ContinuousVariable

     class Problem(ContVarProblem):

           def __init__(self, model=None, simulation='Simulation'):
               super().__init__(model, simulation)
               self.simulation = simulation
           def evaluate(self, x, **kwargs):
              return -self.run(verbose=False).results.Yield.mean()

     problem = Problem(model="Maize", simulation="Sim")
     problem.add_control("Manager", "Sow using a rule", "Population", v_type="grid",
                           start_value=5, values=[5, 9, 11])
     problem.add_control("Manager", "Sow using a rule", "RowSpacing", v_type="grid",
                           start_value=400, values=[400, 800, 1200])
     result = problem.minimize_with_local_solver(method='Powell', options={"maxiter": 300})
     print(result.x_vars)
     {'Population': 9, 'RowSpacing': 800}

   .. py:method:: apsimNGpy.optimizer.single.ContinuousVariable.optimization_type(self)

   Must be implemented as a property in subclass

   .. py:method:: apsimNGpy.optimizer.single.ContinuousVariable.minimize_with_de(self, args=(), strategy='best1bin', maxiter=1000, popsize=15, tol=0.01, mutation=(0.5, 1), recombination=0.7, rng=None, callback=None, disp=True, polish=True, init='latinhypercube', atol=0, updating='immediate', workers=1, constraints=(), x0=None, *, integrality=None, vectorized=False)

   reference; https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html

   .. py:method:: apsimNGpy.optimizer.single.ContinuousVariable.update_pbar(self, labels, extend_by=None) (inherited)

   Extends the tqdm progress bar by `extend_by` steps if current progress exceeds the known max.

   Parameters:
       labels (list): List of variable labels used for tqdm description.
       extend_by (int): Number of additional steps to extend the progress bar.

   .. py:method:: apsimNGpy.optimizer.single.ContinuousVariable.add_control(self, path: str, *, bounds, v_type, q=None, start_value=None, categories=None, **kwargs) (inherited)

   Adds a single APSIM parameter to be optimized.

   Parameters
   ----------
   path : str
       APSIM component path.

    v_type : type
       The Python type of the variable. Should be either `int` or `float` for continous variable problem or
       'uniform', 'choice',  'grid',   'categorical',   'qrandint',  'quniform' for mixed variable problem

   start_value : any (type determined by the variable type.
       The initial value to use for the parameter in optimization routines. Only required for single objective optimizations

   bounds : tuple of (float, float), optional
       Lower and upper bounds for the parameter (used in bounded optimization).
       Must be a tuple like (min, max). If None, the variable is considered unbounded or categorical or the algorithm to be used do not support bounds

   kwargs: dict
       One of the key-value pairs must contain a value of '?', indicating the parameter to be filled during optimization.
       Keyword arguments are used because most APSIM models have unique parameter structures, and this approach allows
       flexible specification of model-specific parameters. It is also possible to pass other parameters associated with the model in question to be changed on the fly.


   Returns
   -------
   self : object
       Returns self to support method chaining.

   .. warning::

       Raises a ``ValueError``
           If the provided arguments do not pass validation via `_evaluate_args`.


   .. Note::

       - This method is typically used before running optimization to define which
         parameters should be tuned.

   Example:

   .. code-block:: python

            from apsimNGpy.core.apsim import ApsimModel
            from apsimNGpy.core.optimizer import MultiObjectiveProblem
            runner = ApsimModel("Maize")

           _vars = [
           {'path': '.Simulations.Simulation.Field.Fertilise at sowing', 'Amount': "?", "bounds": [50, 300],
            "v_type": "float"},
           {'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': "?", 'v_type': 'float',
            'bounds': [4, 14]}
            ]
           problem = MultiObjectiveProblem(runner, objectives=objectives, decision_vars=_vars)
           # or
           problem = MultiObjectiveProblem(runner, objectives=objectives, None)
           problem.add_control(
               **{'path': '.Simulations.Simulation.Field.Fertilise at sowing', 'Amount': "?", "bounds": [50, 300],
                  "v_type": "float"})
           problem.add_control(
               **{'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': "?", 'v_type': 'float',
                  'bounds': [4, 14]})

.. py:class:: apsimNGpy.optimizer.single.MixedVariable

   Defines an optimization problem for continuous variables in APSIM simulations.

   This class enables the user to configure and solve optimization problems involving continuous
   control variables in APSIM models. It provides methods for setting up control variables,
   applying bounds and starting values, inserting variable values into APSIM model configurations,
   and running optimization routines using local solvers or differential evolution.

   Inherits from:
       ``ContinuousVariableProblem``

   Parameters:
       ``model (str):`` The name or path of the APSIM template file.
       .
       ``simulation (str or list, optional)``: The name(s) of the APSIM simulation(s) to target.
                                           Defaults to all simulations.

       ``decision_vars`` (list, optional): A list of VarDesc instances defining variable metadata.

       ``labels (list, optional)``: Variable labels for display and results tracking.

       ``cache_size (int):`` Maximum number of results to store in the evaluation cache.

   Attributes:
       ``model (str):`` The APSIM model template file name.
       ``simulation (str):`` Target simulation(s).
       ``decision_vars (list):`` Defined control variables.
       ``decision_vars (list):`` List of VarDesc instances for optimization.
       ``labels (list): Labels`` for variables.
       ``pbar (tqdm):`` Progress bar instance.
       ```cache (bool):`` Whether to cache evaluation results.
       ```cache_size (int):`` Size of the local cache.

   Methods:
       ``add_control(...):`` Add a new control variable to the optimization problem.
       ``bounds:`` Return the bounds for all control variables as a tuple.
       ``starting_values():`` Return the initial values for all control variables.
       ``minimize_with_local_solver(...):`` Optimize using `scipy.optimize.minimize`.
       ``optimize_with_differential_evolution(...):`` Optimize using `scipy.optimize.differential_evolution`.
       ``_open_pbar(labels, maxiter):`` Open a progress bar.
       ``_close_pbar():`` Close the progress bar.

   Example:
       >>> class Problem(ContVarProblem):
       ...     def evaluate(self, x):
       ...         return -self.run(verbose=False).results.Yield.mean()

       >>> problem = Problem(model="Maize", simulation="Sim")
       >>> problem.add_control("Manager", "Sow using a rule", "Population", int, 5, bounds=[2, 15])
       >>> result = problem.minimize_with_local_solver(method='Powell')
       >>> print(result.x_vars)

   .. py:method:: apsimNGpy.optimizer.single.MixedVariable.__init__(self, apsim_model: 'ApsimNGpy.Core.Model', max_cache_size=400, objectives=None, decision_vars=None)

   Initialize self.  See help(type(self)) for accurate signature.

   .. py:method:: apsimNGpy.optimizer.single.MixedVariable.minimize_with_alocal_solver(self, **kwargs)

       Run a local optimization solver (e.g., Powell, L-BFGS-B, etc.) on given defined problem.

       This method wraps ``scipy.optimize.minimize`` and handles mixed-variable encoding internally
       using the `Objective` wrapper from ``wrapdisc``. It supports any method supported by SciPy's
       `minimize` function and uses the encoded starting values and variable bounds. This decoding implies that you can optimize categorical variable such as start dates or
       cultivar paramter with xy numerical values.

       Progress is tracked using a progress bar, and results are automatically decoded and stored
       in ``self.outcomes``.

       Parameters:
           **kwargs: Keyword arguments passed directly to `scipy.optimize.minimize`.
                     Important keys include:
                       - ``method (str)``: Optimization algorithm (e.g., 'Powell', 'L-BFGS-B').
                       - ``options (dict)``: Dictionary of solver options like maxiter, disp, etc.
   scipy.optimize.minimize provide a number of optimization algorithms see table below or for details check their website:
   https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html#scipy.optimize.minimize

   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | Method           | Type                   | Gradient Required | Handles Bounds | Handles Constraints | Notes                                        |
   +==================+========================+===================+================+=====================+==============================================+
   | Nelder-Mead      | Local (Derivative-free)| No                | No             | No                  | Simplex algorithm                            |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | Powell           | Local (Derivative-free)| No                | Yes            | No                  | Direction set method                         |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | CG               | Local (Gradient-based) | Yes               | No             | No                  | Conjugate Gradient                           |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | BFGS             | Local (Gradient-based) | Yes               | No             | No                  | Quasi-Newton                                 |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | Newton-CG        | Local (Gradient-based) | Yes               | No             | No                  | Newton's method                              |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | L-BFGS-B         | Local (Gradient-based) | Yes               | Yes            | No                  | Limited memory BFGS                          |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | TNC              | Local (Gradient-based) | Yes               | Yes            | No                  | Truncated Newton                             |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | COBYLA           | Local (Derivative-free)| No                | No             | Yes                 | Constrained optimization by linear approx.   |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | SLSQP            | Local (Gradient-based) | Yes               | Yes            | Yes                 | Sequential Least Squares Programming         |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | trust-constr     | Local (Gradient-based) | Yes               | Yes            | Yes                 | Trust-region constrained                     |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | dogleg           | Local (Gradient-based) | Yes               | No             | No                  | Requires Hessian                             |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | trust-ncg        | Local (Gradient-based) | Yes               | No             | No                  | Newton-CG trust region                       |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | trust-exact      | Local (Gradient-based) | Yes               | No             | No                  | Trust-region, exact Hessian                  |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
   | trust-krylov     | Local (Gradient-based) | Yes               | No             | No                  | Trust-region, Hessian-free                   |
   +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+

       Returns:
           result (OptimizeResult): The result of the optimization, with an additional
                                    `x_vars` attribute that provides a labeled dict of optimized
                                    control variable values.

       Raises:
           Any exceptions raised by `scipy.optimize.minimize`.

       Example:
       --------
       The following example shows how to use this method, the evaluation is very basic, but you
       can add a more advanced evaluation by adding a loss function e.g RMSE os NSE by comparing with the observed and predicted,
       and changing the control variables::

       class Problem(MixedVarProblem):
           def __init__(self, model=None, simulation='Simulation'):
               super().__init__(model, simulation)
               self.simulation = simulation

           def evaluate(self, x, **kwargs):
               # All evlauations can be defined inside here, by taking into accound the fact that the results object returns a data frame
               # Also, you can specify the database table or report name holding the ``results``
               return -self.run(verbose=False).results.Yield.mean() # A return is based on your objective definition, but as I said this could a ``RRMSE`` error or any other loss function

       # Ready to initialise the problem

       .. code-block:: python

            problem.add_control(
               path='.Simulations.Simulation.Field.Fertilise at sowing',
               Amount="?",
               bounds=[50, 300],
               v_type="float",
               start_value =50
            )

           problem.add_control(
               path='.Simulations.Simulation.Field.Sow using a variable rule',
               Population="?",
               bounds=[4, 14],
               v_type="float",
               start_value=5
           )

   .. py:method:: apsimNGpy.optimizer.single.MixedVariable.minimize_with_de(self, args=(), strategy='best1bin', maxiter=1000, popsize=15, tol=0.01, mutation=(0.5, 1), recombination=0.7, rng=None, callback=None, disp=True, polish=True, init='latinhypercube', atol=0, updating='immediate', workers=1, constraints=(), x0=None, seed=1, *, integrality=None, vectorized=False)

   Runs differential evolution on the wrapped objective function.
   Reference: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html

   .. py:method:: apsimNGpy.optimizer.single.MixedVariable.optimization_type(self)

   Must be implemented as a property in subclass

   .. py:method:: apsimNGpy.optimizer.single.MixedVariable.update_pbar(self, labels, extend_by=None) (inherited)

   Extends the tqdm progress bar by `extend_by` steps if current progress exceeds the known max.

   Parameters:
       labels (list): List of variable labels used for tqdm description.
       extend_by (int): Number of additional steps to extend the progress bar.

   .. py:method:: apsimNGpy.optimizer.single.MixedVariable.minimize_with_a_local_solver(self, **kwargs) (inherited)

   To be implimneted in sub class

   .. py:method:: apsimNGpy.optimizer.single.MixedVariable.add_control(self, path: str, *, bounds, v_type, q=None, start_value=None, categories=None, **kwargs) (inherited)

   Adds a single APSIM parameter to be optimized.

   Parameters
   ----------
   path : str
       APSIM component path.

    v_type : type
       The Python type of the variable. Should be either `int` or `float` for continous variable problem or
       'uniform', 'choice',  'grid',   'categorical',   'qrandint',  'quniform' for mixed variable problem

   start_value : any (type determined by the variable type.
       The initial value to use for the parameter in optimization routines. Only required for single objective optimizations

   bounds : tuple of (float, float), optional
       Lower and upper bounds for the parameter (used in bounded optimization).
       Must be a tuple like (min, max). If None, the variable is considered unbounded or categorical or the algorithm to be used do not support bounds

   kwargs: dict
       One of the key-value pairs must contain a value of '?', indicating the parameter to be filled during optimization.
       Keyword arguments are used because most APSIM models have unique parameter structures, and this approach allows
       flexible specification of model-specific parameters. It is also possible to pass other parameters associated with the model in question to be changed on the fly.


   Returns
   -------
   self : object
       Returns self to support method chaining.

   .. warning::

       Raises a ``ValueError``
           If the provided arguments do not pass validation via `_evaluate_args`.


   .. Note::

       - This method is typically used before running optimization to define which
         parameters should be tuned.

   Example:

   .. code-block:: python

            from apsimNGpy.core.apsim import ApsimModel
            from apsimNGpy.core.optimizer import MultiObjectiveProblem
            runner = ApsimModel("Maize")

           _vars = [
           {'path': '.Simulations.Simulation.Field.Fertilise at sowing', 'Amount': "?", "bounds": [50, 300],
            "v_type": "float"},
           {'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': "?", 'v_type': 'float',
            'bounds': [4, 14]}
            ]
           problem = MultiObjectiveProblem(runner, objectives=objectives, decision_vars=_vars)
           # or
           problem = MultiObjectiveProblem(runner, objectives=objectives, None)
           problem.add_control(
               **{'path': '.Simulations.Simulation.Field.Fertilise at sowing', 'Amount': "?", "bounds": [50, 300],
                  "v_type": "float"})
           problem.add_control(
               **{'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': "?", 'v_type': 'float',
                  'bounds': [4, 14]})

apsimNGpy.parallel.process
--------------------------

Functions
^^^^^^^^^

.. py:function:: apsimNGpy.parallel.process.custom_parallel(func, iterable: 'Iterable', *args, **kwargs)

   Run a function in parallel using threads or processes.

   Parameters
   ----------
   func : callable
       The function to run in parallel.
   iterable : iterable
       An iterable of items to be processed by ``func``.
   *args
       Additional positional arguments to pass to ``func``.

   Yields
   ------
   Any
       The result of ``func`` for each item in ``iterable``.

   Other Parameters
   ----------------
   use_thread : bool, optional, default=False
       If ``True``, use threads; if ``False``, use processes (recommended for CPU-bound work).
   ncores : int, optional
       Number of worker threads/processes. Defaults to ~50% of available CPU cores.
   verbose : bool, optional, default=True
       Whether to display a progress indicator.
   progress_message : str, optional
       Message shown alongside the progress indicator.
       Defaults to ``f"Processing multiple jobs via {func.__name__}, please wait!"``.
   void : bool, optional, default=False
       If ``True``, consume results internally (do not yield). Useful for
       side-effect–only functions.
   unit : str, optional, default="iteration"
       Label for the progress indicator (cosmetic only).

   Examples
   --------
   Run with processes (CPU-bound):

   >>> list(run_parallel(work, range(5), use_thread=False, ncores=4))

   Run with threads (I/O-bound):

   >>> for _ in run_parallel(download, urls, use_thread=True, verbose=True):
   ...     pass

.. py:function:: apsimNGpy.parallel.process.custom_parallel_chunks(func: 'Callable[..., Any]', jobs: 'Iterable[Iterable[Any]]', *args, **kwargs)

   Run a function in parallel using threads or processes.
   The iterable is automatically divided into chunks, and each chunk is submitted to worker processes or threads.

   Parameters
   ----------
   func : callable
       The function to run in parallel.

   iterable : iterable
       An iterable of items that will be processed by ``func``.

   *args
       Additional positional arguments to pass to ``func``.

   Yields
   ------
   Any
       The results of ``func`` for each item in the iterable.
       If ``func`` returns ``None``, the results will be a sequence of ``None``.
       Note: The function returns a generator, which must be consumed to retrieve results.

   Other Parameters
   ----------------
   use_thread : bool, optional, default=False
       If ``True``, use threads for parallel execution;
       if ``False``, use processes (recommended for CPU-bound tasks).

   ncores : int, optional
       Number of worker processes or threads to use.
       Defaults to 50% of available CPU cores.

   verbose : bool, optional, default=True
       Whether to display a progress bar.

   progress_message : str, optional
       Message to display alongside the progress bar.
       Defaults to ``f"Processing multiple jobs via {func.__name__}, please wait!"``.

   void : bool, optional, default=False
       If ``True``, results are consumed internally (not yielded).
       Useful for functions that operate with side effects and do not return results.

   unit : str, optional, default="iteration"
       Label for the progress bar unit (cosmetic only).

   n_chunks : int, optional
       Number of chunks to divide the iterable into.
       For example, if the iterable length is 100 and ``n_chunks=10``, each chunk will have 10 items.

   chunk_size : int, optional
       Size of each chunk.
       If specified, ``n_chunks`` is determined automatically.
       For example, if the iterable length is 100 and ``chunk_size=10``, then ``n_chunks=10``.
   Examples
   --------
   Run with processes (CPU-bound):
   >>> def worker():
   ... pass

   >>> list(run_parallel(work, range(5), use_thread=False, ncores=4))

   Run with threads (I/O-bound):

   >>> for _ in run_parallel(download, urls, use_thread=True, verbose=True):
   ...     pass

apsimNGpy.validation.evaluator
------------------------------

Evaluate predicted vs. observed data using statistical and mathematical metrics.
For detailed metric definitions, see Archontoulis et al. (2015).

Classes
^^^^^^^

.. py:class:: apsimNGpy.validation.evaluator.Validate

   Compares predicted and observed values using various statistical metrics.

   .. py:method:: apsimNGpy.validation.evaluator.Validate.__init__(self, actual: Union[numpy.ndarray, List[float], pandas.core.series.Series], predicted: Union[numpy.ndarray, List[float], pandas.core.series.Series]) -> None

   Method generated by attrs for class Validate.

   .. py:attribute:: apsimNGpy.validation.evaluator.Validate.METRICS

   Default: ``['RMSE', 'MAE', 'MSE', 'RRMSE', 'bias', 'ME', 'WIA', 'R2', 'CCC', 'slope']``

