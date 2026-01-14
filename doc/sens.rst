Sensitivity Analysis in apsimNGpy Part 1
=========================================

Sensitivity analysis in ``apsimNGpy`` implements the same established
methods used in APSIM—namely the **Morris Elementary Effects** method and
the **Sobol variance–based method**. The key difference is flexibility:
``apsimNGpy`` allows you to **construct a sensitivity analysis directly from
any APSIM template file**, including the model you are actively developing.
With only a few lines of Python code, you can specify the sensitivity
method, configure the factors, build the sensitivity model, and execute it.


``SensitivityManager`` class provides convenient access points for
visualization and custom analysis, enabling you to create your own plots
using Matplotlib, Seaborn, or other Python libraries.

The workflow for creating a sensitivity analysis is conceptually similar to
setting up factorial experiments: define the method, specify the factors,
build the sensitivity experiment node, and run the simulations. The example
below shows a minimal, practical workflow for constructing a sensitivity
analysis directly from Python.

Class: :class:`~apsimNGpy.core.senstivitymanager.SensitivityManager` was added in **V0.39.12.21+**

.. tip::

   ``apsimNGpy`` is designed to integrate sensitivity analysis seamlessly
   into reproducible pipelines. Because everything is defined in Python,
   you can version-control the full sensitivity experiment, regenerate it
   consistently, and run it across multiple APSIM templates or scenarios.

Workflow Overview
-----------------

The sensitivity analysis workflow in ``apsimNGpy`` follows a structured,
reproducible sequence of steps. The process is designed to mirror APSIM’s
internal sensitivity framework while providing full programmatic control in
Python. The key stages are:

1. **Initialize the manager instance**
   Create a ``SensitivityManager`` object using your APSIM template file.
   This instance will hold the experiment configuration and manage all
   subsequent steps.

2. **Define sensitivity factors**
   Add one or more factors (parameters) to the manager instance. Each factor
   corresponds to an APSIM model path and a numerical range to be explored.
   Factors are defined using methods on the instantiated ``SensitivityManager``
   object.

3. **Build the sensitivity simulation model**
   Construct the sensitivity experiment node within the APSIM file.
   During this step the user:

   - selects the sensitivity method (Morris or Sobol),
   - specifies the database table name for storing results,
   - determines the aggregation column used to summarize outputs,
   - and, when using the Morris method:
     - sets the number of jumps,
     - defines the number of intervals,
     - and optionally customizes the step size ``Δ``.
   For **all** sensitivity methods, this step also sets the number of
   parameter paths, which controls the total number of simulations executed.

4. **Run the sensitivity simulations**
   Execute the sensitivity experiment. ``apsimNGpy`` automatically handles
   model execution, path construction, execution, and data storage.


Workflow Diagram
----------------

::

        +-----------------+       +----------------------+
        |instantiate class |----> |  define parameters   |
        +-----------------+       +----------------------+
                                         |
                                         v
        +-----------------+       +----------------------+
        |  run model      |<----- |  Build nodes         |
        +-----------------+       +----------------------+

Step 1.

.. code-block:: python

     from apsimNGpy.core import senstivitymanager import SensitivityManager
     morris = SensitivityManager("Maize", out_path='sob.apsimx')

Step 2.

.. code-block:: python

     morris.add_sens_factor(name='cnr', path='Field.SurfaceOrganicMatter.InitialCNR', lower_bound=10, upper_bound=120)
     morris.add_sens_factor(name='cn2bare', path='Field.Soil.SoilWater.CN2Bare', lower_bound=70, upper_bound=100)

Step 3.

.. code-block:: python

    morris.build_sense_model(method='Morris', aggregation_column_name='Clock.Today', jumps=10)

We can still use any other methods inherited from :class:`~apsimNGpy.core.apsim.ApsimModel` as follows

.. code-block:: python

   morris.inspect_file()

.. code-block:: none

  └── Models.Core.Simulations: .Simulations
    ├── Models.Storage.DataStore: .Simulations.DataStore
    └── Models.Morris: .Simulations.Morris
        └── Models.Core.Simulation: .Simulations.Morris.Simulation
            ├── Models.Clock: .Simulations.Morris.Simulation.Clock
            ├── Models.Core.Zone: .Simulations.Morris.Simulation.Field
            │   ├── Models.Manager: .Simulations.Morris.Simulation.Field.Fertilise at sowing
            │   ├── Models.Fertiliser: .Simulations.Morris.Simulation.Field.Fertiliser
            │   ├── Models.Manager: .Simulations.Morris.Simulation.Field.Harvest
            │   ├── Models.PMF.Plant: .Simulations.Morris.Simulation.Field.Maize
            │   ├── Models.Report: .Simulations.Morris.Simulation.Field.Report
            │   ├── Models.Soils.Soil: .Simulations.Morris.Simulation.Field.Soil
            │   │   ├── Models.Soils.Chemical: .Simulations.Morris.Simulation.Field.Soil.Chemical
            │   │   ├── Models.Soils.Solute: .Simulations.Morris.Simulation.Field.Soil.NH4
            │   │   ├── Models.Soils.Solute: .Simulations.Morris.Simulation.Field.Soil.NO3
            │   │   ├── Models.Soils.Organic: .Simulations.Morris.Simulation.Field.Soil.Organic
            │   │   ├── Models.Soils.Physical: .Simulations.Morris.Simulation.Field.Soil.Physical
            │   │   │   └── Models.Soils.SoilCrop: .Simulations.Morris.Simulation.Field.Soil.Physical.MaizeSoil
            │   │   ├── Models.Soils.Solute: .Simulations.Morris.Simulation.Field.Soil.Urea
            │   │   └── Models.Soils.Water: .Simulations.Morris.Simulation.Field.Soil.Water
            │   ├── Models.Manager: .Simulations.Morris.Simulation.Field.Sow using a variable rule
            │   └── Models.Surface.SurfaceOrganicMatter: .Simulations.Morris.Simulation.Field.SurfaceOrganicMatter
            ├── Models.Graph: .Simulations.Morris.Simulation.Graph
            │   └── Models.Series: .Simulations.Morris.Simulation.Graph.Series
            ├── Models.MicroClimate: .Simulations.Morris.Simulation.MicroClimate
            ├── Models.Soils.Arbitrator.SoilArbitrator: .Simulations.Morris.Simulation.SoilArbitrator
            ├── Models.Summary: .Simulations.Morris.Simulation.Summary
            └── Models.Climate.Weather: .Simulations.Morris.Simulation.Weather

Step 4

.. code-block:: python

   morris.run()

You can access the statics as follows

.. code-block:: python

    morris.statistics

.. code-block:: none

                CheckpointID Clock.Today  ...            ColumnName     Indices
            0               1  1991-05-28  ...  Maize.AboveGround.Wt  FirstOrder
            1               1  1991-05-28  ...  Maize.AboveGround.Wt  FirstOrder
            2               1  1991-05-28  ...  Maize.AboveGround.Wt       Total
            3               1  1991-05-28  ...  Maize.AboveGround.Wt       Total
            4               1  1991-05-28  ...   Maize.AboveGround.N  FirstOrder
            ..            ...         ...  ...                   ...         ...
            355             1  2000-04-05  ...         Maize.Grain.N       Total
            356             1  2000-04-05  ...        Maize.Total.Wt  FirstOrder
            357             1  2000-04-05  ...        Maize.Total.Wt  FirstOrder
            358             1  2000-04-05  ...        Maize.Total.Wt       Total
            359             1  2000-04-05  ...        Maize.Total.Wt       Total
            [360 rows x 10 columns]


We can get a list of available variables as follows

.. code-block:: python

   morris.statistics.columns

.. code-block:: none

   Index(['CheckpointID', 'Parameter', 'Clock.Today', 'Maize.AboveGround.Wt.Mu',
       'Maize.AboveGround.Wt.MuStar', 'Maize.AboveGround.Wt.Sigma',
       'Maize.AboveGround.N.Mu', 'Maize.AboveGround.N.MuStar',
       'Maize.AboveGround.N.Sigma', 'Yield.Mu', 'Yield.MuStar', 'Yield.Sigma',
       'Maize.Grain.Wt.Mu', 'Maize.Grain.Wt.MuStar', 'Maize.Grain.Wt.Sigma',
       'Maize.Grain.Size.Mu', 'Maize.Grain.Size.MuStar',
       'Maize.Grain.Size.Sigma', 'Maize.Grain.NumberFunction.Mu',
       'Maize.Grain.NumberFunction.MuStar', 'Maize.Grain.NumberFunction.Sigma',
       'Maize.Grain.Total.Wt.Mu', 'Maize.Grain.Total.Wt.MuStar',
       'Maize.Grain.Total.Wt.Sigma', 'Maize.Grain.N.Mu',
       'Maize.Grain.N.MuStar', 'Maize.Grain.N.Sigma', 'Maize.Total.Wt.Mu',
       'Maize.Total.Wt.MuStar', 'Maize.Total.Wt.Sigma'],
      dtype='object')


Simulated results can be accessed as follows:

.. code-block:: python

   morris.results
   #same as
   morris.get_simulated_output('Report')

In order to use Sobol, use `method =sobol' as follows

.. code-block:: python

    sobol = SensitivityManager("Maize", out_path='sob.apsimx')
    morris.add_sens_factor(name='cnr', path='Field.SurfaceOrganicMatter.InitialCNR', lower_bound=10, upper_bound=120)
    morris.add_sens_factor(name='cn2bare', path='Field.Soil.SoilWater.CN2Bare', lower_bound=70, upper_bound=100)
    sobol.build_sense_model(method='Sobol', aggregation_column_name='Clock.Today')
    sobol.inspect_file()
    sobol.run()
    sobol.statistics
    sobol.results
    # same as
    sobol.get_simulated_output('Report')

.. code-block:: none

   └── Models.Core.Simulations: .Simulations
    ├── Models.Storage.DataStore: .Simulations.DataStore
    └── Models.Sobol: .Simulations.Sobol
        └── Models.Core.Simulation: .Simulations.Sobol.Simulation
            ├── Models.Clock: .Simulations.Sobol.Simulation.Clock
            ├── Models.Core.Zone: .Simulations.Sobol.Simulation.Field
            │   ├── Models.Manager: .Simulations.Sobol.Simulation.Field.Fertilise at sowing
            │   ├── Models.Fertiliser: .Simulations.Sobol.Simulation.Field.Fertiliser
            │   ├── Models.Manager: .Simulations.Sobol.Simulation.Field.Harvest
            │   ├── Models.PMF.Plant: .Simulations.Sobol.Simulation.Field.Maize
            │   ├── Models.Report: .Simulations.Sobol.Simulation.Field.Report
            │   ├── Models.Soils.Soil: .Simulations.Sobol.Simulation.Field.Soil
            │   │   ├── Models.Soils.Chemical: .Simulations.Sobol.Simulation.Field.Soil.Chemical
            │   │   ├── Models.Soils.Solute: .Simulations.Sobol.Simulation.Field.Soil.NH4
            │   │   ├── Models.Soils.Solute: .Simulations.Sobol.Simulation.Field.Soil.NO3
            │   │   ├── Models.Soils.Organic: .Simulations.Sobol.Simulation.Field.Soil.Organic
            │   │   ├── Models.Soils.Physical: .Simulations.Sobol.Simulation.Field.Soil.Physical
            │   │   │   └── Models.Soils.SoilCrop: .Simulations.Sobol.Simulation.Field.Soil.Physical.MaizeSoil
            │   │   ├── Models.Soils.Solute: .Simulations.Sobol.Simulation.Field.Soil.Urea
            │   │   └── Models.Soils.Water: .Simulations.Sobol.Simulation.Field.Soil.Water
            │   ├── Models.Manager: .Simulations.Sobol.Simulation.Field.Sow using a variable rule
            │   └── Models.Surface.SurfaceOrganicMatter: .Simulations.Sobol.Simulation.Field.SurfaceOrganicMatter
            ├── Models.Graph: .Simulations.Sobol.Simulation.Graph
            │   └── Models.Series: .Simulations.Sobol.Simulation.Graph.Series
            ├── Models.MicroClimate: .Simulations.Sobol.Simulation.MicroClimate
            ├── Models.Soils.Arbitrator.SoilArbitrator: .Simulations.Sobol.Simulation.SoilArbitrator
            ├── Models.Summary: .Simulations.Sobol.Simulation.Summary
            └── Models.Climate.Weather: .Simulations.Sobol.Simulation.Weather

The rest of the workflow is the same as above

The API interface is still the same because all methods and attributes are inherited from the :class:`~apsimNGpy.core.apsim.ApsimModel`. Some examples are given below:

.. code-block:: python

    sobol.inspect_model('Models.Manager')

.. code-block:: none

    ['.Simulations.Sobol.Simulation.Field.Sow using a variable rule',
     '.Simulations.Sobol.Simulation.Field.Fertilise at sowing',
     '.Simulations.Sobol.Simulation.Field.Harvest']

.. code-block:: python

    sobol.inspect_model_parameters_by_path('.Simulations.Sobol.Simulation.Field.Fertilise at sowing')

.. code-block:: none

    {'Crop': 'Maize', 'FertiliserType': 'NO3N', 'Amount': '160.0'}

We can still edit the base simulation models as follows

.. code-block:: python

    sobol.edit_model_by_path('.Simulations.Sobol.Simulation.Field.Fertilise at sowing', Amount=150)

Same as:

.. code-block:: python

    sobol.edit_model(model_type='Models.Manager', model_name='Fertilise at sowing', Amount=150)

Then, you can run the model

.. code-block:: python

   sobol.run(verbose = True)

Before I log off, you can check out the documentation of the following methods, which have been used in this tutorial

:meth:`~apsimNGpy.core.senstivitymanager.SensitivityManager.add_sens_factor`,
:meth:`~apsimNGpy.core.senstivitymanager.SensitivityManager.build_sense_model`,
:meth:`~apsimNGpy.core.senstivitymanager.SensitivityManager.statistics`.


 .. seealso::

    - :ref:`API Reference <api_ref>`
    - :ref:`Download Stable APSIM Version here <apsim_pin_version>`
    - :ref:`Go back to the home page<master>`

.. note::

    The sensitivity analysis workflow described above is effective because it leverages APSIM’s built-in methods and commands.
    However, APSIM currently relies on external R-based sensitivity analysis packages, which may require users to have R installed.
    Outside of Windows environments, this often necessitates some form of containerization, adding complexity to the workflow.

    To address these limitations, Part II of the apsimNGpy sensitivity workflow introduces a fully cross-platform solution by
    integrating the SALib library directly with apsimNGpy. This approach eliminates the dependency on R, simplifies deployment
    across operating systems, and provides greater flexibility.

    In addition, the SALib-based workflow is highly customizable in terms of sampling strategies and supports a wide range of
    sensitivity analysis methods beyond Morris and Sobol.

    **Please check it out on the next page.**
