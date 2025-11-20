"""
Evaluate predicted vs. observed data using statistical and mathematical metrics.
For detailed metric definitions, see Archontoulis et al. (2015).
"""

__all__ = ['Validate']

import numpy as np
import pandas as pd
from attr import dataclass
from scipy.stats import norm, linregress
from typing import Union, List, Dict


ArrayLike = Union[np.ndarray, List[float], pd.Series]


@dataclass
class Validate:
    """
    Compares predicted and observed values using various statistical metrics.
    """

    actual: ArrayLike
    predicted: ArrayLike

    METRICS = ['RMSE', 'MAE', 'MSE', 'RRMSE', 'bias', 'ME', 'WIA', 'R2', 'CCC', 'slope']

    def __post_init__(self):
        self.actual = np.asarray(self.actual)
        self.predicted = np.asarray(self.predicted)
        self.obs_mean = np.mean(self.actual)
        self.pred_mean = np.mean(self.predicted)
        self.std_actual = np.std(self.actual)
        self.std_predicted = np.std(self.predicted)
        assert len(self.actual) == len(self.predicted), "Predicted and actual arrays must have the same length."

    def RRMSE(self) -> float:
        rmse = self.RMSE()
        return rmse / np.mean(self.actual)

    def WIA(self) -> float:
        mean_obs = np.mean(self.actual)
        numerator = np.sum((self.predicted - self.actual) ** 2)
        denominator = np.sum((np.abs(self.predicted - mean_obs) + np.abs(self.actual - mean_obs)) ** 2)
        return 1 - numerator / denominator

    def MSE(self) -> float:
        return np.mean((self.actual - self.predicted) ** 2)

    def RMSE(self) -> float:
        return np.sqrt(self.MSE())

    def MAE(self) -> float:
        return np.mean(np.abs(self.actual - self.predicted))

    def BIA(self) -> float:
        return np.mean(self.actual - self.predicted)

    def SLOPE(self) -> float:
        slope, *_ = linregress(self.actual, self.predicted)
        return slope

    def R2(self) -> float:
        _, _, r_value, _, _ = linregress(self.actual, self.predicted)
        return r_value ** 2

    def ME(self) -> float:
        mse_pred = np.mean((self.predicted - self.actual) ** 2)
        mse_obs = np.mean((self.actual - np.mean(self.actual)) ** 2)
        return 1 - mse_pred / mse_obs

    def CCC(self) -> float:
        return self.rho_ci()['rho_c']['est'].iloc[0]

    def rho_ci(self, ci: str = "z-transform", conf_level: float = 0.95, na_rm: bool = False) -> Dict:
        dat = pd.DataFrame({'x': self.actual, 'y': self.predicted}).dropna() if na_rm else pd.DataFrame({'x': self.actual, 'y': self.predicted})
        k = len(dat)
        r = dat['x'].corr(dat['y'])

        yb, xb = dat['y'].mean(), dat['x'].mean()
        sy2 = dat['y'].var() * (k - 1) / k
        sx2 = dat['x'].var() * (k - 1) / k
        sd1, sd2 = dat['y'].std(), dat['x'].std()

        sxy = r * np.sqrt(sx2 * sy2)
        p = 2 * sxy / (sx2 + sy2 + (yb - xb) ** 2)
        v, u = sd1 / sd2, (yb - xb) / ((sx2 * sy2) ** 0.25)
        C_b = p / r
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

        return {'rho_c': ci_result, 's_shift': v, 'l_shift': u, 'C_b': C_b, 'blalt': blalt}

    def evaluate(self, metric: str = 'RMSE') -> float:
        metrics_lower = {m.lower() for m in self.METRICS}
        assert metric.lower() in metrics_lower, f"Metric '{metric}' is not supported."

        return getattr(self, metric)()

    def evaluate_all(self, verbose: bool = False) -> Dict[str, float]:
        results = {metric: getattr(self, metric)() for metric in self.METRICS}
        if verbose:
            for k, v in results.items():
                print(f"{k}: {v:.4f}")
        return results


if __name__ == "__main__":
    x_data = np.array([1.2, 2.4, 3.6, 4.8, 5.0])
    y_data = np.array([2.0, 3.5, 4.2, 5.7, 6.0])

    validator = Validate(x_data, y_data)
    all_metrics = validator.evaluate_all(verbose=True)
