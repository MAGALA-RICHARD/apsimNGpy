.. meta::
    :description lang=en:
       Instantiating can be done using any of the default APSIM model templates or
       custom apsimx path on your computer

Instantiating `apsimNGpy` Model Objects
========================================

.. rubric:: Table of Contents

.. contents::
   :local:
   :depth: 2
   :class: compact


You can either load a built-in template or use your own APSIM file.

.. admonition:: Loading default APSIM templates

    You can quickly get started by loading a default simulation model (e.g., maize) in one of two ways:

.. code-block:: python

    # Supported by versions 0.35 +
    from apsimNGpy.core.apsim import ApsimModel
    model = ApsimModel(model='Maize', out_path = 'maize.apsimx')

.. note::

   loading default simulations while using :class:`~apsimNGpy.core.apsim.ApsimModel` requires only the name of the default template model without the suffix: ``.apsimx`` these templates are stored in '../Examples' folder.
   Available models at the time of this writing are shown in the list below. The highlighted names are those that can be passed to :class:`~apsimNGpy.core.apsim.ApsimModel` to load the corresponding default model.
     - 'UnderReview/SoilTemperature/``SoilTemperature``.apsimx',
     - 'UnderReview/SoilTemperature/``SoilTemperatureExample``.apsimx',
     - 'Examples/``RedClover``.apsimx',
     - 'Examples/``Chickpea``.apsimx',
     - 'Examples/``Canola``.apsimx',
     - 'Examples/``Pinus``.apsimx',
     - 'Examples/``Mungbean``.apsimx',
     - 'Examples/``FodderBeet``.apsimx',
     - 'Examples/``ControlledEnvironment``.apsimx',
     - 'Examples/``Potato``.apsimx',
     - 'Examples/``Peanut``.apsimx',
     - 'Examples/``Soybean``.apsimx',
     - 'Examples/``Stock``.apsimx',
     - 'Examples/``SCRUM``.apsimx',
     - 'Examples/``Rotation``.apsimx',
     - 'Examples/``SWIM``.apsimx',
     - 'Examples/``Eucalyptus``.apsimx',
     - 'Examples/``Barley``.apsimx',
     - 'Examples/``AgPasture``.apsimx',
     - 'Examples/``SimpleGrazing``.apsimx',
     - 'Examples/``PlantainForage``.apsimx',
     - 'Examples/``Sorghum``.apsimx',
     - 'Examples/``WhiteClover``.apsimx',
     - 'Examples/``BiomassRemovalFromPlant``.apsimx',
     - 'Examples/``Chicory``.apsimx',
     - 'Examples/``Sugarcane``.apsimx',
     - 'Examples/``Maize``.apsimx',
     - 'Examples/``EucalyptusRotation``.apsimx',
     - 'Examples/``CsvWeather``.apsimx',
     - 'Examples/``Oats``.apsimx',
     - 'Examples/``CanolaGrazing``.apsimx',
     - 'Examples/``Wheat``.apsimx',
     - 'Examples/``Grapevine``.apsimx',
     - 'Examples/``Slurp``.apsimx',
     - 'Examples/``Factorial``.apsimx',
     - 'Examples/``OilPalm``.apsimx',
     - 'Examples/``Graph``.apsimx',
     - 'Examples/ManagerExamples/``RegressionExample``.apsimx',
     - 'Examples/Sensitivity/``Morris``.apsimx',
     - 'Examples/Sensitivity/``Sobol``.apsimx',
     - 'Examples/Agroforestry/``Gliricidia Stripcrop Example``.apsimx',
     - 'Examples/Agroforestry/``Tree Belt Example``.apsimx',
     - 'Examples/Agroforestry/``Single Tree Example``.apsimx',
     - 'Examples/Tutorials/``Memo``.apsimx',
     - 'Examples/Tutorials/``ClimateController``.apsimx',
     - 'Examples/Tutorials/``ExcelDataExample``.apsimx',
     - 'Examples/Tutorials/``EventPublishSubscribe``.apsimx',
     - 'Examples/Tutorials/``PredictedObserved``.apsimx',
     - 'Examples/Tutorials/``Sensitivity_SobolMethod``.apsimx',
     - 'Examples/Tutorials/``SWIM``.apsimx',
     - 'Examples/Tutorials/``Report``.apsimx',
     - 'Examples/Tutorials/``PropertyUI``.apsimx',
     - 'Examples/Tutorials/``Sensitivity_FactorialANOVA``.apsimx',
     - 'Examples/Tutorials/``Sensitivity_MorrisMethod``.apsimx',
     - 'Examples/Tutorials/``Manager``.apsimx',
     - 'Examples/Tutorials/Lifecycle/``lifecycle``.apsimx',
     - 'Examples/CLEM/``CLEM_Sensibility_HerdManagement``.apsimx',
     - 'Examples/CLEM/``CLEM_Example_Grazing``.apsimx',
     - 'Examples/CLEM/``CLEM_Example_Cropping``.apsimx',
     - 'Examples/Optimisation/``CroptimizRExample``.apsimx'

.. Hint::

    If ``out_path`` is not specified, the model will be saved to a randomly generated file path on your computer.
    The ``out_path`` parameter accepts both absolute and relative paths. If a relative path is provided, the file will be saved in the current working directory.

.. admonition:: Using a local APSIM file

    If you have an ``.apsimx`` file saved on your machine — whether from a previous session or as a custom template—you can easily load it as shown below.
    By default, a random file path is generated as the output path. However, you can specify a custom path to control where the edited file is saved.
    This approach helps preserve the original file in case something goes wrong during the loading or editing process.

.. code-block:: python

    from apsimNGpy.core.apsim import ApsimModel

    # Load a local APSIM file
    model = ApsimModel(model='path/to/your/apsim/file.apsimx', out_path = './maize.apsimx')


What comes next after editing
------------------------------

.. admonition:: Next actions

    Once your model is instantiated, you're ready to run simulations, edit model components, or inspect simulation settings. See the following sections for editing examples and diagnostics tools.

.. seealso::

   - :meth:`~apsimNGpy.core.apsim.ApsimModel.save`
   - :ref:`API Reference: <api_ref>`
   - :ref:`Download Stable APSIM Version <apsim_pin_version>`
   - :ref:`Go back to the home page<master>`
