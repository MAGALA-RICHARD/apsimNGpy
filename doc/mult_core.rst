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


.. tip::

     The key idea: every file must have a unique identifier to avoid race conditions during parallel execution.

In newer apsimNGpy versions, each job must specify the APSIM ``.apsimx`` model to execute and may
include additional metadata.

Supported job definitions include:

**1. Plain job definitions (no metadata, no edits)**
This assumes that each model file is unique and has already been
edited externally.

.. code-block:: python

   jobs = {
       'model_0.apsimx',
       'model_1.apsimx',
       'model_2.apsimx',
       'model_3.apsimx',
       'model_4.apsimx',
       'model_5.apsimx',
       'model_6.apsimx',
       'model_7.apsimx'
   }

**2. Job definitions with metadata**
This format allows attaching identifiers or other metadata to each
job. Models are assumed to be unique and pre-edited.

.. code-block:: python

   [
       {'model': 'model_0.apsimx', 'ID': 0},
       {'model': 'model_1.apsimx', 'ID': 1},
       {'model': 'model_2.apsimx', 'ID': 2},
       {'model': 'model_3.apsimx', 'ID': 3},
       {'model': 'model_4.apsimx', 'ID': 4},
       {'model': 'model_5.apsimx', 'ID': 5},
       {'model': 'model_6.apsimx', 'ID': 6},
       {'model': 'model_7.apsimx', 'ID': 7}
   ]

**3. Job definitions with internal model edits**
In this format, each job specifies an ``inputs`` list with dicts representing each node to be edited internally by the runner. These
edits must follow the rules of
:meth:`~apsimNGpy.core.apsim.ApsimModel.edit_model_by_path`. The input dictionary is treated as metadata and is attached to the results' tables. When both inputs and additional metadata are provided, they are merged into a single metadata mapping prior to attachment, with former entries overriding earlier metadata keys and thereby avoiding duplicate keys in the results' tables.

.. code-block:: python

  jobs=  [
       {
           'model': 'model_0.apsimx',
           'ID': 0,
           'inputs': [{
               'path': '.Simulations.Simulation.Field.Fertilise at sowing',
               'Amount': 0
           }]
       },
       {
           'model': 'model_1.apsimx',
           'ID': 1,
           'inputs': [{
               'path': '.Simulations.Simulation.Field.Fertilise at sowing',
               'Amount': 50
           }]
       },
       {
           'model': 'model_2.apsimx',
           'ID': 2,
           'inputs': [{
               'path': '.Simulations.Simulation.Field.Fertilise at sowing',
               'Amount': 100
           }]
       }
   ]

Instantiating and Running the Simulations
=========================================

.. code-block:: python

        if __name__ == '__main__': # a guard is required
            # create jobs
            create_jobs = (ApsimModel('Maize', out_path = Path(f"_{i}.apsimx").resolve()).path
            # initialize
            task_manager = MultiCoreManager(db_path=Path('test.db').resolve(), agg_func=None)
            # Run all the jobs
            task_manager.run_all_jobs(create_jobs, n_cores=16, threads=False, clear_db=True)

If ``agg_func`` is specified, it can be one of: mean, median, sum, min, or max. Each results table will then be summarized using the selected aggregation function.

``clear_db`` is used to clear the database tables before all new entries are added

``threads (bool)``: If True, use threads; if False, use processes. For ``CPU-bound`` tasks like this one, processes are preferred as they prevent resource contention and blocking inherent to threads.

``n_cores (int)``: Specifies the number of worker cores to use for the task. The workload will be divided among these workers. If the number of cores is large but the number of tasks is small, some scheduling overhead will occur, and workers may remain idle while waiting for available tasks.

Tracking completed jobs
=========================
MultiCoreManager API displays the number of completed jobs and percentage of the total submitted,
time per simulation(sim) failed jobs (f) elapsed time and seconds per sim

.. code-block:: python

            Processing![0f] :  |██████████| 100.0%| [100/100]| Complete | 1.07s/sim | Elapsed time: 00:01:46.850


Retrieving results
====================
Results can be loaded to memory by :meth:`~apsimNGpy.core.mult_cores.MultiCoreManager.get_simulated_output` or :attr:`~apsimNGpy.core.mult_cores.MultiCoreManager.results`

.. code-block:: python

            df = task_manager.get_simulated_output(axis=0)
            # same as
            data = task_manager.results  # defaults is axis =0

Results can also be transferred to an sql database or to csv as follows

.. code-block:: python

   from sqlite2 import connect
   db  = connect(':memory:")
   or
   db = 'test.db"
   task_manager.save_tosql(db_or_con=db, table_name='agg_table', if_exist='replace', chunk_size=1000)
   # to scv
   task_manager.save_to_csv('test.csv')

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
The above workflow can now be cleanly reproduced using the MultiCoreManager API, as shown below.
This interface allows users to choose between a pure Python execution
mode—where tasks are distributed across multiple Python interpreters
in memory—or a C# execution mode, where simulations are executed through the C# engine.

.. code-block:: python

     Parallel = MultiCoreManager(db_path=db, agg_func='mean', table_prefix='di', )
     jobs = ({'model': 'Maize', 'ID': i, 'payload': [{'path': '.Simulations.Simulation.Field.Fertilise at sowing',
                                                     'Amount': i}]} for i in range(200))
     start = time.perf_counter()
     Parallel.run_all_jobs(jobs=jobs, n_cores=8, engine='csharp', threads=False, chunk_size=100,
                          subset=['Yield'],
                          progressbar=True)
     dff = Parallel.results

When no aggregation is applied, the number of rows increases because each simulation contributes multiple
records. For example, if each simulation spans 10 years, the resulting DataFrame will contain 10 × 200 = 2,000 rows.

Benchmarking computation speed across the different simulation engines
------------------------------------------------------------------------

+------------+--------------+-----------+----------------+
| Batch size | Python (m)   | C# (m)    | Speedup (×)    |
+============+==============+===========+================+
| 100        | 2:30         | 1:25      | ~1.76          |
+------------+--------------+-----------+----------------+
| 200        | 4:44         | 2:54      | ~1.63          |
+------------+--------------+-----------+----------------+
| 300        | 7:13         | 4:23      | ~1.65          |
+------------+--------------+-----------+----------------+
| 400        | 9:24         | 5:26      | ~1.73          |
+------------+--------------+-----------+----------------+
| 500        | 11:55        | 6:58      | ~1.71          |
+------------+--------------+-----------+----------------+
m = minutes,  C# =csharp

.. note::

   Benchmark results were generated on the following system:

   - **Processor:** 12th Gen Intel® Core™ i7-12700 @ 2.10 GHz
   - **Installed RAM:** 32.0 GB (31.7 GB usable)
   - **System type:** 64-bit operating system, x64-based processor

.. tip::

   Reported speedups are indicative and may vary depending on system
   hardware, operating system, available memory, number of CPU cores,
   background workload, and simulation configuration.


.. seealso::

  - API description: :class:`~apsimNGpy.core.mult_cores.MultiCoreManager`
  - run_all_jobs API: :class:`~apsimNGpy.core.mult_cores.MultiCoreManager.run_all_jobs`
  -  :ref:`API Reference: <api_ref>`
  - `Download jupiter notebook example batch simulation workflow <https://github.com/MAGALA-RICHARD/apsimNGpy/blob/main/apsimNGpy/example_jupiter_notebooks/batch_simulations.ipynb>`_
