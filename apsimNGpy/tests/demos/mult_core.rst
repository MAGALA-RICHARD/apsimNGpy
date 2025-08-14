Distributed Computing
=========================

Distributed computing (or parallelism) is the practice of dividing computing tasks among multiple processing resources to speed up computations.

In apsimNGpy, this is achieved through the MultiCoreManager API, which abstracts away most of the setup required for distributing tasks.

Below, we’ll walk through a step-by-step example of using this API


.. code-block:: python

        from apsimNGpy.core.multi_core import MultiCoreManager
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


Here we use the ApsimModel class to clone from the template Maize model shipped with APSIM. If you do not specify the out_path argument, each file is assigned a random filename. This is critical in multi-processing—you must ensure that no two processes share the same filename, otherwise the run will fail.

To explicitly set unique filenames for each simulation:

.. code-block:: python

       create_jobs = (ApsimModel('Maize', out_path = Path(f"_{i}.apsimx").resolve()).path for i in range(10))


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
            # get the results
            df = task_manager.get_simulated_output(axis=0)
            # same as
            data = task_manager.results  # defaults is axis =0

If ``agg_func`` is specified, it can be one of: mean, median, sum, min, or max. Each results table will then be summarized using the selected aggregation function.

``clear_db`` is used to clear the database tables before all new entries are added

``threads (bool)``: If True, use threads; if False, use processes. For ``CPU-bound`` tasks like this one, processes are preferred as they prevent resource contention and blocking inherent to threads.

``n_cores (int)``: Specifies the number of worker cores to use for the task. The workload will be divided among these workers. If the number of cores is large but the number of tasks is small, some scheduling overhead will occur, and workers may remain idle while waiting for available tasks.

Customization
===================

If you dont want to use the above API, you can still build things from scratch

.. code-block:: python

            from pathlib import Path
            from apsimNGpy.core.apsim import ApsimModel
            from apsimNGpy.core_utils.database_utils import read_db_table
            from apsimNGpy.parallel.process import custom_parallel
            import pandas as pd
            from sqlalchemy import create_engine


            DATABAse = str(Path('test_custom.db').resolve())

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


            def worker(nitrogen_rate, model):
                out_path = Path(f"_{nitrogen_rate}.apsimx").resolve()
                model = ApsimModel(model, out_path=out_path)
                model.edit_model("Models.Manager", model_name='Fertilise at sowing', Amount=nitrogen_rate)
                model.run(report_name="Report")
                df = model.results
                # we can even create column for each simulation
                df['nitrogen rate'] = nitrogen_rate
                insert_results(DATABAse, df, 'Report')
                model.clean_up()


            if __name__ == '__main__':

                for _ in custom_parallel(worker, range(0, 400, 10), 'Maize', n_cores=6, use_threads=False):
                    pass
                # get the results
                data = read_db_table(DATABAse, report_name="Report")

            Processing via 'worker' please wait!:  |██████████| 100.0%| [40/40]| Complete | 0.76s/iteration | Elapsed time: 00:00:30.591

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


