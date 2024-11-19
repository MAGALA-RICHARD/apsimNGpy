"""
This script evaluates the predicted and observed data, based on both statistical and mathematical index.
for complete decription of the metrics see Archountoulis et al., (2015) and
"""
__all__ = ['validate', 'validation_metrics', 'evaluate_all']

import numpy as np
import pandas as pd
from scipy.stats import norm, linregress


def RRMSE(actual, predicted):
    """

    Calculate the root-mean-square error (RRMSE) between actual and predicted values.

    Parameters:
    - actual: list or numpy array of actual values
    - predicted: list or numpy array of predicted values

    Returns:
    - float: relative root-mean-square error value
    """
    if not isinstance(actual, np.ndarray) or not isinstance(predicted, np.ndarray):
        actual = np.array(actual)
        predicted = np.array(predicted)
    rmse = np.sqrt(np.mean(np.square(np.subtract(actual, predicted))))
    rrmse = rmse / np.mean(actual)
    return rrmse


def WIA(obs, pred):
    """
    Calculate the Willmott's index of agreement.

    Parameters:
    - obs: array-like, observed values.
    - pred: array-like, predicted values.

    Returns:
    - d: Willmott's index of agreement.
    """
    obs_mean = np.mean(obs)
    pred_mean = np.mean(pred)
    numerator = np.sum((pred - obs) ** 2)
    denominator = np.sum((np.abs(pred - obs_mean) + np.abs(obs - obs_mean)) ** 2)

    d = 1 - numerator / denominator
    return d


def MSE(actual, predicted):
    """
    Calculate the Mean Squared Error (MSE) between actual and predicted values.

    Args:
    actual (array-like): Array of actual values.
    predicted (array-like): Array of predicted values.

    Returns:
    float: The Mean Squared Error (MSE).
    """
    squared_errors = (np.array(actual) - np.array(predicted)) ** 2
    mse = np.mean(squared_errors)
    return mse


def mva(data, window):
    """Calculate the moving average

    Args:
        data: list or array-like
        window: moving window e.g 2

    Returns:

    """
    return np.convolve(data, np.ones(window), 'valid') / window


def rho_ci(x, y, ci="z-transform", conf_level=0.95, na_rm=False):
    dat = pd.DataFrame({'x': x, 'y': y})
    if na_rm:
        dat = dat.dropna()
    N_ = 1 - ((1 - conf_level) / 2)
    zv = norm.ppf(N_, loc=0, scale=1)
    lower = "lwr.ci"
    upper = "upr.ci"
    k = len(dat['y'])
    yb = dat['y'].mean()
    sy2 = dat['y'].var() * (k - 1) / k
    sd1 = dat['y'].std()
    xb = dat['x'].mean()
    sx2 = dat['x'].var() * (k - 1) / k
    sd2 = dat['x'].std()
    r = dat['x'].corr(dat['y'])
    sl = r * sd1 / sd2
    sxy = r * np.sqrt(sx2 * sy2)
    p = 2 * sxy / (sx2 + sy2 + (yb - xb) ** 2)
    delta = (dat['x'] - dat['y'])
    rmean = dat.apply(lambda row: row.mean(), axis=1)
    blalt = pd.DataFrame({'mean': rmean, 'delta': delta})
    v = sd1 / sd2
    u = (yb - xb) / ((sx2 * sy2) ** 0.25)
    C_b = p / r
    sep = np.sqrt(((1 - ((r) ** 2)) * (p) ** 2 * (1 - ((p) ** 2)) / (r) ** 2 +
                   (2 * (p) ** 3 * (1 - p) * (u) ** 2 / r) - 0.5 * (p) ** 4 * (u) ** 4 / (r) ** 2) / (k - 2))
    ll = p - zv * sep
    ul = p + zv * sep
    t = np.log((1 + p) / (1 - p)) / 2
    set_ = sep / (1 - ((p) ** 2))
    llt = t - zv * set_
    ult = t + zv * set_
    llt = (np.exp(2 * llt) - 1) / (np.exp(2 * llt) + 1)
    ult = (np.exp(2 * ult) - 1) / (np.exp(2 * ult) + 1)
    if ci == "asymptotic":
        rho_c = pd.DataFrame({'est': p, lower: ll, upper: ul}, index=[0])
        rval = {'rho_c': rho_c, 's_shift': v, 'l_shift': u, 'C_b': C_b, 'blalt': blalt}
    elif ci == "z-transform":
        rho_c = pd.DataFrame({'est': p, lower: llt, upper: ult}, index=[0])
        rval = {'rho_c': rho_c, 's_shift': v, 'l_shift': u, 'C_b': C_b, 'blalt': blalt}
    return rval


def RMSE(actual, predicted):
    mse = MSE(actual, predicted)
    return np.sqrt(mse)


def CCC(actual, predicted):
    _ccc = rho_ci(actual, predicted)
    return _ccc['rho_c']['est'][0]


def bias(actual, predicted):
    return np.mean(actual - predicted)


def ME(actual, predicted):
    """
    Calculate Modeling Efficiency (MEF) between observed and predicted values.

    Parameters:
    observed (array-like): Array or list of observed values.
    predicted (array-like): Array or list of predicted values.

    Returns:
    float: The Modeling Efficiency (MEF) between observed and predicted values.
    """
    # Convert input data to NumPy arrays for consistent handling
    observed = np.array(actual)
    predicted = np.array(predicted)

    # Calculate the mean squared error of the predictions
    mse_pred = np.mean((predicted - actual) ** 2)

    # Calculate the mean squared error of the observed values
    mse_obs = np.mean((observed - np.mean(actual)) ** 2)

    # Calculate the Modeling Efficiency (MEF)
    mef = 1 - (mse_pred / mse_obs)

    return mef


def slope(observed, predicted):
    slope, intercept, r_value, p_value, std_err = linregress(observed, predicted)
    return slope


def R2(observed, predicted):
    slope, intercept, r_value, p_value, std_err = linregress(observed, predicted)
    return r_value


validation_metrics = {
    'RMSE': RMSE, 'RRMSE': RRMSE, "ME": ME,
    "WIA": WIA, "bias": BIAS, 'R2': R2, "CCC": ccc, 'slope': slope}


def validate(actual_values, predicted_values, metrics=None):
    assert len(actual) == len(predicted), "Target values are of different length please try again===="
    metrics = metrics or 'RMSE'
    selected_metric_function = validation_metrics.get(metrics)
    return selected_metric_function(actual_values, predicted_values)


def evaluate_all(actual_values, predicted_values):
    for name in validation_metrics:
        validate(actual_values, predicted_values, metrics=name)


if __name__ == "__main__":
    x_data = np.array([1.2, 2.4, 3.6, 4.8, 5.0])
    y_data = np.array([2.0, 3.5, 4.2, 5.7, 6.0])

    validate(x_data, y_data)
    al = data.evaluate_all()
    for k, v in al.items():
        print(k, ":", v)
