from dataclasses import dataclass, field
from apsimNGpy.core.apsim import ApsimModel
from scipy.optimize import minimize
import numpy as np
from functools import reduce, lru_cache
from collections import OrderedDict
from functools import wraps
from collections import OrderedDict


class SimpleCache:
    def __init__(self, maxsize=None):
        self.cache = OrderedDict()
        self.maxsize = maxsize

    def cache_res(self, *args, out=None, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))

        if key in self.cache:
            return self.cache[key]

        self.cache[key] = out

        if self.maxsize is not None and len(self.cache) > self.maxsize:
            self.cache.popitem(last=False)  # FIFO: remove oldest

    def get(self, *args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        return self.cache.get(key, None)

    def clear(self):
        self.cache.clear()


results = {}


@dataclass
class Problem:
    apsim: ApsimModel
    simulation: str
    controls: list = field(default_factory=list)
    labels: list = field(default_factory=list)
    cache: bool = field(default_factory=bool)
    cache_size: int = field(default_factory=int)

    def __post_init__(self):
        if self.cache:
            cache_res = SimpleCache(maxsize=self.cache_size)

    def add_control(self, model_type, model_name, parameter_name, label=None):
        self.controls.append({
            "model_type": model_type,
            "model_name": model_name,
            "parameter_name": parameter_name,
            "label": label or f"{model_type}_{model_name}_{parameter_name}"
        })

    def setUP(self, x):
        sim = self.apsim.inspect_model('Simulation', fullpath=False)[0]
        edit = self.apsim.edit_model
        for i, varR in enumerate(self.controls):
            print(x)
            edit(
                model_type=varR['model_type'],
                simulations='Simulation',
                model_name=varR['model_name'],
                cacheit=True,
                **{varR['parameter_name']: x[i]}
            )

    def evaluate(self, x):
        x = tuple([np.round(i) for i in x])
        if results.get(x, None):
            return results[x]
        self.setUP(x)
        result = self.apsim.run(verbose=False).results
        emissions = result.Yield  # placeholder
        result = 10000 - emissions.mean()
        results[x] = result
        return result

    def minimize_problem(self, **kwargs):

        x0 = kwargs.pop("x0", [1] * len(self.controls))  # Starting guess
        result = minimize(self.evaluate, x0=x0, **kwargs)

        labels = [c['label'] for c in self.controls]
        result.x_vars = dict(zip(labels, result.x))
        return result


