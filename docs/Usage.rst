Running and Retrieving Results
==============================

Running loaded models
^^^^^^^^^^^^^^^^^^^^^^^
Running loaded models implies executing the model to generate simulated outputs. This is implemented via ``ApsimModel.run()`` method as shown below.
Users can provide the ``report_name``, which specifies data table name from the simulation for retrieving the results.

.. code-block:: python

    from apsimNGpy.core.apsim import ApsimModel
    # Option 1: Load default maize simulation
    model = ApsimModel(crop='Maize') # case sensitive
    # Run the simulation
    model.run(report_name='Report')

.. tip::

    Please note that ``report_name`` can be a string (``str``), implying a single database table
    or a ``list``, implying that one or more than one database tables. If the later is true, then the results will be concatenated along the rows using ``pandas.concat`` method.
    By default, ``apsimNGpy`` looks for these report database tables automatically, and returns a concatenated pandas data frame. This may not be ideal if they are many report tables, hence the need to clearly specify the preferred report table names


Accessing Simulated Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^
After the simulation runs, results can be accessed  via ``apsim.results`` property attribute as pandas DataFrames. Please see note above. These results can be saved to a CSV file or printed to the console.

Another way to access the results is to use ``get_simulated_output`` on the instantiated class object. This method accepts only one argument ``report_names`` and under the same principle explained above.

.. caution::

     Please note that accessing results through any of the above method before calling ``run()`` may not be allowed, and will raise an ``error``.

.. code-block:: python

    # Retrieve and save the results
    df = model.results
    df.to_csv('apsim_df_res.csv')  # Save the results to a CSV file
    print(model.results)  # Print all DataFrames in the storage domain

      SimulationName  SimulationID  CheckpointID  ... Maize.Total.Wt      Yield   Zone
    0     Simulation             1             1  ...       1964.016   9367.414  Field
    1     Simulation             1             1  ...       1171.894   5645.455  Field
    2     Simulation             1             1  ...        265.911    303.013  Field
    3     Simulation             1             1  ...        944.673   3528.287  Field
    4     Simulation             1             1  ...       1996.779   9204.485  Field
    5     Simulation             1             1  ...       2447.581  10848.238  Field
    6     Simulation             1             1  ...       1325.265   2352.152  Field
    7     Simulation             1             1  ...       1097.480   2239.558  Field
    8     Simulation             1             1  ...       2264.083  10378.414  Field
    9     Simulation             1             1  ...       2006.421   8577.954  Field
    [10 rows x 16 columns]


Saving the Simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
When we load the model, it is usually assigned a random name. However, you can save the file using the save() method.
This method takes a single argument: the desired file path or name.

.. Hint::

    Without specifying the full path to the desired storage location, the file will be saved in the current working directory

.. code-block:: python

    model.save('./edited_maize_model.apsimx')

