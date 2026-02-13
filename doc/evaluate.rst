.. _evaluate_model_on_observed_dataset:

.. meta::
   :description lang=en:
      Learn how to evaluate APSIM simulation outputs against observed datasets
      using apsimNGpy's evaluate method, including calculation of statistical
      performance metrics such as RMSE, R2, CCC, and WIA.

Evaluate Model on Observed Dataset
==================================

.. contents::
   :local:
   :depth: 2


This section demonstrates how to evaluate simulated model outputs
against an observed dataset using
:meth:`~apsimNGpy.core.apsim.ApsimModel.evaluate`.

Import Observed Data
--------------------

Observed data may be loaded from a CSV file or any pandas ``DataFrame``.
For demonstration purposes, we use a mimicked dataset from the test suite.

.. code-block:: python

   from apsimNGpy.tests.unittests.test_factory import obs
   from apsimNGpy.core.apsim import ApsimModel


Initialize and Run the Model
----------------------------

Replace ``'Maize'`` with the path to your own ``.apsimx`` file,
or customize the model configuration as needed.

.. code-block:: python

   with ApsimModel('Maize') as model:

       # Add simulation year to the report
       model.add_report_variable(
           variable_spec='[Clock].Today.Year as year',
           report_name='Report'
       )

       # Run the simulation
       model.run()

       # Evaluate simulation results against observed data
       metrics = model.evaluate(
           ref_data=obs,
           table='Report',
           index_col=['year'],
           target_col='Yield',
           ref_data_col='observed',
           verbose=True
       )


Output
------

If ``verbose=True``, the evaluation summary will be printed to the console.
Otherwise, all metrics are returned as a dictionary.

Example console output:

.. code-block:: none

   Model Evaluation Metrics
   ----------------------------------------
   BIAS   :  -0.0001
   CCC    :   1.0000
   MAE    :   0.0003
   ME     :   1.0000
   MSE    :   0.0000
   R2     :   1.0000
   RMSE   :   0.0003
   RRMSE  :   0.0000
   SLOPE  :   1.0000
   WIA    :   1.0000


Returned Metrics
----------------

The returned dictionary contains:

- **BIAS** — Mean bias error
- **MAE** — Mean absolute error
- **MSE** — Mean squared error
- **RMSE** — Root mean squared error
- **RRMSE** — Relative RMSE
- **R2** — Coefficient of determination
- **CCC** — Concordance correlation coefficient
- **ME** — Model efficiency
- **WIA** — Willmott’s index of agreement
- **SLOPE** — Regression slope


.. seealso::

   :meth:`~apsimNGpy.core.apsim.ApsimModel.evaluate`
