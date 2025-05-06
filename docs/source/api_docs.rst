ApsimModel API Documentation
==============================

.. function:: __init__

.. function:: _change_met_file

   _similar to class weather management but just in case we want to change the weather within the subclass
        # uses existing start and end years to download the weather data

.. function:: _cultivar_params

   returns all params in a cultivar

.. function:: _extract_solute

.. function:: _find_cultivar

.. function:: _find_replacement

.. function:: _find_simulation

.. function:: _find_soil_solute

.. function:: _get_SSURGO_soil_profile

.. function:: _get_initial_chemical_values

.. function:: _kvtodict

.. function:: _remove_related_files

   Remove related database files.

.. function:: _replace_cropsoil_names

.. function:: _replace_initial_chemical_values

   _summary_

        Args:
            name (str): of the solutes e.g  NH4
            values (array): _values with equal lengths as the existing other variable
            simulations (str): simulation name in the root folder

.. function:: _try_literal_eval

.. function:: add_crop_replacements

   Adds a replacement folder as a child of the simulations. Useful when you intend to edit cultivar paramters

             Args:
               _crop: (str) name of the crop to be added the replacement folder
             return:
                instance of apsimNGpy.core.core.apsim.ApsimModel or APSIMNG

             raises an error if crop is not found

.. function:: add_factor

   Adds a factor to the created experiment. Thus, this method only works on factorial experiments

        It Could raise a value error if the experiment is not yet created.

        Under some circumstances, epxeriment will be created automatically as a permutation experiment.

        Parameters:
        ----------

        specification str, required
             A specification can be:
                - multiple values or categories e.g., "[Sow using a variable rule].Script.Population =4, 66, 9, 10"
                - Range of values e.g, "[Fertilise at sowing].Script.Amount = 0 to 200 step 20",
        factor_name: str, required
           - expected to be the user desired name of the factor being specified e.g., population


        Example:
            >>> from apsimNGpy.core import base_data
            >>> apsim = base_data.load_default_simulations(crop='Maize')
            >>> apsim.create_experiment(permutation=False)
            >>> apsim.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20", factor_name='Nitrogen')
            >>> apsim.add_factor(specification="[Sow using a variable rule].Script.Population =4 to 8 step 2", factor_name='Population')
            >>> apsim.run() # doctest: +SKIP

.. function:: add_model

   Adds a model to the Models Simulations namespace.

    Some models are restricted to specific parent models, meaning they can only be added to compatible models.
    For example, a Clock model cannot be added to a Soil model.

    Args:
        model_type (str or Models object): The type of model to add, e.g., `Models.Clock` or just `"Clock"`.
        rename (str): The new name for the model.

        adoptive_parent (Models object): The target parent where the model will be added or moved

        adoptive_parent_name (Models object, optional): Specifies the parent name for precise location.

    Returns:
        None: Models are modified in place, so models retains the same reference.

    Note:
        Added models are initially empty. Additional configuration is required to set parameters.
        For example, after adding a Clock module, you must set the start and end dates.

    Example:

         >>> from apsimNGpy import core
         >>> from apsimNGpy.core.core import Models
         >>> model =core.base_data.load_default_simulations(crop = "Maize")
         >>> model.remove_model(Models.Clock) # first delete model
         >>> model.add_model(Models.Clock, adoptive_parent = Models.Core.Simulation, rename = 'Clock_replaced', verbose=False)

         >>> model.add_model(model_type=Models.Core.Simulation, adoptive_parent=Models.Core.Simulations, rename='Iowa')
         >>> model.preview_simulation() # doctest: +SKIP
         @param adoptive_parent:

.. function:: add_report_variable

   This adds a report variable to the end of other variables, if you want to change the whole report use change_report
        Args:

        -commands (str, required): list of text commands for the report variables e.g., '[Clock].Today as Date'
        -report_name (str, optional): name of the report variable if not specified the first accessed report object will be altered
        Returns:
            returns instance of apsimNGpy.core.core.apsim.ApsimModel or apsimNGpy.core.core.apsim.APSIMNG
           raises an erros if a report is not found
        Example:
        >>> from apsimNGpy import core
        >>> model = core.base_data.load_default_simulations()
        >>> model.add_report_variable(commands = '[Clock].Today as Date', report_name = 'Report')

.. function:: adjustSatDul

.. function:: adjust_dul

   - This method checks whether the soil SAT is above or below DUL and decreases DUL  values accordingly
        - Need to cal this method everytime SAT is changed, or DUL is changed accordingly
        :param simulations: str, name of the simulation where we want to adjust DUL and SAT according
        :return:
        model object

.. function:: change_met

.. function:: change_report

   Set APSIM report variables for specified simulations.

        This function allows you to set the variable names for an APSIM report
        in one or more simulations.

        Parameters
        ----------
        command : str
            The new report string that contains variable names.
        report_name : str
            The name of the APSIM report to update defaults to Report.
        simulations : list of str, optional
            A list of simulation names to update. If `None`, the function will
            update the report for all simulations.

        Returns
        -------
        None

.. function:: change_simulation_dates

   Set simulation dates. this is important to run this method before run the weather replacement method as
        the date needs to be allowed into weather

        Parameters
        -----------------------------------
        start_date, optional
            Start date as string, by default `None`
        end_date, optional
            End date as string, by default `None`
        simulations, optional
            List of simulation names to update, if `None` update all simulations
        note
        ________
        one of the start_date or end_date parameters should at least not be None

        raises assertion error if all dates are None

        @return None
        # Example:
            from apsimNGpy.core.base_data import load_default_simulations

            model = load_default_simulations(crop='maize')

            model.change_simulation_dates(start_date='2021-01-01', end_date='2021-01-12')
             #check if it was successful
             changed_dates = model.extract_dates
             print(changed_dates)
             # OUTPUT
               {'Simulation': {'start': datetime.date(2021, 1, 1),
                'end': datetime.date(2021, 1, 12)}}
            @note
            It is possible to target a specific simulation by specifying simulation name for this case the name is Simulations, so, it could appear as follows
             model.change_simulation_dates(start_date='2021-01-01', end_date='2021-01-12', simulation = 'Simulation')

.. function:: change_som

   Change Surface Organic Matter (SOM) properties in specified simulations.

    Parameters:
        simulations (str ort list): List of simulation names to target (default: None).

        inrm (int): New value for Initial Residue Mass (default: 1250).

        icnr (int): New value for Initial Carbon to Nitrogen Ratio (default: 27).

        surface_om_name (str, optional): name of the surface organic matter child defaults to ='SurfaceOrganicMatter'
    Returns:
        self: The current instance of the class.

.. function:: check_model

.. function:: check_som

.. function:: clean_up

   Clears the file cloned the datastore and associated csv files are not deleted if db is set to False defaults to True.

        Returns:
           >>None: This method does not return a value.
           >> Please proceed with caution, we assume that if you want to clear the model objects, then you don't need them,
           but by making copy compulsory, then, we are clearing the edited files

.. function:: clone

.. function:: clone_model

.. function:: compile_scripts

.. function:: configs

   records activities that have been done on the model including changes to the file

.. function:: convert_to_IModel

.. function:: create_experiment

   Initialize an Experiment instance, adding the necessary models and factors.

        Args:

            **kwargs: Additional parameters for APSIMNG.

            :param permutation (bool). If True, the experiment uses a permutation node to run unique combinations of the specified
            factors for the simulation. For example, if planting population and nitrogen fertilizers are provided,
            each combination of planting population level and fertilizer amount is run as an individual treatment.

           :param  base_name (str, optional): The name of the base simulation to be moved into the experiment setup. if not
            provided, it is expected to be Simulation as the default

.. function:: edit_cultivar

   Edits the parameters of a given cultivar. we don't need a simulation name for this unless if you are defining it in the
        manager section, if that it is the case, see update_mgt.

        Requires:
           required a replacement for the crops

        Args:

          - CultivarName (str, required): Name of the cultivar (e.g., 'laila').

          - commands (str, required): A strings representing the parameter paths to be edited.
                         Example: ('[Grain].MaximumGrainsPerCob.FixedValue', '[Phenology].GrainFilling.Target.FixedValue')

          - values: values for each command (e.g., (721, 760)).

        Returns: instance of the class APSIMNG or ApsimModel

.. function:: examine_management_info

   This will show the current management scripts in the simulation root

        Parameters
        ----------
        simulations, optional
            List or tuple of simulation names to update, if `None` show all simulations. if you are not sure,

            use the property decorator 'extract_simulation_name'

.. function:: extract_any_soil_organic

   extracts any specified soil  parameters in the simulation

        Args:
            :param parameter (string, required): string e.g., Carbon, FBiom.
            open APSIMX file in the GUI and examne the phyicals child for clues on the parameter names
            :param simulation (string, optional): Targeted simulation name.
            Defaults to None.
           :param  param_values (array, required): arrays or list of values for the specified parameter to replace

.. function:: extract_any_soil_physical

   Extracts soil physical parameters in the simulation

        Args:
            parameter (_string_): string e.g. DUL, SAT
            simulations (string, optional): Targeted simulation name. Defaults to None.
        ---------------------------------------------------------------------------
        returns an array of the parameter values

.. function:: extract_crop_soil_water

   deprecated

        Args:
           :param parameter (str): crop soil water parameter names e.g. LL, XF etc
           :param crop (str, optional): crop name. Defaults to "Maize".
            simulation (_str_, optional): _target simulation name . Defaults to None.

        Returns:
            _type_: list[int, float]

.. function:: extract_soil_physical

   Find physical soil

        Parameters
        ----------
        simulation, optional
            Simulation name, if `None` use the first simulation.
        Returns
        -------
            APSIM Models.Soils.Physical object

.. function:: extract_soil_property_by_path

   path to the soil property should be Simulation.soil_child.parameter_name e.g., = 'Simulation.Organic.Carbon.
        @param: index(list), optional position of the soil property to a return
        @return: list

.. function:: extract_start_end_years

   Get simulation dates

        Parameters
        ----------
        simulations, optional
            List of simulation names to get, if `None` get all simulations
        Returns
        -------
            Dictionary of simulation names with dates

.. function:: extract_user_input

   Get user_input of a given model manager script
        returns;  a dictionary of user input with the key as the script parameters and values as the inputs
        Example
        _____________________________________________________
        from apsimNGpy.core.base_data import load_default_simulations
        model = load_default_simulations(crop = 'maize')
        ui = model.extract_user_input(manager_name='Fertilise at sowing')
        print(ui)
        # output
        {'Crop': 'Maize', 'FertiliserType': 'NO3N', 'Amount': '160.0'}

.. function:: find_model

   Find a model from the Models namespace and return its path.

        Args:
            model_name (str): The name of the model to find.
            model_namespace (object, optional): The root namespace (defaults to Models).
            path (str, optional): The accumulated path to the model.

        Returns:
            str: The full path to the model if found, otherwise None.

        Example:
            >>> from apsimNGpy import core  # doctest: +SKIP
             >>> from apsimNGpy.core.core import Models  # doctest: +SKIP
             >>> model =core.base_data.load_default_simulations(crop = "Maize")  # doctest: +SKIP
             >>> model.find_model("Weather")  # doctest: +SKIP
             'Models.Climate.Weather'
             >>> model.find_model("Clock")  # doctest: +SKIP
              'Models.Clock'

.. function:: find_simulations

.. function:: generate_unique_name

.. function:: get_crop_replacement

   :param Crop: crop to get the replacement
        :return: System.Collections.Generic.IEnumerable APSIM plant object

.. function:: get_current_cultivar_name

   Args:
       - ManagerName: script manager module in the zone

       Returns:
           returns the current cultivar name in the manager script 'ManagerName'

.. function:: get_initial_no3

   Get soil initial NO3 content

.. function:: get_manager_ids

.. function:: get_manager_parameters

.. function:: get_report

   Get current report string

        Parameters
        ----------
        simulation, optional
            Simulation name, if `None` use the first simulation.
        Returns
        -------
            List of report lines.
            @param names_only: return the names of the reports as a list if names_only is True

.. function:: get_soil_values_by_path

.. function:: get_weather_online

.. function:: initialise_model

.. function:: inspect

.. function:: inspect_model

   Inspects the model types and returns the model paths or names. usefull if you want ot identify the path
        to the model for editing the model.
        :param model_type: (Models) e.g. Models.Clock will return all fullpath or names of models in the type Clock
        -Models.Manager returns information about the manager scripts in simulations
        -Models.Core.Simulation returns information about the simulation
        -Models.Climate.Weather returns a list of paths or names pertaining to weather models
        -Models.Core.IPlant  returns a list of paths or names pertaining to all crops models available in the simulation
        :param  fullpath: (bool) return the full path of the model relative to the parent simulations node. please note the
            difference between simulations and simulation.
        :return:
         list[str]: list of all full paths or names of the model relative to the parent simulations node
         Example:
            >>> from apsimNGpy.core import base_data
            >>> from apsimNGpy.core.core import Models
            >>> model = base_data.load_default_simulations(crop ='maize')
            >>> model.inspect_model(Models.Manager, fullpath=True)
            ['.Simulations.Simulation.Field.Sow using a variable rule',
             '.Simulations.Simulation.Field.Fertilise at sowing',
             '.Simulations.Simulation.Field.Harvest']
            >>> model.inspect_model(Models.Clock) # gets you the path to the Clock models
             ['.Simulations.Simulation.Clock']
            >>> model.inspect_model(Models.Core.IPlant) # gets you the path to the crop model
            ['.Simulations.Simulation.Field.Maize']
            >>> model.inspect_model(Models.Core.IPlant, fullpath=False) # gets you the name of the crop Models
            ['Maize']
            >>> model.inspect_model(Models.Fertiliser, fullpath=True)
            ['.Simulations.Simulation.Field.Fertiliser']

.. function:: move_model

   Args:

        - model_type (Models): type of model tied to Models Namespace
        - new_parent_type: new model parent (Models)
        - model_name:name of the model e.g., Clock, or Clock2, whatever name that was given to the model
        -  new_parent_name: what is the new parent names =Field2, this fiedl is optional but important if you have nested simulations
        Returns:

          returns instance of apsimNGpy.core.core.apsim.ApsimModel or apsimNGpy.core.core.apsim.APSIMNG

.. function:: preview_simulation

   Preview the simulation file in the apsimNGpy object in the APSIM graphical user interface
        @return: opens the simulation file

.. function:: read_cultivar_params

.. function:: recompile_edited_model

   Args:
        ______________
        out_path: os.PathLike object this method is called to convert the simulation object from ConverterReturnType to model like object

        return: self

.. function:: remove_model

   Removes a model from the Models Simulations NameSpace

        Args:
        -model_type (Models, required): type of the model e.g., Models.Clock

        -model_name (str): name of the model e.g, Clock

        Returns: None

        Example:
               >>> from apsimNGpy import core
               >>> from apsimNGpy.core.core import Models
               >>> model = core.base_data.load_default_simulations(crop = 'Maize')
               >>> model.remove_model(Models.Clock) #deletes the clock node
               >>> model.remove_model(Models.Climate.Weather) #deletes the weather node

.. function:: rename_model

   give new name to a model in the simulations
        @param model_type: (Models) Models types e.g., Models.Clock
        @param old_model_name: (str) current model name
        @param new_model_name: (str) new model name
        @return: None
        Example;
               >>> from apsimNGpy import core
               >>> from apsimNGpy.core.core import Models
               >>> apsim = core.base_data.load_default_simulations(crop = 'Maize')
               >>> apsim = apsim.rename_model(Models.Clock, 'Clock', 'clock')

.. function:: replace_downloaded_soils

   Updates soil parameters and configurations for downloaded soil data in simulation models.

            This method adjusts soil physical and organic parameters based on provided soil tables and applies these
            adjustments to specified simulation models. Optionally, it can adjust the Radiation Use Efficiency (RUE)
            based on a Carbon to Sulfur ratio (CSR) sampled from the provided soil tables.

            Parameters:
                 :param soil_tables (list): A list containing soil data tables. Expected to contain: see the naming
            convention in the for APSIM - [0]: DataFrame with physical soil parameters. - [1]: DataFrame with organic
            soil parameters. - [2]: DataFrame with crop-specific soil parameters. - RUE adjustment. - simulation_names (list of str): Names or identifiers for the simulations to
            be updated.s


            Returns:
            - self: Returns an instance of the class for chaining methods.

            This method directly modifies the simulation instances found by `find_simulations` method calls,
            updating physical and organic soil properties, as well as crop-specific parameters like lower limit (LL),
            drain upper limit (DUL), saturation (SAT), bulk density (BD), hydraulic conductivity at saturation (KS),
            and more based on the provided soil tables.

    ->> key-word argument
             adjust_rue: Boolean, adjust the radiation use efficiency
            'set_sw_con': Boolean, set the drainage coefficient for each layer
            adJust_kl:: Bollean, adjust, kl based on productivity index
            'CultvarName': cultivar name which is in the sowing module for adjusting the rue
            tillage: specify whether you will be carried to adjust some physical parameters

.. function:: replace_met_file

.. function:: replace_met_from_web

.. function:: replace_soil_profile_from_web

.. function:: replace_soil_properties_by_path

.. function:: replace_soil_property_values

   Replaces values in any soil property array. The soil property array
        :param parameter: str: parameter name e.g., NO3, 'BD'

        :param param_values: list or tuple: values of the specified soil property name to replace

        :param soil_child: str: sub child of the soil component e.g., organic, physical etc.

        :param simulations: list: list of simulations to where the child is found if
        not found, all current simulations will receive the new values, thus defaults to None

        :param indices: list. Positions in the array which will be replaced. Please note that unlike C#, python satrt counting from 0

        :crop (str, optional): string for soil water replacement. Default is None

.. function:: replace_soils

.. function:: replace_soils_values_by_path

   set the new values of the specified soil object by path

        unfortunately, it handles one soil child at a time e.g., Physical at a go
        Args:

        node_path (str, required): complete path to the soil child of the Simulations e.g.,Simulations.Simulation.Field.Soil.Organic.
         Use`copy path to node fucntion in the GUI to get the real path of the soil node.

        indices (list, optional): defaults to none but could be the position of the replacement values for arrays

        kwargs (key word arguments): This carries the parameter and the values e.g., BD = 1.23 or BD = [1.23, 1.75]
         if the child is Physical, or Carbon if the child is Organic

         raises raise value error if none of the key word arguments, representing the paramters are specified
         returns:
            - apsimNGpy.core.APSIMNG object and if the path specified does not translate to the child object in
         the simulation

         Example:
              >>> from apsimNGpy.core.base_data import load_default_simulations

             >>> model = load_default_simulations(crop ='Maize', simulations_object=False)# initiate model

              >>> model = APSIMNG(model)# replace with your intended file path
              >>> model.replace_soils_values_by_path(node_path='.Simulations.Simulation.Field.Soil.Organic', indices=[0], Carbon =1.3)

              >>> sv= model.get_soil_values_by_path('.Simulations.Simulation.Field.Soil.Organic', 'Carbon')

               output # {'Carbon': [1.3, 0.96, 0.6, 0.3, 0.18, 0.12, 0.12]}

.. function:: replicate_file

   Replicates a file 'k' times.

        If a path is specified, the copies will be placed in that dir_path with incremented filenames.

        If no path is specified, copies are created in the same dir_path as the original file, also with incremented filenames.

        Parameters:
        - self: The core.api.APSIMNG object instance containing 'path' attribute pointing to the file to be replicated.

        - k (int): The number of copies to create.

        - path (str, optional): The dir_path where the replicated files will be saved. Defaults to None, meaning the
        same dir_path as the source file.

        - suffix (str, optional): a suffix to attached with the copies. Defaults to "replicate"


        Returns:
        - A list of paths to the newly created files if get_back_list is True else a generator is returned.

.. function:: report_ids

.. function:: restart_model

   :param model_info: A named tuple object returned by `load_apsim_model` from the `model_loader` module.

        Notes:
        - This parameter is crucial whenever we need to reinitialize the model, especially after updating management practices or editing the file.
        - In some cases, this method is executed automatically.
        - If `model_info` is not specified, the simulation will be reinitialized from `self`.

        This function is called by `save_edited_file` and `update_mgt`.

        :return: self

.. function:: run

   Run apsim model in the simulations

        Parameters
        ----------
         :param report_name: (iterable, str). defaults to APSIM defaults Report Name if not specified,
        --Notes
          if `report_name` is iterable, all tables are read and aggregated not one data frame, returned one pandas data frame
          if `report_name` is nOne we run but do not collect the results from the data base
          if report name is string e.g.,  report a panda data frame is returned

        simulations (__list_), optional
            List of simulation names to run, if `None` runs all simulations, by default `None`.

        :param clean (_-boolean_), optional
            If `True` remove an existing database for the file before running, deafults to False`

        :param multithread: bool
            If `True` APSIM uses multiple threads, by default, `True`
            :param simulations:

        returns
            instance of the class APSIMNG

.. function:: run_edited_file

   Run simulations in this subclass if we want to clean the database, we need to
         spawn the path with one process to avoid os access permission errors

            :param table_name (str): repot table name in the database

.. function:: save

   Save the simulation models to file
        @param file_name:    The name of the file to save the defaults to none, taking the exising filename
        @return: model object

.. function:: save_edited_file

   Saves the model to the local drive.

            Notes: - If `out_path` is None, the `save_model_to_file` function extracts the filename from the
            `Model.Core.Simulation` object. - `out_path`, however, is given high priority. Therefore,
            we first evaluate if it is not None before extracting from the file. - This is crucial if you want to
            give the file a new name different from the original one while saving.

            Parameters
            - out_path (str): Desired path for the .apsimx file, by default, None.
            - reload (bool): Whether to load the file using the `out_path` or the model's original file name.

.. function:: set_categorical_factor

   wraps around add_factor() to add a continuous factor, just for clarity

        factor_path (str, required): path of the factor definition relative to its child node "[Fertilise at sowing].Script.Amount"
        factor_name: (str) name of the factor.
        categories (tuple, list, required): multiple values of a factor
        return:
         self
        Example:
            >>> from apsimNGpy.core import base_data
            >>> apsim = base_data.load_default_simulations(crop='Maize')
            >>> apsim.create_experiment(permutation=False)
            >>> apsim.set_continuous_factor(factor_path = "[Fertilise at sowing].Script.Amount", lower_bound=100, upper_bound=300, interval=10)

.. function:: set_continuous_factor

   Wraps around `add_factor()` to add a continuous factor, just for clarity

        Args:
            factor_path (str): The path of the factor definition relative to its child node,
                e.g., `"[Fertilise at sowing].Script.Amount"`.
            factor_name (str): The name of the factor.
            lower_bound (int or float): The lower bound of the factor.
            upper_bound (int or float): The upper bound of the factor.
            interval (int or float): The distance between the factor levels.

        Returns:
            ApsimModel or APSIMNG: An instance of `apsimNGpy.core.core.apsim.ApsimModel` or `APSIMNG`.
        Example:
            >>> from apsimNGpy.core import base_data
            >>> apsim = base_data.load_default_simulations(crop='Maize')
            >>> apsim.create_experiment(permutation=False)
            >>> apsim.set_continuous_factor(factor_path = "[Fertilise at sowing].Script.Amount", lower_bound=100, upper_bound=300, interval=10)

.. function:: show_cropsoil_names

.. function:: show_met_file_in_simulation

   Show weather file for all simulations

.. function:: spin_up

   Perform a spin-up operation on the aPSim model.

        This method is used to simulate a spin-up operation in an aPSim model. During a spin-up, various soil properties or
        variables may be adjusted based on the simulation results.

        Parameters:
        ----------
        report_name : str, optional (default: 'Report')
            The name of the aPSim report to be used for simulation results.
        start : str, optional
            The start date for the simulation (e.g., '01-01-2023'). If provided, it will change the simulation start date.
        end : str, optional
            The end date for the simulation (e.g., '3-12-2023'). If provided, it will change the simulation end date.
        spin_var : str, optional (default: 'Carbon'). the difference between the start and end date will determine the spin-up period
            The variable representing the child of spin-up operation. Supported values are 'Carbon' or 'DUL'.

        Returns:
        -------
        self : ApsimModel
            The modified ApsimModel object after the spin-up operation.
            you could call save_edited file and save it to your specified location, but you can also proceed with the simulation

.. function:: strip_time

.. function:: update_cultivar

   Update cultivar parameters

        Parameters
        ----------
       - parameters (dict, required) dictionary of cultivar parameters to update.

       - simulations, optional
            List or tuples of simulation names to update if `None` update all simulations.
       - clear (bool, optional)
            If `True` remove all existing parameters, by default `False`.

.. function:: update_mgt

   Update management settings in the model. This method handles one management parameter at a time.

            Parameters
            ----------
            management : dict or tuple
                A dictionary or tuple of management parameters to update. The dictionary should have 'Name' as the key
                for the management script's name and corresponding values to update. Lists are not allowed as they are mutable
                and may cause issues with parallel processing. If a tuple is provided, it should be in the form (param_name, param_value).

            simulations : list of str, optional
                List of simulation names to update. If `None`, updates all simulations. This is not recommended for large
                numbers of simulations as it may result in a high computational load.

            out : str or pathlike, optional
                Path to save the edited model. If `None`, uses the default output path specified in `self.out_path` or
                `self.model_info.path`. No need to call `save_edited_file` after updating, as this method handles saving.

            Returns
            -------
            self : Editor
                Returns the instance of the `Editor` class for method chaining.

            Notes ----- - Ensure that the `management` parameter is provided in the correct format to avoid errors. -
            This method does not perform validation on the provided `management` dictionary beyond checking for key
            existence. - If the specified management script or parameters do not exist, they will be ignored.
            using a tuple for a specifying management script, paramters is recommended if you are going to pass the function to  a multi-processing class fucntion

.. function:: update_mgt_by_path

   Args:
        _________________
        path: complete node path to the script manager e.g. '.Simulations.Simulation.Field.Sow using a
        variable rule'

        fmt: seperator for formatting the path e.g., ".". Other characters can be used with
        caution, e.g., / and clearly declared in fmt argument.
         For the above path if we want to use the forward slash, it will be '/Simulations/Simulation/Field/Sow using a variable rule', fmt = '/'

        kwargs: Corresponding keyword arguments representing the paramters in the script manager and their values. Values is what you want
        to change to; Example here Population =8.2, values should be entered with their corresponding data types e.g.,
        int, float, bool,str etc.

        return: self

