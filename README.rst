=========
apsimNGpy
=========

.. image:: https://img.shields.io/badge/License-Apache_2.0-blue.svg
   :target: https://opensource.org/licenses/Apache-2.0
   :alt: License: Apache-2.0

.. image:: https://img.shields.io/badge/docs-online-blue.svg
   :target: https://magala-richard.github.io/apsimNGpy-documentations/index.html
   :alt: Documentation

.. image:: https://img.shields.io/pypi/v/apsimNGpy?logo=pypi
   :target: https://pypi.org/project/apsimNGpy/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/dm/apsimNGpy?logo=pypi
   :target: https://pypi.org/project/apsimNGpy/
   :alt: PyPI downloads

.. image:: https://img.shields.io/github/stars/MAGALA-RICHARD/apsimNGpy?style=social
   :target: https://github.com/MAGALA-RICHARD/apsimNGpy/stargazers
   :alt: GitHub Stars

.. image:: https://img.shields.io/github/forks/MAGALA-RICHARD/apsimNGpy?style=social
   :target: https://github.com/MAGALA-RICHARD/apsimNGpy/network/members
   :alt: GitHub Forks



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

- Method 1. clone the current development repository

.. code:: bash

    git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git
    cd apsimNGpy
    pip install .

- Method 2. Use pip straight away and install from github

.. code:: bash

     pip install git+https://github.com/MAGALA-RICHARD/apsimNGpy.git


Full documentation can be found here; https://magala-richard.github.io/apsimNGpy-documentations/index.html


GETTING STARTED
*****************************

Before using apsimNGpy, it is necessary to install APSIM. Please follow the instructions provided at the following link to complete the installation: https://www.apsim.info/download-apsim/downloads/
for MAcOS or Linux users see: https://apsimnextgeneration.netlify.app/install/
model documentation and tutorial are also available via; https://docs.apsim.info/
we expect that by accepting to use apsimNGpy, you have a basic understanding of APSIM process-based model, therefore, our focus is to make sure you are able to use apsimNGpy

In addition, make sure that the APSIM installation binaries folder is added to the system path.
if you run the following code and returns None you need to do something as explained below.

- 1. Use command line interface

.. code-block:: bash

     apsim_bin_path -s

- 2. Use apsimNGpy config module

.. code-block:: python

   from apsimNGpy.core import config
      print(config.get_apsim_bin_path())

You can also try to check if automatic search will be successful as follows

.. code-block:: bash

    apsim_bin_path --auto_search

The short cut

.. code-block:: bash

    apsim_bin_path -a


Locating the APSIM Binaries
***************************************************************
By default the APSIM binaries are located automatically. The process for determining the APSIM binary path is as follows:

In apsimNGpy, priority is first given to the user-supplied binary path.
If no path is supplied, the module searches through the Python global environment
using the os module. If that fails, it searches through other folders.
If all approaches are exhausted and no valid path is found, a ValueError will be raised.


Changing/setting the APSIM installation binaries path
*********************************************************************************
If the automatic search fails, please follow one of the steps below to resolve the issue:

1. Manually configure the APSIM binary path. To do this:
*************************************************************************************

In your home folder you could look for folder named apsimNGpy_meta_info './APSIMNGpy_meta_data'
     1. Locate the folder named `APSIMNGpy_meta_info` in your home directory (e.g., `./APSIMNGpy_meta_data`).
     2. Open the file `apsimNGpy_config.ini` within this folder.
     3. Modify the `apsim_location` entry to reflect your desired APSIM binary path.

2. change based os.environ module
************************************

Alternatively, you can use the code at the top of your script as follows

.. code-block:: python

    # Search for the APSIM binary installation path and add it to os.environ as follows:
    import os
    os.environ['APSIM'] = r'path/to/your/apsim/binary/folder/bin'

- Note:

This approach may not work consistently in all scenarios, but you can try it.
The above script line should always be placed at the beginning of your simulation script.
However, why follow this approach when you can achieve the same result more efficiently? See the approach below:

3. Use the apsimNGpy config module:
*****************************************************************

.. code-block:: python
    
    from apsimNGpy.config import set_apsim_bin_path

    # Set the path to the APSIM binaries:
    set_apsim_bin_path(path=r'path/to/your/apsim/binary/folder/bin')


4. Use command line interface
*********************************************************************

After installing apsimNGpy, navigate to your terminal and run the following

.. code-block:: bash

    apsim_bin_path -u 'path/to/your/apsim/binary/folder/bin'

Or

.. code-block:: bash

    apsim_bin_path --update 'path/to/your/apsim/binary/folder/bin'


# Now that the path is set, you can import any module attached to pythonnet.
*********************************************************************************************

.. code-block:: python
    
    # For example, try importing the ApsimModel class:
    from apsimNGpy.core.apsim import ApsimModel

.. _Usage:

The above code is also applicable for running different versions of APSIM models.
The `set_apsim_bin_path` function can be called once and retained unless you uninstall `apsimNGpy`
or the APSIM application itself. This implies that you can switch between apsim versions easily if you have more than one versions installed on your computer

Examples
********

This example demonstrates how to use `apsimNGpy` to load a default simulation, run it, retrieve results, and visualize the output.

.. code-block:: python

    # Import necessary modules
    import apsimNGpy
    from apsimNGpy.core.base_data import load_default_simulations
    from apsimNGpy.core.apsim import ApsimModel as SoilModel
    from pathlib import Path
    import os
    from apsimNGpy.validation.visual import plot_data

ApsimModel class inherits all methods and properties from :code:`CoreModel` which can be imported from :code:`ApsimNGpy.core.core`
To use :code:'apsimNGpy:, you dont need to have a simulation file on your computer, we can directly access the default simulations and edit them along. There are two way to access the default simulations.


1. use `load_default_simulations` method

.. code-block:: python

    # Load the default simulation
    soybean_model = load_default_simulations(crop='soybean', simulation_object=True)  # Case-insensitive crop specification

The `load_default_simulations` function loads a default APSIM simulation for the specified crop. In this example, the crop is set to soybean, but you can specify other crops as needed.
The importance of this method is that it is cached, so it faster while editing an exisiting simulation during optimization. Caching here has no issues because the default will be the same everytime we load it.

If you prefer not to initialize the simulation object immediately, you can load only the simulation path by setting  :literal:`simulation_object=False`.

.. code:: python

    # Load the simulation path without initializing the object
    soybean_path_model = load_default_simulations(crop='soybean', simulation_object=False)

Now it is possible to initialize the APSIM model using the previously loaded simulation file path, by using ApsimModel class. Note that it is imported in this environment as SoilModel

.. code-block:: python

    # Initialize the APSIM model with the simulation file path
    apsim = SoilModel(soybean_path_model)

2. Use either ApsimModel Class to load directly the default simulations as follows:

.. code-block:: python

    # this load the default simulation. `Maize.apsimx' can be replaced by any user APSIM file on the computer disk.
    apsim = ApsimModel(model ='Maize.apsimx', out_path = './my_maize_model.apsimx')

# Running loaded models
===============================
Running loaded models implies excuting the model to generate simulated outputs. This is implimented via :code:`ApsimModel.run()` method` as follows


.. code-block:: python

    # Run the simulation
    apsim.run(report_name='Report')

- The ``ApsimModel.run()`` method executes the simulation. The ``report_name`` parameter specifies which data table from the simulation will be used for results. Please note that report_name can be a string (``str``), implying a single database table
or a list, implying that one or more than one database tables. if the later is true, then the results will be concatenated along the rows using ``pandas.concat`` method. By default, ``apsimNGpy`` looks for these report database tables automatically, and returns a concatenated pandas data frame.

.. code-block:: python

    # Retrieve and save the results
    df = apsim.results
    df.to_csv('apsim_df_res.csv')  # Save the results to a CSV file
    print(apsim.results)  # Print all DataFrames in the storage domain

After the simulation runs, results are stored in the `apsim.results` attribute as pandas DataFrames. Please see note above. These results can be saved to a CSV file or printed to the console.

The code below retrieves the names of simulations from the APSIM model and examines the management modules used in the specified simulations.

.. code-block:: python

    # Examine management modules in the simulation
    sim_name = apsim.simulation_names  # Retrieve simulation names
    apsim.examine_management_info(simulations=sim_name)


You can preview the current simulation in the APSIM graphical user interface (GUI) using the `preview_simulation` method.


.. code-block:: python

    # Preview the current simulation in the APSIM GUI
    apsim.preview_simulation()

.. note::
   apsimNGpy clones a every simulation file before passing it it dotnet runner, however, when you open it in GUI, take note of the version it will be difficult to re-open
   it in the lower versions after opening it in the higher versions of apsim

Visualise the results. please note that python provide very many plotting libraries below is just a basic description of your results

.. code-block:: python

    # Visualize the simulation results
    res = apsim.results['MaizeR']  # Replace with the appropriate report name
    plot_data(df['Clock.Today'], df.Yield, xlabel='Date', ylabel='Soybean Yield (kg/ha)')

Finally, the `plot_data` function is used to visualize the simulation results. Replace 'df['Clock.Today']' and `df.Yield` with the appropriate report name and column from your simulation results.

A graph similar to the example below should appear


Congratulations you have successfully used apsimNGpy package
*********************************************************************************
.. image:: ./apsimNGpy/examples/Figure_1.png
   :alt: /examples/Figure_1.png

Documentation
===============================

Access the live documentation for the apsimNGpy package here; https://magala-richard.github.io/apsimNGpy-documentations/index.html

Access the live documentation for the apsimNGpy package API here: https://magala-richard.github.io/apsimNGpy-documentations/api.html

How to Contribute to apsimNGpy
*********************************************************************************
We welcome contributions from the community, whether they are bug fixes, enhancements, documentation updates, or new features. Here's how you can contribute to ``apsimNGpy``:

Reporting Issues
----------------
.. note::
  apsimNGpy is developed and maintained by a dedicated team of volunteers. We kindly ask that you adhere to our community standards when engaging with the project. Please maintain a respectful tone when reporting issues or interacting with community members.

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
