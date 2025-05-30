"""
This script evaluates the predicted and observed data, based on both statistical and mathematical index. For complete definition of the
metrics see Archountoulis et al., (2015) and
"""
__all__ = ['validate', 'mets', 'Metrics']

import numpy as np
import pandas as pd
from scipy.stats import norm, linregress


class Metrics:
    """
    This class is holds the evaluation metrics or the loss functions used in evaluating the model performance
    """

    def __init__(self):
        pass

    def RRMSE(self, actual, predicted):
        """

        Calculate the root-mean-square error (RRMSE) between actual and predicted values.

        Parameters:
        :actual: *list or numpy array* of actual values.
        :predicted: *list or numpy array* of predicted values.

        Returns:
        - float: relative root-mean-square error value
        """
        if not isinstance(actual, np.ndarray) or not isinstance(predicted, np.ndarray):
            actual = np.array(actual)
            predicted = np.array(predicted)
        rmse = np.sqrt(np.mean(np.square(np.subtract(actual, predicted))))
        rrmse = rmse / np.mean(actual)
        return rrmse

    def WIA(self, obs, pred):
        """
        Calculate the Willmott's index of agreement.

        Parameters:
        :obs: *array-like*, observed values.
        :pred: *array-like*, predicted values.

        Returns:
        - d: Willmott's index of agreement.
        """
        obs_mean = np.mean(obs)
        pred_mean = np.mean(pred)
        numerator = np.sum((pred - obs) ** 2)
        denominator = np.sum((np.abs(pred - obs_mean) + np.abs(obs - obs_mean)) ** 2)

        d = 1 - numerator / denominator
        return d

    def MSE(self, actual, predicted):
        """
        Calculate the Mean Squared Error (MSE) between actual and predicted values.

        Args:

        :actual: (*array-like*): Array of actual values.
        :predicted: (*array-like*): Array of predicted values.

        :Returns:
          float: The Mean Squared Error (MSE).
        """
        squared_errors = (np.array(actual) - np.array(predicted)) ** 2
        mse = np.mean(squared_errors)
        return mse

    def mva(self, data, window):
        """Calculate the moving average

        Args:
            :param data: list or array-like
            :param window: moving window e.g., 5 year period

        Returns:

        """
        return np.convolve(data, np.ones(window), 'valid') / window

    def rho_ci(self, x, y, ci="z-transform", conf_level=0.95, na_rm=False):
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

    def RMSE(self, actual, predicted):
        mse = self.MSE(actual, predicted)
        return np.sqrt(mse)

    def CCC(self, actual, predicted):
        ccc = self.rho_ci(actual, predicted)
        return ccc['rho_c']['est'][0]

    def bias(self, actual, predicted):
        return np.mean(actual - predicted)

    def ME(self, actual, predicted):
        """
        Calculate Modeling Efficiency (MEF) between observed and predicted values.

        Parameters:
        :observed: (*array-like*): Array or list of observed values.
        :predicted: (*array-like*): Array or list of predicted values.

        :Returns:
           float: The Modeling Efficiency (ME) between observed and predicted values.
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

    def slope(self, observed, predicted):
        slope, intercept, r_value, p_value, std_err = linregress(observed, predicted)
        return slope

    def R2(self, observed, predicted):
        slope, intercept, r_value, p_value, std_err = linregress(observed, predicted)
        return r_value


class metrics_description:
    def __init__(self):
        self.MSE = 'MSE'
        self.RMSE = 'RMSE'
        self.RRMSe = 'RRMSE'
        self.WIA = 'WIA'
        self.CCC = 'CCC'
        self.ME = "ME"
        self.bias = "bias"
        self.slope = 'slope'


mets = metrics_description()


class validate(Metrics):
    """
    supply predicted and observed values for evaluating on the go please see co-current evaluator class
    """

    def __init__(self, actual, predicted):
        """

        :actual (*Array*): observed values
        :predicted (*Array*): predicted values
        :metric (*str*): metric to use default is RMSE
         tip: for metrics use the IntelliSense on mets class e.g., metric = mets.RMSE
        """
        assert len(actual) == len(predicted), "Target values are of different length please try again===="
        self.actual = actual
        self.predicted = predicted

    def evaluate(self, metric: str = mets.RMSE):
        """
        :metric: (str): metric to use default is RMSE
        :return: an evaluation index
        """
        assert isinstance(metric, str), "target metric should be a string"
        return getattr(self, metric)(self.actual, self.predicted)

    def evaluate_all(self, verbose: bool = False):
        """
        verbose (*bool*) will print all the metrics
        """
        attribs = ['RMSE', 'RRMSE', "ME", "WIA", "bias", 'R2', "CCC", 'slope']
        all = {atbs: getattr(self, atbs)(self.actual, self.predicted) for atbs in attribs}
        if verbose:
            for k, v in all.items():
                print(k, ":", v)
        return all


if __name__ == "__main__":
    x_data = np.array([1.2, 2.4, 3.6, 4.8, 5.0])
    y_data = np.array([2.0, 3.5, 4.2, 5.7, 6.0])

    data = validate(x_data, y_data)
    al = data.evaluate_all()
    for k, v in al.items():
        print(k, ":", v)
