from pathlib import Path

import requests
from apsimNGpy.core_utils.database_utils import read_db_table
from apsimNGpy import load_crop_from_disk

ap = load_crop_from_disk('Maize', out='soybean.apsimx')
import time

a = time.perf_counter()
for i in range(10):
    data = {
        "model_path": 'str(ap), str(ap)',
        "exe_path": r"D:\My_BOX\Box\PhD thesis\Objective two\morrow plots 20250821\APSIM2025.8.7844.0\bin\Models.exe",
        "timeout_sec": 7200,
        "extra_args": ["/Parallel", "18"],
    }
    r = requests.post("http://localhost:8000/run", json=data, timeout=7205)
    print(r.text if r.ok else r.text)
b = time.perf_counter()
print(b - a, 'seconds')
df = read_db_table(r'D:\package\apsimNGpy\apsimNGpy\cli\work\apsim_ge6g05w5\soybean.db', 'Report')
