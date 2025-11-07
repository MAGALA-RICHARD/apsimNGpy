from apsimNGpy.core.core import CoreModel
from System import GC
from pathlib import Path
with CoreModel('Maize') as model:
    model.run(verbose=True)
    GC.Collect()
    GC.WaitForPendingFinalizers()
    print('Path exists before exit:', Path(model.path).exists())
    print('datastore Path exists before exit:', Path(model.datastore).exists())
print('Path exists after exit:', Path(model.path).exists())
print('datastore Path exists after exit:', Path(model.datastore).exists())