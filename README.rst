apsimNGpy: The Next Generation Agroecosytem Simulation Library

====================================================================

Our cutting-edge open-source framework, apsimNGpy, empowers advanced agroecosystem modeling through the utilization
of object-oriented principles. It features fast batch file simulation, model prediction, evaluation,
apsimx file editing, seamless weather data retrieval, and efficient soil profile development

Requirements
***********************************************************************************
1. Dotnet, install from https://learn.microsoft.com/en-us/dotnet/core/install/
2. Python3
3. APSIM Binary from https://apsim.info
6. Minimum; 4GB RAM,

.. _Installation:

Installation

********************************************************************************

All versions are currently in development, phase and they can be installed as follows:
- Step 1:
Register, download and install the Apsim Binary from https://apsim.info Its important to keep track
of the location of installation of APSIM binary files. We shall shall use in step 3.
This location of this folder will depend on the operating System.

In windows it will be located in /

In linux it usually is in /usr/local/lib/apsim/{APSIM VERSION}/bin e.g.
/usr/local/lib/apsim/2024.8.7571.0/bin

We will need this value for later usage before running the APSIM File Successfully.

-STEP 2:

-- Either install from PyPI

.. code:: bash

    pip install apsimNGpy

-- Or clone the current development repository

.. code:: bash

    git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git@dev
    cd apsimNGpy
    pip install .

You could also install using pip directly from github.

.. code:: bash

     pip install git+https://github.com/MAGALA-RICHARD/apsimNGpy.git@dev


- STEP 3:
Set APSIM Binary File Path you stored in step 1

In the file /apsimNGpy/apsimNGpyconfig.ini
 Add the following entry:
.. code:: ini
    [Paths]
    APSIM_LOCATION = /usr/local/lib/apsim/2024.8.7571.0/bin


.. _Usage:

If you installed from pip into a virtual environment;
With the virtual environment you can jump straight to the python shell by running apsim_python_shell in terminal
.. code:: python
    from apsimNGpy.core.base_data import load_default_simulations
    crop_model = load_default_simulations(crop='soybean')
    # default supported crops include, soybean, maize, wheat.
    # initialize the simulation
    model_simulation = SoilModel(crop_model)
    result = model_simulation.simulate()
    print(results)
    print(model_simulation.simulation_names)


Required Dependencies:
*****************************

- numpy
- pandas
- pythonnet
- xmltodict
- tqdm
- requests
-

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
    # Alternatively, you can laod from the factory default modules 
    soybean_model = load_default_simulations(crop = 'soybean') # don't worry it is not case senstive
    #the load_default_simulation returns a prelloaded model ready to run the existing module

    # Initialize the simulation methods
    apsim = SoilModel(maize, copy=True)

    # Run the file
    apsim.run() # use run to print time taken to excute or run the model 
    # print the results
    print(apsim.results) # prints all data frames in the storage domain subset usign report names
    # check the manager modules in the apsim simulation file
    # first get the simualtion names
    sim_name = apsim.simulation_names
    apsim.examine_management_info(simulations=sim_name)
    # show current simulation in apsim GUI
    # plot the data
    res = apsim.results['MaizeR']
    plot_data(res.Year, res.Yield, xlabel='Years', ylabel=" Maize Yield (kg/ha)")
    
A graph should be able to appear like the ones below. Note that plot_data function just wraps matplotlib plot function
for quick visualisation

Congratulations you have successfully used apsimNGpy package
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
    rotation  = {'Name': "Simple Rotation", "Crops": 'Maize, Wheat, Soybean'}, # the crops must be seperated my commas
    apsim.update_mgt(management = rotation, reload=True)
    # now you cans see we passed rotation as aturple. That means you can add other scripts as your needs suggest. They will all be changed at the 
    same time

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
    apsim.replace_met_file(weather_file=wf)
    # check again if you want to
    mis = apsim.show_met_file_in_simulation()
    print(mis)

Evaluate Predicted Variables
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

How to Contribute to apsimNGpy
*********************************************************************************
We welcome contributions from the community, whether they are bug fixes, enhancements, documentation updates, or new features. Here's how you can contribute to ``apsimNGpy``:

Reporting Issues
----------------

If you find a bug or have a suggestion for improving ``apsimNGpy``, please first check the `Issue Tracker <https://github.com/MAGALA-RICHARD/apsimNGpy/issues>`_ to see if it has already been reported. If it hasn't, feel free to submit a new issue. Please provide as much detail as possible, including steps to reproduce the issue, the expected outcome, and the actual outcome.

Contributing Code
-----------------

We accept code contributions via Pull Requests (PRs). Here are the steps to contribute:

Fork the Repository
^^^^^^^^^^^^^^^^^^^

Start by forking the ``apsimNGpy`` repository on GitHub. This creates a copy of the repo under your GitHub account.

Clone Your Fork
^^^^^^^^^^^^^^^

Clone your fork to your local machine:

  .. code-block:: bash

    git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git
    cd apsimNGpy

Create a New Branch
  Create a new branch for your changes:

  .. code-block:: bash

    git checkout -b your-branch-name

Make Your Changes
  Make the necessary changes or additions to the codebase. Please try to adhere to the coding style already in place.

Test Your Changes
  Run any existing tests, and add new ones if necessary, to ensure your changes do not break existing functionality.

Commit Your Changes
  Commit your changes with a clear commit message that explains what you've done:

  .. code-block:: bash

    git commit -m "A brief explanation of your changes"

Push to GitHub
  Push your changes to your fork on GitHub:

  .. code-block:: bash

    git push origin your-branch-name

Submit a Pull Request
  Go to the ``apsimNGpy`` repository on GitHub, and you'll see a prompt to submit a pull request based on your branch. Click on "Compare & pull request" and describe the changes you've made. Finally, submit the pull request.

Updating Documentation
----------------------

Improvements or updates to documentation are greatly appreciated. You can submit changes to documentation with the same process used for code contributions.

Join the Discussion
-------------------

Feel free to join in discussions on issues or pull requests. Your feedback and insights are valuable to the community!

Version 0.0.27.8 new features
********************************************************************************
Dynamic handling of simulations and their properties

replacements made easier

object oriented factorial experiment set ups and simulations

Acknowledgements
*********************************************************************************
This project, *ApsimNGpy*, greatly appreciates the support and contributions from various organizations and initiatives that have made this research possible. We extend our gratitude to Iowa State University's C-CHANGE Presidential Interdisciplinary Research Initiative, which has played a pivotal role in the development of this project. Additionally, our work has been significantly supported by a generous grant from the USDA-NIFA Sustainable Agricultural Systems program (Grant ID: 2020-68012-31824), underscoring the importance of sustainable agricultural practices and innovations.

We would also like to express our sincere thanks to the APSIM Initiative. Their commitment to quality assurance and the structured innovation program for APSIM's modelling software has been invaluable. APSIM's software, which is available for free for research and development use, represents a cornerstone for agricultural modeling and simulation. For further details on APSIM and its capabilities, please visit `www.apsim.info <http://www.apsim.info>`_.

Our project stands on the shoulders of these partnerships and support systems, and we are deeply thankful for their contribution to advancing agricultural research and development. Please not that that this library is designed as a bridge to APSIM software, and we hope that by using this library, you have the appropriate APSIM license to do so whether free or commercial.

Lastly but not least, ApsimNGpy is not created in isolation but draws inspiration from apsimx, an R package (https://cran.r-project.org/web/packages/apsimx/vignettes/apsimx.html). We acknowledge and appreciate the writers and contributors of apsimx for their foundational work. ApsimNGpy is designed to complement apsimx by offering similar functionalities and capabilities in the Python ecosystem.
