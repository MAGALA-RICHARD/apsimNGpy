#
from apsimNGpy.core.config import apsim_bin_context, configuration
from apsimNGpy.core.config import load_crop_from_disk
from pathlib import Path
import os, sys
print('starting apsim_bin_context.py')

if __name__ == "__main__":
    from apsimNGpy.core.apsim import ApsimModel

    with apsim_bin_context(apsim_bin_path=r"C:\Users\rmagala\AppData\Local\Programs\APSIM2025.12.7939.0\bin") as bin:

        from apsimNGpy.core.core import CoreModel

        model =CoreModel('Maize', out_path='cc.apsimx')
        CoreModel(model.path)
        print(configuration.bin_path)


        print(model.Simulations.ApsimVersion)
    ap = os.path.realpath('maizeTT.apsimx')
    try:

        maize = load_crop_from_disk('Maize', out=ap)
        print(f'path exists') if os.path.exists(ap) else print('file does not exist')
    finally:
        try:
            Path(ap).unlink(missing_ok=True)
            print('path is cleaned up')
        except PermissionError:
            pass
