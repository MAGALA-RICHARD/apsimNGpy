Inspect Model
=============================

Most of the time, when modifying model parameters and values, you need the full path to the specified APSIM model.  
This is where the `inspect_model` method becomes useful—it allows you to inspect the model without opening the file in the APSIM GUI.

Let's take a look at how it works.

.. code-block:: python

    from apsimNGpy.core import base_data
    from apsimNGpy.core.core import Models

    model = base_data.load_default_simulations(crop='maize')

    # Retrieve paths to Manager models
    model.inspect_model(model_type=Models.Manager, fullpath=True)
    ['.Simulations.Simulation.Field.Sow using a variable rule',
     '.Simulations.Simulation.Field.Fertilise at sowing',
     '.Simulations.Simulation.Field.Harvest']

    # Retrieve paths to Clock models
    model.inspect_model(model_type=Models.Clock)
    ['.Simulations.Simulation.Clock']

    # Retrieve paths to Crop models
    model.inspect_model(model_type=Models.Core.IPlant)
    ['.Simulations.Simulation.Field.Maize']

    # Retrieve crop model names instead of full paths
    model.inspect_model(model_type=Models.Core.IPlant, fullpath=False)
    ['Maize']

    # Retrieve paths to Fertiliser models
    model.inspect_model(Models.Fertiliser, fullpath=True)
    ['.Simulations.Simulation.Field.Fertiliser']

Model Types
""""""""""""""""""""""""""

`model_type` can be any of the following classes from the `Models` namespace:

- **Models.Manager** – Returns information about the manager scripts in simulations.
- **Models.Core.Simulation** – Returns information about the simulation.
- **Models.Climate.Weather** – Returns a list of paths or names pertaining to weather models.
- **Models.Core.IPlant** – Returns a list of paths or names for all crop models available in the simulation.
- *(Additional model types may be available based on APSIM simulation requirements.)*

Finding the Model Type
""""""""""""""""""""""""""""""""""""""

In some cases, determining the model type can be challenging. Fortunately, **apsimNGpy** provides a recursive function to simplify this process—the `find_model` method.  
This method helps identify the model type efficiently. However, you need to know the name of the model, such as **Clock** or **Weather**, to use it effectively.

.. code-block:: python

    from apsimNGpy import core
    from apsimNGpy.core.core import Models

    # Load the default maize simulation
    model = core.base_data.load_default_simulations(crop="Maize")

    # Inspect or find specific components
    model.find_model("Weather")
    Models.Climate.Weather

    model.find_model("Clock")
    Models.Clock

Whole Model inspection
=====================================


Use `inspect_file`` method to inspects all simulations in the file. This method displays a tree showing how each model is connected with each other


.. code-block:: python

    model.inspect_file()



.. image:: ../images/apsim_file_structure.png
    :alt: Tree structure of the APSIM model
    :align: center
    :width: 100%

Note on Model Inspection:
"""""""""""""""""""""""""""""""""""""""""""""""

Only a few key model types are inspected using model.inspect_model under the hood. Inspecting the entire simulation file can produce a large volume of data, much of which may not be relevant or necessary in most use cases.

If certain models do not appear in the inspection output, this is intentional — the tool selectively inspects components to keep results concise and focused.

For a complete view of the entire model structure, we recommend opening the simulation file in the APSIM GUI.