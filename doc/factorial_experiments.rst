.. _quick_factorial_experiments:

Quick and Simple Way to Run Factorial Experiments
=================================================

.. image:: ../images/experiment.gif
   :alt: Run APSIM simulation
   :align: center
   :width: 800px

This guide demonstrates how to set up and run factorial experiments using `apsimNGpy`, `pandas`, and `seaborn`. Factorial experiments involve systematically varying multiple factors to observe their effects on outputs such as crop yield.

Setting Up the Environment
--------------------------

First, import the necessary libraries:

.. code-block:: python

   from apsimNGpy.core.experimentmanager import ExperimentManager
   exp = ExperimentManager("Maize", out_path="Maize_experiment.apsimx")

Adding Factors
--------------

Add nitrogen levels as a continuous factor:

.. code-block:: python

    exp.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20", factor_name='Nitrogen')

Add population density as a categorical factor:

.. code-block:: python

    exp.add_factor(specification="[Sow using a variable rule].Script.Population = 4, 10, 2, 7, 6",
                     factor_name='Population')


Running the Experiment
----------------------

Execute the simulation and visualize results:

.. code-block:: python

    exp.run(report_name='Report')
    df = apsim.results
    df[['population']] = pd.Categorical(['Population'])
    sns.catplot(x='Nitrogen', y='Yield', hue='Population', data=df, kind='box')
    plt.show()

Factorial Experiment with Cultivar Replacements
-----------------------------------------------

.. Hint::

   To conduct a factorial experiment involving ``cultivar`` modifications, a crop replacement must be added.

Load the maize simulations again and initialize APSIM:

.. code-block:: python

   from apsimNGpy.core.experimentmanager import ExperimentManager
   exp = ExperimentManager("Maize", out_path="Maize_experiment.apsimx")


Create an experiment with permutation enabled:

.. code-block:: python

    exp.init_experiment(permutation=True)

Add nitrogen and population density factors:

.. code-block:: python

    exp.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20",
    factor_name='Nitrogen')
    exp.add_factor(specification="[Sow using a variable rule].Script.Population = 4, 10, 2, 7, 6",
                      factor_name='Population')

Replace the crop with an alternative maize cultivar:

.. code-block:: python

    exp.add_crop_replacements(_crop='Maize')

Add a factor for radiation use efficiency (RUE):

.. code-block:: python

     exp.add_factor(specification='[Maize].Leaf.Photosynthesis.RUE.FixedValue = 1.0, 1.23, 4.3',
     factor_name='RUE')

Run the experiment and visualize the impact of ``RUE`` on yield:

.. code-block:: python

    exp.run()
    sns.catplot(x='Nitrogen', y='Yield', hue='RUE', data=exp.results, kind='bar')
    plt.show()

.. admonition:: Conclusion.

   This tutorial demonstrated how to set up and run factorial experiments using apsimNGpy. By systematically varying multiple factors (e.g., nitrogen levels, population density, and RUE), we can analyze their effects on the target variable effectively.

.. include:: new_experiment.rst

.. seealso::

   - :ref:`API Reference: <api_ref>`