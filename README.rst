

apsimNGpy: The Next Generation Agroecosytem Simulation Library
====================================================================

Our cutting-edge open-source framework, apsimNGpy, empowers advanced agroecosystem modeling through the utilization
of object-oriented principles. It features fast batch file simulation, model prediction, evaluation,
apsimx file editing, seamless weather data retrieval, and efficient soil profile development


.. _Requirements

Requirements
***********************************************************************************
1. Dotnet, install from https://learn.microsoft.com/en-us/dotnet/core/install/
2. Python3
3. APSIM: Add the directory containing the models executable to the system's PATH or python path
(to locate the required .dll files). This can be achieved in either of the following ways:
    a. Utilize the APSIM installer provided for this purpose.
    b. Build APSIM from its source code. This is comming soon
4. Minimum; 8GM RAM, CPU Core i7


.. _Installation:

Installation
********************************************************************************

All versions are currently in development, phase and they can be installed as follows:

Method 1. clone the repositry

.. code:: bash

    git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git
    cd apsimNGpy
    pip install .

Method 2. Use pip straight away

.. code:: bash

     pip install git+https://github.com/MAGALA-RICHARD/apsimNGpy.git

If you have apsim installed and the program refuses to load run the following code a the top of your python script
before importing any apsimNGpy class. The classes are  CamelCased.

Required depependencies:
*****************************

 numpy
 pandas
 pythonnet
 xmltodict
 tqdm
 
 Note that apsimNGpy is tested on python3. We are not aware of its performance in python2 becuase it utilizes one of the new libraries like pathlib and f string.



Debugging import error due to improper SYSTEM APSIM path configuration
*********************************************************************************
.. code:: python

    # search for the program binary installation path and add to os.environ as follows
    import os
    os.environ['APSIM'] =r'path/toyourapsimbinaryfolder/bin
    # try importing SoilModel class
    from apsimNGpy.model.soilmodel import SoilModel
    # alternatively, you can add the path to the system environmental variables

.. _Usage:

Usage
*********************************************************************************
.. code:: python

    import apsimNGpy
    from apsimNGpy.base_data import load_example_files
    from apsimNGpy.model.soilmodel import SoilModel
    from pathlib import Path
    import os
    from apsimNGpy.validation import plot_data
    cwd = Path.cwd().home() # sending this to your home folder
    wd = cwd.joinpath("apsimNGpy_demo")
    if not wd.exists():
      os.mkdir(wd)
    # change directory
    os.chdir(wd)
    # Create the data
    data = load_example_files(wd)
    # Get maize model
    maize = data.get_maize()

    # Initialize the simulation methods
    apsim = SoilModel(maize, copy=True)

    # Run the file
    apsim.run_edited_file()
    # print the results
    print(apsim.results)
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
    from apsimNGpy.base_data import load_example_files
    from apsimNGpy.model.soilmodel import SoilModel
    from pathlib import Path
    import os
    from apsimNGpy.validation import plot_data
    cwd = Path.cwd().home() # sending this to your home folder
    wd = cwd.joinpath("apsimNGpy_demo")
    if not wd.exists():
      os.mkdir(wd)
    # change directory
    os.chdir(wd)
    # Create the data
    data = load_example_files(wd)

    # Get maize model
    maize = data.get_maize()

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

    from apsimNGpy.weather import daymet_bylocation_nocsv
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

Future work
*********************************************************************************
Document the optimization algarithm in the package

Add global weather dowwload

Add global soil download

Document the classes and methods in the package

Document the spatial emulator

Document the soil download and editing process

Demonstrate custom function development

document parallel processing

Add running batch files on apsinNG  server







