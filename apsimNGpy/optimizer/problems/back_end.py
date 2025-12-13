import uuid
from typing import Optional, Union, Iterable

import numpy as np
import pandas as pd
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.validation.evaluator import Validate
from apsimNGpy.exceptions import NodeNotFoundError, ApsimRuntimeError

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

metric_bounds = {
    "rmse": (0.0, np.inf),  # RMSE ≥ 0
    "mae": (0.0, np.inf),  # MAE ≥ 0
    "mse": (0.0, np.inf),  # MSE ≥ 0

    # RRMSE can exceed 1 for poor models → upper bound should be ∞
    "rrmse": (0.0, np.inf),

    # Bias is unbounded in both directions
    "bias": (-np.inf, np.inf),

    # Mean error (ME) is signed → can be negative or positive
    "me": (-np.inf, np.inf),

    # Willmott’s index of agreement: 0–1
    "wia": (-1, 0.0),

    # R² is between 0 and 1
    "r2": (-1, 0.0),

    # Lin’s CCC ranges from -1 to 1
    "ccc": (-1.0, 1.0),

    # Regression slope can be negative, positive, or >1
    "slope": (-np.inf, np.inf),
}


def detect_range(metric: str, bounds: tuple):
    """
    Check whether user-defined bounds fall within the allowed metric range.

    Parameters
    ----------
    metric : str
        Name of the metric (e.g., "rmse", "wia", "r2").
    bounds : tuple
        User-specified (lower, upper) bounds.

    Returns
    -------
    bool
        True if the user-specified bounds are valid and within the global metric range.
        False otherwise.

    Raises
    ------
    KeyError
        If the metric is unknown.
    ValueError
        If bounds is not a valid 2-tuple.
    """

    # global reference, e.g. your metric_bounds = { "rmse": (0, inf), ... }
    allowed_range = metric_bounds[metric.lower()]

    if not isinstance(bounds, tuple) or len(bounds) != 2:
        raise ValueError(
            f"Bounds must be a 2-tuple (lower, upper). Got: {bounds}"
        )

    user_low, user_high = bounds
    assert user_low <= user_high, 'lower boundary should not be higher than upper boundary'
    allowed_low, allowed_high = allowed_range

    # Comparison:
    low_ok = user_low >= allowed_low
    high_ok = user_high <= allowed_high

    return low_ok and high_ok


def examine_constraints(metric, constraints):
    if not isinstance(constraints, tuple):
        raise ValueError("only tuple is allowed")
    if len(constraints) != 2:
        raise ValueError("tuple should only be of length 2, with lower and upper boundary, respectively")
    lower_bound, upper_bound = constraints
    if lower_bound > upper_bound:
        raise ValueError("lower bound is higher than upper boudnary")


def _prepare_eval_data(
        obs: pd.DataFrame,
        pred: pd.DataFrame,
        index: Union[str, list],
        pred_col: str,
        obs_col: str,
):
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
        index: Union[str, list, tuple, set],
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

    +---------+-----------------------------------------------+---------------------+------+
    | Metric  | Description                                   | Preferred Direction | Sign |
    +=========+===============================================+=====================+======+
    | RMSE    | Root Mean Square Error                        | Smaller             | +1   |
    +---------+-----------------------------------------------+---------------------+------+
    | MAE     | Mean Absolute Error                           | Smaller             | +1   |
    +---------+-----------------------------------------------+---------------------+------+
    | MSE     | Mean Square Error                             | Smaller             | +1   |
    +---------+-----------------------------------------------+---------------------+------+
    | RRMSE   | Relative RMSE                                 | Smaller             | +1   |
    +---------+-----------------------------------------------+---------------------+------+
    | BIAS    | Mean Bias                                     | Closer to 0         | +1   |
    +---------+-----------------------------------------------+---------------------+------+
    | ME      | Modeling Efficiency                           | Larger              | -1   |
    +---------+-----------------------------------------------+---------------------+------+
    | WIA     | Willmott’s Index of Agreement                 | Larger              | -1   |
    +---------+-----------------------------------------------+---------------------+------+
    | R2      | Coefficient of Determination                  | Larger              | -1   |
    +---------+-----------------------------------------------+---------------------+------+
    | CCC     | Concordance Correlation Coefficient           | Larger              | -1   |
    +---------+-----------------------------------------------+---------------------+------+
    | SLOPE   | Regression Slope                              | Closer to 1         | -1   |
    +---------+-----------------------------------------------+---------------------+------+

    Returns
    -------
    float
        Metric value multiplied by the optimization direction.
    """
    # Metric validation
    if method.lower() not in metric_direction:
        raise ValueError(
            f"Unsupported metric method: '{method}'. "
            f"Choose from {list(metric_direction.keys())}"
        )
    data = _prepare_eval_data(obs, pred, index, pred_col, obs_col)
    if exp:
        data.eval(exp, inplace=True)
    validator = Validate(data[obs_col], data[pred_col])
    metric_value = validator.evaluate(method.upper())

    direction = metric_direction[method.lower()]
    out = direction * metric_value
    return out


def final_eval(
        obs: pd.DataFrame,
        pred: pd.DataFrame,
        index: str,
        pred_col: str,
        obs_col: str,
        exp: Optional[str] = None) -> dict:
    """
    Evaluate observed and predicted values and return the full suite of
    performance metrics supported by the: class:`Validate` class.

    This function:
      • prepares and validates the input data (shared utility),
      • runs all metrics, not just one,
      • returns both the metric dictionary and the aligned dataset.

    Returns
    -------
    dict
        {
            "metrics": {metric_name: value, ...},
            "data": pd.DataFrame (aligned observed/predicted pairs)
        }
    """

    data = _prepare_eval_data(obs, pred, index, pred_col, obs_col)
    if exp:
        data.eval(exp, inplace=True)

    validator = Validate(data[obs_col], data[pred_col])
    metric_dict = validator.evaluate_all(verbose=True)

    return {"metrics": metric_dict, "data": data}


def runner(model, params, table=None):
    # ideally out_path not needed, as ApsimNGpy generate random temporal files automatically when out_path is not provided
    with ApsimModel(model) as model:
        for param in params:
            try:
                model.set_params(param)
            # There is a need at least to present to the user what is going on, because some errors maybe excepted breaking the program
            except ValueError as e:
                print(ValueError, f'occurred while setting parameters{param}', e)
                raise ValueError(f"{str(e)} e") from e
            except AttributeError as ate:
                print(ate)
                print(AttributeError, f'occurred while setting params in APSIM {param}', ate)
                raise AttributeError(f'occurred while setting params in APSIM {param}') from ate
            except ApsimRuntimeError as ape:
                print(ApsimRuntimeError, f'occurred with setting params: {param}', ape)
            except NodeNotFoundError as nfe:
                print(NodeNotFoundError, f'occurred while setting params: {param}', nfe)
                raise NodeNotFoundError(f'Occurred while trying to edit parameters{param}', nfe) from nfe
        model.preview_simulation()
        model.run()

        reports = model.inspect_model('Models.Report', fullpath=False)
        if table and isinstance(table, str) and table not in reports:
            raise ValueError(f"Table {table} not found in the simulation. Available tables are `{reports}`")
        if table and isinstance(table, Iterable) and not isinstance(table, str):
            tabs = [i for i in table if i not in reports]
            if tabs:
                raise ValueError(f"Tables `{tabs}` not found in the simulation available tables are; `{reports}`")
        if not table:
            df = model.results
        else:
            df = model.get_simulated_output(table, axis=0)
        df["date"] = pd.to_datetime(df["Clock.Today"])

        # Extract components
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["day"] = df["date"].dt.day

        return df
    # all transient files are deleted after exiting this block


if __name__ == '__main__':
    from apsimNGpy.tests.unittests.test_factory import obs, pred

    from apsimNGpy.tests.unittests.test_factory import obs, pred

    # _____________________________
    # list index
    # _______________________________
    index = ['year']
    rt = eval_observed(obs, pred, index=index, obs_col='observed', pred_col='predicted', method='ccc', exp=None)
    assert rt, 'metric is none when list is the index'
    # _____________________________
    # tuple index
    # _______________________________
    index = tuple(['year'])
    rt = eval_observed(obs, pred, index=index, obs_col='observed', pred_col='predicted', method='ccc', exp=None)
    assert rt, 'metric is none when tuple  is the index'
    # _____________________________
    # list index
    # _______________________________
    index = set(['year'])
    rt = eval_observed(obs, pred, index=index, obs_col='observed', pred_col='predicted', method='ccc', exp=None)
    assert rt, 'metric is none when set is the index'
    # _____________________________
    # list index
    # _______________________________
    index = 'year'
    rt = eval_observed(obs, pred, index=index, obs_col='observed', pred_col='predicted', method='ccc', exp=None)
    assert rt, 'metric is none when str is the index'
