

apsimNGpy: The next generation agroecosytem simulation library
====================================================================

Our cutting-edge open-source framework, apsimNGpy, empowers advanced agroecosystem modeling through the utilization of object-oriented principles. It features fast batch file simulation, model prediction, evaluation, 
apsimx file editing, seamless weather data retrieval, and efficient soil profile development


.. _Installation:

Installation
********************************************************************************
you may need a dotnet installation if not installed run the code https://dotnet.microsoft.com/en-us/download/dotnet/6.0

First, make sure you have a Python 3 environment installed. Install APSIM and ensure that the directory containing the Models executable is added to the system's PATH or the Python path (to locate the required .dll files). This can be achieved in either of the following ways:

a. Utilize the APSIM installer provided for this purpose.

b. Build APSIM from its source code. This is comming soon


For the current developer versions:

Method 1
.. code:: bash

    git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git
    cd apsimNGpy
    pip install .

Method 2
.. code:: bash
     pip install git+https://github.com/MAGALA-RICHARD/apsimNGpy.git

if you have apsim installed and the program refuses to load run the following code a the top of your python script before importing any apsimNGpy class


Debuging import error due to improper SYSTEM APSIM path configuration
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

Change simulation dates 
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

Change simulation management 
*********************************************************************************
.. code:: python
    # first, examine the manager scripts in the simulation node
    apsim.examine_management_info()
    # now create disctioanry holding the parameters. the key to this is that the name of the script manage rmust be passed in the disctionary
    # in this node we have a script named the Simple Rotation,we want to change the rotation to may Maize, Wheat or something else
    rotation  = {'Name': "Simple Rotation", "Crops": 'Maize, Wheat, Soybean' # the crops must be seperated my commas
    apsim.update_multiple_management_decissions([rotation], simulations=apsim.extract_simulation_name, reload=True)
    # now you cans see we passed rotation as a list. That means you can add other scripts as uch as you can to be changed at thesame time



