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
   model =core.base_data.load_default_simulations(crop = "Maize")
   model.find_model("Weather")
   Models.Climate.Weather
   model.find_model("Clock")
   Models.Clock