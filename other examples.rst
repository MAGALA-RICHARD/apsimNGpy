Change APSIM simulation dates 
*********************************************************************************
.. code-block:: python

    import apsimNGpy
    from apsimNGpy.core.base_data import load_default_simulations
    from apsimNGpy.core.apsim  import ApsimModel as SoilModel
    from pathlib import Path
    import os
    from apsimNGpy.validation.visual import plot_data
    cwd = Path.cwd().home() # sending this to your home folder
    wd = cwd.joinpath("apsimNGpy_demo")
    if not wd.exists():
      os.mkdir(wd)
    # change directory
    os.chdir(wd)
    # Get maize model
    maize_model = load_default_simulations(crop = 'maize')
    # aother 
    from apsimNGpy.core.core import CoreModel
    maize_model = CoreModel(model = 'Maize.apsimx') # here replace with your path or contine editing the default model

Populating the APSIM model with new weather data
*********************************************************************************
.. code-block:: python

    from apsimNGpy.core.weather import daymet_bylocation_nocsv
    lonlat = -93.08, 42.014
    start_year, end_year = 2000, 2002
    wf = daymet_bylocation_nocsv(lonlat, startyear, endyear, filename="mymet.met")
    # you may need to first see what file currently exists in the model
    mis = apsim.show_met_file_in_simulation()
    print(mis)
    # change
    maize_model.replace_met_file(weather_file=wf)
    # check again if you want to
    mis = maize_model.show_met_file_in_simulation()
    print(mis)

Evaluate Predicted Variables
*********************************************************************************
The apsimNGpy Python package provides a convenient way to validate model simulations against measured data. Below 
is a step-by-step guide on how to use the validation.evaluator module from apsimNGpy.

.. code-block:: python

    # Start by importing the required libraries
    from apsimNGpy.validation.evaluator import validate
    import pandas as pd

    # Load the data if external. Replace with your own data
    df = pd.read_csv('evaluation.csv')
    apsim_results = apsim.results  # Assuming 'apsim' is a predefined object from aopsimNGpy.core.core.APSIMN class and contains your simualted results

    # Preparing Data for Validation
    # Extract the relevant columns from your DataFrame for comparison. In this example, we use
    # 'Measured' for observed values and compare them with different model outputs:
    measured = df['Measured']
    predicted = apsim_results['MaizeR'].Yield

    # Now we need to pass both the measured and the observed in the validate class
    val = validate(measured, predicted)

    # Both variables should be the same length, and here we are assuming that they are sorted in the corresponding order

    # There are two options:
    # 1. Evaluate all
    metrics = val.evaluate_all(verbose=True)
    # Setting verbose=True prints all the results on the go; otherwise, a dictionary is returned with the value for each metric

    # 2. Select or pass your desired metric
    RMSE = val.evaluate("RMSE")
    print(RMSE)

    # If you want to see the available metrics, use the code below
    available_metrics = metrics.keys()
    print(available_metrics)
    # Then select your choice from the list

Run factorial experiments faster and efficiently
*********************************************************************************

The apsimNGpy Python package provides a convenient way to run factorial experiments as follows:

.. code-block:: python

    from apsimNGpy.core import base_data
    apsim = base_data.load_default_simulations(crop='Maize')
    apsim.create_experiment(permutation=True)
    apsim.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20", factor_name='Nitrogen')
    # Use categories
    apsim.add_factor(specification="[Sow using a variable rule].Script.Population = 4, 6, 8, 10", factor_name='Population')
    apsim.run()

It is possible to specify factors related to crop cultivars; all you need is to add a replacement folder and add the crop as a replacement as follows:

.. code-block:: python

    apsim.add_crop_replacements(_crop='Maize')  # Assumes that maize is already present in the simulation
    # Add factor and name it RUE
    apsim.add_factor(specification='[Maize].Leaf.Photosynthesis.RUE.FixedValue = 1.0, 1.23, 4.3', factor_name='RUE')
    apsim.run() # assumes that the database table Name is the default of the Report
    # results can be retrieved in the same way
    df = apsim.results
    
Example output:

.. code-block:: text

    SimulationName  SimulationID  ...     Yield   Zone
    0     ExperimentNitrogen0Population10RUE1.0             8  ...  1379.137  Field
    1     ExperimentNitrogen0Population10RUE1.0             8  ...  1084.340  Field
    2     ExperimentNitrogen0Population10RUE1.0             8  ...     0.000  Field
    3     ExperimentNitrogen0Population10RUE1.0             8  ...   797.680  Field
    4     ExperimentNitrogen0Population10RUE1.0             8  ...  3682.210  Field
                                         ...           ...  ...       ...    ...
    1645  ExperimentNitrogen80Population7RUE4.3           148  ...  4538.774  Field
    1646  ExperimentNitrogen80Population7RUE4.3           148  ...  7549.985  Field
    1647  ExperimentNitrogen80Population7RUE4.3           148  ...  4535.009  Field
    1648  ExperimentNitrogen80Population7RUE4.3           148  ...  8798.415  Field
    1649  ExperimentNitrogen80Population7RUE4.3           148  ...  3236.126  Field
    [1650 rows x 20 columns]
