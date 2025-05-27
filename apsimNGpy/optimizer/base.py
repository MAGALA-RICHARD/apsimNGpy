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
import inspect


@lru_cache(maxsize=None)
def get_function_param_names(func):
    """
    Return only the parameter names of a function as a tuple.
    """
    sig = inspect.signature(func)
    return tuple(sig.parameters.keys())


class AbstractProblem(ApsimModel):
    def __init__(self, model, max_cache_size=None):
        super().__init__(model)
        self._cache = OrderedDict()
        self.max_cache_size = max_cache_size

    def insert_cache_result(self, *args, result):

        args  =tuple(args)
        self._cache[args] = result

        if self.max_cache_size is not None and len(self._cache) > self.max_cache_size: # saturation reached according to specified maxsize free space
            self._cache.popitem(last=False)

    def get_cached(self, *args):
        key = tuple(args)
        return self._cache.get(key, None)

    def clear_cache(self):
        self._cache.clear()
    @abstractmethod
    def add_control(self):
        pass
    @abstractmethod
    def evaluate(self, x):
        pass

    @abstractmethod
    def minimize_problem(self, **kwargs):
        pass

    def _evaluate_args(self, *args, **kwargs):
        if not all(isinstance(arg, str) for arg in args):
            raise ValueError("all arguments must be strings")
    def auto_guess(self, data):
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

@dataclass(slots=True, frozen=True)
class VarDesc:
    model_type: str
    model_name: str
    parameter_name: str
    vtype: Union[str, object]
    label: str
    bounds: Tuple[float, int]
    start_value: Union[float, int]


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