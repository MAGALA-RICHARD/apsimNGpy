.. _quick_factorial_experiments:

Quick and Simple Way to Run Factorial Experiments
=================================================

This guide demonstrates how to set up and run factorial experiments using `apsimNGpy`, `pandas`, and `seaborn`. Factorial experiments involve systematically varying multiple factors to observe their effects on outputs such as crop yield.

Setting Up the Environment
--------------------------

First, import the necessary libraries:

.. code-block:: python

    import pandas as pd
    import seaborn as sns
    sns.set_style('whitegrid')
    from matplotlib import pyplot as plt
    from apsimNGpy.core.base_data import load_default_simulations
    from apsimNGpy.core.core import CoreModel

Creating an Experiment
----------------------

Load the default maize simulations and initialize APSIM:

.. code-block:: python

    _apsim = load_default_simulations(crop='Maize', simulations_object=False)
    apsim = CoreModel(_apsim)

Create an experiment with permutation enabled:

.. code-block:: python

    apsim.create_experiment(permutation=True, verbose=False)  # Default is a permutation experiment

Adding Factors
--------------

Add nitrogen levels as a continuous factor:

.. code-block:: python

    apsim.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20", factor_name='Nitrogen')

Add population density as a categorical factor:

.. code-block:: python

    apsim.add_factor(specification="[Sow using a variable rule].Script.Population = 4, 10, 2, 7, 6",
                     factor_name='Population')

Running the Experiment
----------------------

Execute the simulation and visualize results:

.. code-block:: python

    apsim.run(report_name='Report')
    df = apsim.results
    df[['population']] = pd.Categorical(['Population'])
    sns.catplot(x='Nitrogen', y='Yield', hue='Population', data=df, kind='box')
    plt.show()

Factorial Experiment with Cultivar Replacements
-----------------------------------------------

To conduct a factorial experiment involving cultivar modifications, a crop replacement must be added.

Load the maize simulations again and initialize APSIM:

.. code-block:: python

    _apsim = load_default_simulations(crop='Maize', simulations_object=False)
    apsimC = CoreModel(_apsim)

Create an experiment with permutation enabled:

.. code-block:: python

    apsimC.create_experiment(permutation=True, verbose=False)  # Default is a permutation experiment

Add nitrogen and population density factors:

.. code-block:: python

    apsimC.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20", factor_name='Nitrogen')
    apsimC.add_factor(specification="[Sow using a variable rule].Script.Population = 4, 10, 2, 7, 6",
                      factor_name='Population')

Replace the crop with an alternative maize cultivar:

.. code-block:: python

    apsimC.add_crop_replacements(_crop='Maize')

Add a factor for radiation use efficiency (RUE):

.. code-block:: python

    apsimC.add_factor(specification='[Maize].Leaf.Photosynthesis.RUE.FixedValue = 1.0, 1.23, 4.3', factor_name='RUE')

Run the experiment and visualize the impact of RUE on yield:

.. code-block:: python

    apsimC.run()
    sns.catplot(x='Nitrogen', y='Yield', hue='RUE', data=apsimC.results, kind='bar')
    plt.show()

Conclusion
----------

This tutorial demonstrated how to set up and run factorial experiments using APSIM NG. By systematically varying multiple factors (e.g., nitrogen levels, population density, and RUE), we can analyze their effects on crop yield effectively.
