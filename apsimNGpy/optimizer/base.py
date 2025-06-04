from dataclasses import dataclass, field
from apsimNGpy.core.apsim import ApsimModel
from scipy.optimize import minimize
import numpy as np
from functools import reduce, lru_cache, cache
from collections import OrderedDict
from functools import wraps
from collections import OrderedDict
from abc import ABC, abstractmethod
from wrapdisc.var import ChoiceVar, GridVar, QrandintVar, QuniformVar, RandintVar, UniformVar
import inspect
from typing import Union
import wrapdisc
from numpy import floating
from scipy.stats import norm, linregress
from typing import Union, List, Dict, Any
import pandas as pd
ArrayLike = Union[np.ndarray, List[float], pd.Series]


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

    @cache
    def _insert_apsim_model(self, model:str, outpath=None, **kwargs):
        return ApsimModel(model, out_path=outpath)

    @cache
    def _get_editable_model(self):
        return self.model

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

    @staticmethod
    def rrmse(actual, predicted) -> float:
        return AbstractProblem.rmse(actual, predicted) / np.mean(actual)

    @staticmethod
    def wia(actual, predicted) -> float:
        mean_obs = np.mean(actual)
        numerator = np.sum((predicted - actual) ** 2)
        denominator = np.sum((np.abs(predicted - mean_obs) + np.abs(actual - mean_obs)) ** 2)
        return 1 - numerator / denominator

    @staticmethod
    def mse(actual, predicted) -> floating[Any]:
        return np.mean((actual - predicted) ** 2)

    @staticmethod
    def rmse(actual, predicted) -> float:
        return np.sqrt(AbstractProblem.mse(actual, predicted))

    @staticmethod
    def mae(actual, predicted) -> float:
        return np.mean(np.abs(actual - predicted))

    @staticmethod
    def bias(actual, predicted) -> floating[Any]:
        return np.mean(actual - predicted)

    @staticmethod
    def slope(actual, predicted) -> float:
        slope, *_ = linregress(actual, predicted)
        return slope

    @staticmethod
    def r2(actual, predicted) -> float:
        _, _, r_value, _, _ = linregress(actual, predicted)
        return r_value ** 2

    @staticmethod
    def me(actual, predicted) -> float:
        mse_pred = np.mean((predicted - actual) ** 2)
        mse_obs = np.mean((actual - np.mean(actual)) ** 2)
        return 1 - mse_pred / mse_obs

    @staticmethod
    def rho_ci(actual, predicted, ci: str = "z-transform", conf_level: float = 0.95, na_rm: bool = False) -> Dict:
        dat = pd.DataFrame({'x': actual, 'y': predicted}).dropna() if na_rm else pd.DataFrame(
            {'x': actual, 'y': predicted})
        k = len(dat)
        r = dat['x'].corr(dat['y'])

        yb, xb = dat['y'].mean(), dat['x'].mean()
        sy2 = dat['y'].var() * (k - 1) / k
        sx2 = dat['x'].var() * (k - 1) / k
        sd1, sd2 = dat['y'].std(), dat['x'].std()

        sxy = r * np.sqrt(sx2 * sy2)
        p = 2 * sxy / (sx2 + sy2 + (yb - xb) ** 2)
        v, u = sd1 / sd2, (yb - xb) / ((sx2 * sy2) ** 0.25)
        c_b = p / r
        zv = norm.ppf(1 - (1 - conf_level) / 2)

        sep = np.sqrt(((1 - r ** 2) * p ** 2 * (1 - p ** 2) / r ** 2 +
                       (2 * p ** 3 * (1 - p) * u ** 2 / r) -
                       0.5 * p ** 4 * u ** 4 / r ** 2) / (k - 2))

        if ci == "z-transform":
            t = np.log((1 + p) / (1 - p)) / 2
            set_ = sep / (1 - p ** 2)
            llt = t - zv * set_
            ult = t + zv * set_
            llt, ult = [(np.exp(2 * val) - 1) / (np.exp(2 * val) + 1) for val in (llt, ult)]
            ci_result = pd.DataFrame({'est': [p], 'lwr.ci': [llt], 'upr.ci': [ult]})
        else:
            ci_result = pd.DataFrame({'est': [p], 'lwr.ci': [p - zv * sep], 'upr.ci': [p + zv * sep]})

        delta = dat['x'] - dat['y']
        rmean = dat.mean(axis=1)
        blalt = pd.DataFrame({'mean': rmean, 'delta': delta})

        return {'rho_c': ci_result, 's_shift': v, 'l_shift': u, 'C_b': c_b, 'blalt': blalt}

    @staticmethod
    def ccc(actual, predicted) -> float:
        return AbstractProblem.rho_ci(actual, predicted)['rho_c']['est'].iloc[0]

@dataclass(slots=True, frozen=True)
class VarDesc:
    model_type: str
    model_name: str
    parameter_name: str
    vtype: Union[str, object, wrapdisc.var]
    label: str
    start_value: Union[float, int]
    bounds: tuple[float, int]

predicted = np.array([
        8469.616,
        4668.505,
        555.047,
        3504.000,
        7820.075,
        8823.517,
        3587.101,
        2939.152,
        8379.435,
        7370.301
    ])
def g_ran_observed_variables(predicted, dist='normal'):


    # Calculate mean and standard deviation of predicted
    mean_pred = np.mean(predicted)
    std_pred = np.std(predicted)

    # Generate observed values from a normal distribution with same mean and std
    np.random.seed(42)  # for reproducibility
    if dist.lower() == 'normal':
      return np.random.normal(loc=mean_pred, scale=std_pred, size=predicted.shape)
    if dist.lower() == 'uniform':
        return np.random.uniform(low=np.min(predicted), high=np.max(predicted), size=predicted.shape)
if __name__ == '__main__':
    obs =  np.array([
        7000.0,
        5000.505,
        1000.047,
        3504.000,
        7820.075,
        7000.517,
        3587.101,
        4000.152,
        8379.435,
        4000.301
    ])
    val = dict(mse=AbstractProblem.mse(obs, predicted),
    rmse =AbstractProblem.rmse(obs, predicted),
    mae= AbstractProblem.mae(obs, predicted),
    rrmse = AbstractProblem.rrmse(obs, predicted),
    wia = AbstractProblem.wia(obs, predicted),
    ccc= AbstractProblem.ccc(obs, predicted),
    slope = AbstractProblem.slope(obs, predicted),
    r2 = AbstractProblem.r2(obs, predicted))
    print(val)