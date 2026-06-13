from asyncio import as_completed
from concurrent.futures import ProcessPoolExecutor

from apsimNGpy.core._multi_core import _inspect_job, IDENTIFICATION
from apsimNGpy.core.apsim import ApsimModel


def change_inputs(job, call_back):
    model, metadata, inputs = _inspect_job(job)
    ID = metadata.get(IDENTIFICATION, None) if metadata else None
    file_name = f"{ID}.apsimx"
    _model = ApsimModel(model, out_path=file_name)
    try:
        if call_back and callable(call_back):
            # there might be additional works that the user wants to enforce
            call_back(_model)
        if inputs:
            # set before running
            for in_put in inputs:
                _model.set_params(**in_put)
        _model.save(file_name=file_name, reload=False)
        yield ID, file_name
    finally:
        del _model


def run_block(jobs, block_size=100):
    from apsimNGpy.parallel.process import custom_parallel
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(change_inputs, job) for job in jobs]

        for future in as_completed(futures):
            job_id, result = future.result()
            print(job_id, result)


