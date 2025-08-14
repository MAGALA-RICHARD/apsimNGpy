if True:

    from apsimNGpy.core.mult_cores import MultiCoreManager
    from apsimNGpy.core.apsim import ApsimModel
    from pathlib import Path

    if __name__ == "__main__":
        # create some jobs for the demo
        create_jobs = [ApsimModel('Maize').path for _ in range(1000)]  # substitute with real simulation tasks
        # initialize
        task_manager = MultiCoreManager(db_path=Path('test.db').resolve(), agg_func=None)
        # Run all the jobs
        task_manager.run_all_jobs(create_jobs, n_cores=16, threads=False, clear_db=True)
        # get the results
        df = task_manager.get_simulated_output(axis=0)
        # same as
        data = task_manager.results  # defaults is axis =0
