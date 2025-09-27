from __future__ import annotations
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, Tuple, Union, Literal, Callable, List
from functools import wraps
import pandas as pd

InsertFn = Callable[[str, pd.DataFrame, str, str], None]  # (db_path, df, table, if_exists)


def _default_insert_fn(db: str, df: pd.DataFrame, table: str, if_exists: str) -> None:
    """
    Default insertion implementation for `collect_returned_results`.

    Opens a short-lived SQLAlchemy engine for a SQLite file and writes a single
    DataFrame to a table using `pandas.DataFrame.to_sql`.

    Parameters
    ----------
    db : str
        Target SQLite database path. Created if it does not exist.
    df : pandas.DataFrame
        Data to write.
    table : str
        Destination table name. Created if missing.
    if_exists: {"fail", "replace", "append"}
        Passed through to `DataFrame.to_sql`:
        - "fail": raise if table exists
        - "replace": drop and recreate the table, then insert
        - "append": append rows into the existing table

    Returns
    -------
    None

    Raises
    ------
    ImportError
        If SQLAlchemy is not installed.
    sqlalchemy.exc.SQLAlchemyError
        On engine/connection errors.
    pandas.errors.DatabaseError or ValueError
        Propagated from `to_sql` on I/O/typing issues.
    OSError
        On path/permission problems.

    Side Effects
    ------------
    - Creates the SQLite file and the table schema if missing.
    - May drop and recreate the table when `if_exists="replace"`.

    Cautions
    --------
    - **Table name safety: ** `to_sql` will quote identifiers, but avoid passing user-controlled
      table names to minimize the risks of unintended table creation or injection.
    - **Dtype inference: ** `to_sql` infers SQL types and may coerce mixed-type columns to TEXT.
      Define consistent dtypes up-front for critical data.
    - **Engine lifecycle: ** The engine is ephemeral and not connection-pooled here. For
      high throughput or multi-inserts, supply a custom `insert_fn` that reuses a connection,
      wraps inserts in a transaction, and/or enables WAL mode.

    Rationale
    ---------
     Provides a minimal, dependency-light default while encouraging power users to swap in a
       specialized `insert_fn` for performance and control.
    """

    from sqlalchemy import create_engine
    eng = create_engine(f"sqlite:///{db}")
    df.to_sql(table, eng, if_exists=if_exists, index=False)


def _to_dataframe(obj: Any) -> pd.DataFrame:
    """
    Best-effort coercion of common Python shapes into a `pandas.DataFrame`.

    Accepted shapes
    ---------------
    - `pandas.DataFrame`: returned as-is.
    - List/tuple of mappings (records): `[{...}, {...}]` -> `DataFrame(records)`.
    - Mapping of columns to sequences/scalars (dict-of-columns): `{"col": [..], ...}`
      -> `DataFrame(mapping)`.

    Parameters
    ----------
    obj : Any
        The object to coerce.

    Returns
    -------
    pandas.DataFrame
        A new DataFrame view of `obj` when possible.

    Raises
    ------
    TypeError
        If `obj` is not a DataFrame, list/tuple of mappings, or dict-of-columns.

    Cautions
    --------
    - **Heterogeneous keys in records: ** Building a DataFrame from a list of dicts with
      non-uniform keys will introduce `NaN` for missing entries.
    - **Dict-of-columns alignment: ** Column lengths should match; otherwise pandas will
      broadcast scalars or raise.
    - **Object dtype:** Mixed types can yield `object` dtype, affecting performance and
      downstream SQL type inference.
    - **Memory footprint: ** Coercion copies data in many cases; large inputs may be costly.

    Side Effects
    ------------
    None (pure transformation).

    Rationale
    ---------
    Centralize shape-to-DataFrame coercion so callers and normalizers can share consistent
    behavior and error messages.
    """

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
    Normalize a function's return value to a uniform list of `(table, DataFrame)` pairs.

    Supported shapes (in evaluation order)
    --------------------------------------
    1) `None` -> `[]` (no-op).
    2) `DataFrame` -> `[(default_table, df)]`.
    3) `(table: str, df: DataFrame)` -> `[(table, df)]`.
    4) `list/tuple` of `DataFrame` -> `[(default_table, df_1), (default_table, df_2), ...]`.
    5) `list/tuple` of `(table, DataFrame)` -> each routed per pair.
    6) Mapping with `{"data": <df|records|dict-of-cols>, "table": "Name"}` -> a single pair.
    7) Mapping of `{"TblA": df_or_records, "TblB": df2, ...}` -> multiple pairs.
    8) Sequence of mappings (records) -> coerced to DataFrame -> `[(default_table, df)]`.
    9) Dict-of-columns -> coerced to DataFrame -> `[(default_table, df)]`.

    Parameters
    ----------
    result : Any
        The object to interpret.
    default_table : str
        Table name to use when the shape does not carry its own table.

    Returns
    -------
    list[tuple[str, pandas.DataFrame]]
        A list of normalized `(table, DataFrame)` pairs; may be empty.

    Raises
    ------
    TypeError
        If `result` does not match any supported shape.

    Cautions
    --------
    - **Ambiguity in mappings:v** A mapping with a `"data"` key is treated as the
      special case (6). Otherwise, the function attempts to interpret the mapping as
      a table->payload mapping (7). If neither fit, a final attempt interprets it
      as a dict-of-columns (9).
    - **Evaluation order matters: ** More specific shapes are matched before general ones.
      E.g., a two-tuple of `(name, df)` will not be mistaken for a generic sequence.
    - **Ordering: ** For shape (7), Python dicts preserve insertion order (3.7+), so
      output order mirrors the input mapping order.
    - **Data coercion: ** When records/dict-of-columns are provided, `_to_dataframe` handles
      the conversion. See its cautions on dtype and memory.

    Side Effects
    ------------
    - Allocates new DataFrames when coercion is needed; may copy data.

    Rationale
    ---------
     Provides a single, predictable normalization pathway that supports flexible return
    types while keeping the downstream insert loop trivial.
    """

    items: List[Tuple[str, pd.DataFrame]] = []

    if result is None:
        return items  # no-op

    # Single DataFrame -> default table
    if isinstance(result, pd.DataFrame):
        items.append((default_table, result))
        return items

    # Tuple (table, df)
    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], pd.DataFrame) and isinstance(result[0],
                                                                                                             str):
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


def write_results_to_sql(
        db_path: Union[str, Path],
        table: str = "Report",
        *,
        if_exists: Literal["fail", "replace", "append"] = "append",
        insert_fn: InsertFn | None = None,
        ensure_parent: bool = True,
) -> Callable:
    """
    Decorator factory: collect the wrapped function's returned data and insert it or saves it into SQLite database.

    After the wrapped function executes, its return value is normalized to a list of
    `(table, DataFrame)` pairs via `_normalize_result` and inserted into `db_path` using
    either the provided `insert_fn` or the default `_default_insert_fn` (which relies on
    `pandas.DataFrame.to_sql` + SQLAlchemy). The original return value is passed through
    unchanged to the caller.

    Accepted return shapes
    ----------------------
    - `pd.DataFrame`                          -> appended to `table`
    - `(table_name: str, df: pd.DataFrame)`   -> appended to `table_name`
    - `list[pd.DataFrame]`                    -> each appended to `table`
    - `list[(table_name, df)]`                -> routed per pair
    - `{"data": <df|list[dict]|dict-of-cols>, "table": "MyTable"}` -> to "MyTable"
    - `{"TblA": df_or_records, "TblB": df2}`  -> multiple tables
    - `list[dict]` or `dict-of-columns`       -> coerced to DataFrame -> appended to `table`
    - `None`                                  -> no-op

    Parameters
    ----------
    db_path : str | pathlib.Path
        Destination SQLite file. A `.db` suffix is enforced if missing. If `ensure_parent`
        is True, parent directories are created.
    table : str, default "Report"
        Default table name when the return shape does not carry one.
    if_exists: {"fail", "replace", "append"}, default "append"
        Passed to `to_sql` by the inserter. See panda docs for semantics.
    insert_fn : callable, optional
        Custom inserter `(db_path, df, table, if_exists) -> None`. Use this to:
        - reuse a single connection/transaction across multiple tables,
        - enable SQLite WAL mode and retry on lock,
        - control dtype mapping or target a different DBMS.
    ensure_parent : bool, default True
        If True, create missing parent directories for `db_path`.

    Returns
    -------
    Callable
        A decorator that, when applied to a function, performs the persistence step
        after the function returns and then yields the original result.

    Raises
    ------
    TypeError
        If the wrapped function's result cannot be normalized by `_normalize_result`.
    RuntimeError
        If any insert operation fails (original exception is chained as `__cause__`).
    OSError
        On path or filesystem errors when creating the database directory/file.

    Side Effects
    ------------
    - Creates parent directories for `db_path` (when `ensure_parent=True`).
    - Creates/opens the SQLite database and writes one or more tables.
    - **Skips empty frames**: pairs where `df` is `None` or `df.empty` are ignored.
    - May DROP + CREATE the table when `if_exists="replace"`.

    Cautions
    --------
    - **SQLite concurrency: ** Concurrent writers can trigger "database is locked".
      Consider a custom `insert_fn` enabling WAL mode, retries, and transactional
      batching for robustness.
    - **Table name safety: ** Avoid propagating untrusted table names; identifier quoting
      is driver-dependent.
    - **Schema drift:** `to_sql` infers SQL schema from the DataFrame's dtypes each call.
      Ensure stable dtypes or manage schema explicitly in your `insert_fn`.
    - **Timezones: ** Pandas may localize/naivify datetime on writing; verify round-trips
      if timezone fidelity matters.
    - **Performance: ** Creating a new engine/connection per insert is simple but not optimal.
      For high-volume pipelines, supply an `insert_fn` that reuses a connection and commits
      once per batch.

    Design rationale
    ----------------
    Separates computation from persistence. The decorator is explicit about *where* data
    goes (db path, table names) and flexible about *what* callers return, reducing boilerplate
    in the business logic while still allowing power users to override insertion strategy.

    Examples
    --------
    Basic usage, single table with default appends::

        @collect_returned_results("outputs/results.db", table="Report")
        def run_analysis(...):
            return df  # a DataFrame

    Multiple tables using a mapping shape::

        @collect_returned_results("outputs/results.db")
        def summarize(...):
            return {"Summary": df1, "Metrics": df2}

    Custom inserter enabling WAL mode and a single transaction::

        def wal_insert(db, df, table, if_exists):
            import sqlite3
            con = sqlite3.connect(db, isolation_level="DEFERRED")
            try:
                con.execute("PRAGMA journal_mode=WAL;")
                df.to_sql(table, con, if_exists=if_exists, index=False)
                con.commit()
            finally:
                con.close()

        @collect_returned_results("out.db", insert_fn=wal_insert)
        def compute(...):
            ...

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
