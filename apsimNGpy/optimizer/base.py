from dataclasses import dataclass, field
from apsimNGpy.core.apsim import ApsimModel
from scipy.optimize import minimize
import numpy as np
from functools import reduce, lru_cache
from collections import OrderedDict
from functools import wraps
from collections import OrderedDict
from abc import ABC, abstractmethod
from wrapdisc.var import ChoiceVar, GridVar, QrandintVar, QuniformVar, RandintVar, UniformVar
class AbstractProblem(ABC):
    def __init__(self, max_cache_size=None):
        self._cache = OrderedDict()
        self.max_cache_size = max_cache_size

    def insert_cache_result(self, result=None, *args,  **kwargs):
        key = (args, tuple(sorted(kwargs.items())))

        if key in self._cache:
            return self._cache[key]

        self._cache[key] = result

        if self.max_cache_size is not None and len(self._cache) > self.max_cache_size: # saturation reached according to specified maxsize free space
            self._cache.popitem(last=False)

    def get_cached(self, *args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        return self._cache.get(key, None)

    def clear_cache(self):
        self._cache.clear()

    @abstractmethod
    def evaluate(self, x):
        pass

    @abstractmethod
    def minimize_problem(self, **kwargs):
        pass

    def _evaluate_args(self, main_param, params, label, var_desc):
        assertion_msg = 'params  must be a  '
        if not isinstance(params, dict):
            raise ValueError(assertion_msg)
        if not isinstance(label, str):
            raise ValueError('label must be a string')
        if not isinstance(main_param, str):
            raise ValueError('main param must be defined as a string')
        try:
            # CHECK IF UPDATOR IS A valid attribute from ApsimModel
            getattr(ApsimModel, updater)
        except AttributeError as e:
            raise AttributeError(f'{updater} is not a valid method for updating parameters')

    def auto_guess(data):
        if isinstance(data, ChoiceVar):
            sample_set = np.random.choice(data.categories, size=1)[0]
        elif isinstance(data, GridVar):
            sample_set = np.random.choice(data.values, size=1)[0]
        elif isinstance(data, (QrandintVar, RandintVar, QuniformVar)):
            sample_set = data.lower
        elif isinstance(data, UniformVar):
            if len(data.bounds) == 1:
                bounds = data.bounds[0]
            else:
                bounds = data.bounds
            sample_set = np.random.uniform(bounds[0], bounds[1], size=1)[0]
        else:
            raise ValueError(f'data: {type(data)} not supported')
        return sample_set

class OptimizationProblem:

    def __init__(self, problem, args, kwargs) -> None:
        super().__init__()
        self.problem = problem
        self.args = args
        self.kwargs = kwargs

    def __call__(self, x):
        out = dict()
        self.problem._evaluate(x, out, *self.args, **self.kwargs)
        return out