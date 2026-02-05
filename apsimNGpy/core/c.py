from pathlib import Path

from apsimNGpy.core.core import CoreModel

with CoreModel('Maize') as model:
    model.run(verbose=True)

    print('Path exists before exit:', Path(model.path).exists())
    print('datastore Path exists before exit:', Path(model.datastore).exists())
print('Path exists after exit:', Path(model.path).exists())
print('datastore Path exists after exit:', Path(model.datastore).exists())