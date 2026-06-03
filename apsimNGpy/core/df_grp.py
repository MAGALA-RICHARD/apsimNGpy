"""
Sorts data frames based on their schemas used in batch running scripts, where we don't know the database schema
"""

import pandas as pd
from collections import defaultdict
from typing import Iterable, Dict, List, Tuple, Hashable, Optional

def _normalize_dtype(dtype: pd.api.extensions.ExtensionDtype | str) -> str:
    """
    Map equivalent/nullable dtypes to a stable string so schemas match
    (e.g., Int64 -> int64, string -> object if you prefer).
    Adjust the mappings below to your needs.
    """
    s = str(dtype).lower()
    # Common harmonizations (edit as needed)
    mapping = {
        "int8": "int8", "int16": "int16", "int32": "int32", "int64": "int64",
        "uint8": "uint8", "uint16": "uint16", "uint32": "uint32", "uint64": "uint64",
        "float16": "float16", "float32": "float32", "float64": "float64",
        "boolean": "bool", "bool": "bool",
        "datetime64[ns]": "datetime64[ns]",
        "timedelta64[ns]": "timedelta64[ns]",
        "category": "category",
        "string": "object",   # or keep "string" if you want strict separation
        "object": "object",
    }
    # Handle pandas nullable ints/floats like Int64/Float64
    for base in ("int8","int16","int32","int64","uint8","uint16","uint32","uint64","float32","float64"):
        if s == base.capitalize():   # e.g., "Int64"
            return base
    return mapping.get(s, s)

def _schema_signature(
    df: pd.DataFrame,
    *,
    order_sensitive: bool = False,
    normalize_dtypes: bool = True
) -> Tuple[Tuple[Hashable, str], ...]:
    """
    Return a hashable signature of the schema: ((col, dtype), ...).
    If order_sensitive=False, columns are sorted by name before signing.
    """
    items = []
    for col, dtype in df.dtypes.items():
        dt = _normalize_dtype(dtype) if normalize_dtypes else str(dtype)
        items.append((col, dt))
    if not order_sensitive:
        items.sort(key=lambda x: str(x[0]))
    return tuple(items)

def group_and_concat_by_schema(
    dfs: Iterable[pd.DataFrame],
    *,
    axis: int = 0,
    order_sensitive: bool = False,
    normalize_dtypes: bool = True,
    add_keys: bool = True,
    keys_prefix: str = "g"
) -> Dict[Tuple[Tuple[Hashable, str], ...], pd.DataFrame]:
    """
    Group a list of DataFrames by (columns, dtypes) schema and concatenate each group.

    Parameters
    ----------
    dfs : iterable of DataFrame
    axis : {0,1}
        0 -> stack rows (requires equal columns/dtypes within a group);
        1 -> glue columns by index (useful when same schema but you want side-by-side).
    order_sensitive : bool
        If True, column order must match to be grouped.
    normalize_dtypes : bool
        If True, harmonize nullable/alias dtypes so equivalent schemas match.
    add_keys : bool
        If True, label parts during concat (MultiIndex on axis stacked).
    keys_prefix : str
        Prefix for keys (e.g., g0, g1, ...). Keys reflect insertion order within each group.

    Returns
    -------
    dict: {schema_signature: concatenated DataFrame}
    """
    # 1) group
    buckets: Dict[Tuple[Tuple[Hashable, str], ...], List[pd.DataFrame]] = defaultdict(list)
    for df in dfs:
        sig = _schema_signature(df, order_sensitive=order_sensitive, normalize_dtypes=normalize_dtypes)
        buckets[sig].append(df)

    # 2) concat per group
    out: Dict[Tuple[Tuple[Hashable, str], ...], pd.DataFrame] = {}
    for sig, group in buckets.items():
        # Optionally enforce identical columns order if not order_sensitive
        if not order_sensitive and axis == 0:
            # align group columns to a common sorted order to avoid minor column-order drift
            cols_sorted = [c for c, _ in sorted(sig, key=lambda x: str(x[0]))]
            group = [g.reindex(columns=cols_sorted) for g in group]

        keys = [f"{keys_prefix}{i}" for i in range(len(group))] if add_keys else None
        out[sig] = pd.concat(group, axis=axis, keys=keys, copy=False)
    return out
