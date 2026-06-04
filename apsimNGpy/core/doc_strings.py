# docs/edit_model_docs.py

COMMON_DOC = """
Modify APSIM model components by model type and name.

Editing may target:

- All simulations
- One simulation
- Multiple simulations
- All simulations except those listed in ``exclude``

.. tip::

   APSIM models do not need to be located in a
   ``Replacements`` folder to be edited.

   Cultivar editing is a special case because APSIM
   treats cultivars as read-only objects. apsimNGpy
   automatically creates and attaches derived cultivars.
"""


PARAMETERS_DOC = """
Parameters
----------
model_type : str
    APSIM model type.

model_name : str
    Name of the APSIM model instance.

simulations : str | list[str], optional
    Simulation(s) to edit. Defaults to all simulations.

exclude : str | Iterable[str], optional
    Simulation(s) that should be skipped.

verbose : bool, default=False
    Display editing status information.

clear_old : bool, default=False
    For Morris, Report and Sobol models, remove existing parameter
    definitions before applying new ones.

**kwargs
    Model-specific arguments.
"""


WEATHER_DOC = """
Weather Models
--------------
Supported model types:

- Weather
- Models.Climate.Weather

Examples
--------
.. code-block:: python

    from apsimNGpy import ApsimModel
    model = ApsimModel('Maize')
    model.edit_model(
        model_type="Weather",
        model_name="Weather",
        weather_file="new_weather.met"
    )
"""


CLOCK_DOC = """
Clock Models
------------
Examples
--------
Parameters supported
---------------------
- Name
- End
- Start

.. code-block:: python

    model.edit_model(
        model_type="Clock",
        model_name="Clock",
        Start="2021-01-01",
        End="2021-12-31"
    )
"""


MANAGER_DOC = """
Manager Models
--------------
Examples
--------
Parameters are script specific using inspect model paramters to get them fully as shown::

  params = model.inspect_model_parameters('Models.Manager', 'Sow using a variable rule')['Parameters']
      {'Crop': 'Maize',
     'StartDate': '1-nov',
     'EndDate': '10-jan',
     'MinESW': '100.0',
     'MinRain': '25.0',
     'RainDays': '7',
     'CultivarName': 'Dekalb_XL82',
     'SowingDepth': '30.0',
     'RowSpacing': '750.0',
     'Population': '6.0'}
  
We could edit/change values for any of the above as follows:

.. code-block:: python

    model.edit_model(
        model_type="Manager",
        model_name="Sow using a variable rule",
        population=8.4
        
    )
"""


SOIL_DOC = """
Soil Models
-----------
Supported:

- Physical
- Organic
- Chemical
- Water
- Solute
- WaterBalance

For layered parameters, values are assigned by layer index.

- If `index` is provided, values are applied to the specified layers.
- If `index` is omitted, layer indices are inferred from the position of each value in the supplied sequence.
- If a scalar value is supplied, only the top layer (layer 0) is modified.
- Layered data must be provided as an ordered sequence (e.g., `list`, `tuple`, `numpy.ndarray`, or `pandas.Series`).
- `set` objects are not permitted because APSIM layer assignments depend on positional ordering.

Examples
--------
.. code-block:: python

    model.edit_model(
        model_type="Organic",
        model_name="Organic",
        Carbon=1.23
    )
    # layered properties
    model.edit_model(
        model_type="Organic",
        model_name="Organic",
        Carbon=[1.23, 1.0]
    )
    # edit water balance model
    model.edit_model(WaterBalance, 
         model_name='SoilWater',
          SWCON=[3, 3, 5, 50, 60], )
"""


REPORT_DOC = """
Report Models
-------------
By default, new variables are appended to the existing variable list. To replace all existing variables with the supplied ones, set `clear_old=True`.

Examples
--------
.. code-block::python

    model.edit_model(
        model_type="Report",
        model_name="Report",
        variable_spec=
            "[Maize].AboveGround.Wt as abw"
    )
    
    model.edit_model(
        model_type="Report",
        model_name="Report",
        clear_old=True,
        variable_spec=[
            "[Maize].AboveGround.Wt as abw",
            "[Maize].Grain.Total.Wt as grain"
        ]
    )
"""


SURFACE_OM_DOC = """
Surface Organic Matter
----------------------
key parameters
---------------
- Name
- InitialCNR
- InitialResidueMass
- InitialResidueName
- InitialResidueType
- InitialCPR
- InitialStandingFraction

Examples
--------------------------
.. code-block:: python

    model.edit_model(
        model_type="SurfaceOrganicMatter",
        model_name="SurfaceOrganicMatter",
        InitialResidueMass=2500
    )
    
    model.edit_model(
        model_type="SurfaceOrganicMatter",
        model_name="SurfaceOrganicMatter",
        InitialCNR=85
    )
"""


CULTIVAR_DOC = r"""
Cultivar Models
---------------
Cultivars are read-only APSIM objects.

apsimNGpy edits cultivars by creating a derived
cultivar and attaching it through a sowing manager.

Recommended usage
^^^^^^^^^^^^^^^^^

.. code-block:: python

    params = {
        "[Leaf].Photosynthesis.RUE.FixedValue": 1.89,
        "[Phenology].GrainFilling.Target.FixedValue": 710,
        "[Grain].MaximumGrainsPerCob.FixedValue": 810,
    }

    model.edit_model(
        model_type="Cultivar",
        model_name="Dekalb_XL82",
        plant="Maize",
        commands=params,
        managers: {"Sow using a variable rule":"CultivarName"},
    )

Supported command formats
^^^^^^^^^^^^^^^^^^^^^^^^^

Dictionary:

.. code-block:: python

    commands = {
        "[Phenology].Juvenile.Target.FixedValue": 256
    }

Iterable:

.. code-block:: python

    commands = [
        "[Phenology].Juvenile.Target.FixedValue=256"
    ]
"""


SENSITIVITY_DOC = """
Sensitivity Models
------------------
Supported:

- Models.Sobol
- Models.Morris

Examples
--------

with ApsimModel("Morris") as model:

    model.edit_model(
        model_type="Models.Morris",
        model_name="FallowSensitivity",
        clear_old= False
        Parameters=[
            dict(
                Name="Residue",
                Path="Field.SurfaceOrganicMatter.InitialResidueMass",
                LowerBound=10,
                UpperBound=400
            )
        ],
        NumPaths=200
    )

    model.run()

    stats = model.get_simulated_output(
        "SobolStatistics"
    )
    raw_results=  model.results
"""


ERRORS_DOC = """
Raises
------
ValueError
    If the model cannot be found or required
    arguments are missing.

AttributeError
    If an invalid model attribute is supplied.

NotImplementedError
    If editing logic for a model type has not
    been implemented.
"""


SEEALSO_DOC = """
See Also
--------
:meth:`apsimNGpy.core.apsim.ApsimModel.edit_model_by_path`
"""


EDIT_MODEL_DOC = "\n\n".join(
    [
        COMMON_DOC,
        PARAMETERS_DOC,
        WEATHER_DOC,
        CLOCK_DOC,
        MANAGER_DOC,
        SOIL_DOC,
        REPORT_DOC,
        SURFACE_OM_DOC,
        CULTIVAR_DOC,
        SENSITIVITY_DOC,
        ERRORS_DOC,
        SEEALSO_DOC,
    ]
)