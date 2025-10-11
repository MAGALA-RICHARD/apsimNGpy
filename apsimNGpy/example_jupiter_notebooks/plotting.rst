Plotting and Visualizing Simulated Output
=========================================
Visualizing simulated results, is a critical step in understanding and communicating model behavior.
Visualization serves as the blueprint of any experiment as it generates scientific insight underlying the data.
The goal of this tutorial, therefore, is to help you quickly set up, diagnose, and report your simulation outcomes effectively,
enabling clear interpretation and compelling presentation of your results.

.. code-block:: python

    from apsimNGpy.core.experimentmanager import ExperimentManager
    from matplotlib import pyplot as plt

Create the experiment
----------------------
.. code-block:: python

    model = ExperimentManager('Maize', out_path = 'my_experiment.apsimx')
    # init the experiment
    model.init_experiment(permutation =True)

Adding factors to the experiment
--------------------------------
Adding factors to the experiment requires that we understand the model structure. This can be accomplished
by: :meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.inspect_model`, :meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.inspect_file`,
:meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.inspect_model_parameters_by_path`

Inspect the whole simulation tree

.. code-block:: python

   model.inspect_file()

.. code-block:: none

  └── Simulations: .Simulations
    ├── DataStore: .Simulations.DataStore
    └── Experiment: .Simulations.Experiment
        ├── Factors: .Simulations.Experiment.Factors
        │   └── Permutation: .Simulations.Experiment.Factors.Permutation
        └── Simulation: .Simulations.Experiment.Simulation
            ├── Clock: .Simulations.Experiment.Simulation.Clock
            ├── Field: .Simulations.Experiment.Simulation.Field
            │   ├── Fertilise at sowing: .Simulations.Experiment.Simulation.Field.Fertilise at sowing
            │   ├── Fertiliser: .Simulations.Experiment.Simulation.Field.Fertiliser
            │   ├── Harvest: .Simulations.Experiment.Simulation.Field.Harvest
            │   ├── Maize: .Simulations.Experiment.Simulation.Field.Maize
            │   ├── Report: .Simulations.Experiment.Simulation.Field.Report
            │   ├── Soil: .Simulations.Experiment.Simulation.Field.Soil
            │   │   ├── Chemical: .Simulations.Experiment.Simulation.Field.Soil.Chemical
            │   │   ├── NH4: .Simulations.Experiment.Simulation.Field.Soil.NH4
            │   │   ├── NO3: .Simulations.Experiment.Simulation.Field.Soil.NO3
            │   │   ├── Organic: .Simulations.Experiment.Simulation.Field.Soil.Organic
            │   │   ├── Physical: .Simulations.Experiment.Simulation.Field.Soil.Physical
            │   │   │   └── MaizeSoil: .Simulations.Experiment.Simulation.Field.Soil.Physical.MaizeSoil
            │   │   ├── Urea: .Simulations.Experiment.Simulation.Field.Soil.Urea
            │   │   └── Water: .Simulations.Experiment.Simulation.Field.Soil.Water
            │   ├── Sow using a variable rule: .Simulations.Experiment.Simulation.Field.Sow using a variable rule
            │   └── SurfaceOrganicMatter: .Simulations.Experiment.Simulation.Field.SurfaceOrganicMatter
            ├── Graph: .Simulations.Experiment.Simulation.Graph
            │   └── Series: .Simulations.Experiment.Simulation.Graph.Series
            ├── MicroClimate: .Simulations.Experiment.Simulation.MicroClimate
            ├── SoilArbitrator: .Simulations.Experiment.Simulation.SoilArbitrator
            ├── Summary: .Simulations.Experiment.Simulation.Summary
            └── Weather: .Simulations.Experiment.Simulation.Weather

Inspect the full paths to the manager scripts in the model

.. code-block:: python

   model.inspect_model('Models.Manager')

.. code-block:: none

    ['.Simulations.Experiment.Simulation.Field.Sow using a variable rule',
     '.Simulations.Experiment.Simulation.Field.Fertilise at sowing',
     '.Simulations.Experiment.Simulation.Field.Harvest']

Inspect the names to the manager scripts in the model


.. code-block:: python

   model.inspect_model('Models.Manager', fullpath=False)

.. code-block:: none

    ['Sow using a variable rule', 'Fertilise at sowing', 'Harvest']

If we want to edit any of the above script in the experiment, there is need to inspect the associated underlying parameters

1. '.Simulations.Experiment.Simulation.Field.Sow using a variable rule'

.. code-block:: python

  model.inspect_model_parameters_by_path('.Simulations.Experiment.Simulation.Field.Sow using a variable rule')

.. code-block:: python

        {'Crop': 'Maize',
     'StartDate': '1-nov',
     'EndDate': '10-jan',
     'MinESW': '100.0',
     'MinRain': '25.0',
     'RainDays': '7',
     'CultivarName': 'Dekalb_XL82',
     'SowingDepth': '30.0',
     'RowSpacing': '750.0',
     'Population': '6.0'}

2. '.Simulations.Experiment.Simulation.Field.Fertilise at sowing'

.. code-block:: python

   model.inspect_model_parameters_by_path('.Simulations.Experiment.Simulation.Field.Fertilise at sowing')

.. code-block:: python

    {'Crop': 'Maize', 'FertiliserType': 'NO3N', 'Amount': '160.0'}

Add factors along the the paramters; `Amount` and `Population` from the last and first scripts, respectively.

.. code-block:: python

    # Population
    model.add_factor(specification='[Sow using a variable rule].Script.Population = 4, 6, 8, 10', factor_name='Population')
    # Nitrogen fertilizers
    model.add_factor(specification='[Fertilise at sowing].Script.Amount= 0, 100,150, 200, 250', factor_name= 'Nitrogen')

Before we run,let's add one report variable for an easy demonstration

.. code-block:: python

   model.add_report_variable(variable_spec=['[Clock].Today.Year as year'], report_name='Report')
   # run the model to generate output
   model.run()

Inspect the simulated results

.. code-block:: python

    model.results.info()

# By default, the parameter name of each factor is also populated in the data frame.

.. code-block:: python

   model.plot_mva(table='Report', response='Yield', time_col='year', col_wrap=2, palette='tab10',
      errorbar=None, estimator='mean', grouping=('Amount', 'Population'), hue='Nitrogen', col='Population')


.. code-block:: image

  ./images/'mva_hue_nitrogen_grp_n_p.png'


Categorical Plots
------------------

