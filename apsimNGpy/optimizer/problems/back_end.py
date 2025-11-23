from typing import Optional, Union
import pandas as pd
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.validation.evaluator import Validate

__all__ = ['runner', 'eval_observed']

obs_suffix = '_obs'
pred_suffix = '_pred'

metric_direction = {
    "rmse": 1,
    "mae": 1,
    "mse": 1,
    "rrmse": 1,
    "bias": 1,
    "me": -1,
    "wia": -1,
    "r2": -1,
    "ccc": -1,
    "slope": -1,
}

def _prepare_eval_data(
        obs: pd.DataFrame,
        pred: pd.DataFrame,
        index: Union[str,list],
        pred_col: str,
        obs_col: str,
        method: str):
    """
    Shared utility to validate inputs, cast types, align datasets,
    and return the cleaned merged evaluation DataFrame.

    Internal utility for validation, type coercion, and alignment of observed and
    predicted datasets. This function centralizes all repeated preprocessing steps
    used by both :func:`eval_observed` and :func:`final_eval`.

    Steps handled:
      • required-column validation
      • metric-name validation
      • dtype normalization (ensure numeric + string index)
      • inner merge on the evaluation index
      • NA removal on evaluation columns

    Parameters
    ----------
    obs : pd.DataFrame
        Observed values with at least ``index`` and ``obs_col``.
    pred : pd.DataFrame
        Predicted values with at least ``index`` and ``pred_col``.
    index : str
        Column for alignment (e.g., "year", "site").
    pred_col : str
        Name of predicted column.
    obs_col : str
        Name of observed column.
    method : str
        Evaluation metric name (validated here).

    Returns
    -------
    pd.DataFrame
        Cleaned, merged DataFrame containing observed and predicted values.

    Raises
    ------
    ValueError
        If required columns are missing or the metric is unsupported.

    """
    if isinstance(index, str):
        index = {index}

    # Required column validation
    required_cols_obs = {*index, obs_col}

    required_cols_pred = {*index, pred_col}

    if not required_cols_obs.issubset(obs.columns):
        raise ValueError(
            f"Missing required columns in observed DataFrame: "
            f"{required_cols_obs - set(obs.columns)}"
        )

    if not required_cols_pred.issubset(pred.columns):
        raise ValueError(
            f"Missing required columns in predicted DataFrame: "
            f"{required_cols_pred - set(pred.columns)}"
        )

    # Metric validation
    if method.lower() not in metric_direction:
        raise ValueError(
            f"Unsupported metric method: '{method}'. "
            f"Choose from {list(metric_direction.keys())}"
        )

    # Cast types for alignment
    index = list(index)
    obs[index] = obs[index].astype(str)
    pred[index] = pred[index].astype(str)
    obs[obs_col] = pd.to_numeric(obs[obs_col], errors="coerce")
    pred[pred_col] = pd.to_numeric(pred[pred_col], errors="coerce")

    # Merge and drop missing
    data = pd.merge(
        obs[[*index, obs_col]],
        pred[[*index, pred_col]],
        on=index,
        how="inner",
    )
    data.dropna(subset=[obs_col, pred_col], inplace=True)

    return data


def eval_observed(
        obs: pd.DataFrame,
        pred: pd.DataFrame,
        index: Union[str,list],
        pred_col: str,
        obs_col: str,
        method: str = "rmse",
        exp: Optional[str] = None) -> float:
    """
    Evaluate observed and predicted values using a selected performance metric.

    This function:
      • validates and aligns the datasets,
      • computes the selected metric through :class:`Validate`,
      • applies the metric's optimization direction (min/max),
      • returns a single scalar performance value.

    Supported Metrics
    -----------------
    | Metric    | Description                          | Direction | Sign |
    |---------- |--------------------------------------|-----------|------|
    | RMSE      | Root Mean Square Error               | Smaller   | -1   |
    | MAE       | Mean Absolute Error                  | Smaller   | -1   |
    | MSE       | Mean Square Error                    | Smaller   | -1   |
    | RRMSE     | Relative RMSE                        | Smaller   | -1   |
    | bias      | Mean Bias                            | Close 0   | -1   |
    | ME        | Modeling Efficiency                  | Larger    | +1   |
    | WIA       | Willmott’s Index of Agreement        | Larger    | +1   |
    | R2        | Coefficient of Determination         | Larger    | +1   |
    | CCC       | Concordance Correlation Coefficient  | Larger    | +1   |
    | slope     | Regression Slope                     | Close 1   | +1   |

    Returns
    -------
    float
        Metric value multiplied by the optimization direction.
    """

    data = _prepare_eval_data(obs, pred, index, pred_col, obs_col, method)

    validator = Validate(data[obs_col], data[pred_col])
    metric_value = validator.evaluate(method.upper())

    direction = metric_direction[method.lower()]
    out= direction * metric_value
    return out


def final_eval(
        obs: pd.DataFrame,
        pred: pd.DataFrame,
        index: str,
        pred_col: str,
        obs_col: str,
        method: str = "rmse",
        exp: Optional[str] = None) -> dict:
    """
    Evaluate observed and predicted values and return the full suite of
    performance metrics supported by the :class:`Validate` class.

    This function:
      • prepares and validates the input data (shared utility),
      • runs all metrics, not just one,
      • returns both the metric dictionary and the aligned dataset.

    Returns
    -------
    dict
        {
            "metrics": {metric_name: value, ...},
            "data":    pd.DataFrame (aligned observed/predicted pairs)
        }
    """

    data = _prepare_eval_data(obs, pred, index, pred_col, obs_col, method)

    validator = Validate(data[obs_col], data[pred_col])
    metric_dict = validator.evaluate_all(verbose=True)

    return {"metrics": metric_dict, "data": data}


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

    rt = eval_observed(obs, pred, index=('year',), obs_col='observed', pred_col='predicted', method='ccc', exp=None)
