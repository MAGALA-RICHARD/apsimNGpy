Distributed Computing
=========================

Distributed computing or parallelism is diving computing tasks amon g the computer resources to fasten computations. In apsimNGpy this is achieved by by the MultiCoreManager API
that abstract most of the setup mechanics for parallezing tasks. Here, let's go through a set by step process of using this API.

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
            for _ in range(10)
        )


The above code uses the ApsimModel class to clone from the template Maize model, shipped with APSIM, because without specifying the out_path, the files are randomly assigned a filename, which is critcal in multi-processing as you dont want to share file anme across different cores, it will fail
if you want a name for each file or simulation, here is how you can achieve it.


.. code-block:: python

       create_jobs = (ApsimModel('Maize', out_path = Path(f"_{i}.apsimx").resolve()).path for i in range(10))


.. tip::

    The basic idea so far is that all files should have a unique identifies to avoid race conditioning.

Instantiating and Running the Simulations
==================================

.. code-block:: python

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