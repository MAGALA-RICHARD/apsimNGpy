import sys
from pathlib import Path

from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core._tiny_core import _assign_edit, generate_simulation, serialize_root
from apsimNGpy.core.tiny_core import run_batch_simulations, SimulationDescription


def test_SimulationDescription():
    _ = SimulationDescription(
        model="Maize",
        ID=[1],
        payload=[{'Amount': 1, 'others': {}}]
    )
    _ = SimulationDescription(
        model="Maize",
        ID={1},
        payload=[{'Amount': 1, 'others': {}}]
    )
    _ = SimulationDescription(
        model="Maize",
        ID='sim-001',
        payload=[{'Amount': 1, 'others': {}}]
    )


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
    sims = [generate_simulation(ld) for ld in loads]
    root = serialize_root()
    with ApsimModel(root) as model:
        _ = [model.append_simulation(simulation=sim) for sim in sims]
        model.run()
        return model.results


def lod(i):
    return {'model_name': "Fertilise at sowing", "model_type": "Models.Manager",
            'Amount': i}


if __name__ == '__main__':
    test_SimulationDescription()
    p_loads = [
        {"model": "Maize", "ID": f"sim-{i}", 'payload': [lod(i)]}
        for i in list(range(1, 30, 1))
    ]
    ps = [SimulationDescription(**d) for d in p_loads]

    op = run_batch_simulations(simulation_descriptions=p_loads, )

    op_mean = (
        op.groupby("SimName")["Yield"]
        .mean()
        .sort_index(ascending=True)
    )

    root = serialize_root()
    sdf = run_single(p_loads).sort_values(by='SimulationID')
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
    def evaluate(*arg):
        are_equal = np.allclose(
            arg[0].to_numpy(),
            arg[1].to_numpy(),
            rtol=1e-7,
            atol=1e-9,
            equal_nan=True,
        )
        print(f"Means are equal: {are_equal}", file=sys.stderr)
        return are_equal


    evaluate(op_mean, sdf_mean)
    print('Running with SimulationDescriptions', file=sys.stderr)
    op = run_batch_simulations(simulation_descriptions=ps, )

    op_mean = (
        op.groupby("SimName")["Yield"]
        .mean()
        .sort_index(ascending=True)
    )
    evaluate(op_mean, sdf_mean)
    fps = Path(".").glob('*tmp_*')
    _ = [i.unlink() for i in fps if i.suffix != '.py']
