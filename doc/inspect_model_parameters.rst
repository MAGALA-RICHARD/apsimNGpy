.. _inspect_params:

.. rubric:: Table of Contents

.. contents::
   :local:
   :depth: 2
   :class: compact

Inspect Model Parameters
=============================

Once we have reviewed the structure of our APSIM model—including the model paths and component names—we are in a good position to explore model internals more deeply.
This tutorial introduces the  :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_model_parameters` method, which provides a unified way to extract parameters from a variety of APSIM model components.

.. Note::

    The :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_model_parameters` method simplifies parameter inspection
    by consolidating functionality that was previously spread across multiple methods such as:

    - examine_management_info

    - read_cultivar_params

    - Various model-specific inspectors

.. admonition:: inspect_model_parameters function ``signature``

    .. code-block:: python

        inspect_model_parameters(
            model_type: str,
            simulations: Union[str, list],
            model_name: str,
            parameters: Union[str, set, list, tuple] = 'all',
            **kwargs
            ) -> Union[dict, list, pd.DataFrame, Any]


model_type : (``str``) see more :ref:`details here <model_List>`
    The type or class of the model to inspect.

Examples:
    Shorthand:      ``'Clock'``, ``'Weather'``
    Fully qualified: ``'Models.Clock'``, ``'Models.Climate.Weather'``

simulations (``str`` or ``list``):
    One or more simulation names from your APSIM file to query. defaults to all

model_name: (``str``)
    The instance name of the model within the simulation.
    Example: If model_type = ``Solute``,  this could be ``'NO3'``, ``'NH4'``, or ``'Urea'``. if the model was renamed, the new name is the model_name

parameters (``str, set, list, tuple``, optional):
Specific parameter(s) to retrieve. Defaults to ``'all'``, which returns all available attributes.
Common examples for layered models like Solute: ``Depth, InitialValues, SoluteBD, Thickness``.

``**kwargs``: Reserved for future use (currently unused).

Returns

+--------------+----------------------------------------------------+
| Model Type   | Return Format                                      |
+==============+====================================================+
| Weather      | File ``path(s)`` as string(s)                      |
+--------------+----------------------------------------------------+
| Clock        | Dictionary with ``Start`` and ``End`` datetimes    |
+--------------+----------------------------------------------------+
| Manager      | ``Dictionary`` of script parameters                |
+--------------+----------------------------------------------------+
| Soil models  | ``pandas.DataFrame`` with layered data             |
+--------------+----------------------------------------------------+
| Report       | ``Dictionary`` with VariableNames and EventNames   |
+--------------+----------------------------------------------------+
| Cultivar     | ``Dictionary`` of parameter strings                |
+--------------+----------------------------------------------------+


Let's take a look at how it works.

.. code-block:: python

    from apsimNGpy.core import ApsimModel
    model_instance = ApsimModel('Maize')

Inspect full soil ``Organic`` profile:

.. code-block:: python

        model_instance.inspect_model_parameters('Organic', simulations='Simulation',
         model_name='Organic')

# output

.. code-block:: none

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

        model_instance.inspect_model_parameters('Physical', simulations='Simulation',
         model_name='Physical')

# output

.. code-block:: none

            AirDry        BD       DUL  ...        SWmm Thickness  ThicknessCumulative
        0  0.130250  1.010565  0.521000  ...   78.150033     150.0                150.0
        1  0.198689  1.071456  0.496723  ...   74.508522     150.0                300.0
        2  0.280000  1.093939  0.488438  ...  146.531282     300.0                600.0
        3  0.280000  1.158613  0.480297  ...  144.089091     300.0                900.0
        4  0.280000  1.173012  0.471584  ...  141.475079     300.0               1200.0
        5  0.280000  1.162873  0.457071  ...  137.121171     300.0               1500.0
        6  0.280000  1.187495  0.452332  ...  135.699528     300.0               1800.0
        [7 rows x 17 columns]

Inspect soil ``Chemical`` profile:

.. code-block:: python

        model_instance.inspect_model_parameters('Chemical', simulations='Simulation',
         model_name='Chemical')

# output

.. code-block:: none

               Depth   PH  Thickness
        0      0-150  8.0      150.0
        1    150-300  8.0      150.0
        2    300-600  8.0      300.0
        3    600-900  8.0      300.0
        4   900-1200  8.0      300.0
        5  1200-1500  8.0      300.0
        6  1500-1800  8.0      300.0


.. tip::

    Inspect ``one`` or ``more`` specific parameters. This can be achievement by key word argument ``parameters``.
    This argument accepts both strings and ``lists`` or ``tuple``. Please see the examples below.

.. code-block:: python

        model_instance.inspect_model_parameters('Organic',
           simulations='Simulation',
           model_name='Organic', parameters='Carbon')

#output

.. code-block:: none

          Carbon
        0    1.20
        1    0.96
        2    0.60
        3    0.30
        4    0.18
        5    0.12
        6    0.12


.. tip::

     only few selected parameters ``'Carbon'``, ``'CNR'``

.. code-block:: python

        model_instance.inspect_model_parameters('Organic',
         simulations='Simulation',
          model_name='Organic',
          parameters=['Carbon', 'CNR'])

# output

.. code-block:: python

           Carbon   CNR
        0    1.20  12.0
        1    0.96  12.0
        2    0.60  12.0
        3    0.30  12.0
        4    0.18  12.0
        5    0.12  12.0
        6    0.12  12.0


Inspect ``Report`` model attributes.

.. Hint::

    Report attributes are returned in two categories;
     1. 'EventNames': used for triggering recording or reporting events.
     2. 'VariableNames': actual variable  paths.

.. code-block:: python

        model_instance.inspect_model_parameters('Report',
         simulations='Simulation',
          model_name='Report')

 # output

.. code-block:: none

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

.. code-block:: python

        model_instance.inspect_model_parameters('Report',
         simulations='Simulation',
         model_name='Report',
         parameters='EventNames')

# output

.. code-block:: python

        {'EventNames': ['[Maize].Harvesting']}

Inspect  ``Weather`` path

.. hint::
   The returned weather file is a ``path`` for weather data

.. code-block:: python

        model_instance.inspect_model_parameters('Weather', simulations='Simulation',
          model_name='Weather')

        # output
        '%root%/Examples/WeatherFiles/AU_Dalby.met'

Inspect ``Manager`` script parameters.

.. tip::

    These scripts are from the Manager Module. You need to know the exact name of the script hence you may want to inspect the whole Manager Models in the simulations file.
    Please use ``inspect_model(model_type='Manager', fullpath=False)`` to make a selection:

.. code-block:: python

        model_instance.inspect_model_parameters('Manager',
        simulations='Simulation', model_name='Sow using a variable rule')

# output

.. code-block:: none

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

.. tip::

    Script Manager parameters can vary significantly between different scripts. To understand what parameters are available in a given context, it’s best to inspect them using the method above.
    In the following example, we demonstrate how to inspect the value of a specific parameter—Population

.. code-block:: python

        model_instance.inspect_model_parameters('Manager',
        simulations='Simulation', model_name='Sow using a variable rule',
        parameters='Population')

# Output

.. code-block:: python

        {'Population': '10'}

Inspect ``Cultivar`` parameters::

        model_instance.inspect_model_parameters('Cultivar',
        simulations='Simulation', model_name='B_110') # lists all path specifications for B_110 parameters abd their values

# output

.. code-block:: none

        {'[Phenology].Juvenile.Target.FixedValue': '210',
        '[Phenology].Photosensitive.Target.XYPairs.X': '0, 12.5, 24',
        '[Phenology].Photosensitive.Target.XYPairs.Y': '0, 0, 0',
        '[Phenology].FlagLeafToFlowering.Target.FixedValue': '1',
        '[Phenology].FloweringToGrainFilling.Target.FixedValue': '170',
        '[Phenology].GrainFilling.Target.FixedValue': '730',
        '[Phenology].Maturing.Target.FixedValue': '1',
        '[Phenology].MaturityToHarvestRipe.Target.FixedValue': '100',
        '[Rachis].DMDemands.Structural.DMDemandFunction.MaximumOrganWt.FixedValue': '36'}

.. code-block:: python

        model_instance.inspect_model_parameters('Cultivar', simulations='Simulation',
         model_name='B_110', parameters='[Phenology].Juvenile.Target.FixedValue')


.. code-block:: none

        {'[Phenology].Juvenile.Target.FixedValue': '210'}

.. caution::

  Please note that cultivar parameters are represented with an equal operator before the values,
  here they are returned as key value pairs with parameters as the keys

Inspect ``SurfaceOrganicMatter`` module. the surface organic matter parameters are not layered as ``Organic, Physical and Water or Chemical``::

        model_instance.inspect_model_parameters('Models.Surface.SurfaceOrganicMatter',
        simulations='Simulation', model_name='SurfaceOrganicMatter')

# output

.. code-block:: none

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


.. code-block:: python

        model_instance.inspect_model_parameters('Models.Surface.SurfaceOrganicMatter', simulations='Simulation',
         model_name='SurfaceOrganicMatter', parameters={'InitialCNR', 'InitialResidueMass'})

        # output
        {'InitialCNR': 100.0, 'InitialResidueMass': 500.0}

The code below inspects the soil water balance node

.. code-block:: python

    model.inspect_model_parameters('Models.WaterModel.WaterBalance', 'SoilWater')

.. code-block:: none

   {'Water': None,
     'SWCON': [4.0, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
     'CNCov': 0.8,
     'KLAT': None,
     'SummerDate': '1-Nov',
     'PotentialInfiltration': 0.0,
     'WinterCona': 5.0,
     'DiffusSlope': 16.0,
     'DiffusConst': 40.0,
     'SummerU': 5.0,
     'PSIDul': -100.0,
     'PrecipitationInterception': 0.0,
     'Depth': ['0-150',
      '150-300',
      '300-600',
      '600-900',
      '900-1200',
      '1200-1500',
      '1500-1800'],
     'PoreInteractionIndex': None,
     'CN2Bare': 73.0,
     'CatchmentArea': nan,
     'WinterDate': '1-Apr',
     'SWmm': None,
     'WinterU': 5.0,
     'Salb': 0.12,
     'SummerCona': 5.0,
     'DischargeWidth': nan,
     'dictionary': {'Salib': 'Fraction of incoming solar radiation',
      'WinterU': 'Cumulative soil water evaporation to reach end of stage 1 soil water evaporation in winter',
      'SummerU': 'Cumulative soil water evaporation to reach end of stage 1 soil water evaporation in winter',
      'PSIDul': 'Matric Pontential at DUL (cm)',
      'CNCov': 'Cover for maximum curve number reduction',
      'DiffusSlope': 'effect of soil water storage above the lower limit on on soil water diffusivity (mm)',
      'DischargeWidth': '',
      'SummerCona': 'Drying coefficient for stage 2 soil water evaporation in summer',
      'DiffusConst': 'Constant in soil water diffusivity calculations',
      'CN2Bare': 'Run off curve number ofr bare soil with average moisture',
      'CatchmentArea': 'Catchment area flow calculations (m2)',
      'WinterDate': 'Start date to switch to winter parameters',
      'WinterCona': 'Drying coefficient for stage 2 soil water evaporation in winter',
      'SummerDate': 'Start date to switch to summer parameters'}}

Description of parameter short names is given by the dictionary key as shown above in the output

.. tip::

    If there are more than one simulation, using :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_model_parameters` without specifying the simulation name will return a nested dictionary.

    Inspect simulation ``Clock``. Only two attributes are inspected ``Start`` and ``End`` dates, and they are are returned as python datetime objects

Example:

.. code-block:: python

        model_instance.inspect_model_parameters('Clock', simulations='Simulation',
          model_name='Clock')


.. code-block:: python

        {'End': datetime.datetime(2000, 12, 31, 0, 0),
        'Start': datetime.datetime(1990, 1, 1, 0, 0)}

.. code-block:: python

        model_instance.inspect_model_parameters('Clock', simulations='Simulation',
        model_name='Clock', parameters='End')

# Output

.. code-block:: none

        datetime.datetime(2000, 12, 31, 0, 0)

Extract ``Start`` year only. let's see with ``start`` year as an example::

        model_instance.inspect_model_parameters('Clock', simulations='Simulation',
        model_name='Clock', parameters='Start').year

        # output
        1990

Extract  ``End`` year only::

        model_instance.inspect_model_parameters('Clock', simulations='Simulation',
        model_name='Clock', parameters='End').year
        2000

For this model_type, argument values to parameters can be ``start_date, end, End, Start, end_date, start``. All will return the same thing, respectively.
Example::

        model_instance.inspect_model_parameters('Clock', simulations='Simulation',
        model_name='Clock', parameters='end_date')

# output

.. code-block:: none

        datetime.datetime(2000, 12, 31, 0, 0)


# Inspect ``Solute`` models with ``Urea`` as an example. Others Solutes include ``NO3``, ``NH4``

.. code-block:: python

        model_instance.inspect_model_parameters('Solute', simulations='Simulation', model_name='Urea')


output

.. code-block:: python

               Depth  InitialValues  SoluteBD  Thickness
        0      0-150            0.0  1.010565      150.0
        1    150-300            0.0  1.071456      150.0
        2    300-600            0.0  1.093939      300.0
        3    600-900            0.0  1.158613      300.0
        4   900-1200            0.0  1.173012      300.0
        5  1200-1500            0.0  1.162873      300.0
        6  1500-1800            0.0  1.187495      300.0

Inspect NH4 ``InitialValues``For layered properties,

.. Hint::

  All are returned as pandas even if one parameter is specified.

.. code-block:: python

        model_instance.inspect_model_parameters('Solute', simulations='Simulation',
         model_name='NH4',
         parameters='InitialValues')

output

.. code-block:: none

            InitialValues
        0            0.1
        1            0.1
        2            0.1
        3            0.1
        4            0.1
        5            0.1
        6            0.1


.. tip::

   The primary limitation of inspect_model_parameters is its verbosity—it often requires passing ``model_type, model_name`` and ``simulations`` or navigating deeply nested structures.

   The :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_model_parameters_by_path` method addresses this verbosity problem by allowing users to simply specify the path to the model component and (optionally) the parameters to inspect. This makes the API more concise and user-friendly.

   As with :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_model_parameters`, the parameters argument is optional—if not provided, the method will attempt to extract all available parameters from the model at the given path.

Inspect ``SurfaceOrganicMatter`` module parameters

.. code-block:: python

   model = ApsimModel('Maize')
   model.inspect_model_parameters_by_path('.Simulations.Simulation.Field.SurfaceOrganicMatter')
   # output

.. code-block:: none

   {'InitialCPR': 0.0,
     'InitialCNR': 100.0,
     'NH4': 0.0,
     'NO3': 0.0,
     'Cover': 0.0,
     'LabileP': 0.0,
     'N': 0.0,
     'SurfOM': <System.Collections.Generic.List[SurfOrganicMatterType] object at 0x1ae5c10c0>,
     'InitialResidueMass': 500.0,
     'LyingWt': 0.0,
     'StandingWt': 0.0,
     'C': 0.0,
     'P': 0.0}

Inspect surface organic matter module parameters by selecting a few parameters

.. code-block:: python

    model.inspect_model_parameters_by_path('.Simulations.Simulation.Field.SurfaceOrganicMatter',
     parameters = 'InitialCNR')
    # output

.. code-block:: python

    {'InitialCNR': 100.0}

Inspect ``Sow using a variable rule`` manager module parameters

.. code-block:: python

     model.inspect_model_parameters_by_path('.Simulations.Simulation.Field.Sow using a variable rule')

.. code-block:: none

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




Inspect ``Sow using a variable rule`` manager module parameters by selecting a few parameters

.. code-block:: python

    model.inspect_model_parameters_by_path('.Simulations.Simulation.Field.Sow using a variable rule',
       parameters= 'Population')

.. code-block:: python

    # output
    {'Population': '10'}

.. seealso::

  API: :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_model_parameters_by_path`


.. tip::

   Getting model path can be done in three ways:

       1. Use: :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_file` method to print a tree of the model structure to the console

       2. Use: :meth:`~apsimNGpy.core.apsim.inspect_model` to return the path to all the models in the specified class

       3. Use ``copy node path`` method in the graphical user interface

.. admonition:: GUI Simulation Preview.

     If that is not enough, you can preview the current simulation in the APSIM graphical user interface (GUI) using the :meth:`~apsimNGpy.core.apsim.ApsimModel.preview_simulation` method as follows;.

.. code-block:: python

     model.preview_simulation()


When executed, a window similar to the image below will open on your computer. The APSIM GUI that appears is the one currently defined as the bin path in your apsimNGpy configuration.



.. hint::

If you edit the file opened in the GUI, the changes are not automatically reflected in your ApsimModel instance. This is because the GUI opens a cloned copy of the input file.
To apply your edits to the model instance, you’ll need to reload the file .

.. seealso::

   - :ref:`API Reference: <api_ref>`
   - :ref:`Editing Models: <editor>`
   - :ref:`Plain Model Inspection: <plain_inspect>`
   - :meth:`~apsimNGpy.core.apsim.ApsimModel.preview_simulation`
   - :ref:`Models namespace <model_List>`




