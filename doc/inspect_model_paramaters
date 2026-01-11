Inspect Model
=============================

After inspecting model paths and names, now we can confortably single out specifci models and inpect their paramters in details

"""
        Inspect the input parameters of a specific APSIM model type instance within selected simulations.

        This method consolidates functionality previously spread across `examine_management_info`, `read_cultivar_params`, and other inspectors,
        allowing a unified interface for querying parameters of interest across a wide range of APSIM models.

        Parameters
        ----------
        model_type : str
            The name of the model class to inspect (e.g., 'Clock', 'Manager', 'Physical', 'Chemical', 'Water', 'Solute').
            Shorthand names are accepted (e.g., 'Clock', 'Weather') as well as fully qualified names (e.g., 'Models.Clock', 'Models.Climate.Weather').
        simulations : Union[str, list]
            A single simulation name or a list of simulation names within the APSIM context to inspect.
        model_name : str
            The name of the specific model instance within each simulation. For example, if `model_type='Solute'`,
            `model_name` might be 'NH4', 'Urea', or another solute name.
        parameters : Union[str, set, list, tuple], optional
            A specific parameter or a collection of parameters to inspect. Defaults to `'all'`, in which case all accessible attributes are returned.
            For layered models like Solute, valid parameters include `Depth`, `InitialValues`, `SoluteBD`, `Thickness`, etc.
        **kwargs : dict
            Reserved for future compatibility; currently unused.

        Returns
        -------
        Union[dict, list, pd.DataFrame, Any]
            The format depends on the model type:
            - Weather: file path(s) as string(s)
            - Clock: dictionary with start and end datetime objects (or a single datetime if only one is requested)
            - Manager: dictionary of script parameters
            - Soil-related models: pandas DataFrame of layered values
            - Report: dictionary with `VariableNames` and `EventNames`
            - Cultivar: dictionary of parameter strings

        Raises
        ------
        ValueError
            If the specified model or simulation is not found or arguments are invalid.
        NotImplementedError
            If the model type is unsupported by the current interface.

        Requirements
        ------------
        - APSIM Next Generation Python bindings (`apsimNGpy`)
        - Python 3.10+

        Examples
        --------
        >>> model_instance = CoreModel('Maize')

        # Inspect full soil organic profile

        >>> model_instance.inspect_model_parameters('Organic', simulations='Simulation', model_name='Organic')
           CNR  Carbon      Depth  FBiom  ...         FOM  Nitrogen  SoilCNRatio  Thickness
        0  12.0    1.20      0-150   0.04  ...  347.129032     0.100         12.0      150.0
        1  12.0    0.96    150-300   0.02  ...  270.344362     0.080         12.0      150.0
        2  12.0    0.60    300-600   0.02  ...  163.972144     0.050         12.0      300.0
        3  12.0    0.30    600-900   0.02  ...   99.454133     0.025         12.0      300.0
        4  12.0    0.18   900-1200   0.01  ...   60.321981     0.015         12.0      300.0
        5  12.0    0.12  1200-1500   0.01  ...   36.587131     0.010         12.0      300.0
        6  12.0    0.12  1500-1800   0.01  ...   22.191217     0.010         12.0      300.0
        [7 rows x 9 columns]

        # inspect soil physical profile
        >>> model_instance.inspect_model_parameters('Physical', simulations='Simulation', model_name='Physical')
            AirDry        BD       DUL  ...        SWmm Thickness  ThicknessCumulative
        0  0.130250  1.010565  0.521000  ...   78.150033     150.0                150.0
        1  0.198689  1.071456  0.496723  ...   74.508522     150.0                300.0
        2  0.280000  1.093939  0.488438  ...  146.531282     300.0                600.0
        3  0.280000  1.158613  0.480297  ...  144.089091     300.0                900.0
        4  0.280000  1.173012  0.471584  ...  141.475079     300.0               1200.0
        5  0.280000  1.162873  0.457071  ...  137.121171     300.0               1500.0
        6  0.280000  1.187495  0.452332  ...  135.699528     300.0               1800.0
        [7 rows x 17 columns]

        # Inspect soil chemical profile
        >>> model_instance.inspect_model_parameters('Chemical', simulations='Simulation', model_name='Chemical')
               Depth   PH  Thickness
        0      0-150  8.0      150.0
        1    150-300  8.0      150.0
        2    300-600  8.0      300.0
        3    600-900  8.0      300.0
        4   900-1200  8.0      300.0
        5  1200-1500  8.0      300.0
        6  1500-1800  8.0      300.0

        # Inspect chemical soil properties

        >>> model_instance.inspect_model_parameters('Chemical', simulations='Simulation', model_name='Chemical')

        # Inspect one or more specific parameters

        >>> model_instance.inspect_model_parameters('Organic', simulations='Simulation', model_name='Organic', parameters='Carbon')
          Carbon
        0    1.20
        1    0.96
        2    0.60
        3    0.30
        4    0.18
        5    0.12
        6    0.12

        >>> model_instance.inspect_model_parameters('Organic', simulations='Simulation', model_name='Organic', parameters=['Carbon', 'CNR'])
           Carbon   CNR
        0    1.20  12.0
        1    0.96  12.0
        2    0.60  12.0
        3    0.30  12.0
        4    0.18  12.0
        5    0.12  12.0
        6    0.12  12.0

        # Inspect Report module attributes

        >>> model_instance.inspect_model_parameters('Report', simulations='Simulation', model_name='Report')
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

        >>> model_instance.inspect_model_parameters('Report', simulations='Simulation', model_name='Report', parameters='EventNames')
        {'EventNames': ['[Maize].Harvesting']}

        # Inspect weather file path

        >>> model_instance.inspect_model_parameters('Weather', simulations='Simulation', model_name='Weather')
        '%root%/Examples/WeatherFiles/AU_Dalby.met'

        # Inspect manager script parameters

        >>> model_instance.inspect_model_parameters('Manager',
        ... simulations='Simulation', model_name='Sow using a variable rule')
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

        >>> model_instance.inspect_model_parameters('Manager',
        ... simulations='Simulation', model_name='Sow using a variable rule',
        ... parameters='Population')
        {'Population': '10'}

        # Inspect cultivar parameters

        >>> model_instance.inspect_model_parameters('Cultivar',
        ... simulations='Simulation', model_name='B_110') # lists all path specifications for B_110 parameters abd their values
        >>> model_instance.inspect_model_parameters('Cultivar', simulations='Simulation',
        ... model_name='B_110', parameters='[Phenology].Juvenile.Target.FixedValue')
        {'[Phenology].Juvenile.Target.FixedValue': '210'}

        # Inspect surface organic matter module

        >>> model_instance.inspect_model_parameters('Models.Surface.SurfaceOrganicMatter',
        ... simulations='Simulation', model_name='SurfaceOrganicMatter')
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

        >>> model_instance.inspect_model_parameters('Models.Surface.SurfaceOrganicMatter', simulations='Simulation',
        ... model_name='SurfaceOrganicMatter', parameters={'InitialCNR', 'InitialResidueMass'})
        {'InitialCNR': 100.0, 'InitialResidueMass': 500.0}

        # Inspect simulation clock

        >>> model_instance.inspect_model_parameters('Clock', simulations='Simulation', model_name='Clock')
        {'End': datetime.datetime(2000, 12, 31, 0, 0),
        'Start': datetime.datetime(1990, 1, 1, 0, 0)}

        >>> model_instance.inspect_model_parameters('Clock', simulations='Simulation',
        ... model_name='Clock', parameters='End')
        datetime.datetime(2000, 12, 31, 0, 0)

        >>> model_instance.inspect_model_parameters('Clock', simulations='Simulation',
        ... model_name='Clock', parameters='Start').year # gets the start year only
        1990

        # Inspect solute models

        >>> model_instance.inspect_model_parameters('Solute', simulations='Simulation', model_name='Urea')
               Depth  InitialValues  SoluteBD  Thickness
        0      0-150            0.0  1.010565      150.0
        1    150-300            0.0  1.071456      150.0
        2    300-600            0.0  1.093939      300.0
        3    600-900            0.0  1.158613      300.0
        4   900-1200            0.0  1.173012      300.0
        5  1200-1500            0.0  1.162873      300.0
        6  1500-1800            0.0  1.187495      300.0

        >>> model_instance.inspect_model_parameters('Solute', simulations='Simulation', model_name='NH4',
        ... parameters='InitialValues')
            InitialValues
        0            0.1
        1            0.1
        2            0.1
        3            0.1
        4            0.1
        5            0.1
        6            0.1
        """
