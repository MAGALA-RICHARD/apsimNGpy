.. _api_ref:

apsimNGpy: API Reference
========================

This page provides the public Python API for ``apsimNGpy``.

apsimNGpy
---------

.. automodule:: apsimNGpy

Classes
^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.Apsim

.. autoclass:: apsimNGpy.Apsim
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

apsimNGpy.config
----------------

.. automodule:: apsimNGpy.config

Functions
^^^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.config.get_apsim_bin_path
   apsimNGpy.config.load_crop_from_disk
   apsimNGpy.config.set_apsim_bin_path

.. autofunction:: apsimNGpy.config.get_apsim_bin_path

.. autofunction:: apsimNGpy.config.load_crop_from_disk

.. autofunction:: apsimNGpy.config.set_apsim_bin_path

Classes
^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.config.apsim_bin_context

.. autoclass:: apsimNGpy.config.apsim_bin_context
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

apsimNGpy.core.apsim
--------------------

.. automodule:: apsimNGpy.core.apsim

Classes
^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.core.apsim.ApsimModel

.. autoclass:: apsimNGpy.core.apsim.ApsimModel
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

apsimNGpy.core.experiment
-------------------------

.. automodule:: apsimNGpy.core.experiment

Functions
^^^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.core.experiment.create_experiment_from_file
   apsimNGpy.core.experiment.pre_experiment_test

.. autofunction:: apsimNGpy.core.experiment.create_experiment_from_file

.. autofunction:: apsimNGpy.core.experiment.pre_experiment_test

Classes
^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.core.experiment.ExperimentManager

.. autoclass:: apsimNGpy.core.experiment.ExperimentManager
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

apsimNGpy.core.mult_cores
-------------------------

.. automodule:: apsimNGpy.core.mult_cores

Classes
^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.core.mult_cores.MultiCoreManager

.. autoclass:: apsimNGpy.core.mult_cores.MultiCoreManager
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

apsimNGpy.core.runner
---------------------

.. automodule:: apsimNGpy.core.runner

Functions
^^^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.core.runner.build_apsim_command
   apsimNGpy.core.runner.collect_csv_by_model_path
   apsimNGpy.core.runner.collect_csv_from_dir
   apsimNGpy.core.runner.collect_db_from_dir
   apsimNGpy.core.runner.dir_simulations_to_csv
   apsimNGpy.core.runner.dir_simulations_to_dfs
   apsimNGpy.core.runner.dir_simulations_to_sql
   apsimNGpy.core.runner.get_apsim_version
   apsimNGpy.core.runner.get_matching_files
   apsimNGpy.core.runner.run_apsim_by_path
   apsimNGpy.core.runner.run_dir_simulations
   apsimNGpy.core.runner.run_model_externally
   apsimNGpy.core.runner.trial_run
   apsimNGpy.core.runner.upgrade_apsim_file

.. autofunction:: apsimNGpy.core.runner.build_apsim_command

.. autofunction:: apsimNGpy.core.runner.collect_csv_by_model_path

.. autofunction:: apsimNGpy.core.runner.collect_csv_from_dir

.. autofunction:: apsimNGpy.core.runner.collect_db_from_dir

.. autofunction:: apsimNGpy.core.runner.dir_simulations_to_csv

.. autofunction:: apsimNGpy.core.runner.dir_simulations_to_dfs

.. autofunction:: apsimNGpy.core.runner.dir_simulations_to_sql

.. autofunction:: apsimNGpy.core.runner.get_apsim_version

.. autofunction:: apsimNGpy.core.runner.get_matching_files

.. autofunction:: apsimNGpy.core.runner.run_apsim_by_path

.. autofunction:: apsimNGpy.core.runner.run_dir_simulations

.. autofunction:: apsimNGpy.core.runner.run_model_externally

.. autofunction:: apsimNGpy.core.runner.trial_run

.. autofunction:: apsimNGpy.core.runner.upgrade_apsim_file

Classes
^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.core.runner.RunError

.. autoclass:: apsimNGpy.core.runner.RunError
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

apsimNGpy.core.sensitivity_manager
----------------------------------

.. automodule:: apsimNGpy.core.sensitivity_manager

Classes
^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.core.sensitivity_manager.SensitivityManager

.. autoclass:: apsimNGpy.core.sensitivity_manager.SensitivityManager
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

apsimNGpy.core_utils.database_utils
-----------------------------------

.. automodule:: apsimNGpy.core_utils.database_utils

Functions
^^^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.core_utils.database_utils.chunker
   apsimNGpy.core_utils.database_utils.clear_all_tables
   apsimNGpy.core_utils.database_utils.dataview_to_dataframe
   apsimNGpy.core_utils.database_utils.delete_all_tables
   apsimNGpy.core_utils.database_utils.delete_table
   apsimNGpy.core_utils.database_utils.dispose
   apsimNGpy.core_utils.database_utils.drop_table
   apsimNGpy.core_utils.database_utils.get_db_table_names
   apsimNGpy.core_utils.database_utils.insert_table
   apsimNGpy.core_utils.database_utils.read_db_table
   apsimNGpy.core_utils.database_utils.read_with_pandas
   apsimNGpy.core_utils.database_utils.read_with_query
   apsimNGpy.core_utils.database_utils.write_df_to_sql
   apsimNGpy.core_utils.database_utils.write_results_to_sql
   apsimNGpy.core_utils.database_utils.write_schema_grouped_tables

.. autofunction:: apsimNGpy.core_utils.database_utils.chunker

.. autofunction:: apsimNGpy.core_utils.database_utils.clear_all_tables

.. autofunction:: apsimNGpy.core_utils.database_utils.dataview_to_dataframe

.. autofunction:: apsimNGpy.core_utils.database_utils.delete_all_tables

.. autofunction:: apsimNGpy.core_utils.database_utils.delete_table

.. autofunction:: apsimNGpy.core_utils.database_utils.dispose

.. autofunction:: apsimNGpy.core_utils.database_utils.drop_table

.. autofunction:: apsimNGpy.core_utils.database_utils.get_db_table_names

.. autofunction:: apsimNGpy.core_utils.database_utils.insert_table

.. autofunction:: apsimNGpy.core_utils.database_utils.read_db_table

.. autofunction:: apsimNGpy.core_utils.database_utils.read_with_pandas

.. autofunction:: apsimNGpy.core_utils.database_utils.read_with_query

.. autofunction:: apsimNGpy.core_utils.database_utils.write_df_to_sql

.. autofunction:: apsimNGpy.core_utils.database_utils.write_results_to_sql

.. autofunction:: apsimNGpy.core_utils.database_utils.write_schema_grouped_tables

apsimNGpy.exceptions
--------------------

.. automodule:: apsimNGpy.exceptions

Classes
^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.exceptions.ApsimBinPathConfigError
   apsimNGpy.exceptions.ApsimNGpyError
   apsimNGpy.exceptions.ApsimNotFoundError
   apsimNGpy.exceptions.ApsimRuntimeError
   apsimNGpy.exceptions.CastCompilationError
   apsimNGpy.exceptions.EmptyDateFrameError
   apsimNGpy.exceptions.ForgotToRunError
   apsimNGpy.exceptions.InvalidInputErrors
   apsimNGpy.exceptions.ModelNotFoundError
   apsimNGpy.exceptions.NodeNotFoundError
   apsimNGpy.exceptions.TableNotFoundError

.. autoclass:: apsimNGpy.exceptions.ApsimBinPathConfigError
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

.. autoclass:: apsimNGpy.exceptions.ApsimNGpyError
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

.. autoclass:: apsimNGpy.exceptions.ApsimNotFoundError
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

.. autoclass:: apsimNGpy.exceptions.ApsimRuntimeError
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

.. autoclass:: apsimNGpy.exceptions.CastCompilationError
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

.. autoclass:: apsimNGpy.exceptions.EmptyDateFrameError
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

.. autoclass:: apsimNGpy.exceptions.ForgotToRunError
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

.. autoclass:: apsimNGpy.exceptions.InvalidInputErrors
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

.. autoclass:: apsimNGpy.exceptions.ModelNotFoundError
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

.. autoclass:: apsimNGpy.exceptions.NodeNotFoundError
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

.. autoclass:: apsimNGpy.exceptions.TableNotFoundError
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

apsimNGpy.optimizer.minimize.single_mixed
-----------------------------------------

.. automodule:: apsimNGpy.optimizer.minimize.single_mixed

Classes
^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.optimizer.minimize.single_mixed.MixedVariableOptimizer

.. autoclass:: apsimNGpy.optimizer.minimize.single_mixed.MixedVariableOptimizer
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

apsimNGpy.optimizer.problems.back_end
-------------------------------------

.. automodule:: apsimNGpy.optimizer.problems.back_end

Functions
^^^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.optimizer.problems.back_end.eval_observed

.. autofunction:: apsimNGpy.optimizer.problems.back_end.eval_observed

apsimNGpy.optimizer.problems.smp
--------------------------------

.. automodule:: apsimNGpy.optimizer.problems.smp

Classes
^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.optimizer.problems.smp.MixedProblem

.. autoclass:: apsimNGpy.optimizer.problems.smp.MixedProblem
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

apsimNGpy.parallel.process
--------------------------

.. automodule:: apsimNGpy.parallel.process

Functions
^^^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.parallel.process.custom_parallel
   apsimNGpy.parallel.process.custom_parallel_chunks
   apsimNGpy.parallel.process.parallelize_chunks

.. autofunction:: apsimNGpy.parallel.process.custom_parallel

.. autofunction:: apsimNGpy.parallel.process.custom_parallel_chunks

.. autofunction:: apsimNGpy.parallel.process.parallelize_chunks

apsimNGpy.sensitivity.sens_file
-------------------------------

.. automodule:: apsimNGpy.sensitivity.sens_file

Functions
^^^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.sensitivity.sens_file.evaluate_model_sensitivity

.. autofunction:: apsimNGpy.sensitivity.sens_file.evaluate_model_sensitivity

Classes
^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.sensitivity.sens_file.ConfigProblem

.. autoclass:: apsimNGpy.sensitivity.sens_file.ConfigProblem
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

apsimNGpy.sensitivity.sensitivity
---------------------------------

.. automodule:: apsimNGpy.sensitivity.sensitivity

Functions
^^^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.sensitivity.sensitivity.run_sensitivity

.. autofunction:: apsimNGpy.sensitivity.sensitivity.run_sensitivity

Classes
^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.sensitivity.sensitivity.ConfigProblem

.. autoclass:: apsimNGpy.sensitivity.sensitivity.ConfigProblem
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

apsimNGpy.validation.evaluator
------------------------------

.. automodule:: apsimNGpy.validation.evaluator

Classes
^^^^^^^

.. autosummary::
   :nosignatures:

   apsimNGpy.validation.evaluator.Validate

.. autoclass:: apsimNGpy.validation.evaluator.Validate
   :members:
   :show-inheritance:
   :member-order: bysource
   :inherited-members:

