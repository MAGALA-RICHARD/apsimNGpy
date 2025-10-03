from __future__ import annotations

from collections.abc import Sequence as _Sequence
from typing import Hashable, Optional, Union
import pandas as pd


def mva(
        data: pd.DataFrame,
        time_col: Hashable,
        response: Hashable,
        window: int = 5,
        min_period: int = 1,
        grouping: Optional[Union[Hashable, _Sequence[Hashable]]] = None,
        preserve_start: bool = True,
) -> pd.DataFrame:
    """
    Centered moving average of `response`, optionally within groups, with an option
    to preserve the first `window//2` values in each group (avoids leading-edge attenuation).


     Parameters
    ----------
    data : pandas.DataFrame
        Input table.
    time_col : Hashable
        Column that defines temporal order within each group.
    response : Hashable
        Column to smooth. Non-numeric values are coerced to NaN.
    window : int, default 7
        Rolling window size (>=1). Use a **centered** window.
    min_period : int, default 1
        Minimum observation required in the window (1 ≤ min_period ≤ window).
    grouping : Hashable | Sequence[Hashable] | None, default None
        Column name(s) to group by. If None/empty, compute over the entire column.
        Groups with NaN keys are retained.
    preserve_start : bool, default True
        If True and `window` > 1, copy the first `window//2` values of each group
        from the original series to mitigate leading-edge attenuation.

    Returns -------
    pandas.DataFrame Copy of `data` with ``f"{response}_roll_mean"`` (float). The original data is
    not mutated as the function first performs a deep copy of the original

    Raises
    ------
    TypeError
        If `data` is not a DataFrame.
    KeyError
        If required columns are missing.
    ValueError
        If `window` < 1 or `min_period` ∉ [1, window].
    """
    # --- Validation ---
    if not isinstance(data, pd.DataFrame):
        raise TypeError("`data` must be a pandas DataFrame.")

    for col in (time_col, response):
        if col not in data.columns:
            raise KeyError(f"Missing required column: {col!r}")

    if not isinstance(window, int) or window < 1:
        raise ValueError("`window` must be an integer >= 1.")
    if not isinstance(min_period, int) or not (1 <= min_period <= window):
        raise ValueError("`min_period` must be an integer in [1, window].")

    # --- Normalize grouping to a list of column names (handle str specially) ---
    if grouping is None or (isinstance(grouping, _Sequence) and not isinstance(grouping, str) and len(grouping) == 0):
        group_cols: list[Hashable] = []
    elif isinstance(grouping, str):
        group_cols = [grouping]
    elif isinstance(grouping, _Sequence):
        group_cols = list(grouping)
    else:
        group_cols = [grouping]

    missing_groups = [g for g in group_cols if g not in data.columns]
    if missing_groups:
        raise KeyError(f"Grouping column(s) not found: {missing_groups}")

    # --- Prepare data (stable sort; numeric response; keep original order) ---
    df = data.copy()
    out_col = f"{response}_roll_mean"
    original_index = df.index

    # Coerce response to numeric (non-numeric -> NaN)
    df["_mva_resp_"] = pd.to_numeric(df[response], errors="coerce")

    sort_cols = (group_cols + [time_col]) if group_cols else [time_col]
    df = df.sort_values(sort_cols, kind="mergesort")

    # --- Rolling function applied per group/series ---
    def _roll_preserve_start(s: pd.Series) -> pd.Series:
        r = s.rolling(window=window, center=True, min_periods=min_period).mean()
        if preserve_start and window > 1:
            k = window // 2
            if len(s) <= k:
                return s  # too short to smooth meaningfully
            r.iloc[:k] = s.iloc[:k]
        return r

    # --- Compute rolling mean ---
    if group_cols:
        # Use DataFrameGroupBy to avoid 1-D grouper errors
        try:
            rolled = df.groupby(group_cols, sort=False, dropna=False)["_mva_resp_"].transform(_roll_preserve_start)
        except TypeError:
            # Fallback for older pandas versions without dropna=
            rolled = df.groupby(group_cols, sort=False)["_mva_resp_"].transform(_roll_preserve_start)
    else:
        rolled = _roll_preserve_start(df["_mva_resp_"])

    df[out_col] = rolled
    # Restore original row order
    df = df.loc[original_index].copy()
    # Clean up helper column
    df.drop(columns=["_mva_resp_"], inplace=True)

    return df
