.. _quick_factorial_experiments:

Quick and Simple Way to Run Factorial Experiments
=================================================

.. image:: ../images/experiment_r.gif
   :alt: Run APSIM simulation
   :align: center
   :width: 800px

This guide demonstrates how to set up and run factorial experiments using `apsimNGpy`, `pandas`, and `seaborn`. Factorial experiments involve systematically varying multiple factors to observe their effects on outputs such as crop yield.

The :class:`~apsimNGpy.core.experimentmanager.ExperimentManager`: API in ``apsimNGpy`` provides a high-level interface to build factorial experiments
programmatically using APSIM. It is ideal for users who want to automate the creation of simulation treatments
by varying input parameters or management scripts — all without manually editing ``.apsimx`` files.

Why apsimNGpy for factorial experiments
======================================

Data in apsimNGpy is **lazily loaded**, allowing users and researchers to run
large design-of-experiments (DoE) workflows without excessive memory usage.
Simulation outputs are also readily available for downstream analysis.

Quick Overview
==============

The :class:`~apsimNGpy.core.experimentmanager.ExperimentManager`: class wraps an existing APSIM model and allows you to:

- Clone and isolate a base simulation
- Add multiple input factors (e.g., fertilizer rate, sowing density)
- Generate permutations or combinations of those factors
- Export the updated ``.apsimx`` file with fully configured experiments
- visualize outputs easily

Step 1. Import the API and initialize it
-----------------------------------------

.. code-block:: python

   from apsimNGpy.core.experimentmanager import ExperimentManager
   exp = ExperimentManager("Maize", out_path="Maize_experiment.apsimx")

Step 2. Adding Factors
----------------------------
The following example demonstrates how plant population density and nitrogen fertilizer rates are added with one at a time.

a) Add nitrogen levels as a continuous factor:

.. code-block:: python

    exp.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20", factor_name='Nitrogen')

b) Add population density as a categorical factor:

.. code-block:: python

    exp.add_factor(specification="[Sow using a variable rule].Script.Population = 4, 10, 2, 7, 6",
                     factor_name='Population')


Step 3. Running the Experiment
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