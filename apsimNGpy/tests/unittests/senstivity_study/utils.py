from sklearn.metrics import root_mean_squared_error
import numpy as np

y_true = np.array([10, 20, 30, 40])
y_pred = np.array([12, 18, 29, 43])

from scipy.stats import linregress

def fit_pearson(y_true, y_pred):
    """
    Fit linear regression and calculate Pearson correlation.
    """
    fit = linregress(y_true, y_pred)

    return {
        "slope": fit.slope,
        "intercept": fit.intercept,
        "r": fit.rvalue,
        "r_squared": fit.rvalue**2,
        "p_value": fit.pvalue,
        "std_err": fit.stderr
    }

def rmse(y_true, y_pred):
    rmse = root_mean_squared_error(y_true, y_pred)
    rrmse = rmse / np.mean(y_true)

    print("RMSE:", rmse)
    print("RRMSE:", rrmse)
    print("RRMSE (%):", rrmse * 100)
    return {'RMSE':rmse, "RRMSE":rrmse}
