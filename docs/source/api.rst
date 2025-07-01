apsimNGpy: API Reference
~~~~~~~~~~~~~~~~~~~~~~~~

ApsimModel 
~~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: apsimNGpy.core.apsim.ApsimModel(model: Union[os.PathLike, dict, str], out_path: Union[str, pathlib.Path] = None, out: Union[str, pathlib.Path] = None, lonlat: tuple = None, soil_series: str = 'domtcp', thickness: int = 20, bottomdepth: int = 200, thickness_values: list = None, run_all_soils: bool = False, set_wd=None, **kwargs)

   Main class for apsimNGpy modules.
    It inherits from the CoreModel class and therefore has access to a repertoire of methods from it.

    This implies that you can still run the model and modify parameters as needed.
    Example:
        >>> from apsimNGpy.core.apsim import ApsimModel
        >>> from apsimNGpy.core.base_data import load_default_simulations
        >>> path_model = load_default_simulations(crop='Maize', simulations_object=False)
        >>> model = ApsimModel(path_model, set_wd=Path.home())# replace with your path
        >>> model.run(report_name='Report') # report is the default replace as needed

.. function:: apsimNGpy.core.apsim.ApsimModel.adjust_dul(self, simulations: Union[tuple, list] = None)

   - This method checks whether the soil ``SAT`` is above or below ``DUL`` and decreases ``DUL``  values accordingly
        - Need to call this method everytime ``SAT`` is changed, or ``DUL`` is changed accordingly.

        ``simulations``: str, name of the simulation where we want to adjust DUL and SAT according.

        ``returns``:
            model object

.. function:: apsimNGpy.core.apsim.ApsimModel.auto_gen_thickness_layers(self, max_depth, n_layers=10, thin_layers=3, thin_thickness=100, growth_type='linear', thick_growth_rate=1.5)

   Generate layer thicknesses from surface to depth, starting with thin layers and increasing thickness.

        Args:
            ``max_depth`` (float): Total depth in mm.

            ``n_layers`` (int): Total number of layers.

            ``thin_layers`` (int): Number of initial thin layers.

            ``thin_thickness`` (float): Thickness of each thin layer.

            ``growth_type`` (str): 'linear' or 'exponential'.

            ``thick_growth_rate`` (float): Growth factor for thick layers (e.g., +50% each layer if exponential).

        ``Returns:``
            List[float]: List of layer thicknesses summing to max_depth.

.. function:: apsimNGpy.core.apsim.ApsimModel.replace_downloaded_soils(self, soil_tables: Union[dict, list], simulation_names: Union[tuple, list], **kwargs)

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

.. function:: apsimNGpy.core.apsim.ApsimModel.run_edited_file(self, table_name=None)

   :param table_name (str): repot table name in the database

.. function:: apsimNGpy.core.apsim.ApsimModel.spin_up(self, report_name: str = 'Report', start=None, end=None, spin_var='Carbon', simulations=None)

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

ContVarProblem 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: apsimNGpy.optimizer.one_obj.ContVarProblem(apsim_model: 'ApsimNGpy.Core.Model', max_cache_size=400, objectives=None, decision_vars=None)

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

.. function:: apsimNGpy.optimizer.one_obj.ContVarProblem.minimize_with_differential_evolution(self, args=(), strategy='best1bin', maxiter=1000, popsize=15, tol=0.01, mutation=(0.5, 1), recombination=0.7, rng=None, callback=None, disp=True, polish=True, init='latinhypercube', atol=0, updating='immediate', workers=1, constraints=(), x0=None, *, integrality=None, vectorized=False)

   reference; https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html

.. function:: apsimNGpy.optimizer.one_obj.ContVarProblem.minimize_with_local_solver(self, **kwargs)

   Run a local optimization solver using `scipy.optimize.minimize`.

        This method wraps ``scipy.optimize.minimize`` to solve APSIM optimization problems
        defined using APSIM control variables and variable encodings. It tracks optimization progress via a progress bar,
        and decodes results into user-friendly labeled dictionaries.

        Optimization methods available in `scipy.optimize.minimize` include:

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

          from apsimNGpy.optimizer.one_objective import ContVarProblem
          class Problem(ContVarProblem):
                def __init__(self, model=None, simulation='Simulation'):
                    super().__init__(model, simulation)
                    self.simulation = simulation
                def evaluate(self, x, **kwargs):
                   return -self.run(verbose=False).results.Yield.mean()

          problem = Problem(model="Maize", simulation="Sim")
          problem.add_control("Manager", "Sow using a rule", "Population", vtype="grid",
                                start_value=5, values=[5, 9, 11])
          problem.add_control("Manager", "Sow using a rule", "RowSpacing", vtype="grid",
                                start_value=400, values=[400, 800, 1200])
          result = problem.minimize_with_local_solver(method='Powell', options={"maxiter": 300})
          print(result.x_vars)
          {'Population': 9, 'RowSpacing': 800}

.. function:: apsimNGpy.optimizer.one_obj.ContVarProblem.update_pbar(self, labels, extend_by=None)

   Extends the tqdm progress bar by `extend_by` steps if current progress exceeds the known max.

        Parameters:
            labels (list): List of variable labels used for tqdm description.
            extend_by (int): Number of additional steps to extend the progress bar.

CoreModel 
~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: apsimNGpy.core.core.CoreModel(model: Union[str, pathlib.Path, dict] = None, out_path: Union[str, pathlib.Path, NoneType] = None, out: Union[str, pathlib.Path, NoneType] = None, set_wd: Union[str, pathlib.Path, NoneType] = None, experiment: bool = False, copy: Optional[bool] = None) -> None

   Modify and run APSIM Next Generation (APSIM NG) simulation models.

    This class serves as the entry point for all apsimNGpy simulations and is inherited by the `ApsimModel` class.
    It is designed to be base class for all apsimNGpy models.

    Parameters:

        ``model`` (os.PathLike): The file path to the APSIM NG model. This parameter specifies the model file to be used in the simulation.

        ``out_path`` (str, optional): The path where the output file should be saved. If not provided, the output will be saved with the same name as the model file in the current dir_path.

        ``out`` (str, optional): Alternative path for the output file. If both `out_path` and `out` are specified, `out` takes precedence. Defaults to `None`.

        ``experiment`` (bool, optional): Specifies whether to initiate your model as an experiment defaults to false
          by default, the experiment is created with permutation but permutation can be passed as a kewy word argument to change
    Keyword parameters:
      **``copy`` (bool, deprecated)**: Specifies whether to clone the simulation file. This parameter is deprecated because the simulation file is now automatically cloned by default.

    .. tip::

          When an ``APSIM`` file is loaded, it is automatically copied to ensure a fallback to the original file in case of any issues during operations.

   .. Note::

       Starting with version 0.35, accessing default simulations no longer requires the load_default_simulations function from the base_data module.
       Instead, default simulations can now be retrieved directly via the CoreModel attribute or the ApsimModel class by specifying the name of the crop (e.g., "Maize").
       This means the relevant classes can now accept either a file path or a string representing the crop name.

.. function:: apsimNGpy.core.core.CoreModel.add_crop_replacements(self, _crop: str)

   Adds a replacement folder as a child of the simulations.

        Useful when you intend to edit cultivar **parameters**.

        **Args:**
            ``_crop`` (*str*): Name of the crop to be added to the replacement folder.

        ``Returns:``
            - *ApsimModel*: An instance of `apsimNGpy.core.core.apsim.ApsimModel` or `CoreModel`.

        ``Raises:``
            - *ValueError*: If the specified crop is not found.

.. function:: apsimNGpy.core.core.CoreModel.add_db_table(self, variable_spec: list = None, set_event_names: list = None, rename: str = 'my_table', simulation_name: Union[str, list, tuple] = <UserOptionMissing>)

   Adds a new database table, which ``APSIM`` calls ``Report`` (Models.Report) to the ``Simulation`` under a Simulation Zone.

        This is different from ``add_report_variable`` in that it creates a new, named report
        table that collects data based on a given list of _variables and events.

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

.. function:: apsimNGpy.core.core.CoreModel.add_factor(self, specification: str, factor_name: str = None, **kwargs)

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

.. function:: apsimNGpy.core.core.CoreModel.add_model(self, model_type, adoptive_parent, rename=None, adoptive_parent_name=None, verbose=False, source='Models', source_model_name=None, override=True, **kwargs)

   Adds a model to the Models Simulations namespace.

        Some models are restricted to specific parent models, meaning they can only be added to compatible models.
        For example, a Clock model cannot be added to a Soil model.

        Args:
            ``model_type`` (str or Models object): The type of model to add, e.g., `Models.Clock` or just `"Clock"`. if the APSIM Models namespace is exposed to the current script, then model_type can be Models.Clock without strings quotes

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

            model.add_model(model_type=Models.Core.Simulation, adoptive_parent=Models.Core.Simulations, rename='Iowa')

            model.preview_simulation()  # doctest: +SKIP

            model.add_model(
                Models.Core.Simulation,
                adoptive_parent='Simulations',
                rename='soybean_replaced',
                source='Soybean')  # basically adding another simulation from soybean to the maize simulation

.. function:: apsimNGpy.core.core.CoreModel.add_report_variable(self, variable_spec: Union[list, str, tuple], report_name: str = None, set_event_names: Union[str, list] = None)

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

        Example::

            from apsimNGpy import core
            model = core.base_data.load_default_simulations('Maize')
            model.add_report_variable(variable_spec = '[Clock].Today as Date', report_name = 'Report')

.. function:: apsimNGpy.core.core.CoreModel.change_report(self, *, command: str, report_name='Report', simulations=None, set_DayAfterLastOutput=None, **kwargs)

   Set APSIM report _variables for specified simulations.

        This function allows you to set the variable names for an APSIM report
        in one or more simulations.

        Parameters
        ----------
        ``command`` : str
            The new report string that contains variable names.
        ``report_name`` : str
            The name of the APSIM report to update defaults to Report.
        ``simulations`` : list of str, optional
            A list of simulation names to update. If `None`, the function will
            update the report for all simulations.

        Returns
        -------
        None

.. function:: apsimNGpy.core.core.CoreModel.change_simulation_dates(self, start_date: str = None, end_date: str = None, simulations: Union[tuple, list] = None)

   Set simulation dates.

        @deprecated

        Parameters
        -----------------------------------

        ``start_date``: (str) optional
            Start date as string, by default ``None``.

        ``end_date``: str (str) optional.
            End date as string, by default ``None``.

        ``simulations`` (str), optional
            List of simulation names to update, if ``None`` update all simulations.
        Note
        ________
        one of the ``start_date`` or ``end_date`` parameters should at least not be None

        raises assertion error if all dates are None

        ``return``: ``none``

        Example:
        ---------
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

.. function:: apsimNGpy.core.core.CoreModel.change_som(self, *, simulations: Union[tuple, list] = None, inrm: int = None, icnr: int = None, surface_om_name='SurfaceOrganicMatter', **kwargs)

   @deprecated in v0.38 +

         Change ``Surface Organic Matter`` (``SOM``) properties in specified simulations.

    Parameters:
        ``simulations`` (str ort list): List of simulation names to target (default: None).

        ``inrm`` (int): New value for Initial Residue Mass (default: 1250).

        ``icnr``` (int): New value for Initial Carbon to Nitrogen Ratio (default: 27).

        ``surface_om_name`` (str, optional): name of the surface organic matter child defaults to ='SurfaceOrganicMatter'

    Returns:
        self: The current instance of the class.

.. function:: apsimNGpy.core.core.CoreModel.check_som(self, simulations=None)

   @deprecated in versions 0.38+

.. function:: apsimNGpy.core.core.CoreModel.clean_up(self, db=True, verbose=False)

   Clears the file cloned the datastore and associated csv files are not deleted if db is set to False defaults to True.

        Returns:
           >>None: This method does not return a value.

        .. caution::

           Please proceed with caution, we assume that if you want to clear the model objects, then you don't need them,
           but by making copy compulsory, then, we are clearing the edited files

.. function:: apsimNGpy.core.core.CoreModel.clone_model(self, model_type, model_name, adoptive_parent_type, rename=None, adoptive_parent_name=None)

   Clone an existing  ``model`` and move it to a specified parent within the simulation structure.
        The function modifies the simulation structure by adding the cloned model to the ``designated parent``.

        This function is useful when a model instance needs to be duplicated and repositioned in the ``APSIM`` simulation
        hierarchy without manually redefining its structure.

        Parameters:
        ----------
        ``model_type`` : Models
            The type of the model to be cloned, e.g., `Models.Simulation` or `Models.Clock`.
        ``model_name`` : str
            The unique identification name of the model instance to be cloned, e.g., `"clock1"`.
        ``adoptive_parent_type`` : Models
            The type of the new parent model where the cloned model will be placed.
        ``rename`` : str, optional
            The new name for the cloned model. If not provided, the clone will be renamed using
            the original name with a `_clone` suffix.
        ``adoptive_parent_name`` : str, optional
            The name of the parent model where the cloned model should be moved. If not provided,
            the model will be placed under the default parent of the specified type.
        ``in_place`` : bool, optional
            If ``True``, the cloned model remains in the same location but is duplicated. Defaults to ``False``.

        Returns:
        -------
        None


        Example:
        -------
         Create a cloned version of `"clock1"` and place it under `"Simulation"` with the new name ``"new_clock`"`::

            from apsimNGpy.core.base_data import load_default_simulations
            model  = load_default_simulations('Maize')
            model.clone_model('Models.Clock', "clock1", 'Models.Simulation', rename="new_clock",adoptive_parent_type= 'Models.Core.Simulations', adoptive_parent_name="Simulation")

.. function:: apsimNGpy.core.core.CoreModel.create_experiment(self, permutation: bool = True, base_name: str = None, **kwargs)

   Initialize an ``Experiment`` instance, adding the necessary models and factors.

        Args:

            ``kwargs``: Additional parameters for CoreModel.

            ``permutation`` (bool). If True, the experiment uses a permutation node to run unique combinations of the specified
            factors for the simulation. For example, if planting population and nitrogen fertilizers are provided,
            each combination of planting population level and fertilizer amount is run as an individual treatment.

           ``base_name`` (str, optional): The name of the base simulation to be moved into the experiment setup. if not
            provided, it is expected to be Simulation as the default.

        .. warning::

            ``base_name`` is optional but the experiment may not be created if there are more than one base simulations. Therefore, an error is likely.

.. function:: apsimNGpy.core.core.CoreModel.detect_model_type(self, model_instance: Union[str, Field(name='Models',type=<class 'object'>,default=<module 'Models'>,default_factory=<dataclasses._MISSING_TYPE object at 0x000001187E186E10>,init=False,repr=True,hash=None,compare=True,metadata=mappingproxy({}),kw_only=False,_field_type=_FIELD)])

   Detects the model type from a given APSIM model instance or path string.

.. function:: apsimNGpy.core.core.CoreModel.edit_cultivar(self, *, CultivarName: str, commands: str, values: Any, **kwargs)

   @deprecated
        Edits the parameters of a given cultivar. we don't need a simulation name for this unless if you are defining it in the
        manager section, if that it is the case, see update_mgt.

        Requires:
           required a replacement for the crops

        Args:

          - CultivarName (str, required): Name of the cultivar (e.g., 'laila').

          - variable_spec (str, required): A strings representing the parameter paths to be edited.
                         Example: ('[Grain].MaximumGrainsPerCob.FixedValue', '[Phenology].GrainFilling.Target.FixedValue')

          - values: values for each command (e.g., (721, 760)).

        Returns: instance of the class CoreModel or ApsimModel

.. function:: apsimNGpy.core.core.CoreModel.edit_model(self, model_type: str, model_name: str, simulations: Union[str, list] = 'all', cacheit=False, cache_size=300, verbose=False, **kwargs)

   Modify various APSIM model components by specifying the model type and name across given simulations.

        Parameters
        ----------
        ``model_type``: str
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
                If the logic for the specified `model_type` is not implemented.

        Examples::

            from apsimNGpy.core.apsim import ApsimModel
            model = ApsimModel(model='Maize')

        Example of how to edit a cultivar model::

            model.edit_model(model_type='Cultivar',
                 simulations='Simulation',
                 commands='[Phenology].Juvenile.Target.FixedValue',
                 values=256,
                 model_name='B_110',
                 new_cultivar_name='B_110_edited',
                 cultivar_manager='Sow using a variable rule')

        Edit a soil organic matter module::

            model.edit_model(
                 model_type='Organic',
                 simulations='Simulation',
                 model_name='Organic',
                 Carbon=1.23)

        Edit multiple soil layers::

            model.edit_model(
                 model_type='Organic',
                 simulations='Simulation',
                 model_name='Organic',
                 Carbon=[1.23, 1.0])

        Example of how to edit solute models::

           model.edit_model(
                 model_type='Solute',
                 simulations='Simulation',
                 model_name='NH4',
                 InitialValues=0.2)
           model.edit_model(
                model_type='Solute',
                simulations='Simulation',
                model_name='Urea',
                InitialValues=0.002)

        Edit a manager script::

           model.edit_model(
                model_type='Manager',
                simulations='Simulation',
                model_name='Sow using a variable rule',
                population=8.4)

        Edit surface organic matter parameters::

            model.edit_model(
                model_type='SurfaceOrganicMatter',
                simulations='Simulation',
                model_name='SurfaceOrganicMatter',
                InitialResidueMass=2500)

            model.edit_model(
                model_type='SurfaceOrganicMatter',
                simulations='Simulation',
                model_name='SurfaceOrganicMatter',
                InitialCNR=85)

        Edit Clock start and end dates::

            model.edit_model(
                model_type='Clock',
                simulations='Simulation',
                model_name='Clock',
                Start='2021-01-01',
                End='2021-01-12')

        Edit report _variables::

            model.edit_model(
                model_type='Report',
                simulations='Simulation',
                model_name='Report',
                variable_spec='[Maize].AboveGround.Wt as abw')

        Multiple report _variables::

            model.edit_model(
                model_type='Report',
                simulations='Simulation',
                model_name='Report',
                variable_spec=[
                '[Maize].AboveGround.Wt as abw',
                '[Maize].Grain.Total.Wt as grain_weight'])

.. function:: apsimNGpy.core.core.CoreModel.examine_management_info(self, simulations: Union[list, tuple] = None)

   @deprecated in versions 0.38+
        This will show the current management scripts in the simulation root

        Parameters
        ----------
        ``simulations``, optional
            List or tuple of simulation names to update, if `None` show all simulations.

.. function:: apsimNGpy.core.core.CoreModel.extract_any_soil_physical(self, parameter, simulations: [<class 'list'>, <class 'tuple'>] = <UserOptionMissing>)

   Extracts soil physical parameters in the simulation

        Args::
            ``parameter`` (_string_): string e.g. DUL, SAT
            ``simulations`` (string, optional): Targeted simulation name. Defaults to None.
        ---------------------------------------------------------------------------
        returns an array of the parameter values

.. function:: apsimNGpy.core.core.CoreModel.extract_soil_physical(self, simulations: [<class 'tuple'>, <class 'list'>] = None)

   Find physical soil

        Parameters
        ----------
        ``simulation``, optional
            Simulation name, if `None` use the first simulation.
        Returns
        -------
            APSIM Models.Soils.Physical object

.. function:: apsimNGpy.core.core.CoreModel.extract_start_end_years(self, simulations: str = None)

   Get simulation dates. deprecated

        Parameters
        ----------
        ``simulations``: (str) optional
            List of simulation names to use if `None` get all simulations.

        ``Returns``
            Dictionary of simulation names with dates.

.. function:: apsimNGpy.core.core.CoreModel.find_model(model_name: str)

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

.. function:: apsimNGpy.core.core.CoreModel.get_crop_replacement(self, Crop)

   :param Crop: crop to get the replacement
        :return: System.Collections.Generic.IEnumerable APSIM plant object

.. function:: apsimNGpy.core.core.CoreModel.get_model_paths(self, cultivar=False) -> list[str]

   Select out a few model types to use for building the APSIM file inspections

.. function:: apsimNGpy.core.core.CoreModel.get_simulated_output(self, report_names: Union[str, list], **kwargs) -> pandas.core.frame.DataFrame

   Reads report data from CSV files generated by the simulation.

        Parameters:
        -----------
        ``report_names`` : Union[str, list]
            Name or list of names of report tables to read. These should match the
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
          model.run() # if we are going to use get_simulated_output, no to need to provide the report name in ``run()`` method
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

.. function:: apsimNGpy.core.core.CoreModel.get_weather_from_web(self, lonlat: tuple, start: int, end: int, simulations=<UserOptionMissing>, source='nasa', filename=None)

   Replaces the meteorological (met) file in the model using weather data fetched from an online source.

            ``lonlat``: ``tuple`` containing the longitude and latitude coordinates.

            ``start``: Start date for the weather data retrieval.

            ``end``: End date for the weather data retrieval.

            ``simulations``: str, list of simulations to place the weather data, defaults to ``all`` as a string

            ``source``: Source of the weather data. Defaults to 'nasa'.

            ``filename``: Name of the file to save the retrieved data. If None, a default name is generated.

            ``Returns:``
             self. replace the weather data with the fetched data.

            Example::

              from apsimNgpy.core.apsim import ApsimModel
              model = ApsimModel(model= "Maize")
              model.get_weather_from_web(lonlat = (-93.885490, 42.060650), start = 1990, end  =2001)

            Changing weather data with unmatching start and end dates in the simulation will lead to ``RuntimeErrors``. To avoid this first check the start and end date before proceedign as follows::

              dt = model.inspect_model_parameters(model_type='Clock', model_name='Clock', simulations='Simulation')
              start, end = dt['Start'].year, dt['End'].year
              # output: 1990, 2000

.. function:: apsimNGpy.core.core.CoreModel.inspect_file(self, cultivar=False, **kwargs)

   Inspect the file by calling ``inspect_model()`` through ``get_model_paths.``
        This method is important in inspecting the ``whole file`` and also getting the ``scripts paths``

.. function:: apsimNGpy.core.core.CoreModel.inspect_model(self, model_type: Union[str, Field(name='Models',type=<class 'object'>,default=<module 'Models'>,default_factory=<dataclasses._MISSING_TYPE object at 0x000001187E186E10>,init=False,repr=True,hash=None,compare=True,metadata=mappingproxy({}),kw_only=False,_field_type=_FIELD)], fullpath=True, **kwargs)

   Inspect the model types and returns the model paths or names. usefull if you want to identify the path to the
        model for editing the model.

        ``model_type``: (Models) e.g. ``Models.Clock`` or just ``'Clock'`` will return all fullpath or names
            of models in the type Clock ``-Models.Manager`` returns information about the manager scripts in simulations. strings are allowed
            to, in the case you may not need to import the global namespace, Models. e.g ``Models.Clock`` will still work well.
            ``-Models.Core.Simulation`` returns information about the simulation -Models.Climate.Weather returns a list of
            paths or names pertaining to weather models ``-Models.Core.IPlant``  returns a list of paths or names pertaining
            to all crops models available in the simulation.

        ``fullpath``: (bool) return the full path of the model
        relative to the parent simulations node. please note the difference between simulations and simulation.

        Return: list[str]: list of all full paths or names of the model relative to the parent simulations node 


        Examples::

             from apsimNGpy.core import base_data
             from apsimNGpy.core.core import Models
        load default ``maize`` module::

             model = base_data.load_default_simulations(crop ='maize')

        Find the path to all the manager script in the simulation::

             model.inspect_model(Models.Manager, fullpath=True)
             [.Simulations.Simulation.Field.Sow using a variable rule', '.Simulations.Simulation.Field.Fertilise at
             sowing', '.Simulations.Simulation.Field.Harvest']

        Inspect the full path of the Clock Model::

             model.inspect_model(Models.Clock) # gets the path to the Clock models
             ['.Simulations.Simulation.Clock']

        Inspect the full path to the crop plants in the simulation::

             model.inspect_model(Models.Core.IPlant) # gets the path to the crop model
             ['.Simulations.Simulation.Field.Maize']

        Or use full string path as follows::

             model.inspect_model(Models.Core.IPlant, fullpath=False) # gets you the name of the crop Models
             ['Maize']
        Get full path to the fertiliser model::

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

        Inspect using full model namespace path::

             model.inspect_model('Models.Core.IPlant')

        What about weather model?::

             model.inspect_model('Weather') # inspects the weather module
             ['.Simulations.Simulation.Weather']

        Alternative::

             # or inspect using full model namespace path
             model.inspect_model('Models.Climate.Weather')
             ['.Simulations.Simulation.Weather']

        Try finding path to the cultivar model::

             model.inspect_model('Cultivar', fullpath=False) # list all available cultivar names
             ['Hycorn_53',  'Pioneer_33M54', 'Pioneer_38H20',  'Pioneer_34K77',  'Pioneer_39V43',  'Atrium', 'Laila', 'GH_5019WX']

        # we can get only the names of the cultivar models using the full string path::

             model.inspect_model('Models.PMF.Cultivar', fullpath = False)
             ['Hycorn_53',  'Pioneer_33M54', 'Pioneer_38H20',  'Pioneer_34K77',  'Pioneer_39V43',  'Atrium', 'Laila', 'GH_5019WX']

        .. tip::

            Models can be inspected either by importing the Models namespace or by using string paths. The most reliable approach is to provide the full model path—either as a string or as a Models object.
            However, remembering full paths can be tedious, so allowing partial model names or references can significantly save time during development and exploration.

.. function:: apsimNGpy.core.core.CoreModel.inspect_model_parameters(self, model_type: Union[Field(name='Models',type=<class 'object'>,default=<module 'Models'>,default_factory=<dataclasses._MISSING_TYPE object at 0x000001187E186E10>,init=False,repr=True,hash=None,compare=True,metadata=mappingproxy({}),kw_only=False,_field_type=_FIELD), str], model_name: str, simulations: Union[str, list] = <UserOptionMissing>, parameters: Union[list, set, tuple, str] = 'all', **kwargs)

   Inspect the input parameters of a specific ``APSIM`` model type instance within selected simulations.

        This method consolidates functionality previously spread across ``examine_management_info``, ``read_cultivar_params``, and other inspectors,
        allowing a unified interface for querying parameters of interest across a wide range of APSIM models.

        Parameters
        ----------
        ``model_type`` : str
            The name of the model class to inspect (e.g., 'Clock', 'Manager', 'Physical', 'Chemical', 'Water', 'Solute').
            Shorthand names are accepted (e.g., 'Clock', 'Weather') as well as fully qualified names (e.g., 'Models.Clock', 'Models.Climate.Weather').

        ``simulations`` : Union[str, list]
            A single simulation name or a list of simulation names within the APSIM context to inspect.

        ``model_name`` : str
            The name of the specific model instance within each simulation. For example, if `model_type='Solute'`,
            `model_name` might be 'NH4', 'Urea', or another solute name.

        ``parameters`` : Union[str, set, list, tuple], optional
            A specific parameter or a collection of parameters to inspect. Defaults to `'all'`, in which case all accessible attributes are returned.
            For layered models like Solute, valid parameters include `Depth`, `InitialValues`, `SoluteBD`, `Thickness`, etc.

        ``kwargs`` : dict
            Reserved for future compatibility; currently unused.

        ``Returns``
        -------
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

           model_instance = CoreModel('Maize')

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

.. function:: apsimNGpy.core.core.CoreModel.move_model(self, model_type: Field(name='Models',type=<class 'object'>,default=<module 'Models'>,default_factory=<dataclasses._MISSING_TYPE object at 0x000001187E186E10>,init=False,repr=True,hash=None,compare=True,metadata=mappingproxy({}),kw_only=False,_field_type=_FIELD), new_parent_type: Field(name='Models',type=<class 'object'>,default=<module 'Models'>,default_factory=<dataclasses._MISSING_TYPE object at 0x000001187E186E10>,init=False,repr=True,hash=None,compare=True,metadata=mappingproxy({}),kw_only=False,_field_type=_FIELD), model_name: str = None, new_parent_name: str = None, verbose: bool = False, simulations: Union[str, list] = None)

   Args:

        - ``model_type`` (Models): type of model tied to Models Namespace

        - ``new_parent_type``: new model parent type (Models)

        - ``model_name``:name of the model e.g., Clock, or Clock2, whatever name that was given to the model

        -  ``new_parent_name``: what is the new parent names =Field2, this field is optional but important if you have nested simulations

        Returns:

          returns instance of apsimNGpy.core.core.apsim.ApsimModel or apsimNGpy.core.core.apsim.CoreModel

.. function:: apsimNGpy.core.core.CoreModel.preview_simulation(self)

   Preview the simulation file in the apsimNGpy object in the APSIM graphical user interface.

        ``return``: opens the simulation file

.. function:: apsimNGpy.core.core.CoreModel.recompile_edited_model(self, out_path: os.PathLike)

   Args:
        ______________
        ``out_path``: os.PathLike object this method is called to convert the simulation object from ConverterReturnType to model like object

        ``return:`` self

.. function:: apsimNGpy.core.core.CoreModel.remove_model(self, model_type: Field(name='Models',type=<class 'object'>,default=<module 'Models'>,default_factory=<dataclasses._MISSING_TYPE object at 0x000001187E186E10>,init=False,repr=True,hash=None,compare=True,metadata=mappingproxy({}),kw_only=False,_field_type=_FIELD), model_name: str = None)

   Removes a model from the APSIM Models.Simulations namespace.

        Parameters
        ----------
        ``model_type`` : Models
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

.. function:: apsimNGpy.core.core.CoreModel.rename_model(self, model_type, *, old_name, new_name)

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
               model.rename_model(model_type="Simulation", old_name ='Simulation', new_name='my_simulation')
               # check if it has been successfully renamed
               model.inspect_model(model_type='Simulation', fullpath = False)
               ['my_simulation']
               # The alternative is to use model.inspect_file to see your changes
               model.inspect_file()

.. function:: apsimNGpy.core.core.CoreModel.replace_model_from(self, model, model_type: str, model_name: str = None, target_model_name: str = None, simulations: str = None)

   Replace a model e.g., a soil model with another soil model from another APSIM model.
        The method assumes that the model to replace is already loaded in the current model and is is the same class as source model.
        e.g., a soil node to soil node, clock node to clock node, et.c

        Args:
            ``model``: Path to the APSIM model file or a CoreModel instance.

            ``model_type`` (str): Class name (as string) of the model to replace (e.g., "Soil").

            ``model_name`` (str, optional): Name of the model instance to copy from the source model.
                If not provided, the first match is used.

            ``target_model_name`` (str, optional): Specific simulation name to target for replacement.
                Only used when replacing Simulation-level objects.

            ``simulations`` (str, optional): Simulation(s) to operate on. If None, applies to all.

        Returns:
            self: To allow method chaining.

        ``Raises:``
            ``ValueError``: If ``model_type`` is "Simulations" which is not allowed for replacement.

.. function:: apsimNGpy.core.core.CoreModel.replace_soil_property_values(self, *, parameter: str, param_values: list, soil_child: str, simulations: list = <UserOptionMissing>, indices: list = None, crop=None, **kwargs)

   Replaces values in any soil property array. The soil property array.

        ``parameter``: str: parameter name e.g., NO3, 'BD'

        ``param_values``: list or tuple: values of the specified soil property name to replace

        ``soil_child``: str: sub child of the soil component e.g., organic, physical etc.

        ``simulations``: list: list of simulations to where the child is found if
          not found, all current simulations will receive the new values, thus defaults to None

        ``indices``: list. Positions in the array which will be replaced. Please note that unlike C#, python satrt counting from 0

        ``crop`` (str, optional): string for soil water replacement. Default is None

.. function:: apsimNGpy.core.core.CoreModel.replace_soils_values_by_path(self, node_path: str, indices: list = None, **kwargs)

   set the new values of the specified soil object by path. only layers parameters are supported.

        Unfortunately, it handles one soil child at a time e.g., ``Physical`` at a go

        Args:

        ``node_path`` (str, required): complete path to the soil child of the Simulations e.g.,Simulations.Simulation.Field.Soil.Organic.
         Use`copy path to node fucntion in the GUI to get the real path of the soil node.

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

.. function:: apsimNGpy.core.core.CoreModel.replicate_file(self, k: int, path: os.PathLike = None, suffix: str = 'replica')

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

.. function:: apsimNGpy.core.core.CoreModel.restart_model(self, model_info=None)

   ``model_info``: A named tuple object returned by `load_apsim_model` from the `model_loader` module.

        Notes:
        - This parameter is crucial whenever we need to ``reinitialize`` the model, especially after updating management practices or editing the file.
        - In some cases, this method is executed automatically.
        - If ``model_info`` is not specified, the simulation will be reinitialized from `self`.

        This function is called by ``save_edited_file`` and ``update_mgt``.

        :return: self

.. function:: apsimNGpy.core.core.CoreModel.run(self, report_name: Union[tuple, list, str] = None, simulations: Union[tuple, list] = None, clean_up: bool = False, verbose: bool = False, **kwargs) -> 'CoreModel'

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

        ``clean_up`` : bool, optional
            If True, removes existing database before running.

        ``verbose`` : bool, optional
            If True, enables verbose output for debugging. The method continues with debugging info anyway if the run was unsuccessful

        ``kwargs`` : dict
            Additional keyword arguments, e.g., to_csv=True

        Returns
        -------
        ``CoreModel``
            Instance of the class CoreModel.
       ``RuntimeError``
            Raised if the ``APSIM`` run is unsuccessful. Common causes include ``missing meteorological files``,
            mismatched simulation ``start`` dates with ``weather`` data, or other ``configuration issues``.

       Example:

       Instatiate an ``apsimNGpy.core.apsim.ApsimModel`` object and run ::

              from apsimNGpy.core.apsim import ApsimModel
              model = ApsimModel(model= 'Maize')# replace with your path to the apsim template model
              model.run(report_name = "Report")

.. function:: apsimNGpy.core.core.CoreModel.save(self, file_name=None)

   Save the simulation models to file

        ``file_name``:    The name of the file to save the defaults to none, taking the exising filename

        Returns: model object

.. function:: apsimNGpy.core.core.CoreModel.save_edited_file(self, out_path: os.PathLike = None, reload: bool = False) -> Optional[ForwardRef('CoreModel')]

   Saves the model to the local drive.
            @deprecated: use save() method instead

            Notes: - If `out_path` is None, the `save_model_to_file` function extracts the filename from the
            `Model.Core.Simulation` object. - `out_path`, however, is given high priority. Therefore,
            we first evaluate if it is not None before extracting from the file. - This is crucial if you want to
            give the file a new name different from the original one while saving.

            Parameters
            - out_path (str): Desired path for the .apsimx file, by default, None.
            - reload (bool): Whether to load the file using the `out_path` or the model's original file name.

.. function:: apsimNGpy.core.core.CoreModel.set_categorical_factor(self, factor_path: str, categories: Union[list, tuple], factor_name: str = None)

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

.. function:: apsimNGpy.core.core.CoreModel.set_continuous_factor(self, factor_path, lower_bound, upper_bound, interval, factor_name=None)

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

.. function:: apsimNGpy.core.core.CoreModel.show_met_file_in_simulation(self, simulations: list = None)

   Show weather file for all simulations

.. function:: apsimNGpy.core.core.CoreModel.summarize_numeric(self, data_table: Union[str, tuple, list] = None, columns: list = None, percentiles=(0.25, 0.5, 0.75), round=2) -> pandas.core.frame.DataFrame

   Summarize numeric columns in a simulated pandas DataFrame. Useful when you want to quickly look at the simulated data

        Parameters:

            -  data_table (list, tuple, str): The names of the data table attached to the simulations. defaults to all data tables.
            -  specific (list) columns to summarize.
            -  percentiles (tuple): Optional percentiles to include in the summary.
            -  round (int): number of decimal places for rounding off.

        Returns:

            pd.DataFrame: A summary DataFrame with statistics for each numeric column.

.. function:: apsimNGpy.core.core.CoreModel.update_cultivar(self, *, parameters: dict, simulations: Union[list, tuple] = None, clear=False, **kwargs)

   Update cultivar parameters

        Parameters
        ----------
       ``parameters`` (dict, required) dictionary of cultivar parameters to update.

       ``simulations``, optional
            List or tuples of simulation names to update if `None` update all simulations.

       ``clear`` (bool, optional)
            If `True` remove all existing parameters, by default `False`.

.. function:: apsimNGpy.core.core.CoreModel.update_mgt(self, *, management: Union[dict, tuple], simulations: [<class 'list'>, <class 'tuple'>] = <UserOptionMissing>, out: [<class 'pathlib.Path'>, <class 'str'>] = None, reload: bool = True, **kwargs)

   Update management settings in the model. This method handles one management parameter at a time.

            Parameters
            ----------
            ``management`` : dict or tuple
                A dictionary or tuple of management parameters to update. The dictionary should have 'Name' as the key
                for the management script's name and corresponding values to update. Lists are not allowed as they are mutable
                and may cause issues with parallel processing. If a tuple is provided, it should be in the form (param_name, param_value).

            ``simulations`` : list of str, optional
                List of simulation names to update. If `None`, updates all simulations. This is not recommended for large
                numbers of simulations as it may result in a high computational load.

            ``out`` : str or pathlike, optional
                Path to save the edited model. If `None`, uses the default output path specified in `self.out_path` or
                `self.model_info.path`. No need to call `save_edited_file` after updating, as this method handles saving.

            Returns
            -------
            self : CoreModel
                Returns the instance of the `CoreModel` class for method chaining.

            Notes - Ensure that the ``management`` parameter is provided in the correct format to avoid errors. -
            This method does not perform ``validation`` on the provided ``management`` dictionary beyond checking for key
            existence. - If the specified management script or parameters do not exist, they will be ignored.

.. function:: apsimNGpy.core.core.CoreModel.update_mgt_by_path(self, *, path: str, fmt='.', **kwargs)

   Args:
        _________________
        ``path``: complete node path to the script manager e.g. '.Simulations.Simulation.Field.Sow using a variable rule'

        ``fmt``: seperator for formatting the path e.g., ".". Other characters can be used with
         caution, e.g., / and clearly declared in fmt argument. If you want to use the forward slash, it will be '/Simulations/Simulation/Field/Sow using a variable rule', fmt = '/'

        ``kwargs``: Corresponding keyword arguments representing the paramters in the script manager and their values. Values is what you want
        to change to; Example here ``Population`` =8.2, values should be entered with their corresponding data types e.g.,
         int, float, bool,str etc.

        return: self

ModelTools 
~~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: apsimNGpy.core._modelhelpers.ModelTools() -> None

   A utility class providing convenient access to core APSIM model operations and constants.

       Attributes:
           ``ADD`` (callable): Function or class for adding components to an APSIM model.

           ``DELETE`` (callable): Function or class for deleting components from an APSIM model.

           ``MOVE`` (callable): Function or class for moving components within the model structure.

           ``RENAME`` (callable): Function or class for renaming components.

           ``CLONER`` (callable): Utility to clone APSIM models or components.

           ``REPLACE`` (callable): Function to replace components in the model.

           ``MultiThreaded`` (Enum): Enumeration value to specify multi-threaded APSIM runs.

           ``SingleThreaded`` (Enum): Enumeration value to specify single-threaded APSIM runs.

           ``ModelRUNNER`` (class): APSIM run manager that handles simulation execution.

           ``CLASS_MODEL`` (type): The type of the APSIM Clock model, often used for type checks or instantiation.

           ``ACTIONS`` (tuple): Set of supported string actions ('get', 'delete', 'check').

           ``COLLECT`` (callable): Function for forcing memory checks

apsimNGpy.core.base_data 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: apsimNGpy.core.base_data.load_default_sensitivity_model(method: str, set_wd: str = None, simulations_object: bool = True)

   Load default simulation model from ``APSIM`` Example Folder.

    ``method``: string of the sentitivity child to load e.g. ``"Morris"`` or ``Sobol``, not case-sensitive.

    ``set_wd``: string of the set_wd to copy the model.

    ``simulations_object``: bool to specify whether to return apsimNGp.core simulation object defaults to ``True``.

    ``Returns:`` apsimNGpy.core.CoreModel simulation objects

     Example
     -----------------

    # load apsimNG object directly

    >>> morris_model = load_default_sensitivity_model(method = 'Morris', simulations_object=True)

    >>> morris_model.run()

.. class:: apsimNGpy.core.apsimSoilModel

   Main class for apsimNGpy modules.
    It inherits from the CoreModel class and therefore has access to a repertoire of methods from it.

    This implies that you can still run the model and modify parameters as needed.
    Example:
        >>> from apsimNGpy.core.apsim import ApsimModel
        >>> from apsimNGpy.core.base_data import load_default_simulations
        >>> path_model = load_default_simulations(crop='Maize', simulations_object=False)
        >>> model = ApsimModel(path_model, set_wd=Path.home())# replace with your path
        >>> model.run(report_name='Report') # report is the default replace as needed

   .. method::apsimNGpy.core.apsim.ApsimModel.adjust_dul(self, simulations: Union[tuple, list] = None)

      - This method checks whether the soil ``SAT`` is above or below ``DUL`` and decreases ``DUL``  values accordingly
        - Need to call this method everytime ``SAT`` is changed, or ``DUL`` is changed accordingly.

        ``simulations``: str, name of the simulation where we want to adjust DUL and SAT according.

        ``returns``:
            model object

   .. method::apsimNGpy.core.apsim.ApsimModel.auto_gen_thickness_layers(self, max_depth, n_layers=10, thin_layers=3, thin_thickness=100, growth_type='linear', thick_growth_rate=1.5)

      Generate layer thicknesses from surface to depth, starting with thin layers and increasing thickness.

        Args:
            ``max_depth`` (float): Total depth in mm.

            ``n_layers`` (int): Total number of layers.

            ``thin_layers`` (int): Number of initial thin layers.

            ``thin_thickness`` (float): Thickness of each thin layer.

            ``growth_type`` (str): 'linear' or 'exponential'.

            ``thick_growth_rate`` (float): Growth factor for thick layers (e.g., +50% each layer if exponential).

        ``Returns:``
            List[float]: List of layer thicknesses summing to max_depth.

   .. method::apsimNGpy.core.apsim.ApsimModel.replace_downloaded_soils(self, soil_tables: Union[dict, list], simulation_names: Union[tuple, list], **kwargs)

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

   .. method::apsimNGpy.core.apsim.ApsimModel.run_edited_file(self, table_name=None)

      :param table_name (str): repot table name in the database

   .. method::apsimNGpy.core.apsim.ApsimModel.spin_up(self, report_name: str = 'Report', start=None, end=None, spin_var='Carbon', simulations=None)

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

apsimNGpy.core.load_model 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

apsimNGpy.core.runner 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: apsimNGpy.core.runner.collect_csv_by_model_path(model_path) -> dict[typing.Any, typing.Any]

   Collects the data from the simulated model after run

.. function:: apsimNGpy.core.runner.collect_csv_from_dir(dir_path, pattern, recursive=False) -> pandas.core.frame.DataFrame

   Collects the csf=v files in a directory using a pattern, usually the pattern resembling the one of the simulations used to generate those csv files
    ``dir_path``: (str) path where to look for csv files
    ``recursive``: (bool) whether to recursively search through the directory defaults to false:
    ``pattern``:(str) pattern of the apsim files that produced the csv files through simulations

    returns
        a generator object with pandas data frames

    Example::

         mock_data = Path.home() / 'mock_data' # this a mock directory substitute accordingly
         df1= list(collect_csv_from_dir(mock_data, '*.apsimx', recursive=True)) # collects all csf file produced by apsimx recursively
         df2= list(collect_csv_from_dir(mock_data, '*.apsimx',  recursive=False)) # collects all csf file produced by apsimx only in the specified directory directory

.. function:: apsimNGpy.settings.config_internal(key: str, value: str) -> None

   Stores the apsim version and many others to be used by the app

.. function:: apsimNGpy.core.runner.get_apsim_version(verbose: bool = False)

   Display version information of the apsim model currently in the apsimNGpy config environment.

    ``verbose``: (bool) Prints the version information ``instantly``

    Example::

            apsim_version = get_apsim_version()

.. function:: apsimNGpy.core.runner.run_from_dir(dir_path, pattern, verbose=False, recursive=False, write_tocsv=True) -> [<class 'pandas.core.frame.DataFrame'>]

   This function acts as a wrapper around the ``APSIM`` command line recursive tool, automating
       the execution of APSIM simulations on all files matching a given pattern in a specified
       directory. It facilitates running simulations recursively across directories and outputs
       the results for each file are stored to a csv file in the same directory as the file'.

       What this function does is that it makes it easy to retrieve the simulated files, returning a generator that
       yields data frames

       :Parameters:
       __________________
       ``dir_path``: (str or Path, required). The path to the directory where the
           simulation files are located.
       ``pattern``: (str, required): The file pattern to match for simulation files
           (e.g., "*.apsimx").
       ``recursive``: (bool, optional):  Recursively search through subdirectories for files
           matching the file specification.
       ``write_tocsv``: (bool, optional): specify whether to write the
           simulation results to a csv. if true, the exported csv files bear the same name as the input apsimx file name
           with suffix reportname.csv. if it is ``False``,
          - if ``verbose``, the progress is printed as the elapsed time and the successfully saved csv

       ``returns``
        -- a ``generator`` that yields data frames knitted by pandas


       Example::

            mock_data = Path.home() / 'mock_data'  # As an example, let's mock some data; move the APSIM files to this directory before running
            mock_data.mkdir(parents=True, exist_ok=True)

            from apsimNGpy.core.base_data import load_default_simulations
            path_to_model = load_default_simulations(crop='maize', simulations_object=False)  # Get base model

            ap = path_to_model.replicate_file(k=10, path=mock_data) if not list(mock_data.rglob("*.apsimx")) else None

            df = run_from_dir(str(mock_data), pattern="*.apsimx", verbose=True, recursive=True)  # All files that match the pattern

.. function:: apsimNGpy.core.runner.run_model_externally(model: Union[pathlib.Path, str], verbose: bool = False, to_csv: bool = False) -> subprocess.Popen[str]

   Runs an ``APSIM`` model externally, ensuring cross-platform compatibility.

    Although ``APSIM`` models can be run internally, compatibility issues across different APSIM versions—
    particularly with compiling manager scripts—led to the introduction of this method.

    ``model``: (str) Path to the ``APSIM`` model file or a filename pattern.

    ``verbose``: (bool) If ``True``, prints stdout output during execution.

    ``to_csv``: (bool) If ``True``, write the results to a CSV file in the same directory.

    ``returns``: A subprocess.Popen object.

    Example::

        result =run_model_externally("path/to/model.apsimx", verbose=True, to_csv=True)
        from apsimNGpy.core.base_data import load_default_simulations
        path_to_model = load_default_simulations(crop ='maize', simulations_object =False)
        pop_obj = run_model_externally(path_to_model, verbose=False)
        pop_obj1 = run_model_externally(path_to_model, verbose=True)# when verbose is true, will print the time taken

.. function:: apsimNGpy.core.runner.upgrade_apsim_file(file: str, verbose: bool = True)

   Upgrade a file to the latest version of the .apsimx file format without running the file.

    Parameters
    ---------------
    ``file``: file to be upgraded to the newest version

    ``verbose``: Write detailed messages to stdout when a conversion starts/finishes.

    ``return``
       The latest version of the .apsimx file with the same name as the input file

    Example::

        from apsimNGpy.core.base_data import load_default_simulations
        filep =load_default_simulations(simulations_object= False)# this is just an example perhaps you need to pass a lower verion file because this one is extracted from thecurrent model as the excutor
        upgrade_file =upgrade_apsim_file(filep, verbose=False)

apsimNGpy.core_utils.database_utils 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: apsimNGpy.core_utils.database_utils.clear_all_tables(db)

   Deletes all rows from all user-defined tables in the given SQLite database.

    ``db``: Path to the SQLite database file.

    ``return``: None

.. function:: apsimNGpy.core_utils.database_utils.clear_table(db, table_name)

   ``db``: path to db.

    ``table_name``: name of the table to clear.

    ``return``: None

.. function:: apsimNGpy.core_utils.database_utils.dataview_to_dataframe(_model, reports)

   Convert .NET System.Data.DataView to Pandas DataFrame.
    report (str, list, tuple) of the report to be displayed. these should be in the simulations
    :param apsimng model: CoreModel object or instance
    :return: Pandas DataFrame

.. function:: apsimNGpy.core_utils.database_utils.get_db_table_names(d_b)

   ``d_b``: database name or path.

    ``return:`` all names ``SQL`` database table ``names`` existing within the database

.. function:: apsimNGpy.core.pythonet_config.load_pythonnet()

   A method for loading Python for .NET (pythonnet) and APSIM models.

    This class provides a callable method for initializing the Python for .NET (pythonnet) runtime and loading APSIM models.
    Initialize the Python for .NET (pythonnet) runtime and load APSIM models.

        This method attempts to load the 'coreclr' runtime, and if not found, falls back to an alternate runtime.
        It also sets the APSIM binary path, adds necessary references, and returns a reference to the loaded APSIM models.

        Returns:
        -------
        lm: Reference to the loaded APSIM models

        Raises:
        ------
        KeyError: If APSIM path is not found in the system environmental variable.
        ValueError: If the provided APSIM path is invalid.

        Notes:
        It raises a KeyError if APSIM path is not found. Please edit the system environmental variable on your computer.
    Attributes:
    ----------
    None

.. function:: apsimNGpy.core_utils.database_utils.read_db_table(db, report_name)

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

.. function:: apsimNGpy.core_utils.database_utils.read_with_query(db, query)

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

.. class:: apsimNGpy.core_utils.exceptionsTableNotFoundError

   Exception raised when the specified table cannot be found.

apsimNGpy.manager.soilmanager 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: apsimNGpy.manager.soilmanager.DownloadsurgoSoiltables(lonlat, select_componentname=None, summarytable=False)

   Downloads SSURGO soil tables

    Parameters
    ------------------
    :param lonlat: tuple of (longitude, latitude)
    :param select_componentname: specific component name within the map unit, default None
    :param summarytable: if True, prints summary table of component names and their percentages

.. function:: apsimNGpy.manager.soilmanager.set_depth(depththickness)

   parameters
  depththickness (array):  an array specifying the thicknness for each layer
  nlayers (int); number of layers just to remind you that you have to consider them
  ------
  return
bottom depth and top depth in a turple

apsimNGpy.manager.weathermanager 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: apsimNGpy.manager.weathermanager.daterange(start, end)

   :param start: (int) the starting year to download the weather data
  -----------------
  :param end: (int) the year under which download should stop

.. function:: apsimNGpy.manager.weathermanager.day_of_year_to_date(year, day_of_year)

   Convert day of the year to a date.

    Parameters:
    -----------
    ``year`` : int
        The year to which the day of the year belongs.

    ``day_of_year`` : int
        The day of the year (1 to 365 or 366).

    ``Returns:``
    --------
    ``datetime.date`` : he corresponding date. ``datetime.date``
        T

.. function:: apsimNGpy.manager.weathermanager.get_iem_by_station(dates_tuple, station, path, met_tag)

   ``dates_tuple``: (tuple, list) is a tupple/list of strings with date ranges
      
      - an example date string should look like this: ``dates`` = ["01-01-2012","12-31-2012"]
      ``station``: (str) is the station where toe xtract the data from
      -If ``station`` is given data will be downloaded directly from the station the default is false.
      
      :param met_tag: your preferred suffix to save on file

.. function:: apsimNGpy.manager.weathermanager.merge_columns(df1_main, common_column, df2, fill_column, df2_colummn)

   Parameters:
    ``df_main`` (pd.DataFrame): The first DataFrame to be merged and updated.

    ``common_column`` (str): The name of the common column used for merging.

    ``df2`` (pd.DataFrame): The second DataFrame to be merged with 'df_main'.

    ``fill_column`` (str): The column in 'edit' to be updated with values from 'df2_column'.

    ``df2_column`` (str): The column in 'df2' that provides replacement values for 'fill_column'.

    ``Returns``:
      ``pd.DataFrame``: A new DataFrame resulting from the merge and update operations.

apsimNGpy.parallel.process 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: apsimNGpy.parallel.process.custom_parallel(func, iterable: Iterable, *args, **kwargs)

   Run a function in parallel using threads or processes.

    *Args:
        ``func`` (callable): The function to ``run`` in parallel.

        ``iterable`` (iterable): An iterable of items that will be ran_ok by the function.

        ``*args``: Additional arguments to pass to the ``func`` function.

    Yields:
        Any: The results of the ``func`` function for each item in the iterable.

   **kwargs
     ``use_thread`` (bool, optional): If True, use threads for parallel execution; if False, use processes. Default is False.

     ``ncores`` (int, optional): The number of threads or processes to use for parallel execution. Default is 50% of cpu
         cores on the machine.

     ``verbose`` (bool): if progress should be printed on the screen, default is True.
         progress_message (str) sentence to display progress such processing weather please wait. defaults to f"Processing multiple jobs via 'func.__name__' please wait!".

     ``void`` (bool, optional): if True, it implies that the we start consuming data internally right away, recomended for methods that operates on objects without returning data,
         such that you dont need to unzip or iterate on such returned data objects.

.. function:: apsimNGpy.core_utils.database_utils.read_db_table(db, report_name)

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

.. function:: apsimNGpy.parallel.process.run_apsimx_files_in_parallel(iterable_files: Iterable, **kwargs)

   Run APSIMX simulation from multiple files in parallel.

    Args:
    ``iterable_files`` (list): A list of APSIMX  files to be run in parallel.

    ``ncores`` (int, optional): The number of CPU cores or threads to use for parallel processing. If not provided, it defaults to 50% of available CPU cores.

    ``use_threads`` (bool, optional): If set to True, the function uses thread pool execution; otherwise, it uses process pool execution. Default is False.

    Returns:
    ``returns`` a generator object containing the path to the datastore or sql databases

    Example:

    # Example usage of read_result_in_parallel function

    >>> from apsimNGpy.parallel.process import run_apsimx_files_in_parallel
    >>> simulation_files = ["file1.apsimx", "file2.apsimx", ...]  # Replace with actual database file names

    # Using processes for parallel execution

    >>> result_generator = run_apsimxfiles_in_parallel(simulation_files, ncores=4, use_threads=False)
    ```

    Notes:
    - This function efficiently reads db file results in parallel.
    - The choice of thread or process execution can be specified with the `use_threads` parameter.
    - By default, the function uses 50% of available CPU cores or threads if `ncores` is not provided.
    - Progress information is displayed during execution.
    - Handle any exceptions that may occur during execution for robust processing.

.. function:: apsimNGpy.core_utils.run_utils.run_model(path)

   :param path: path to apsimx file
    :return: none

.. class:: apsimNGpy.core_utils.progbarProgressBar

   ProgressBar(total: int, prefix: str = '', suffix: str = '', length: int = 10, fill: str = '█', color: str = 'green', leader_head: str = ' ', show_time: bool = True, unit: str = 'iteration')

   .. method::apsimNGpy.core_utils.progbar.ProgressBar.refresh(self, new_total=None)

      Force a redraw of the current progress bar without changing the iteration.

apsimNGpy.validation.evaluator 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. class:: apsimNGpy.validation.evaluatorValidate

   Compares predicted and observed values using various statistical metrics.

