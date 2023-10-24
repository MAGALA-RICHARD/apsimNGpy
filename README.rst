

apsimNGpy: The next generation agroecosytem simulation library
====================================================================

Our cutting-edge open-source framework, apsimNGpy, empowers advanced agroecosystem modeling through the utilization of object-oriented principles. It features fast batch file simulation, model prediction, evaluation, 
apsimx file editing, seamless weather data retrieval, and efficient soil profile development


.. _Installation:

Installation
********************************************************************************

First, make sure you have a Python 3 environment installed. Install APSIM and ensure that the directory containing the Models executable is added to the system's PATH or the Python path (to locate the required .dll files). This can be achieved in either of the following ways:

a. Utilize the APSIM installer provided for this purpose.

b. Build APSIM from its source code. This is soon


For the current developer versions:

Method 1
.. code:: bash

    git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git
    cd apsimNGpy
    pip install .

Method 2
.. code:: bash
     pip install git+https://github.com/MAGALA-RICHARD/apsimNGpy.git


.. _Usage:

Usage
********************************************************************************

Please check our documentation for all the details.
However, for instance, sample usgae

.. code:: python
    import apsimNGpy
    from apsimNGpy.base_data import load_example_files
    from apsimNGpy.apsimpy import ApsimSoil
    from pathlib import Path

    cwd = Path.cwd()

    # Create the data
    data = load_example_files(cwd)

    # Get maize model
    maize = data.get_maize()

    # Initialize the simulation methods
    apsim = ApsimSoil(maize, copy=True)

    # Run the file
    apsim.run_edited_file()
    # print the results
    print(apsim.results)
    # check the manager modules in the apsim simulation file
    # first th=get the simualtion names
    sim_name = apsim.extract_simulation_name
    apsim.examine_management_info(simulations=sim_name)
    # show current simulation in apsim GUI
    apsim.show_file_in_APSIM_GUI()




