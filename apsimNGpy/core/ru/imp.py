import shutil
from pathlib import Path
import sys

base = Path(__file__).parent / 'target/maturin/apsim_runner.dll'
xc = Path(sys.executable).parent
import os
from apsimNGpy.core_utils.database_utils import read_db_table

os.startfile(str(xc))
import apsim_runner
from apsimNGpy import configuration
from apsimNGpy.core.runner import APSIM_EXEC
from apsimNGpy import load_crop_from_disk
import time

out = Path(r'D:/')
maize = load_crop_from_disk('Maize', out='out.apsimx')
dp = out / 'temp'
dp.mkdir(parents=True, exist_ok=True)
crops = [load_crop_from_disk('Soybean', out=dp / f'i__{i}.apsimx') for i in range(400)]
try:
    a = time.perf_counter()
    ap = apsim_runner.run_apsim_by_path([str(i) for i in crops], str(APSIM_EXEC), n_cores=12, verbose=True)
    b = time.perf_counter()
    df = [read_db_table(crop.with_suffix('.db'), 'Report') for crop in crops]
    print(b - a, 'seconds')
finally:
    # Path(crop).unlink(missing_ok=True)
    # Path(crop).with_suffix('.db').unlink(missing_ok=True)
    shutil.rmtree(str(dp), ignore_errors=True)
