import os

from apsimNGpy.core.pythonet_config import load_pythonnet
from pathlib import Path
from subprocess import run
from apsimNGpy.core.model_loader import load_apsim_model
from apsimNGpy.core.cs_resources import CastHelper
from apsimNGpy.core.model_tools import find_child
from Models.Core.Run import Runner
CI = load_pythonnet()
from APSIM.Core import Node
import subprocess
out_path = Path.home() / 'Documents/testing_run.apsimx'
if out_path.exists():
    out_path.unlink(missing_ok=True)
model = load_apsim_model('Maize', out_path=out_path)
simulation = find_child(model.Simulations, 'Simulation', "Simulation")
from apsimNGpy.core.config import get_apsim_bin_path, set_apsim_bin_path

#____get currently installed path______
bin_path  = get_apsim_bin_path()
try:
    tr = set_apsim_bin_path(r"C:\Users\rmagala\AppData\Local\Programs\APSIM2025.9.7856.0")
    print(tr)
    runner = Runner(model.IModel)
    errors = runner.Run()
    assert errors is not None
    db = out_path.with_suffix('.db')
    models = CI.bin_path/'Models.exe'
    json_path = CI.bin_path/'Models.runtimeconfig.json'
    env = os.environ.copy()
    os.chdir(CI.bin_path)
    subprocess.run(
        [str(models), str(out_path)],
        check=True,
        cwd=str(CI.bin_path),   # launch from the APSIM bin folder
        env=env
    )
    subprocess.run([str(models), str(out_path)], check=True)
finally:
    isBin = set_apsim_bin_path(bin_path)
    print(isBin)
