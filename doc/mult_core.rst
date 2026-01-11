Distributed Computing
=========================

Distributed computing (or parallelism) is the practice of dividing computing tasks among multiple processing resources to speed up computations.
See Li, Z., Qi, Z., Liu, Y., Zheng, Y., & Yang, Y. (2023). A modularized parallel distributed High–Performance computing framework for simulating seasonal frost dynamics in Canadian croplands. Computers and Electronics in Agriculture, 212, 108057.

In apsimNGpy, this is achieved through the :class:`~apsimNGpy.core.mult_cores.MultiCoreManager` API, which abstracts away most of the setup required for distributing tasks.

Below, we’ll walk through a step-by-step example of using this API


.. code-block:: python

        from apsimNGpy.core.multi_cores import MultiCoreManager
        from apsimNGpy.core.apsim import ApsimModel
        from pathlib import Path


In this example (v0.39.03.11+), we assume your APSIM files are already prepared (or available in various locations) and you simply want a speed boost when running them and processing results.
For demonstration purposes, we’ll generate some example jobs:

.. code-block:: python

        # Best to supply a generator so jobs are created on the fly
        create_jobs = (
            ApsimModel('Maize').path
            for _ in range(100)
        )


Here we use the :class:`~apsimNGpy.core.apsim.ApsimModel` class to clone from the template Maize model shipped with APSIM. If you do not specify the out_path argument, each file is assigned a random filename. This is critical in multi-processing—you must ensure that no two processes share the same filename, otherwise the run will fail.

To explicitly set unique filenames for each simulation:

.. code-block:: python

       create_jobs = (ApsimModel('Maize', out_path = Path(f"_{i}.apsimx").resolve()).path
       for i in range(100))


.. tip::

    The key idea: every file must have a unique identifier to avoid race conditions during parallel execution.

Instantiating and Running the Simulations
=========================================

.. code-block:: python

        if __name__ == '__main__': # a guard is required
            # initialize
            task_manager = MultiCoreManager(db_path=Path('test.db').resolve(), agg_func=None)
            # Run all the jobs
            task_manager.run_all_jobs(create_jobs, n_cores=16, threads=False, clear_db=True)

# this is the progress info

.. code-block:: python

            Processing all jobs. Please wait!: :  |██████████| 100.0%| [100/100]| Complete | 1.07s/iteration | Elapsed time: 00:01:46.850

# get the results

.. code-block:: python

            df = task_manager.get_simulated_output(axis=0)
            # same as
            data = task_manager.results  # defaults is axis =0

If ``agg_func`` is specified, it can be one of: mean, median, sum, min, or max. Each results table will then be summarized using the selected aggregation function.

``clear_db`` is used to clear the database tables before all new entries are added

``threads (bool)``: If True, use threads; if False, use processes. For ``CPU-bound`` tasks like this one, processes are preferred as they prevent resource contention and blocking inherent to threads.

``n_cores (int)``: Specifies the number of worker cores to use for the task. The workload will be divided among these workers. If the number of cores is large but the number of tasks is small, some scheduling overhead will occur, and workers may remain idle while waiting for available tasks.

Customization
===================
If you don’t want to use the higher-level API, you can build the pipeline from scratch.
The simplest path is to decorate your worker with :func:`~apsimNGpy.core_utils.database_utils.write_results_to_sql`, which writes the worker’s return
value to the database after each run. The worker must return either a pandas DataFrame or a dict—that way you control exactly which variables/columns are written.
Alternatively, skip the decorator and call your own writer/aggregator inside the worker, as shown below.

.. code-block:: python

            from pathlib import Path
            from apsimNGpy.core.apsim import ApsimModel
            from apsimNGpy.core_utils.database_utils import read_db_table, write_results_to_sql
            from apsimNGpy.parallel.process import custom_parallel
            import pandas as pd
            from sqlalchemy import create_engine


            DATABAse = str(Path('test_custom.db').resolve())



Minimal example 1: Writing your own worker and data storage function
--------------------------------------------------------------------

.. code-block:: python

            # define function to insert insert results
            def insert_results(db_path, results, table_name):
                """
                Insert a pandas DataFrame into a SQLite table.

                Parameters
                ----------
                db_path : str or Path
                    Path to the SQLite database file.
                results : pandas.DataFrame
                    DataFrame to insert into the database.
                table_name : str
                    Name of the table to insert the data into.
                """
                if not isinstance(results, pd.DataFrame):
                    raise TypeError("`results` must be a pandas DataFrame")

                engine = create_engine(f"sqlite:///{db_path}")
                results.to_sql(table_name, con=engine, if_exists='append', index=False)
            # ____________worker___________________________-
            def worker(nitrogen_rate, model):
                out_path = Path(f"_{nitrogen_rate}.apsimx").resolve()
                model = ApsimModel(model, out_path=out_path)
                model.edit_model("Models.Manager", model_name='Fertilise at sowing', Amount=nitrogen_rate)
                model.run(report_name="Report")
                df = model.results
                # we can even create column for each simulation
                df['nitrogen rate'] = nitrogen_rate

                insert_results(db_path = DATABAse, results =df, table_name='Report')
                model.clean_up()
                # no need to return results

Minimal example 2: Writing your own worker and use data storage decorator from data_base_utils (only latest version)
--------------------------------------------------------------------------------------------------------------------

.. code-block:: python

            @write_results_to_sql(DATABAse, table='Report', if_exists='append')
            def worker(nitrogen_rate, model):
                out_path = Path(f"_{nitrogen_rate}.apsimx").resolve()
                model = ApsimModel(model, out_path=out_path)
                model.edit_model("Models.Manager", model_name='Fertilise at sowing', Amount=nitrogen_rate)
                model.run(report_name="Report")
                df = model.results
                # we can even create column for each simulation
                df['nitrogen rate'] = nitrogen_rate
                model.clean_up()
                return df

Running all jobs
===================
Always run parallel code under the standard Python entry-point guard: ``if __name__ == '__main__':``
Without the guard, top-level code re-executes in each child and can recursively spawn processes.

.. code-block:: python

            if __name__ == '__main__':

                for _ in custom_parallel(worker, range(0, 400, 10), 'Maize', n_cores=6, use_threads=False):
                    pass
                # get the results
                data = read_db_table(DATABAse, report_name="Report")

.. code-block:: python

   Processing please wait!:  ██████████ 100% (40/40) >> completed (elapsed=>0:30, eta=>00:00) , (0.76 s/iteration or 1.23 iteration/s)

.. code-block:: python

            print(data)
                SimulationName  SimulationID  ...  source_table nitrogen rate
            0       Simulation             1  ...        Report            20
            1       Simulation             1  ...        Report            20
            2       Simulation             1  ...        Report            20
            3       Simulation             1  ...        Report            20
            4       Simulation             1  ...        Report            20
            ..             ...           ...  ...           ...           ...
            395     Simulation             1  ...        Report           380
            396     Simulation             1  ...        Report           380
            397     Simulation             1  ...        Report           380
            398     Simulation             1  ...        Report           380
            399     Simulation             1  ...        Report           380
            [400 rows x 18 columns]


Our 40 simulations ran in 30 seconds only, almost 0.76 seconds per simulation.

.. note::

   Performance can vary between systems depending on hardware specifications,
   such as RAM, processor clock speed, and the number of CPU cores.


Working in notebooks (Jupyter/Colab)
=====================================
When using Jupyter notebooks, the workflow follows the same structure as described above. For stability and reproducibility,
it is recommended to define worker functions in a standalone Python module (.py file) and import them into the notebook.

Minimal Example 3: Run All Simulations Using the C# Backend
----------------------------------------------------------

This example shows how to execute a folder of APSIM simulations using the C\# engine
(`Models.exe`) and either:

1. store the results directly into a SQL database, or
2. load the grouped outputs into memory as pandas DataFrames.

We begin by creating a directory containing multiple APSIMX files.

.. code-block:: python

   from apsimNGpy.tests.unittests.test_factory import mimic_multiple_files
   from apsimNGpy.core.runner import dir_simulations_to_sql, dir_simulations_to_dfs

   file_dir = mimic_multiple_files(
       out_file="test_dir",
       size=100,
       suffix="__",
       mix=False
   )

3a) Running All Simulations and Storing Results in a SQL Database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from sqlalchemy import create_engine, inspect

   # Use an in-memory SQLite database; replace with a file path for persistence
   engine = create_engine("sqlite:///:memory:")

   try:
       dir_simulations_to_sql(
           dir_path=file_dir,
           pattern="*__.apsimx",
           recursive=False,
           tables="Report",# could be a list of table names if more than one tables are anticipated or needed
           cpu_count=10,
           connection=engine,
       )

       # Inspect which tables were created
       inspector = inspect(engine)
       tables = inspector.get_table_names()
       print(tables)

       # Expected tables:
       #   1) a data table containing all Report rows aggregated by schema
       #   2) a schema table documenting column names and dtypes
   finally:
       engine.dispose(close=True)

In this workflow, all APSIMX files matching ``*__.apsimx`` are executed using the
C\# simulation engine. The resulting ``Report`` tables are collected from the APSIM
databases, grouped in memory by schema, and written into the SQL database specified
by ``connection``.

The grouped data are stored in one table, and a separate schema table
(``_schemas`` by default) records the column names and dtypes associated with each
group. Calling ``inspect(engine).get_table_names()`` allows you to verify that both
tables were created.

3b) Running All Simulations and Loading Grouped Results Into Memory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    groups = dir_simulations_to_dfs(
        dir_path=file_dir,
        pattern="*__.apsimx",
        recursive=False,
        tables="Report",# could be a list of table names if more than one tables are anticipated or needed
        cpu_count=10,
    )

In this mode, the results are not written to disk. Instead, ``groups`` is returned as
a dictionary where:

* **keys** are schema signatures (tuples describing each column and its dtype), and
* **values** are DataFrames containing all rows that share that schema.

If different simulations generate different ``Report`` table structures, multiple
schema groups will be produced. For example, if two distinct report schemas are
encountered, ``groups`` will contain two keys, each mapping to a DataFrame with its
corresponding structure.


.. seealso::

  - API description: :class:`~apsimNGpy.core.mult_cores.MultiCoreManager`
  -  :ref:`API Reference: <api_ref>`