def clean_a_group(self, dff, X, groupings=False):
    """
    Align SALib input matrix X with model outputs in dff.

    Returns
    -------
    new_xvars : np.ndarray
        Cleaned X matrix aligned with output rows.

    out : np.ndarray or pd.DataFrame
        Cleaned output values. Returns DataFrame if groupings=True.
    """

    import numpy as np
    import pandas as pd

    if self.index_id not in dff.columns:
        raise KeyError(f"{self.index_id!r} not found in dff columns.")

    missing_outputs = [col for col in self.outputs if col not in dff.columns]
    if missing_outputs:
        raise KeyError(f"Missing output columns in dff: {missing_outputs}")

    X_df = pd.DataFrame(X).copy()

    if len(X_df) != len(dff):
        raise ValueError(
            f"X and dff must have the same number of rows before cleaning. "
            f"Got len(X)={len(X_df)} and len(dff)={len(dff)}."
        )

    X_df[self.index_id] = dff[self.index_id].to_numpy()

    if X_df[self.index_id].duplicated().any():
        duplicated = X_df.loc[X_df[self.index_id].duplicated(), self.index_id].unique()
        raise ValueError(f"Duplicate IDs found in X: {duplicated[:10]}")

    if dff[self.index_id].duplicated().any():
        duplicated = dff.loc[dff[self.index_id].duplicated(), self.index_id].unique()
        raise ValueError(f"Duplicate IDs found in dff: {duplicated[:10]}")

    # Keep only rows where all requested outputs are available.
    output_cols = [self.index_id] + list(self.outputs)

    out_df = (
        dff[output_cols]
        .copy()
        .dropna(subset=self.outputs)
        .sort_values(self.index_id)
        .reset_index(drop=True)
    )

    if out_df.empty:
        raise ValueError(
            "No valid rows remain after dropping missing output values."
        )

    X_df = (
        X_df
        .sort_values(self.index_id)
        .reset_index(drop=True)
    )

    # Inner merge guarantees that X and Y correspond to the same simulation IDs.
    joined = out_df.merge(
        X_df,
        on=self.index_id,
        how="inner",
        validate="one_to_one"
    )

    if joined.empty:
        raise ValueError("No matching IDs between X and output dataframe.")

    if len(joined) != len(out_df):
        missing_ids = set(out_df[self.index_id]) - set(joined[self.index_id])
        raise ValueError(
            f"Some output rows do not have matching X rows. "
            f"Missing IDs example: {list(missing_ids)[:10]}"
        )

    x_cols = [col for col in joined.columns if col not in output_cols]

    new_xvars = joined[x_cols].to_numpy(dtype=float)

    y_df = joined[[self.index_id] + list(self.outputs)].copy()

    # Final alignment checks
    if new_xvars.shape[0] != y_df.shape[0]:
        raise RuntimeError(
            f"Alignment failed: X rows={new_xvars.shape[0]}, "
            f"Y rows={y_df.shape[0]}"
        )

    if y_df[self.outputs].isna().any().any():
        raise RuntimeError("NaN values remain in output data after cleaning.")

    self.NewXVars = new_xvars

    if groupings:
        out = y_df
    else:
        out = y_df[self.outputs].to_numpy(dtype=float)

    return new_xvars, out