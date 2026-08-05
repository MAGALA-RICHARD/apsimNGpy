from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.starter.starter import CLR
from pathlib import Path
from uuid import uuid4


def creat_root_in_memory(root_name=None):
    node = CLR.Node.Create(CLR.Models.Core.Simulations())
    if root_name is not None:
        node.Name = root_name
    node.AddChild(CLR.Models.Storage.DataStore())
    return node


def get_base_simulation(model, base_name):
    simulations = [simulation.Name for simulation in model]

    if isinstance(base_name, int):
        if 0 <= base_name < len(model):
            return model[base_name]

        raise IndexError(
            f"Simulation index {base_name} is out of range. "
            f"Valid indices are 0 to {len(model) - 1}."
        )

    if isinstance(base_name, str):
        if base_name in simulations:
            index = simulations.index(base_name)
            return model[index]

        raise KeyError(
            f"Simulation {base_name!r} is not available. "
            f"Available simulations: {simulations}"
        )

    raise TypeError(
        "base_name must be a simulation name or integer index, "
        f"not {type(base_name).__name__}."
    )


def serialize_root(root_dir='.', file_name=None, base_file=None):
    if base_file:
        model = ApsimModel(base_file)
        children = list(model.Simulations.GetChildren())
        for Child in children:
            typ = Child.GetType()
            if typ not in (CLR.Models.Storage.DataStore().GetType(), CLR.Models.Core.Folder().GetType()):
                model.Simulations.RemoveChild(Child)
        model.save()

        return model.path
    else:
        root_dir = Path(root_dir).resolve()
        file_name = file_name or f'tmp_{uuid4()}.apsimx'
        out_path = root_dir / file_name
        from apsimNGpy.core.model_loader import save_model_to_file
        node = creat_root_in_memory()
        save_model_to_file(node, out=out_path)
        return out_path


def _filter_out_simulation(model: ApsimModel):
    children = list(model.Simulations.GetChildren())
    datastore_type = CLR.Models.Storage.DataStore().GetType()
    for Child in children:
        typ = Child.GetType()
        if typ not in {datastore_type,
                       CLR.Models.Core.Folder().GetType()}:
            model.Simulations.RemoveChild(Child)
            # Add datastore here
    sim_children_types = [i.GetType() for i in model.Simulations.Children]
    if datastore_type not in sim_children_types:
        model.Simulations.Children.Add(CLR.Models.Storage.DataStore())


def get_root_model(base, simulation_name):
    'returns only models at the at root of Models.Core.Simulation like replacement folder, datastore '
    match base:
        case str() | Path():
            model = ApsimModel(base)
            sim = get_base_simulation(model, simulation_name)
            _filter_out_simulation(model)
            model.save()
            return dict(root=model, simulation=sim)

        case ApsimModel():
            sim = get_base_simulation(base, simulation_name)
            _filter_out_simulation(base)
            base.save()
            return dict(root=base, simulation=sim)

        case _:
            raise TypeError(
                f"Expected a str, Path, or ApsimModel, "
                f"got {type(base).__name__}"
            )


def create_factor_table(name_column='FactorFromFile', **parameters, ):
    """parameter_path: and values"""
    from pandas import DataFrame
    df = DataFrame(parameters)
    df[name_column] = [str(i) for i in range(1, df.shape[0] + 1)]
    return df
