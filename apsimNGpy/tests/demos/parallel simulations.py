if True:

    from apsimNGpy.core.marathon import ParallelRunner
    from apsimNGpy.core.apsim import ApsimModel
    from pathlib import Path
    import shutil

    if __name__ == "__main__":
        create_jobs = [ApsimModel('Maize').path for _ in range(1000)] # substitute with real simulation tasks
        Parallel = ParallelRunner(db_path= Path('test.db').resolve(), agg_func=None)
        Parallel.run_all_jobs(create_jobs, n_cores=16, threads=False, clear_db=True)
        df = Parallel.get_simulated_output(axis=0)
        wdr = Path(".").glob("*scratch")
        try:
            [shutil.rmtree(i) for i in wdr]
            print("Deleted scratch work space")
        except PermissionError:
            pass





