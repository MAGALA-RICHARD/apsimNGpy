#
"""
Testing requirements
====================

.. note::

   Running this test script requires that a ``.env`` file is defined either
   in the **root directory of the unit tests** or in the **same directory
   where the script is located**.

   The ``.env`` file must explicitly define the APSIM versions required for
   testing. For example:

   - ``7939`` = ``C:/Program Files/APSIM2025.2.7939.0/bin``
   - ``7672`` = ``C:/Program Files/APSIM2025.2.7672.0/bin``

   Additional APSIM versions may be specified later.

   These environment variables are used by the test framework to locate
   the appropriate APSIM ``bin`` directories at runtime.

"""
from apsimNGpy.core.config import apsim_bin_context, configuration, load_crop_from_disk

from pathlib import Path
import os, sys
import dotenv
dotenv.load_dotenv()

apsim_bin_7939 = os.getenv('7939')
apsim_bin_7672 =os.getenv('7672')
print('starting apsim_bin_context.py')

if __name__ == "__main__":
    #

    from apsimNGpy.core.config import configuration

    print(configuration.bin_path, '\n')
    sys_before= set(sys.path)

    from apsimNGpy.core.apsim import ApsimModel
    sys_after= set(sys.path)

    print('end')
    def im():
        from apsimNGpy.core.apsim import ApsimModel
        with ApsimModel('Maize') as model:
            print(model.Simulations.ApsimVersion)
        return True

    #sys.path.remove(r'C:\\Program Files\\dotnet\\shared\\Microsoft.NETCore.App\\9.0.0\\')
    with apsim_bin_context(apsim_bin_path=apsim_bin_7939) as bin:

        from apsimNGpy.core.core import CoreModel

        model = CoreModel('Maize', out_path='cc.apsimx')
        CoreModel(model.path)
        print(configuration.bin_path, 'first')

    with apsim_bin_context(
            apsim_bin_path=apsim_bin_7672):
        from apsimNGpy.core.core import CoreModel

        model = CoreModel('Maize', out_path='cc.apsimx')
        CoreModel(model.path)
        print(configuration.bin_path, 'second')

        print(model.Simulations.ApsimVersion)
    im()
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
