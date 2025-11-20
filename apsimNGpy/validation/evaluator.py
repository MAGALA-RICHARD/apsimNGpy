"""
Evaluate predicted vs. observed data using statistical and mathematical metrics.

Implements standard model evaluation metrics used in crop modeling and other
environmental simulation contexts. For detailed metric definitions, see:

    Archontoulis, S. V., & Miguez, F. E. (2015).
    Nonlinear regression models and applications in agricultural research.
    *Agronomy Journal*, 107(2), 786–798.
"""

__all__ = ["Validate"]

import numpy as np
import pandas as pd
from attr import dataclass
from scipy.stats import norm, linregress
from typing import Union, List, Dict, Any

ArrayLike = Union[np.ndarray, List[float], pd.Series]


@dataclass
class Validate:
    """
    Compare predicted and observed values using statistical performance metrics.

    Parameters
    ----------
    actual : ArrayLike
        Observed (measured) values.
    predicted : ArrayLike
        Model-predicted values of the same length as `actual`.

    Notes
    -----
    This class provides a consistent interface for evaluating model performance
    using commonly used metrics such as RMSE, MAE, R², Willmott’s Index of Agreement,
    and the Concordance Correlation Coefficient (CCC).

    Available metrics
    -----------------
    | Metric  | Description                          | Goal / Direction | Sign |
    | :------- | :----------------------------------- | :---------------- | :---- |
    | **RMSE** | Root Mean Square Error               | Smaller is better | `-1` |
    | **MAE**  | Mean Absolute Error                  | Smaller is better | `-1` |
    | **MSE**  | Mean Square Error                    | Smaller is better | `-1` |
    | **RRMSE**| Relative RMSE                        | Smaller is better | `-1` |
    | **bias** | Mean Bias                            | Close to 0        | `-1` |
    | **ME**   | Modeling Efficiency (NSE)            | Larger is better  | `+1` |
    | **WIA**  | Willmott’s Index of Agreement        | Larger is better  | `+1` |
    | **R2**   | Coefficient of Determination         | Larger is better  | `+1` |
    | **CCC**  | Concordance Correlation Coefficient  | Larger is better  | `+1` |
    | **slope**| Regression slope                     | Close to 1        | `+1` |

    Examples
    --------
    .. code-block:: python

        from apsimNGpy.optimizer.problems.validation import Validate
        import numpy as np

        obs = np.array([1.2, 2.4, 3.6, 4.8, 5.0])
        pred = np.array([2.0, 3.5, 4.2, 5.7, 6.0])

        val = Validate(obs, pred)
        print(val.RMSE())
        print(val.evaluate_all(verbose=True))
    """

    actual: ArrayLike
    predicted: ArrayLike

    METRICS = ["RMSE", "MAE", "MSE", "RRMSE", "bias", "ME", "WIA", "R2", "CCC", "slope"]

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    def __post_init__(self):
        self.actual = np.asarray(self.actual, dtype=float)
        self.predicted = np.asarray(self.predicted, dtype=float)

        if self.actual.shape != self.predicted.shape:
            raise ValueError("`actual` and `predicted` arrays must have the same shape.")

        if len(self.actual) == 0:
            raise ValueError("Empty arrays provided to Validate().")

        self.obs_mean = np.mean(self.actual)
        self.pred_mean = np.mean(self.predicted)
        self.std_actual = np.std(self.actual, ddof=1)
        self.std_predicted = np.std(self.predicted, ddof=1)

    # -------------------------------------------------------------------------
    # Core metrics
    # -------------------------------------------------------------------------
    def MSE(self) -> float:
        """Mean Square Error."""
        return float(np.mean((self.actual - self.predicted) ** 2))

    def RMSE(self) -> float:
        """Root Mean Square Error."""
        return float(np.sqrt(self.MSE()))

    def MAE(self) -> float:
        """Mean Absolute Error."""
        return float(np.mean(np.abs(self.actual - self.predicted)))

    def RRMSE(self) -> float:
        """Relative Root Mean Square Error (normalized by mean of observed)."""
        return float(self.RMSE() / np.mean(self.actual))

    def bias(self) -> float:
        """Mean Bias (positive = overestimation, negative = underestimation)."""
        return float(np.mean(self.predicted - self.actual))

    def ME(self) -> float:
        """Modeling Efficiency (Nash–Sutcliffe Efficiency)."""
        mse_model = np.mean((self.predicted - self.actual) ** 2)
        mse_obs = np.mean((self.actual - np.mean(self.actual)) ** 2)
        return float(1 - mse_model / mse_obs)

    def WIA(self) -> float:
        """Willmott’s Index of Agreement."""
        mean_obs = np.mean(self.actual)
        numerator = np.sum((self.predicted - self.actual) ** 2)
        denominator = np.sum((np.abs(self.predicted - mean_obs) + np.abs(self.actual - mean_obs)) ** 2)
        return float(1 - numerator / denominator)

    def R2(self) -> float:
        """Coefficient of Determination."""
        _, _, r_value, _, _ = linregress(self.actual, self.predicted)
        return float(r_value ** 2)

    def SLOPE(self) -> float:
        """Regression slope between observed and predicted."""
        slope, *_ = linregress(self.actual, self.predicted)
        return float(slope)

    def CCC(self) -> float:
        """Concordance Correlation Coefficient."""
        return float(self._rho_ci()["rho_c"]["est"].iloc[0])

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------
    def _rho_ci(
        self,
        ci: str = "z-transform",
        conf_level: float = 0.95,
        na_rm: bool = False
    ) -> Dict[str, Any]:
        """
        Compute Lin’s Concordance Correlation Coefficient (CCC) with confidence interval.

        Parameters
        ----------
        ci : {"z-transform", "approx"}, default="z-transform"
            Method for confidence interval estimation.
        conf_level : float, default=0.95
            Confidence level.
        na_rm : bool, default=False
            If True, remove NA pairs before computation.

        Returns
        -------
        dict
            Dictionary containing the CCC estimate and related statistics.
        """
        dat = pd.DataFrame({"x": self.actual, "y": self.predicted}).dropna() if na_rm else \
              pd.DataFrame({"x": self.actual, "y": self.predicted})
        k = len(dat)
        if k < 3:
            raise ValueError("Insufficient data to compute CCC (minimum 3 pairs required).")

        r = dat["x"].corr(dat["y"])
        yb, xb = dat["y"].mean(), dat["x"].mean()
        sy2, sx2 = dat["y"].var(ddof=1), dat["x"].var(ddof=1)
        sd1, sd2 = np.sqrt(sy2), np.sqrt(sx2)
        sxy = r * np.sqrt(sx2 * sy2)
        p = 2 * sxy / (sx2 + sy2 + (yb - xb) ** 2)

        v, u = sd1 / sd2, (yb - xb) / ((sx2 * sy2) ** 0.25)
        C_b = p / r
        zv = norm.ppf(1 - (1 - conf_level) / 2)

        sep = np.sqrt(
            ((1 - r ** 2) * p ** 2 * (1 - p ** 2) / r ** 2 +
             (2 * p ** 3 * (1 - p) * u ** 2 / r) -
             0.5 * p ** 4 * u ** 4 / r ** 2) / (k - 2)
        )

        if ci == "z-transform":
            t = np.log((1 + p) / (1 - p)) / 2
            set_ = sep / (1 - p ** 2)
            llt, ult = t - zv * set_, t + zv * set_
            llt, ult = [(np.exp(2 * val) - 1) / (np.exp(2 * val) + 1) for val in (llt, ult)]
            ci_result = pd.DataFrame({"est": [p], "lwr.ci": [llt], "upr.ci": [ult]})
        else:
            ci_result = pd.DataFrame({"est": [p], "lwr.ci": [p - zv * sep], "upr.ci": [p + zv * sep]})

        delta = dat["x"] - dat["y"]
        mean_xy = dat.mean(axis=1)
        blalt = pd.DataFrame({"mean": mean_xy, "delta": delta})

        return {"rho_c": ci_result, "s_shift": v, "l_shift": u, "C_b": C_b, "blalt": blalt}

    # -------------------------------------------------------------------------
    # Evaluation wrappers
    # -------------------------------------------------------------------------
    def evaluate(self, metric: str = "RMSE") -> float:
        """
        Compute a single metric value.

        Parameters
        ----------
        metric : str, default="RMSE"
            Name of the metric to compute (case-insensitive).

        Returns
        -------
        float
            Metric value.

        Raises
        ------
        ValueError
            If the metric name is not recognized.
        """
        metric_upper = metric.upper()
        if metric_upper not in self.METRICS:
            raise ValueError(f"Unsupported metric '{metric}'. Must be one of {self.METRICS}.")
        return getattr(self, metric_upper)()

    def evaluate_all(self, verbose: bool = False) -> Dict[str, float]:
        """
        Compute all available metrics at once.

        Parameters
        ----------
        verbose : bool, default=False
            If True, print metrics to console.

        Returns
        -------
        dict
            Dictionary mapping metric names to their computed values.
        """
        results = {metric: getattr(self, metric)() for metric in self.METRICS}
        if verbose:
            print("\nModel Evaluation Metrics")
            print("-" * 40)
            for k, v in results.items():
                print(f"{k:<8s}: {v:>10.4f}")
        return results


# -----------------------------------------------------------------------------
# Standalone use example
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    x_data = np.array([1.2, 2.4, 3.6, 4.8, 5.0])
    y_data = np.array([2.0, 3.5, 4.2, 5.7, 6.0])
    validator = Validate(x_data, y_data)
    all_metrics = validator.evaluate_all(verbose=True)
