import os.path as osp
import os
import shutil

def check_version(apsim_version):
    path = True if osp.exists(apsim_version) and apsim_version.endswith("bin") and 'APSIM'  in apsim_version else None
    print(path)
    if not path:
        raise ValueError("This is not an apsimx model path")

sh = shutil.which('Models')
check_version(r"C:\Program Files\APSIM2023.11.7349.0\bin")
