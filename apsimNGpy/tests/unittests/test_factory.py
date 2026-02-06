import os
from pathlib import Path
from shutil import copy2, rmtree
from apsimNGpy.starter.starter import is_file_format_modified, CLR
from apsimNGpy.core.config import load_crop_from_disk
from apsimNGpy.starter.cs_resources import CastHelper
from functools import partial
import numpy as np
import pandas as pd

Models = CLR.Models


def mimic_multiple_files(out_file: str | os.PathLike, size: int = 20, mix=True, prefix='__',
                         suffix='__') -> str | os.PathLike:
    """
    Create a directory named <stem of out_file>, write a template .apsimx into it,
    and clone that file `size` times as __0__.apsimx, __1__.apsimx, ...

    Example:
        _mimic_multiple_files('output', size=20) -> creates ./output/ with 20 files.
    """
    out_file = Path(out_file)

    # Directory to hold the clones (named after the stem)
    di = Path(out_file.stem).resolve()

    # Recreate the directory cleanly
    if di.exists():
        if di.is_dir():
            try:
                rmtree(di)
            except PermissionError:
                # As a fallback, try to remove read-only attrs on Windows or skip files in use
                raise
        else:
            di.unlink()
    di.mkdir(parents=True, exist_ok=True)

    # Create a template .apsimx file inside the directory
    template_path = di / "template.apsimx"
    template_path2 = di / "template2.apsimx"
    template = load_crop_from_disk(crop="Maize", out=template_path)
    if mix:
        template2 = load_crop_from_disk(crop="Soybean", out=template_path2)
        template2 = Path(template2)

    # `load_crop_from_disk` may return a str or Path; normalize:
    template = Path(template)

    # Clone the template N times
    if mix:
        size = int(size / 2)
    for i in range(size):
        dst = di / f"{prefix}{i}{suffix}.apsimx"
        copy2(template, dst)
    if mix:
        for i in range(size):
            dst = di / f"_2_{prefix}{i}{suffix}.apsimx"
            copy2(template2, dst)

    # Open the folder on Windows (no-op elsewhere)
    size_out = size if not mix else size * 2
    # print(f"Copied {size_out} files to {di}")
    return di


def create_simulation(name, base_simulation=None):
    """
    Clones a simulation a completely new object from Models.Core.Simulation
    Parameters
    ---------------
    name: str
       new name to give to the simulation object
    base_simulation: Models.Core.Simulation optional default is None
       existing simulation object
    Returns
    ------------
     Models.Core.Simulation object

    """
    if base_simulation is not None:
        node = getattr(base_simulation, 'Node', base_simulation)
        sim_obj = CLR.Node.Clone(node)
        CLR.Node.Rename(sim_obj, name)
        return CastHelper.CastAs[Models.Core.Simulation](sim_obj.Model)
    else:
        sim_obj = Models.Core.Simulation()
        zone = Models.Core.Zone()
        sim_obj.Children.Add(zone)
    sim_obj.Name = name
    return sim_obj


def mock_multiple_simulations(n, base_simulation=None):
    sims = [create_simulation(name=f"sim_{i}", base_simulation=base_simulation) for i in range(n)]
    datastore = Models.Storage.DataStore()
    if not is_file_format_modified():
        return
    if not base_simulation:
        mock_sims = CLR.Node.Create(Models.Core.Simulations())
        mock_sims.AddChild(datastore)
        for s in sims:
            mock_sims.AddChild(s)
        return CastHelper.CastAs[Models.Core.Simulations](mock_sims.Model)
    else:
        mock_sims = Models.Core.Simulations()
        for s in sims:
            mock_sims.Children.Add(s) if hasattr(s, 'Node') else mock_sims.Children.Add(s.Model)
        return mock_sims


pred_data = np.array([
    8469.616, 4668.505, 555.047, 3504.000, 7820.075,
    8823.517, 3587.101, 2939.152, 8379.435, 7370.301
])

obs = np.array([
    8469.616,
    4674.820,
    555.017,
    3504.282,
    7820.120,
    8823.516,
    3802.295,
    2943.070,
    8379.928,
    7393.633

])

years = np.arange(1991, 2001)

obs = pd.DataFrame({
    "year": years,
    "observed": obs,

})

pred = pd.DataFrame({
    "year": years,
    "predicted": pred_data
})


def clone_simulation(self, sim_name, rename, inplace=True):
    """
    Clone an existing simulation and optionally attach it to the current model.

    This method locates a simulation by name, creates a deep clone of its
    underlying APSIM node, renames the cloned simulation, and optionally
    adds it to the model's ``Simulations`` container.

    Parameters
    ----------
    sim_name : str
        Name of the simulation to be cloned.
    rename : str
        New name to assign to the cloned simulation.
    inplace : bool, optional
        If True (default), the cloned simulation is added to the current
        model's ``Simulations`` node. If False, the cloned node is returned
        without being attached to the model tree.

    Returns
    -------
    node : APSIM.Core.Node
        The cloned simulation node.

    Raises
    ------
    ValueError
        If no simulation with the specified name is found.

    Notes
    -----
    When ``inplace=True``, the cloned simulation becomes part of the model
    and will be included in subsequent runs. When ``inplace=False``, the
    caller is responsible for managing or attaching the returned node.
    """
    for s in self.simulations:
        if s.Name == sim_name:
            break
    else:
        raise ValueError("Simulation {} not found".format(sim_name))

    node = CLR.Node.Clone(s.Node) if hasattr(s, 'Node') else CLR.Node.Clone(s)
    CLR.Node.Rename(node, rename)

    if inplace:
        self.Simulations.Children.Add(node.Model)

    return node


if __name__ == "__main__":
    sim = mock_multiple_simulations(n=5)
    from apsimNGpy.core.apsim import ApsimModel

    with ApsimModel('Maize') as m:
        s = m.simulations[0]
        new = s.Node.Clone()
        new.Name = 'new'
        print(new.FileName)
        # s.Name='uu'
        c = CLR.Node.Clone(s.Node)
        CLR.Node.Rename(c, 'new_babe')
        # c.set_FileName(m.path)
        m.Simulations.Children.Add(c.Model)
        m.save()
        # m.preview_simulation()
        m.inspect_file()
        m.edit_model('Models.Manager', 'Sow using a variable rule', Population=4, simulations='new_babe')
        m.run(verbose=True)

        df = m.results
        # mock simulations when base is Models.Core.Simulation object
    sim2 = mock_multiple_simulations(n=5, base_simulation=s)
    print([i.Name for i in sim2.Children])
