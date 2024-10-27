from apsimNGpy.core.base_data import LoadExampleFiles, load_default_simulations
model = load_default_simulations(crop = 'maize')
def run(model):
    for _ in [1]:
        model
        model.run("report")
import time
a  = time.perf_counter()
run(model)
b = time.perf_counter()
print(b-a, 'seconds')

from apsimNGpy.config import Config

import apsimNGpy
print(apsimNGpy.__file__)