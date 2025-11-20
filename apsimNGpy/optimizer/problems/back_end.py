from typing import Optional
import pandas as pd
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.validation.evaluator import Validate

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


def eval_observed(
        obs: pd.DataFrame,
        pred: pd.DataFrame,
        index: str,
        pred_col: str,
        obs_col: str,
        method: str = "rmse",
        exp: Optional[str] = None) -> float:
    """
    Evaluate observed and predicted values using a selected performance metric.

    Supported metrics include:

    | Metric    | Description                          | Preferred Direction | Sign |
    | :-------- | :----------------------------------- | :------------------ | :--- |
    | **RMSE**  | Root Mean Square Error               | Smaller             | `-1` |
    | **MAE**   | Mean Absolute Error                  | Smaller             | `-1` |
    | **MSE**   | Mean Square Error                    | Smaller             | `-1` |
    | **RRMSE** | Relative RMSE                        | Smaller             | `-1` |
    | **bias**  | Mean Bias                            | Closer to 0         | `-1` |
    | **ME**    | Modeling Efficiency (Nash–Sutcliffe) | Larger              | `+1` |
    | **WIA**   | Willmott’s Index of Agreement        | Larger              | `+1` |
    | **R2**    | Coefficient of Determination         | Larger              | `+1` |
    | **CCC**   | Concordance Correlation Coefficient  | Larger              | `+1` |
    | **slope** | Regression slope                     | Closer to 1         | `+1` |

    Parameters
    ----------
    obs : pandas.DataFrame
        DataFrame containing observed values. Must include the `index` and `obs_col` columns.

    pred : pandas.DataFrame
        DataFrame containing predicted values. Must include the `index` and `pred_col` columns.

    index : str
        Column name used for aligning observed and predicted datasets (e.g., `"year"`, `"site"`).

    pred_col : str
        Column name for predicted variable (e.g., `"Yield_pred"`).

    obs_col : str
        Column name for observed variable (e.g., `"Yield_obs"`).

    method : str, default="rmse"
        Performance metric to evaluate. Case-insensitive; see the supported list above.

    exp : str, optional
        Optional label for the experiment or simulation context, for logging or tracing.

    Returns
    -------
    float
        The evaluated metric value multiplied by its optimization direction
        (`-1` for minimization metrics, `+1` for maximization metrics).

    Raises
    ------
    ValueError
        If required columns are missing or the metric method is unsupported.

    Notes
    -----
    This function aligns observed and predicted datasets by the specified index,
    enforces float type consistency, and delegates the metric computation to the:
      class:`Validate` class. The result is automatically signed according to
    the optimization convention defined in :data:`metric_direction`.

    Examples
    --------
    .. code-block:: python

        from apsimNGpy.optimizer.evaluation import eval_observed

        out = eval_observed(
            obs=df_obs,
            pred=df_pred,
            index="year",
            pred_col="Yield_pred",
            obs_col="Yield_obs",
            method="CCC"
        )
        print(out)
    """
    # Input validation
    required_cols_obs = {index, obs_col}
    required_cols_pred = {index, pred_col}
    if not required_cols_obs.issubset(obs.columns):
        raise ValueError(f"Missing required columns in observed DataFrame: {required_cols_obs - set(obs.columns)}")
    if not required_cols_pred.issubset(pred.columns):
        raise ValueError(f"Missing required columns in predicted DataFrame: {required_cols_pred - set(pred.columns)}")

    if method.lower() not in metric_direction:
        raise ValueError(f"Unsupported metric method: '{method}'. "
                         f"Choose from {list(metric_direction.keys())}")

    # Ensure float dtype for computation
    obs[index] = obs[index].astype(str)
    pred[index] = pred[index].astype(str)
    obs[obs_col] = pd.to_numeric(obs[obs_col], errors="coerce")
    pred[pred_col] = pd.to_numeric(pred[pred_col], errors="coerce")

    # Align and join
    data = pd.merge(obs[[index, obs_col]], pred[[index, pred_col]], on=index, how="inner")
    data.dropna(subset=[obs_col, pred_col], inplace=True)

    # Compute metric
    validator = Validate(data[obs_col], data[pred_col])
    metric_value = validator.evaluate(method.upper())

    # Apply the optimization direction
    direction = metric_direction[method.lower()]
    return direction * metric_value


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
