"""
This script evaluates the predicted and observed data, based on both statistical and mathematical index. for complete decription of the
metrics see Archountoulis et al., (2015) and
"""
__all__ = ['evaluator', 'mets', 'Metrics']
import numpy as np
class Metrics:
    def __init__(self):
        # define the existing methods
        self.MSE = 'MSE'
        self.RMSE = 'RMSE'
        self.RRMSe = 'RRMSE'
        self.WIA = 'WIA'
    def RMSE(self, actual, predicted):
        """
        Calculate the root mean square error (RMSE) between actual and predicted values.

        Parameters:
        - actual: list or numpy array of actual values
        - predicted: list or numpy array of predicted values

        Returns:
        - float: root mean square error value
        """
        actual = np.array(actual)
        predicted = np.array(predicted)
        return np.sqrt(np.mean(np.square(np.subtract(actual, predicted))))

    def RRMSE(self, actual, predicted):
        """
        Calculate the root mean square error (RMSE) between actual and predicted values.

        Parameters:
        - actual: list or numpy array of actual values
        - predicted: list or numpy array of predicted values

        Returns:
        - float: root mean square error value
        """
        rmse = np.sqrt(np.mean(np.square(np.subtract(actual, predicted))))
        rrmse = rmse/np.mean(actual)
        return rrmse

    def WIA(self, observed, predicted):
        if not isinstance(observed, np.ndarray) or not isinstance(observed, np.ndarray):
            observed = np.array(observed)
            predicted = np.array(predicted)
        mean_observed = np.mean(observed)
        # Calculate the numerator and denominator for the Wilmot IA formula
        numerator = np.sum((observed - predicted)**2)
        den1 = np.abs(np.sum(observed - mean_observed))
        den2 = np.sum(predicted-mean_observed)
        den = np.sum((den1 + den2)**2)

        # Calculate the Wilmont Index of Agreement
        return 1 - (numerator / den)

    def MSE(self, actual, predicted):
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
    def RMSE(self, actual, predicted):
        mse = self.MSE(actual, predicted)
        return np.sqrt(mse)
class metrics_description:
    def __init__(self):
        self.MSE = 'MSE'
        self.RMSE = 'RMSE'
        self.RRMSe = 'RRMSE'
        self.WIA = 'WIA'
mets = metrics_description()
class evaluator(Metrics):
    """
    this evaluated supplied predicted and observed values for evaluating on the go please see co-current evaluator class
    """
    def __init__(self, actual, predicted):
        """

        :param actual (Array): observed values
        :param predicted (Array): predicted values
        :param metric (str): metric to use default is RMSE
         tip: for metrics use the intellisence on mets class e.g metric = mets.RMSE or call the evaluator class has this attributes
        """
        assert len(actual) == len(predicted), "Target values are of different length please try again===="
        self.actual = actual
        self.predicted = predicted
    def evaluate(self, metric = 'RMSE'):
        """
        :param metric (str): metric to use default is RMSE
        :return: returns an index
        """
        assert isinstance(metric, str), "target metric should be a string"
        metric_index = getattr(self, metric)(self.actual, self.predicted)
        return metric_index
