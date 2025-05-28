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
from typing import Union
import wrapdisc



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
        self._outcomes = None
        self.labels = []

    def _insert_cache_result(self, *args, result):

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
    def minimize_with_local_solver(self, **kwargs):
        pass

    def __str__(self):
        summary = f"Optimization Problem for APSIM Model: {self.model}\n"
        summary += f"===================================================\n"
        summary += f"Simulation: {self.simulation}\n"
        summary += f"Number of Control Variables: {len(self.control_vars)}\n\n"
        summary += "Control Variables:\n"
        for var in self.control_vars:
            summary += (
                f"  - {var.label} ({type(var.vtype).__name__}): "
                f"model_type={var.model_type}, model_name='{var.model_name}', "
                f"param='{var.parameter_name}'\n"
                f"Results summary:: {self.outcomes}\n"
            )
        return summary

    def __repr__(self):
        return self.__str__()

    @property
    def outcomes(self):
        return self._outcomes

    @outcomes.setter
    def outcomes(self, value):
        self._outcomes = value

    def _evaluate_args(self, *args, **kwargs):
        if not all(isinstance(arg, str) for arg in args):
            raise ValueError("all arguments must be strings")
    def _auto_guess(self, data):
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
    vtype: Union[str, object, wrapdisc.var]
    label: str
    start_value: Union[float, int]
    bounds: tuple[float, int]



