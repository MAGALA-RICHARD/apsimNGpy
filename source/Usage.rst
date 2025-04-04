Examples
----------------

This example demonstrates how to use `apsimNGpy` to load a default simulation, run it, retrieve results, and visualize the output.

.. code-block:: python

    # Import necessary modules
    import apsimNGpy
    from apsimNGpy.core.base_data import load_default_simulations
    from apsimNGpy.core.apsim import ApsimModel as SoilModel
    from pathlib import Path
    import os
    from apsimNGpy.validation.visual import plot_data

The above code imports the necessary modules for running APSIM simulations. This includes `apsimNGpy` modules for loading default simulations and managing results, as well as standard Python libraries for file handling and visualization.


.. code-block:: python

    # Load the default simulation
    soybean_model = load_default_simulations(crop='soybean')  # Case-insensitive crop specification

The `load_default_simulations` function loads a default APSIM simulation for the specified crop. In this example, the crop is set to soybean, but you can specify other crops as needed.

.. code:: python

    # Load the simulation path without initializing the object
    soybean_path_model = load_default_simulations(crop='soybean', simulation_object=False)

If you prefer not to initialize the simulation object immediately, you can load only the simulation path by setting `simulation_object=False`.

.. code-block:: python

    # Initialize the APSIM model with the simulation file path
    apsim = SoilModel(soybean_path_model)

This code initializes the APSIM model using the previously loaded simulation file path.

.. code-block:: python

    # Run the simulation
    apsim.run(report_name='Report')

The `run` method executes the simulation. The `report_name` parameter specifies which data table from the simulation will be used for results.

.. note:
   report_name accepts a list of simulation data tables and hence can return a concatenated pandas data frame for all the data tables
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
