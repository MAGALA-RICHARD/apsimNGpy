import os
from pathlib import Path
from shutil import copy2, rmtree
from apsimNGpy.starter.starter import is_file_format_modified, CLR
from apsimNGpy.core.config import load_crop_from_disk
from apsimNGpy.starter.cs_resources import CastHelper

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


def create_simulation(name):
    if is_file_format_modified():
        from starter.cs_resources import CastHelper
    else:
        return
        # creates a Models.Core.Simulations object
    sim = Models.Core.Simulation()
    # add zone
    zone = Models.Core.Zone()
    sim.Children.Add(zone)
    sim.Name = name
    return sim


def mock_multiple_simulations(n):
    sims = map(create_simulation, [f"sim_{i}" for i in range(n)])
    datastore = Models.Storage.DataStore()
    if is_file_format_modified():
        pass
    mock_sims = CLR.Node.Create(Models.Core.Simulations())
    mock_sims.AddChild(datastore)
    for s in sims:
        mock_sims.AddChild(s)
    return CastHelper.CastAs[Models.Core.Simulations](mock_sims.Model)



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

if __name__ == "__main__":
    sim = mock_multiple_simulations(n=5)
