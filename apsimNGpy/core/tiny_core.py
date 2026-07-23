import os
import sys
from pathlib import Path
from apsimNGpy.starter.starter import CLR
from apsimNGpy import ApsimModel
from multiprocessing import Lock
from uuid import uuid4

lock = Lock()


def _assign_edit(model, load):
    simulation_id = load.get('ID')
    payload = load.get('payload')
    # print(f"`simulation_id={simulation_id}Amount={p}`", file=sys.stderr)
    if payload is not None:
        _ = [model.edit_model(**dict(pay)) for pay in payload]
    reports = model.inspect_model('Models.Report', fullpath=False)

    simulation = model[0]
    simulation.Name = f"{simulation_id}"
    _ = [model.edit_model(model_type='Models.Report', model_name=rep,
                          variable_spec=['[Simulation].Name as SimName']) for rep in reports]
    model.save()
    return simulation_id


def edit(load):
    with lock:
        base = load.get('model')
        with ApsimModel(base) as model:
            _assign_edit(model, load)
            return model[0]


def creat_root_in_memory(root_name=None):
    node = CLR.Node.Create(CLR.Models.Core.Simulations())
    if root_name is not None:
        node.Name = root_name
    node.AddChild(CLR.Models.Storage.DataStore())
    return node


def serialize_root_from_memory(root_dir='.', file_name=None):
    root_dir = Path(root_dir).resolve()
    file_name = file_name or f'tmp_{uuid4()}.apsimx'
    out_path = root_dir / file_name
    from apsimNGpy.core.model_loader import save_model_to_file
    node = creat_root_in_memory()
    save_model_to_file(node, out=out_path)
    return out_path


def append_one(simulation, parent):
    pa = getattr(parent, 'Simulations', parent)
    pa = getattr(pa, 'Model', pa)
    pa.Children.Add(simulation)


def edit_simulations(loads, max_worker=20, show_progress=True):
    from apsimNGpy.parallel.process import custom_parallel
    return custom_parallel(edit, loads, ncores=max_worker, use_thread=True, progressbar=show_progress,
                           progress_message='Editing simulations')


def assemble_simulations(simulations, max_workers=20, show_progress=True):
    from apsimNGpy.parallel.process import custom_parallel
    iterables = simulations
    root_sim_file = serialize_root_from_memory()
    model = ApsimModel(root_sim_file)
    try:
        for _ in custom_parallel(append_one, iterables, model, use_thread=True, ncores=max_workers,
                                 progress_message=f'Assembling simulations', progressbar=show_progress):
            pass
        model.save()
        return model
    finally:
        rtp = Path(root_sim_file)
        try:
            rtp.unlink(missing_ok=True)
            rtp.with_suffix('.db').unlink(missing_ok=True)
        except PermissionError:
            pass


def run_batch_simulations(simulations, max_worker=20, reports=None, show_progress=True,):
    model = assemble_simulations(simulations, max_workers=max_worker, show_progress=show_progress)
    model.run(report_name=reports, cpu_count=max_worker)
    return model.results


def create_simulations(load):
    base = load.get('model')
    with ApsimModel(base) as model:
        dis = _assign_edit(model, load)
        model.run(cpu_count=20)
        df = model.results
        df['SimulationID'] = dis
        return df


def run_single(loads):
    import pandas as pd
    data = []
    for load in loads:
        df = create_simulations(load)
        data.append(df)
    return pd.concat(data, ignore_index=True)


def run_single_append_method(loads):
    sims = [edit(ld) for ld in loads]
    root = serialize_root_from_memory()
    with ApsimModel(root) as model:
        _ = [model.append_simulation(simulation=sim) for sim in sims]
        model.run()
        return model.results


if __name__ == '__main__':
    def lod(i):
        return {'model_name': "Fertilise at sowing", "model_type": "Models.Manager",
                'Amount': i}


    ploads = [
        {"model": "Maize", "ID": i, 'payload': [lod(i)]}
        for i in list(range(1, 81, 1))
    ]
    sims = edit_simulations(ploads)
    op = run_batch_simulations(sims, )
    print(op.columns)
    op_mean = (
        op.groupby("SimName")["Yield"]
        .mean()
        .sort_index(ascending=True)
    )

    root = serialize_root_from_memory()
    sdf = run_single(ploads).sort_values(by='SimulationID')
    # sims = edit_simulations(ploads)
    # sdf = append_simulations_with_threads(sims, )

    import numpy as np
    import pandas as pd

    sdf_mean = (
        sdf.groupby("SimName")["Yield"]
        .mean()
        .sort_index(ascending=True)
    )

    # Ensure both results contain the same SimulationIDs
    if not op_mean.index.equals(sdf_mean.index):
        missing_in_op = sdf_mean.index.difference(op_mean.index)
        missing_in_sdf = op_mean.index.difference(sdf_mean.index)

        raise ValueError(
            f"SimulationID mismatch. "
            f"Missing in op: {missing_in_op.tolist()}; "
            f"missing in sdf: {missing_in_sdf.tolist()}"
        )

    # Floating-point-safe comparison
    are_equal = np.allclose(
        op_mean.to_numpy(),
        sdf_mean.to_numpy(),
        rtol=1e-7,
        atol=1e-9,
        equal_nan=True,
    )

    print(f"Means are equal: {are_equal}")
    import pandas as pd

    pp = [{'SimulationID': pl['ID'], **pl['payload'][0]} for pl in ploads]
    amount = pd.DataFrame(pp)
