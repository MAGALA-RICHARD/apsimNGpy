Evaluate model on observed dataset
====================================

import the observed data
ideally could be on a csv file but here we are used a mimicked version

.. code-block:: python
  from apsimNGpy.tests.unittests.test_factory import obs
  from apsimNGpy.core.apsim import ApsimModel

Initialise the model. replace `maize model with your model on file or go a heand and customize it as you want


.. code-block:: python

        with ApsimModel('Maize') as model:
            model.add_report_variable(variable_spec='[Clock].Today.Year as year', report_name='Report')
            model.run()
            metrics = model.evaluate(ref_data=obs, table='Report', index_col=['year'],
                                     target_col='Yield', ref_data_col='observed')
            self.assertIsInstance(metrics, dict, f'Metrics should be a dictionary, got {type(metrics)}')
            self.assertIn('data', metrics.keys(), f'data  key not found in {metrics.keys()}')
 the above code will produce something similar to below;

.. code-block:: none

   Model Evaluation Metrics
   =----------------------------------------
    BIAS    :    -0.0001
    CCC     :     1.0000
    MAE     :     0.0003
    ME      :     1.0000
    MSE     :     0.0000
    R2      :     1.0000
    RMSE    :     0.0003
    RRMSE   :     0.0000
    SLOPE   :     1.0000
    WIA     :     1.0000