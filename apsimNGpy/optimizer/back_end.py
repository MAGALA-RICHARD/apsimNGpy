import pandas as pd
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.validation.evaluator import Validate
from apsimNGpy.exceptions import ApsimRuntimeError

obs_suffix = '_obs'
pred_suffix = '_pred'

metric_direction = {
    "rmse": -1,
    "mae": -1,
    "mse": -1,
    "rrmse": -1,
    "bias": -1,
    "me": 1,
    "wia": 1,
    "r2": 1,
    "ccc": 1,
    "slope": 1,
}


def eval_observed(obs, pred, index, pred_col, obs_col, method='rmse', exp=None):
    """"
    Evaluate the observed and predicted values based on a given loss function method
    examples of supported loss functions:
     ['RMSE', 'MAE', 'MSE', 'RRMSE', 'bias', 'ME', 'WIA', 'R2', 'CCC', 'slope']
        | Metric    | Meaning                             | Better when | Sign                           |
        | :-------- | :---------------------------------- | :---------- | :----------------------------- |
        | **RMSE**  | Root Mean Square Error              | smaller     | `-1`                           |
        | **MAE**   | Mean Absolute Error                 | smaller     | `-1`                           |
        | **MSE**   | Mean Square Error                   | smaller     | `-1`                           |
        | **RRMSE** | Relative RMSE                       | smaller     | `-1`                           |
        | **bias**  | Mean Bias                           | closer to 0 | `-1` (minimize magnitude)      |
        | **ME**    | Modeling Efficiency (NSE)           | larger      | `+1`                           |
        | **WIA**   | Willmott’s Index of Agreement       | larger      | `+1`                           |
        | **R2**    | Coefficient of Determination        | larger      | `+1`                           |
        | **CCC**   | Concordance Correlation Coefficient | larger      | `+1`                           |
        | **slope** | Regression slope                    | closer to 1 | `+1` (maximize closeness to 1) |

    """
    observed = obs.copy()
    predicted = pred.copy()
    # 3 make the same dtype
    predicted[index] = predicted[index].astype(float)
    observed[index] = observed[index].astype(float)
    observed.set_index(index, inplace=True)
    predicted.set_index(index, inplace=True)
    data = observed.join(predicted, rsuffix=obs_suffix, lsuffix=pred_suffix)
    data.reset_index(inplace=True)
    if obs_col == pred_col:
        out = Validate(data[f"{obs_col}{obs_suffix}"], data[f"{pred_col}{pred_suffix}"]).evaluate(
            method.upper())
    else:
        out = Validate(data[f"{obs_col}"], data[f"{pred_col}"]).evaluate(method.upper())

    return metric_direction[method.lower()] * out


def runner(model, params, table=None):
    with ApsimModel(model) as model:
        for param in params:
            model.set_params(param)
        df = model.run(report_name=table).results
        df["date"] = pd.to_datetime(df["Clock.Today"])

        # Extract components
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["day"] = df["date"].dt.day

        return df


if __name__ == '__main__':
    from apsimNGpy.tests.unittests.test_factory import obs, pred

    rt = eval_observed(obs, pred, index='year', obs_col='observed', pred_col='predicted', method='ccc', exp=None)
