.. meta::
   :description lang=en:
          APSIM simulations can be executed sequentially using the `run` method or in parallel
          using the `run_all_jobs` method of the `MultiCoreManager` API.

.. image:: ../images/run.gif
   :alt: Run APSIM simulation
   :align: center
   :width: 800px

Running and Retrieving Results
==============================

Running loaded models
^^^^^^^^^^^^^^^^^^^^^^^
Running loaded models implies executing the model to generate simulated outputs. This is implemented via :meth:`~apsimNGpy.core.apsim.ApsimModel.run` method as shown below.
Users can provide the ``report_name``, which specifies data table name from the simulation for retrieving the results.

.. code-block:: python

    from apsimNGpy.core.apsim import ApsimModel
    # Option 1: Load default maize simulation
    model = ApsimModel('Maize') # case sensitive
    # Run the simulation
    model.run(report_name='Report')

.. tip::

    Please note that ``report_name`` can be a string (``str``), implying a single database table
    or a ``list``, implying that one or more than one database tables. If the later is true, then the results will be concatenated along the rows using ``pandas.concat`` method.
    By default, ``apsimNGpy`` looks for these report database tables automatically, and returns a concatenated pandas data frame. This may not be ideal if they are many report tables, hence the need to clearly specify the preferred report table names


Accessing Simulated Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^
After the simulation runs, results can be accessed  via :attr:`~apsimNGpy.core.apsim.ApsimModel.results` property attribute as pandas DataFrames. Please see note above. These results can be saved to a CSV file or printed to the console.

Another way to access the results is to use :meth:`~apsimNGpy.core.apsim.ApsimModel.get_simulated_output` on the instantiated class object. This method accepts only one argument ``report_names`` and under the same principle explained above.

.. seealso::

   :attr:`~apsimNGpy.core.apsim.ApsimModel.results`
   :meth:`~apsimNGpy.core.apsim.ApsimModel.get_simulated_output`

.. caution::

     Please note that accessing results through any of the above method before calling :meth:`~apsimNGpy.core.apsim.ApsimModel.run` may not be allowed, and will raise an ``error``.

.. code-block:: python

    # Retrieve and save the results
    df = model.results
    df.to_csv('apsim_df_res.csv')  # Save the results to a CSV file
    print(model.results)  # Print all DataFrames in the storage domain

.. code-block:: python

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

Using a context manager for class ApsimModel
--------------------------------------------

Instantiate, use model and discard the edited model afterwards

.. code-block:: python

    from apsimNGpy.core.apsim import ApsimModel
    with ApsimModel('Maize') as model:
        model.run()
        df =model.results
        summary= df.mean(numeric_only=True)
        print(summary)
        # beyond this point, the cloned files from the model are automatically deleted

.. code-block:: none

    CheckpointID                     1.000000
    SimulationID                     1.000000
    Maize.AboveGround.Wt          1225.099950
    Maize.AboveGround.N             12.381196
    Yield                         5636.529504
    Maize.Grain.Wt                 563.652950
    Maize.Grain.Size                 0.284941
    Maize.Grain.NumberFunction    1986.770519
    Maize.Grain.Total.Wt           563.652950
    Maize.Grain.N                    7.459296
    Maize.Total.Wt                1340.837427
    dtype: float64

.. versionadded:: v0.39.10.20

Saving the Simulation
^^^^^^^^^^^^^^^^^^^^^^^^
When we load the model, it is usually assigned a random name. However, you can save the file using the :meth:`~apsimNGpy.core.apsim.ApsimModel.save` method.
This method takes a single argument: the desired file path or name.

.. admonition:: see `Save` API details

    :meth:`~apsimNGpy.core.apsim.ApsimModel.save`


.. Hint::

    Without specifying the full path to the desired storage location, the file will be saved in the current working directory

.. code-block:: python

    model.save('./edited_maize_model.apsimx')

Reloading Saved Models
-----------------------------
By default, when a model is saved, the saved file path is automatically
reloaded into memory and becomes the new reference for the active :class:`~apsimNGpy.core.apsim.ApsimModel` object.

Recent versions of **apsimNGpy** allow users to explicitly control this
behavior using the ``reload`` argument in :meth:`~apsimNGpy.core.apsim.ApsimModel.save`.

Controlling Reload Behavior
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can indicate whether the saved model should be reloaded into the
current model object using the ``reload`` flag.

.. code-block:: python

    model.save("./edited_maize_model.apsimx", reload=False)


Example: Reload Enabled (Default Behavior)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
When ``reload=True`` (the default), the saved file becomes the new active
model and the internal ``model.path`` is updated accordingly, as shown in the code below.

.. code-block:: python

    from apsimNGpy.core.apsim import ApsimModel
    from pathlib import Path

    model = ApsimModel("Maize", out_path=Path("my_model.apsimx").resolve())

    # Current model path
    print(Path(model.path).name)
    # 'my_model.apsimx'

    model.save("./edited_maize_model.apsimx", reload=True)

    # Model path is updated in memory
    print(Path(model.path).name)
    # 'edited_maize_model.apsimx'



Example: Reload Disabled
^^^^^^^^^^^^^^^^^^^^^^^^^^^
With ``reload=False``, the model is written to disk, but the in-memory
model object continues to reference the original path as shown in the code below.

.. code-block:: python

    from apsimNGpy.core.apsim import ApsimModel
    from pathlib import Path

    model = ApsimModel("Maize", out_path=Path("my_model.apsimx").resolve())

    print(Path(model.path).name)
    # 'my_model.apsimx'

    model.save("./edited_maize_model.apsimx", reload=False)

    # Path remains unchanged in memory
    print(Path(model.path).name)
    # 'my_model.apsimx'

Here, the new file exists on disk, but the active model object continues
to reference the original file.

Using ``save`` Inside a Context Manager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
When using :class:`ApsimModel` as a context manager, special care is required. The saved file path must be different
from the current ``model.path`` and ``reload`` must be set to ``False`` as shown below.

.. code-block:: python

    from apsimNGpy.core.apsim import ApsimModel
    from pathlib import Path

    with ApsimModel("Maize", out_path=Path("my_model.apsimx").resolve()) as model:
        print(Path(model.path).name)
        # 'my_model.apsimx'

        model.save("./edited_maize_model.apsimx", reload=False)

        print(Path(model.path).name)
        # 'my_model.apsimx'

In this case, the saved file remains on disk, and the in-memory model
continues to reference the original path.

.. warning::

   If the saved path matches the active model path and ``reload=True``,
   the saved model file may be deleted when exiting the context.

   When ``reload=False``, only associated APSIM database files are
   cleaned up, and the newly saved model file is preserved.

.. seealso::

    - :ref:`API Reference <api_ref>`
    - :ref:`Download Stable APSIM Version here <apsim_pin_version>`
    - :ref:`Go back to the home page<master>`

