import gc
import time

from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.parallel.data_manager import write_results_to_sql
import numpy as np
import multiprocessing as mp
from apsimNGpy.parallel.executors import custom_parallel_chunks
from apsimNGpy.exceptions import ApsimRuntimeError
from apsimNGpy.core_utils.database_utils import read_db_table

class mo: pass


@write_results_to_sql(db_path="dm.db", table="Report")
def worker(nit):
    def inside_worker(n):
        model = mo()
        try:
            # ______________init model_________________
            model = ApsimModel('Maize', out_path=f"__{n}.apsimx")
            # do any edits to the model as you wish

            model.edit_model("Models.Manager", model_name="Fertilise at sowing", Amount=float(n))
            model.run(report_name="Report", verbose=False)
            df = model.results
            df["nitrogen rate"] = str(n)
            # ___________cleanup____________
            # return results
            return df
        finally:
            if isinstance(model, ApsimModel):
                model.clean_up(db=True, coerce=True)

    try:
        return inside_worker(nit)
    except ApsimRuntimeError:
        return inside_worker(nit)


def main():
    _iteraB = (i for i in np.arange(1, 340, 0.02))
    for _ in custom_parallel_chunks(worker, _iteraB, ncores=16, n_chunks=500):
        pass


if __name__ == '__main__':
    from apsimNGpy.parallel.process import custom_parallel
    from apsimNGpy.parallel.data_manager import chunker

    # df =read_db_table("DATAB.db", report_name="Report")
    # jjs = (ApsimModel("Maize", out_path=f"_{idn}").path for idn in range(200))
    iteraB = (i for i in np.arange(1, 340, 0.2))
    ch = chunker(iteraB, chunk_size=500)
    main()
