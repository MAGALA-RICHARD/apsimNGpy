from dataclasses import dataclass, field
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
from abc import ABC, abstractmethod
from collections.abc import Iterable
from apsimNGpy.optimizer.optutils import compute_hyper_volume, edit_runner

ArrayLike = Union[np.ndarray, List[float], pd.Series]
from collections import OrderedDict

SING_OBJ_CONT_VAR = 'single-continuous-vars'
SING_OBJ_MIXED_VAR = 'single-mixed-vars'

@lru_cache(maxsize=None)
def get_function_param_names(func):
    """
    Return only the parameter names of a function as a tuple.
    """
    sig = inspect.signature(func)
    return tuple(sig.parameters.keys())


def _evaluate_args(*args, **kwargs):
    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("all arguments must be strings")


class AbstractProblem(ABC):
    def __init__(self, apsim_model, max_cache_size=400, objectives = None, decision_vars=None, **kwargs):
        self.apsim_model = apsim_model
        self._cache = OrderedDict()
        self.max_cache_size = max_cache_size
        self._outcomes = None
        self.editor = edit_runner
        self.decision_vars = decision_vars or []
        self.objectives = objectives or []
        self.optimizer = None
        self.target_parameters = OrderedDict()

    @property
    @abstractmethod
    def optimization_type(self):
        """Must be implemented as a property in subclass"""
        pass
    def _insert_cache_result(self, *args, result):

        args = tuple(args)
        self._cache[args] = result

        if self.max_cache_size is not None and len(
                self._cache) > self.max_cache_size:  # saturation reached according to specified maxsize free space
            self._cache.popitem(last=False)

    def get_cached(self, *args):
        key = tuple(args)

        return self._cache.get(key, None)


    @cache
    def _get_editable_model(self):
        return self.apsim_model

    def clear_cache(self):
        self._cache.clear()

    @abstractmethod
    def extract_bounds(self):
        xl, xu = [], []
        for var in self.decision_vars:
            if var['v_type'] not in {'int', 'float'}:
                raise ValueError(f"Unsupported variable type: {var['v_type']}")
            xl.append(var['bounds'][0])
            xu.append(var['bounds'][1])
        print(xl, xu)
        return xl, xu

    def add_control(self, path: str, *, bounds, v_type, q=None, start_value=None, categories=None, **kwargs):
        """
        Adds a single APSIM parameter to be optimized.

        Parameters
        ----------
        path : str
            APSIM component path.

         v_type : type
            The Python type of the variable. Should be either `int` or `float` for continous variable problem or
            'uniform', 'choice',  'grid',   'categorical',   'qrandint',  'quniform' for mixed variable problem

        start_value : any (type determined by the variable type.
            The initial value to use for the parameter in optimization routines. Only required for single objective optimizations

        bounds : tuple of (float, float), optional
            Lower and upper bounds for the parameter (used in bounded optimization).
            Must be a tuple like (min, max). If None, the variable is considered unbounded or categorical or the algorithm to be used do not support bounds

        kwargs: dict
            One of the key-value pairs must contain a value of '?', indicating the parameter to be filled during optimization.
            Keyword arguments are used because most APSIM models have unique parameter structures, and this approach allows
            flexible specification of model-specific parameters. It is also possible to pass other parameters associated with the model in question to be changed on the fly.


        Returns
        -------
        self : object
            Returns self to support method chaining.

        .. warning::

            Raises a ``ValueError``
                If the provided arguments do not pass validation via `_evaluate_args`.


        .. Note::

            - This method is typically used before running optimization to define which
              parameters should be tuned.

        Example:

        .. code-block:: python

                 from apsimNGpy.core.apsim import ApsimModel
                 from apsimNGpy.core.optimizer import MultiObjectiveProblem
                 runner = ApsimModel("Maize")

                _vars = [
                {'path': '.Simulations.Simulation.Field.Fertilise at sowing', 'Amount': "?", "bounds": [50, 300],
                 "v_type": "float"},
                {'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': "?", 'v_type': 'float',
                 'bounds': [4, 14]}
                 ]
                problem = MultiObjectiveProblem(runner, objectives=objectives, decision_vars=_vars)
                # or
                problem = MultiObjectiveProblem(runner, objectives=objectives, None)
                problem.add_control(
                    **{'path': '.Simulations.Simulation.Field.Fertilise at sowing', 'Amount': "?", "bounds": [50, 300],
                       "v_type": "float"})
                problem.add_control(
                    **{'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': "?", 'v_type': 'float',
                       'bounds': [4, 14]})
        """
        self.apsim_model.check_kwargs(path, **kwargs)
        if not start_value and self.optimization_type in [SING_OBJ_CONT_VAR, SING_OBJ_MIXED_VAR]:
            raise ValueError("start_value must be provided for this problem to proceed")

        to_fill = [k for k, v in kwargs.items() if v in ('?', "")]
        if len(to_fill) != 1:
            raise ValueError("Exactly one parameter must be unspecified with '?' or '' .")

        var_spec = {
            'path': path,
            'bounds': bounds,
            'v_type': v_type,
            'q':q,
            'categories': categories,
            'start_value': start_value,
            'kwargs': kwargs
        }
        tp = to_fill[0]
        self.target_parameters[tp] = var_spec # if the parameter changes, then it is a new control
        # update decissions vars
        self.decision_vars = [self.target_parameters[i] for i in self.target_parameters]

    @abstractmethod
    def evaluate_objectives(self):
        pass



    def __str__(self):
        opt_type = self.optimization_type
        if isinstance(self.objectives, Iterable):
           ob_names = [i.__name__ for i in self.objectives ]
           ob_names = ', '.join(ob_names)
        if callable(self.objectives):
            ob_names = self.objectives.__name__
        else:
            ob_names = 'None'
        summary = f"Optimization Problem for APSIM Model: {self.model}\n"

        summary += f"===================================================\n"
        summary += f"objective_name: {ob_names}\n"
        summary += f"Number of Control Variables: {len(self.decision_vars)}\n"
        summary += "Control Variables:\n"
        for count, var in enumerate(self.decision_vars):
             count += 1
             vard = var.copy()
             vark = vard.pop('kwargs', var).copy()

             data  = vard | vark

             for key, value in data.items():
                if key in self.labels and self.outcomes:
                    x_var = getattr(self.outcomes, 'x_vars')[key]
                    summary += (
                        f"  -variable {count}: {key} = ({value}): optimized_value={x_var}\n "
                    )
                else:
                    x_var = ''
                    summary += (
                        f"  -variable {count}: {key} = ({value}):\n "
                    )
        summary += f"Results summary:: {self.outcomes}\n"
        return summary

    def __repr__(self):
        return self.__str__()
    @property
    def labels(self):
        labels = []
        for var in self.decision_vars:
            vark = var.get('kwargs', var).copy()
            data = var | vark
            for key, value in data.items():
                if value in ['?', ""]:
                 labels.append(key)
        return labels



    @property
    def indicators(self) -> List[str]:
        inds = ['mse', 'mae', 'rmse', 'rrmse', 'r2', 'wia', 'ccc', 'bias', 'slope', 'me', 'hv']
        return [i for i in inds if getattr(self, i, None) is not None]
    @property
    def outcomes(self):
        return self._outcomes

    @outcomes.setter
    def outcomes(self, value):
        self._outcomes = value
    @staticmethod
    def hv(F, reference_point=None, normalize=False, normalization_bounds=None):
        return compute_hyper_volume(F, reference_point=None, normalize=False, normalization_bounds=None)
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
        assert len(actual) == len(predicted), f'{len(actual)} != {len(predicted)}'
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


if __name__ == '__main__':
    pred_data = np.array([
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

    obs = np.array([
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
    val = dict(mse=AbstractProblem.mse(obs, pred_data),
               rmse=AbstractProblem.rmse(obs, pred_data),
               mae=AbstractProblem.mae(obs, pred_data),
               rrmse=AbstractProblem.rrmse(obs, pred_data),
               wia=AbstractProblem.wia(obs, pred_data),
               ccc=AbstractProblem.ccc(obs, pred_data),
               slope=AbstractProblem.slope(obs, pred_data),
               r2=AbstractProblem.r2(obs, pred_data))
    import pprint
    pprint.pprint(val, indent=4, width=4)
