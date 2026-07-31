from dataclasses import dataclass
from pathlib import Path
from multiprocessing import Lock
from pathlib import Path
from typing import List, Any, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from apsimNGpy import ApsimModel
from apsimNGpy.parallel.process import custom_parallel
from apsimNGpy.starter.starter import CLR

lock = Lock()

_Payload = dict[str, Any]


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


class _SimulationDescription(BaseModel):
    model: Union[str, Path]
    ID: int | str | tuple
    full_path: bool = False
    payload: List[_Payload] = Field(default_factory=list)


def _assign_edit(model, load):
    load = _SimulationDescription.model_validate(load)
    simulation_id = load.ID
    payload = load.payload
    simulation_obj = model[0]
    new_sim_name = f"{simulation_id}"
    simulation_obj.Name = new_sim_name
    # print(f"`simulation_id={simulation_id}Amount={p}`", file=sys.stderr)
    if payload is not None:
        for p in payload:
            p['simulations'] = new_sim_name
        if not load.full_path:

            _ = [model.edit_model(**dict(pay)) for pay in payload]
        else:
            _ = [model.set_params(pay) for pay in payload]
    reports = model.inspect_model('Models.Report', fullpath=False)

    _ = [model.edit_model(model_type='Models.Report', model_name=rep,
                          variable_spec=['[Simulation].Name as SimName']) for rep in reports]
    model.save()
    return simulation_id


def generate_simulation(load, select=None):
    # validate it:
    load = _SimulationDescription.model_validate(load)
    base = load.model
    with ApsimModel(base) as model:
        _assign_edit(model, load)
        if select is not None:
            return model[select]
        return model[0]


def creat_root_in_memory(root_name=None):
    node = CLR.Node.Create(CLR.Models.Core.Simulations())
    if root_name is not None:
        node.Name = root_name
    node.AddChild(CLR.Models.Storage.DataStore())
    return node


def append_one(apsim_simulation, parent):
    with lock:
        pa = getattr(parent, 'Simulations', parent)
        pa = getattr(pa, 'Model', pa)
        pa.Children.Add(apsim_simulation)


@dataclass(slots=True)
class Simulation:
    # for keeping the root uniform from the provided models
    parent: Any = None
    root: Any = None

    def _generate_sim(self, load, select=None):
        # validate it:
        load = _SimulationDescription.model_validate(load)
        base = load.model

        if self.parent is None:
            root = serialize_root(base_file=load.model)
            self.parent = ApsimModel(root)
        with ApsimModel(base) as model:
            model_name = model[0].Name
            _assign_edit(model, load)
            if select is not None:
                return model[select]
            return model[0]

    def append(self, load, select=None):
        sim = self._generate_sim(load, select)
        parent = self.parent
        with lock:
            pa = getattr(parent, 'Simulations', parent)
            pa = getattr(pa, 'Model', pa)
            pa.Children.Add(sim)


def edit_simulations(loads, max_worker=20, show_progress=True, ):
    return custom_parallel(generate_simulation, loads, ncores=max_worker, use_thread=True,
                           progressbar=show_progress,
                           progress_message='Generating simulations')


def _assemble_simulations(simulation_descriptions, simulation_editor, max_workers=20, show_progress=True):
    from apsimNGpy.parallel.process import custom_parallel

    try:
        for _ in custom_parallel(simulation_editor.append, simulation_descriptions, use_thread=True, ncores=max_workers,
                                 progress_message=f'Assembling simulations', progressbar=show_progress):
            pass

        model = simulation_editor.parent
        if model is not None:
            model.save()
            return model
    finally:
        if simulation_editor.root:
            rtp = Path(simulation_editor.root)
            try:
                rtp.unlink(missing_ok=True)
                rtp.with_suffix('.db').unlink(missing_ok=True)
            except PermissionError:
                pass


def _run_batch_simulations(simulation_descriptions, max_worker=20, reports=None, show_progress=True):
    simulation_editor = Simulation()
    model = _assemble_simulations(simulation_descriptions, max_workers=max_worker, show_progress=show_progress,
                                  simulation_editor=simulation_editor)
    model.run(report_name=reports, cpu_count=max_worker)
    return model.results


if __name__ == '__main__':
    simulation = _SimulationDescription(
        model="Maize",
        ID=[1],
        payload=[{'Amount': 1, 'others': {}}]
    )
