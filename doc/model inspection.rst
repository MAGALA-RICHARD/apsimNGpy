.. _plain_inspect:

Inspect Model
=============================

.. image:: ../images/inspect.gif
   :alt: Run APSIM simulation
   :align: center
   :width: 800px

Most of the time, when modifying model parameters and values, you need the full path to the specified APSIM model.  
This is where the :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_model` method becomes useful—it allows you to inspect the model without opening the file in the APSIM GUI.

.. hint::
    Models can be inspected either by importing the ``Models`` namespace or by using string paths. The most reliable approach is to provide the full model path—either as a string or as a ``Models`` attribute path.
    However, remembering full paths can be tedious, so allowing partial model names or references can significantly save time during development and exploration.

If you are stranded, check the list below, red color are the modules,
and not allowed in this function and below each module are the model types

.. _model_List:

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

Let's take a look at how it works.

.. code-block:: python

         from apsimNGpy.core.core import Models
         from apsimNGpy.core.apsim import ApsimModel

load default ``maize`` module::

    model = ApsimModel(model= 'Maize')


Find the path to all the manager script in the simulation::

     model.inspect_model(Models.Manager, fullpath=True)

.. code-block:: python

     [.Simulations.Simulation.Field.Sow using a variable rule',
     '.Simulations.Simulation.Field.Fertilise at sowing',
     '.Simulations.Simulation.Field.Harvest']

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

.. Hint::

    The models from APSIM Models namespace are abstracted to use strings. All you need is to specify the name or the full path to the model enclosed in a string as follows::

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

     model.inspect_model('Models.PMF.Cultivar', fullpath=True) # list all available cultivar path relative to the **Simulations** parent node

.. code-block:: none

    ['.Simulations.Simulation.Field.Maize.CultivarFolder.Hycorn_53',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_33M54',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_38H20',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_34K77',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_39V43',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Atrium',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Laila',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.GH_5019WX',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Hycorn_40',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.GH_5009',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.malawi_local',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.mh19',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.mh17',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.mh16',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.mh12',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.sc623',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.sc625',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.sc601',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.CG4141',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.mh18',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.r215',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Melkassa',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.sr52',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.sc501',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.r201',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.sc401',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.NSCM_41',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Makueni',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Katumani',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_3153',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Pioneer_39G12',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_80',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_90',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_95',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_100',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_103',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_105',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_108',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_110',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_112',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_115',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_120',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_130',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_80',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_90',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_95',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_100',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_103',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_105',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_108',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_110',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_112',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_115',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_120',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.A_130',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.HY_110',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.LY_110',
     '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.P1197']


We can get only the names of the cultivar models using the full string path::

     model.inspect_model('Models.PMF.Cultivar', fullpath = False)

.. code-block:: none

     ['Hycorn_53',  'Pioneer_33M54', 'Pioneer_38H20',  'Pioneer_34K77',
      'Pioneer_39V43',  'Atrium', 'Laila', 'GH_5019WX']


.. hint::

    ``model_type`` can be any of the following classes from the `Models` namespace, and
    can be passed as strings or as full path to Models namespace if Models is imported. See the description about :ref:`model_List`.


.. seealso::

  API description: :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_model`

.. tip::

    In some cases, determining the model type can be challenging. Fortunately, **apsimNGpy** provides a recursive function to simplify this process—the :meth:`~apsimNGpy.core.apsim.ApsimModel.find_model` method.
    This method helps identify the model type efficiently. However, you need to know the name of the model, such as *Clock* or *Weather*, to use it effectively.

.. code-block:: python

    from apsimNGpy import core
    from apsimNGpy.core.core import Models
    from apsimNGpy.core.apsim import ApsimModel

    # Load the default maize simulation
    model = ApsimModel(model= 'Maize')

    # Inspect or find specific components
    model.find_model("Weather")
    Models.Climate.Weather

    model.find_model("Clock")
    Models.Clock

Whole Model inspection
=====================================

Use :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_file` method to inspects all simulations in the file.
This method displays a tree showing how each model is connected with each other.
``Model types or classes`` are colored and are followed by their corresponding full paths relative to their parent node; ``Simulations``.

For interactive consoles (e.g., Jupyter Notebook), this is a game changer, you’ll hardly ever need the GUI.


.. code-block:: python

    model.inspect_file(cultivar =False)



.. image:: ../images/apsim_file_structure.png
    :alt: Tree structure of the APSIM model
    :align: center
    :width: 100%
    :name: tree_structure_model

.. tip::

  To include cultivar paths to the above simulation tree, use ``cultivar = True`` as shown below. For developers who are testing the method please use console = False

.. code-block:: python

    model.inspect_file(cultivar = True)

.. code-block:: none

    Results of the above code not displayed because it is too long

The advantages of apsimNGpy is its ability to work with very nested apsimx json model. One of the examples is the  `Report.apsimx` shipped within the `Example` folder

.. code-block:: python

    model = ApsimModel('Report')
    sims = model.simulations_list
    print(sims)
    ['SimpleReportingSim', 'Annual Reporting In June', 'ContinuousWheatExample', 'Seasonal']
    print(model.tables_list)
    ['ReportSimple', 'ReportOnEvents', 'ReportOnSpecificDaysEveryYear', 'ReportOnSpecificDates', 'ReportArrays',
     'ReportDaily', 'ReportWeekly', 'ReportMonthly', 'ReportYearly', 'ReportSimulation', 'AnnualReporting',
     'MonthlyReporting', 'DailyReporting', 'ReportInCropAnnually', 'ReportGrainOnHarvesting', 'ReportGrainDaily',
     'ReportSpecificDates', 'SeasonalOverall', 'SeasonalByYear', 'SeasonalByYearWithOnKeyword']
    model.inspect_model('Models.Manager')
    ['.Simulations.SimpleReportingSim.Field.Sowing',
     '.Simulations.SimpleReportingSim.Field.Fertilise at sowing',
     '.Simulations.SimpleReportingSim.Field.Harvest',
     '.Simulations.SimpleReportingSim.Field.AutoIrrig',
     '.Simulations.SimpleReportingSim.Field.ReportHelper',
     '.Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.CutRotation',
     '.Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.AutomaticFertiliser',
     '.Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.FertiliseOnFixedDates',
     '.Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.AutomaticIrrigation',
     '.Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.ReportHelper',
     '.Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Sowing',
     '.Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Fertilise at sowing',
     '.Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Harvest',
     '.Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.ReportHelper',
     '.Simulations.Grouping.Seasonal.ClimateController',
     '.Simulations.Grouping.Seasonal.Field.AutomaticIrrigation']
    model.inspect_model('Models.Clock')
    ['.Simulations.SimpleReportingSim.Clock',
     '.Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Clock',
     '.Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Clock',
     '.Simulations.Grouping.Seasonal.Clock']
     # inspect the whole file, check how nested
     model.inspect_file()




.. code-block:: none

   ── Models.Core.Simulations: .Simulations
        ├── Models.Storage.DataStore: .Simulations.DataStore
        ├── Models.Core.Folder: .Simulations.Grouping
        │   └── Models.Core.Simulation: .Simulations.Grouping.Seasonal
        │       ├── Models.Manager: .Simulations.Grouping.Seasonal.ClimateController
        │       ├── Models.Clock: .Simulations.Grouping.Seasonal.Clock
        │       ├── Models.Core.Zone: .Simulations.Grouping.Seasonal.Field
        │       │   ├── Models.Manager: .Simulations.Grouping.Seasonal.Field.AutomaticIrrigation
        │       │   ├── Models.Fertiliser: .Simulations.Grouping.Seasonal.Field.Fertiliser
        │       │   ├── Models.Irrigation: .Simulations.Grouping.Seasonal.Field.Irrigation
        │       │   ├── Models.Operations: .Simulations.Grouping.Seasonal.Field.IrrigationSchedule
        │       │   ├── Models.Report: .Simulations.Grouping.Seasonal.Field.SeasonalByYear
        │       │   ├── Models.Report: .Simulations.Grouping.Seasonal.Field.SeasonalByYearWithOnKeyword
        │       │   ├── Models.Report: .Simulations.Grouping.Seasonal.Field.SeasonalOverall
        │       │   ├── Models.Soils.Soil: .Simulations.Grouping.Seasonal.Field.Soil
        │       │   │   ├── Models.Soils.Chemical: .Simulations.Grouping.Seasonal.Field.Soil.Chemical
        │       │   │   ├── Models.Soils.Solute: .Simulations.Grouping.Seasonal.Field.Soil.NH4
        │       │   │   ├── Models.Soils.Solute: .Simulations.Grouping.Seasonal.Field.Soil.NO3
        │       │   │   ├── Models.Soils.Organic: .Simulations.Grouping.Seasonal.Field.Soil.Organic
        │       │   │   ├── Models.Soils.Physical: .Simulations.Grouping.Seasonal.Field.Soil.Physical
        │       │   │   │   ├── Models.Soils.SoilCrop: .Simulations.Grouping.Seasonal.Field.Soil.Physical.AGPRyegrassSoil
        │       │   │   │   └── Models.Soils.SoilCrop: .Simulations.Grouping.Seasonal.Field.Soil.Physical.AGPWhiteCloverSoil
        │       │   │   ├── Models.Soils.Solute: .Simulations.Grouping.Seasonal.Field.Soil.Urea
        │       │   │   └── Models.Soils.Water: .Simulations.Grouping.Seasonal.Field.Soil.Water
        │       │   └── Models.Surface.SurfaceOrganicMatter: .Simulations.Grouping.Seasonal.Field.SurfaceOrganicMatter
        │       ├── Models.MicroClimate: .Simulations.Grouping.Seasonal.MicroClimate
        │       ├── Models.Soils.Arbitrator.SoilArbitrator: .Simulations.Grouping.Seasonal.SoilArbitrator
        │       ├── Models.Summary: .Simulations.Grouping.Seasonal.Summary
        │       └── Models.Climate.Weather: .Simulations.Grouping.Seasonal.Weather
        ├── Models.Core.Folder: .Simulations.More Reporting Examples
        │   ├── Models.Core.Folder: .Simulations.More Reporting Examples.Annual Crop Example
        │   │   ├── Models.Core.Folder: .Simulations.More Reporting Examples.Annual Crop Example.Comparing Rainfall during the Crop and All Year
        │   │   │   └── Models.Graph: .Simulations.More Reporting Examples.Annual Crop Example.Comparing Rainfall during the Crop and All Year.Rainfall during Crop and All Year
        │   │   │       ├── Models.Series: .Simulations.More Reporting Examples.Annual Crop Example.Comparing Rainfall during the Crop and All Year.Rainfall during Crop and All Year.Rainfall all year
        │   │   │       └── Models.Series: .Simulations.More Reporting Examples.Annual Crop Example.Comparing Rainfall during the Crop and All Year.Rainfall during Crop and All Year.Rainfall from sowing to harvest
        │   │   ├── Models.Core.Simulation: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample
        │   │   │   ├── Models.Clock: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Clock
        │   │   │   ├── Models.Core.Zone: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field
        │   │   │   │   ├── Models.Manager: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Fertilise at sowing
        │   │   │   │   ├── Models.Fertiliser: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Fertiliser
        │   │   │   │   ├── Models.Manager: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Harvest
        │   │   │   │   ├── Models.Irrigation: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Irrigation
        │   │   │   │   ├── Models.MicroClimate: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.MicroClimate
        │   │   │   │   ├── Models.Report: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.ReportGrainDaily
        │   │   │   │   ├── Models.Report: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.ReportGrainOnHarvesting
        │   │   │   │   ├── Models.Manager: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.ReportHelper
        │   │   │   │   ├── Models.Report: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.ReportInCropAnnually
        │   │   │   │   ├── Models.Report: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.ReportSpecificDates
        │   │   │   │   ├── Models.Soils.Soil: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Soil
        │   │   │   │   │   ├── Models.Soils.Chemical: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Soil.Chemical
        │   │   │   │   │   ├── Models.Soils.Solute: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Soil.NH4
        │   │   │   │   │   ├── Models.Soils.Solute: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Soil.NO3
        │   │   │   │   │   ├── Models.Soils.Organic: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Soil.Organic
        │   │   │   │   │   ├── Models.Soils.Physical: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Soil.Physical
        │   │   │   │   │   │   └── Models.Soils.SoilCrop: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Soil.Physical.WheatSoil
        │   │   │   │   │   ├── Models.Soils.Solute: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Soil.Urea
        │   │   │   │   │   └── Models.Soils.Water: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Soil.Water
        │   │   │   │   ├── Models.Manager: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Sowing
        │   │   │   │   ├── Models.Surface.SurfaceOrganicMatter: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.SurfaceOrganicMatter
        │   │   │   │   └── Models.PMF.Plant: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Wheat
        │   │   │   ├── Models.Soils.Arbitrator.SoilArbitrator: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.SoilArbitrator
        │   │   │   ├── Models.Summary: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.SummaryFile
        │   │   │   └── Models.Climate.Weather: .Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Weather
        │   │   ├── Models.Core.Folder: .Simulations.More Reporting Examples.Annual Crop Example.Reporting Yield and When Things Can Seem to Go Wrong
        │   │   │   └── Models.Graph: .Simulations.More Reporting Examples.Annual Crop Example.Reporting Yield and When Things Can Seem to Go Wrong.Final and Harvested Yield
        │   │   │       ├── Models.Series: .Simulations.More Reporting Examples.Annual Crop Example.Reporting Yield and When Things Can Seem to Go Wrong.Final and Harvested Yield.Final Yield Corrected
        │   │   │       ├── Models.Series: .Simulations.More Reporting Examples.Annual Crop Example.Reporting Yield and When Things Can Seem to Go Wrong.Final and Harvested Yield.Final Yield with Error
        │   │   │       ├── Models.Series: .Simulations.More Reporting Examples.Annual Crop Example.Reporting Yield and When Things Can Seem to Go Wrong.Final and Harvested Yield.Grain Daily Report
        │   │   │       └── Models.Series: .Simulations.More Reporting Examples.Annual Crop Example.Reporting Yield and When Things Can Seem to Go Wrong.Final and Harvested Yield.Harvested Yield
        │   │   └── Models.Core.Folder: .Simulations.More Reporting Examples.Annual Crop Example.Soil Water storage during the Cropping Phase
        │   │       └── Models.Graph: .Simulations.More Reporting Examples.Annual Crop Example.Soil Water storage during the Cropping Phase.Soil water stroage
        │   │           ├── Models.Series: .Simulations.More Reporting Examples.Annual Crop Example.Soil Water storage during the Cropping Phase.Soil water stroage.Full soil profile
        │   │           ├── Models.Series: .Simulations.More Reporting Examples.Annual Crop Example.Soil Water storage during the Cropping Phase.Soil water stroage.Top three layers all crop
        │   │           ├── Models.Series: .Simulations.More Reporting Examples.Annual Crop Example.Soil Water storage during the Cropping Phase.Soil water stroage.Top three layers reproductive
        │   │           └── Models.Series: .Simulations.More Reporting Examples.Annual Crop Example.Soil Water storage during the Cropping Phase.Soil water stroage.Top three layers vegetative
        │   └── Models.Core.Folder: .Simulations.More Reporting Examples.Perennial Crop Example
        │       ├── Models.Core.Simulation: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June
        │       │   ├── Models.Clock: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Clock
        │       │   ├── Models.Core.Zone: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field
        │       │   │   ├── Models.Report: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.AnnualReporting
        │       │   │   ├── Models.Manager: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.AutomaticFertiliser
        │       │   │   ├── Models.Manager: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.AutomaticIrrigation
        │       │   │   ├── Models.Manager: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.CutRotation
        │       │   │   ├── Models.Report: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.DailyReporting
        │       │   │   ├── Models.Manager: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.FertiliseOnFixedDates
        │       │   │   ├── Models.Fertiliser: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.Fertiliser
        │       │   │   ├── Models.Irrigation: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.Irrigation
        │       │   │   ├── Models.MicroClimate: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.MicroClimate
        │       │   │   ├── Models.Report: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.MonthlyReporting
        │       │   │   ├── Models.Manager: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.ReportHelper
        │       │   │   ├── Models.Soils.Soil: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.Soil
        │       │   │   │   ├── Models.Soils.Chemical: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.Soil.Chemical
        │       │   │   │   ├── Models.Soils.Solute: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.Soil.NH4
        │       │   │   │   ├── Models.Soils.Solute: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.Soil.NO3
        │       │   │   │   ├── Models.Soils.Organic: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.Soil.Organic
        │       │   │   │   ├── Models.Soils.Physical: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.Soil.Physical
        │       │   │   │   │   ├── Models.Soils.SoilCrop: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.Soil.Physical.AGPRyegrassSoil
        │       │   │   │   │   └── Models.Soils.SoilCrop: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.Soil.Physical.AGPWhiteCloverSoil
        │       │   │   │   ├── Models.Soils.Solute: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.Soil.Urea
        │       │   │   │   └── Models.Soils.Water: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.Soil.Water
        │       │   │   └── Models.Surface.SurfaceOrganicMatter: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.SurfaceOrganicMatter
        │       │   ├── Models.Soils.Arbitrator.SoilArbitrator: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.SoilArbitrator
        │       │   ├── Models.Summary: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Summary
        │       │   └── Models.Climate.Weather: .Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Weather
        │       ├── Models.Core.Folder: .Simulations.More Reporting Examples.Perennial Crop Example.Daily and Monthly Leaching
        │       │   └── Models.Graph: .Simulations.More Reporting Examples.Perennial Crop Example.Daily and Monthly Leaching.Daily and Monthly Leaching
        │       │       ├── Models.Series: .Simulations.More Reporting Examples.Perennial Crop Example.Daily and Monthly Leaching.Daily and Monthly Leaching.Cumulative Annual Leaching
        │       │       ├── Models.Series: .Simulations.More Reporting Examples.Perennial Crop Example.Daily and Monthly Leaching.Daily and Monthly Leaching.DailyLeaching
        │       │       └── Models.Series: .Simulations.More Reporting Examples.Perennial Crop Example.Daily and Monthly Leaching.Daily and Monthly Leaching.MonthlyLeaching
        │       ├── Models.Core.Folder: .Simulations.More Reporting Examples.Perennial Crop Example.Getting Annual Patterns of Herbage Accumulation
        │       │   └── Models.Graph: .Simulations.More Reporting Examples.Perennial Crop Example.Getting Annual Patterns of Herbage Accumulation.Annual Accumulation of Pasture Growth Reported in June
        │       │       ├── Models.Series: .Simulations.More Reporting Examples.Perennial Crop Example.Getting Annual Patterns of Herbage Accumulation.Annual Accumulation of Pasture Growth Reported in June.ReportedAnnually
        │       │       └── Models.Series: .Simulations.More Reporting Examples.Perennial Crop Example.Getting Annual Patterns of Herbage Accumulation.Annual Accumulation of Pasture Growth Reported in June.ReportedMonthly
        │       └── Models.Core.Folder: .Simulations.More Reporting Examples.Perennial Crop Example.Working with Soil Carbon
        │           └── Models.Graph: .Simulations.More Reporting Examples.Perennial Crop Example.Working with Soil Carbon.Change In Soil Carbon
        │               ├── Models.Series: .Simulations.More Reporting Examples.Perennial Crop Example.Working with Soil Carbon.Change In Soil Carbon.AnnualChangeInTotalC
        │               ├── Models.Series: .Simulations.More Reporting Examples.Perennial Crop Example.Working with Soil Carbon.Change In Soil Carbon.CumulativeChangeInTotalC
        │               └── Models.Series: .Simulations.More Reporting Examples.Perennial Crop Example.Working with Soil Carbon.Change In Soil Carbon.TotalC_tonnes
        ├── Models.Core.Folder: .Simulations.Reporting at Intervals Beyond Every Day
        │   ├── Models.Graph: .Simulations.Reporting at Intervals Beyond Every Day.Maximum Temperatures with Varying Aggregation
        │   │   ├── Models.Series: .Simulations.Reporting at Intervals Beyond Every Day.Maximum Temperatures with Varying Aggregation.Daily MaxT
        │   │   ├── Models.Series: .Simulations.Reporting at Intervals Beyond Every Day.Maximum Temperatures with Varying Aggregation.Monthly Maximum MaxT
        │   │   ├── Models.Series: .Simulations.Reporting at Intervals Beyond Every Day.Maximum Temperatures with Varying Aggregation.Weekly Maximum MaxT
        │   │   └── Models.Series: .Simulations.Reporting at Intervals Beyond Every Day.Maximum Temperatures with Varying Aggregation.Yearly Maximum MaxT
        │   └── Models.Graph: .Simulations.Reporting at Intervals Beyond Every Day.Minimum Temperatures with Varying Aggregation
        │       ├── Models.Series: .Simulations.Reporting at Intervals Beyond Every Day.Minimum Temperatures with Varying Aggregation.Daily MaxT
        │       ├── Models.Series: .Simulations.Reporting at Intervals Beyond Every Day.Minimum Temperatures with Varying Aggregation.Monthly Minimum MaxT
        │       ├── Models.Series: .Simulations.Reporting at Intervals Beyond Every Day.Minimum Temperatures with Varying Aggregation.Weekly Minimum MaxT
        │       └── Models.Series: .Simulations.Reporting at Intervals Beyond Every Day.Minimum Temperatures with Varying Aggregation.Yearly Minimum MaxT
        └── Models.Core.Simulation: .Simulations.SimpleReportingSim
            ├── Models.Clock: .Simulations.SimpleReportingSim.Clock
            ├── Models.Core.Zone: .Simulations.SimpleReportingSim.Field
            │   ├── Models.Manager: .Simulations.SimpleReportingSim.Field.AutoIrrig
            │   ├── Models.Manager: .Simulations.SimpleReportingSim.Field.Fertilise at sowing
            │   ├── Models.Fertiliser: .Simulations.SimpleReportingSim.Field.Fertiliser
            │   ├── Models.Manager: .Simulations.SimpleReportingSim.Field.Harvest
            │   ├── Models.Irrigation: .Simulations.SimpleReportingSim.Field.Irrigation
            │   ├── Models.MicroClimate: .Simulations.SimpleReportingSim.Field.MicroClimate
            │   ├── Models.Report: .Simulations.SimpleReportingSim.Field.ReportArrays
            │   ├── Models.Report: .Simulations.SimpleReportingSim.Field.ReportDaily
            │   ├── Models.Manager: .Simulations.SimpleReportingSim.Field.ReportHelper
            │   ├── Models.Report: .Simulations.SimpleReportingSim.Field.ReportMonthly
            │   ├── Models.Report: .Simulations.SimpleReportingSim.Field.ReportOnEvents
            │   ├── Models.Report: .Simulations.SimpleReportingSim.Field.ReportOnSpecificDates
            │   ├── Models.Report: .Simulations.SimpleReportingSim.Field.ReportOnSpecificDaysEveryYear
            │   ├── Models.Report: .Simulations.SimpleReportingSim.Field.ReportSimple
            │   ├── Models.Report: .Simulations.SimpleReportingSim.Field.ReportSimulation
            │   ├── Models.Report: .Simulations.SimpleReportingSim.Field.ReportWeekly
            │   ├── Models.Report: .Simulations.SimpleReportingSim.Field.ReportYearly
            │   ├── Models.Soils.Soil: .Simulations.SimpleReportingSim.Field.Soil
            │   │   ├── Models.Soils.Chemical: .Simulations.SimpleReportingSim.Field.Soil.Chemical
            │   │   ├── Models.Soils.Solute: .Simulations.SimpleReportingSim.Field.Soil.NH4
            │   │   ├── Models.Soils.Solute: .Simulations.SimpleReportingSim.Field.Soil.NO3
            │   │   ├── Models.Soils.Organic: .Simulations.SimpleReportingSim.Field.Soil.Organic
            │   │   ├── Models.Soils.Physical: .Simulations.SimpleReportingSim.Field.Soil.Physical
            │   │   │   └── Models.Soils.SoilCrop: .Simulations.SimpleReportingSim.Field.Soil.Physical.WheatSoil
            │   │   ├── Models.Soils.Solute: .Simulations.SimpleReportingSim.Field.Soil.Urea
            │   │   └── Models.Soils.Water: .Simulations.SimpleReportingSim.Field.Soil.Water
            │   ├── Models.Manager: .Simulations.SimpleReportingSim.Field.Sowing
            │   ├── Models.Surface.SurfaceOrganicMatter: .Simulations.SimpleReportingSim.Field.SurfaceOrganicMatter
            │   └── Models.PMF.Plant: .Simulations.SimpleReportingSim.Field.Wheat
            ├── Models.Soils.Arbitrator.SoilArbitrator: .Simulations.SimpleReportingSim.SoilArbitrator
            ├── Models.Summary: .Simulations.SimpleReportingSim.SummaryFile
            └── Models.Climate.Weather: .Simulations.SimpleReportingSim.Weather

In the next tutorial, I will teach you how to use exclusion and specification strategies to target and edit such nested models.

.. seealso::

  :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_file` in the :ref:`API Reference <api_ref>`

.. Warning::

    Only a few key model types are inspected using :meth:`~apsimNGpy.core.apsim.ApsimModel.inspect_model` under the hood. Inspecting the entire simulation file can produce a large volume of data, much of which may not be relevant or necessary in most use cases.

    If certain models do not appear in the inspection output, this is intentional. The tool selectively inspects components to keep results concise and focused.

    For a complete view of the entire model structure, we recommend opening the simulation file in the APSIM GUI using :meth:`apsimNGpy.core.apsim.ApsimModel.preview_simulation`.
Please see the next tutorial

.. seealso::

   - :ref:`API Reference <api_ref>`
   - :ref:`inspect_params`

