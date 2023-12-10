apsimNGpy: The Next Generation Agroecosytem Simulation Library
====================================================================

Our cutting-edge open-source framework, apsimNGpy, empowers advanced agroecosystem modeling through the utilization
of object-oriented principles. It features fast batch file simulation, model prediction, evaluation,
apsimx file editing, seamless weather data retrieval, and efficient soil profile development

Requirements
***********************************************************************************
1. Dotnet, install from https://learn.microsoft.com/en-us/dotnet/core/install/
2. Python3
3. APSIM: Add the directory containing the models executable to the system's PATH or python path (to locate the required .dll files). This can be achieved in either of the following ways:
4. Utilize the APSIM installer provided for this purpose.
5. Build APSIM from its source code. This is comming soon
6. Minimum; 8GM RAM, CPU Core i7

.. _Installation:

Installation
********************************************************************************

All versions are currently in development, phase and they can be installed as follows:

- Method 1. install from PyPI

.. code:: bash

    pip install apsimNGpy

- Method 1. clone the current development repositry    

.. code:: bash

    git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git@dev
    cd apsimNGpy
    pip install .

- Method 2. Use pip straight away and install from github

.. code:: bash

     pip install git+https://github.com/MAGALA-RICHARD/apsimNGpy.git@dev


Debugging import error due to improper SYSTEM APSIM path configuration
*********************************************************************************

If you have apsim installed and the program refuses to load run the following code at the top of your python script
before importing any apsimNGpy class, especially class from ApsimNGpy.core modules The classes are  CamelCased.

.. code:: python

    # search for the program binary installation path and add to os.environ as follows
    import os
    os.environ['APSIM'] =r'path/toyourapsimbinaryfolder/bin
    # try importing SoilModel class
    from apsimNGpy.core.apsim import ApsimModel
    # alternatively, you can add the path to the system environmental variables

.. _Usage:

The above code is also applicable for running different versions of APSIM models. Please note that if your APSIM installation hasn't been added to the system path, this script line should always be placed at the beginning of your simulation script.

Required Dependencies:
*****************************

- numpy
- pandas
- pythonnet
- xmltodict
- tqdm
- requests

Please note that apsimNGpy is tested on Python 3. We are not aware of its performance in Python 2 because it utilizes some of the new libraries like pathlib and f-strings.

Usage
*********************************************************************************
.. code:: python

    import apsimNGpy
    from apsimNGpy.core.base_data import LoadExampleFiles
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
    # Create the data
    data = LoadExampleFiles(wd)
    # Get maize model
    maize = data.get_maize

    # Initialize the simulation methods
    apsim = SoilModel(maize, copy=True)

    # Run the file
    apsim.run() # use run to print time taken to excute or run the model 
    # print the results
    print(apsim.results) # prints all data frames in the storage domain subset usign report names
    # check the manager modules in the apsim simulation file
    # first get the simualtion names
    sim_name = apsim.extract_simulation_name
    apsim.examine_management_info(simulations=sim_name)
    # show current simulation in apsim GUI
    # plot the data
    res = apsim.results['MaizeR']
    plot_data(res.Year, res.Yield, xlabel='Years', ylabel=" Maize Yield (kg/ha)")
    
A graph should be able to appear like the ones below. Note that plot_data function just wraps matplotlib plot function
for quick visualisation

Congratulations you have successfuly used apsimNGpy package
*********************************************************************************
.. image:: ./apsimNGpy/examples/Figure_1.png
   :alt: /examples/Figure_1.png

Change APSIM simulation dates 
*********************************************************************************
.. code:: python

    import apsimNGpy
    from apsimNGpy.core.base_data import LoadExampleFiles
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
    # Create the data
    data = LoadExampleFiles(wd)

    # Get maize model
    maize = data.get_maize

    # Initialize the simulation methods
    apsim = SoilModel(maize, copy=True)
    apsim.change_simulation_dates(start_date='01/01/1998', end_date='12/31/2010')

Change  APSIM model management decisions
*********************************************************************************
.. code:: python

    # First, examine the manager scripts in the simulation node
    apsim.examine_management_info()
    # now create dictionary holding the parameters. the key to this is that the name of the script manage must be
    passed in the dictionary.

    # in this node we have a script named the Simple Rotation,we want to change the rotation to maybe Maize, Wheat or
    something else
    rotation  = {'Name': "Simple Rotation", "Crops": 'Maize, Wheat, Soybean' # the crops must be seperated my commas
    apsim.update_multiple_management_decisions([rotation], simulations=apsim.extract_simulation_name, reload=True)
    # now you cans see we passed rotation as a list. That means you can add other scripts as much as you all  to be
    changed at the same time

Populating the APSIM model with new weather data
*********************************************************************************
.. code:: python

    from apsimNGpy.core.weather import daymet_bylocation_nocsv
    lonlat = -93.08, 42.014
    start_year, end_year = 2000, 2002
    wf = daymet_bylocation_nocsv(lonlat, startyear, endyear, filename="mymet.met")
    # you may need to first see what file currently exists in the model
    mis = apsim.show_met_file_in_simulation()
    print(mis)
    # change
    apsim.replace_met_file(wf)
    # check again if you want to
    mis = apsim.show_met_file_in_simulation()
    print(mis)

Evaluate Predicted Valuables
*********************************************************************************
The apsimNGpy Python package provides a convenient way to validate model simulations against measured data. Below 
is a step-by-step guide on how to use the validation.evaluator module from apsimNGpy.

.. code:: python

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




