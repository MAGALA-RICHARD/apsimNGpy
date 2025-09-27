from __future__ import annotations
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, Tuple, Union, Literal, Callable, List
from functools import wraps
import pandas as pd

InsertFn = Callable[[str, pd.DataFrame, str, str], None]  # (db_path, df, table, if_exists)

def _default_insert_fn(db: str, df: pd.DataFrame, table: str, if_exists: str) -> None:
    """Default inserter using pandas.to_sql via SQLAlchemy."""
    from sqlalchemy import create_engine
    eng = create_engine(f"sqlite:///{db}")
    df.to_sql(table, eng, if_exists=if_exists, index=False)

def _to_dataframe(obj: Any) -> pd.DataFrame:
    """Best-effort coercion of common Python shapes to a DataFrame."""
    if isinstance(obj, pd.DataFrame):
        return obj
    # list of dicts OR dict-of-columns
    if isinstance(obj, (list, tuple)) and (not obj or isinstance(obj[0], Mapping)):
        return pd.DataFrame(list(obj))
    if isinstance(obj, Mapping):
        # dict-of-columns (values are list-like/scalars)
        return pd.DataFrame(obj)
    raise TypeError("Cannot coerce object to DataFrame. Expected DataFrame, list[dict], or dict-of-columns.")

def _normalize_result(
    result: Any,
    default_table: str,
) -> List[Tuple[str, pd.DataFrame]]:
    """
    Normalize various return shapes into a list of (table, DataFrame).
    """
    items: List[Tuple[str, pd.DataFrame]] = []

    if result is None:
        return items  # no-op

    # Single DataFrame -> default table
    if isinstance(result, pd.DataFrame):
        items.append((default_table, result))
        return items

    # Tuple (table, df)
    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], pd.DataFrame) and isinstance(result[0], str):
        items.append((result[0], result[1]))
        return items

    # List/tuple of DataFrames -> same default table
    if isinstance(result, (list, tuple)) and result and all(isinstance(x, pd.DataFrame) for x in result):
        items.extend((default_table, df) for df in result)  # append all to same table
        return items

    # List/tuple of (table, df) pairs
    if isinstance(result, (list, tuple)) and result and all(
        isinstance(x, (list, tuple)) and len(x) == 2 and isinstance(x[0], str) and isinstance(x[1], pd.DataFrame)
        for x in result
    ):
        items.extend((tbl, df) for tbl, df in result)
        return items

    # Mapping cases
    if isinstance(result, Mapping):
        # Shape: {"data": <df|list[dict]|dict-of-cols>, "table": "Name"}
        if "data" in result:
            table = result.get("table", default_table)
            df = result["data"]
            df = _to_dataframe(df)
            items.append((str(table), df))
            return items

        # Shape: {"TableA": df_or_records, "TableB": df_or_records, ...}
        ok = True
        for key, val in result.items():
            try:
                df = _to_dataframe(val)
            except TypeError:
                ok = False
                break
            items.append((str(key), df))
        if ok and items:
            return items

    # Sequence of dicts (records) -> default table
    if isinstance(result, (list, tuple)) and (not result or isinstance(result[0], Mapping)):
        df = _to_dataframe(result)
        items.append((default_table, df))
        return items

    # Dict-of-columns -> default table
    if isinstance(result, Mapping):
        try:
            df = _to_dataframe(result)
            items.append((default_table, df))
            return items
        except TypeError:
            pass

    raise TypeError(
        "Unsupported result shape. Return one of: "
        "DataFrame; (table, DataFrame); list[DataFrame]; list[(table, DataFrame)]; "
        "dict with {'data': <records|df|dict-of-cols>, 'table': <name>}; "
        "dict mapping table-><df|records|dict-of-cols>; list[dict]; or dict-of-columns."
    )

def collect_returned_results(
    db_path: Union[str, Path],
    table: str = "Report",
    *,
    if_exists: Literal["fail", "replace", "append"] = "append",
    insert_fn: InsertFn | None = None,
    ensure_parent: bool = True,
) -> Callable:
    """
    Decorator: after the wrapped function returns, normalize its result into one or
    more (table, DataFrame) pairs and insert each into a SQLite database.

    Accepted return shapes
    ----------------------
    - pd.DataFrame                          -> appended to `table`
    - (table_name: str, df: pd.DataFrame)   -> appended to `table_name`
    - list[pd.DataFrame]                    -> each appended to `table`
    - list[(table_name, df)]                -> routed per pair
    - {"data": <df|list[dict]|dict-of-cols>, "table": "MyTable"} -> routed to "MyTable"
    - {"TblA": df_or_records, "TblB": df2}  -> multiple tables
    - list[dict] or dict-of-columns         -> coerced to DataFrame -> appended to `table`
    - None                                  -> no-op

    Parameters
    ----------
    db_path : str | Path
        Destination SQLite file. A `.db` suffix is ensured.
    table : str, default "Report"
        Default table name when not provided in the result shape.
    if_exists : {"fail","replace","append"}, default "append"
        Insert mode (passed to pandas.DataFrame.to_sql).
    insert_fn : callable, optional
        Custom inserter with signature (db_path, df, table, if_exists).
    ensure_parent : bool, default True
        Create parent directories for `db_path` if missing.

    Raises
    ------
    TypeError
        If the function's result cannot be normalized to DataFrame(s).
    RuntimeError
        If any insert operation fails.

    Notes
    -----
    - This decorator **does not touch** or depend on non-picklable C#/.NET objects.
    - For large batches, consider chunking within your `insert_fn`.
    """
    insert_impl = insert_fn or _default_insert_fn
    dbp = Path(db_path)
    if dbp.suffix.lower() != ".db":
        dbp = dbp.with_suffix(".db")
    if ensure_parent:
        dbp.parent.mkdir(parents=True, exist_ok=True)
    dbp_str = str(dbp)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            pairs = _normalize_result(result, default_table=table)
            for tbl, df in pairs:
                if df is None or df.empty:
                    continue
                try:
                    insert_impl(dbp_str, df, tbl, if_exists)
                except Exception as exc:
                    raise RuntimeError(f"Failed to insert into table '{tbl}' in '{dbp_str}'.") from exc

            return result
        return wrapper
    return decorator

