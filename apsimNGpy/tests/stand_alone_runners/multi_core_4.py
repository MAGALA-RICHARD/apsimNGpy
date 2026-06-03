import tempfile
from apsimNGpy.core.apsim import ApsimModel
import uuid
from pathlib import Path
from apsimNGpy.core.mult_cores import MultiCoreManager
from loguru import logger

if __name__ == '__main__':
    from sqlalchemy import create_engine
    from apsimNGpy.tests.stand_alone_runners.connection import engine
    logger.info("Starting mult_core tests >> agg_func = mean")
    with tempfile.TemporaryDirectory() as td:
        create_jobs = [ApsimModel('Barley', out_path=Path(td) / f"{i}.apsimx").path for i in range(16)]
        db_path = Path(td) / f"{uuid.uuid4().hex}.db"
        test_agg_db = Path(td) / f"{uuid.uuid4().hex}.db"

        Parallel = MultiCoreManager(db_path=test_agg_db, agg_func='mean')
        Parallel.run_all_jobs(create_jobs, n_cores=12, threads=False, clear_db=False, retry_rate=3, subset=None,
                              ignore_runtime_errors=False)
        df = Parallel.get_simulated_output(axis=0)
        logger.info(df.shape)
        print(len(Parallel.tables))
        Parallel.clear_scratch()

        # test saving to already an existing table
        ve = False
        db_path.unlink(missing_ok=True)
        try:
            try:
                # ___________________first__________________________________
                Parallel.save_tosql(db_path, table_name='results', if_exists='replace')
                # ______________________ then _________________________________
                Parallel.save_tosql(db_path, table_name='results', if_exists='fail')
            except ValueError:
                ve = True
            assert ve == True, 'fail method is not raising value error'

            # ____________test saving by replacing existing table _______________
            ve = False
            try:

                Parallel.save_tosql(db_path, table_name='results', if_exists='replace')
            except ValueError:
                ve = True
            assert ve == False, 'replace method failed'

            # ____________test appending to an existing table _______________
            ve = False
            try:
                Parallel.save_tosql(db_path, table_name='results', if_exists='append')
            except ValueError:
                ve = True
            assert ve == False, 'append method failed'
        finally:
            pass
