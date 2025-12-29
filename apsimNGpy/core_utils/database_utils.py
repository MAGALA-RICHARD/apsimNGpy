"""
Interface to APSIM simulation models using Python.NET 
"""
from __future__ import annotations

import gc
import sqlite3
from collections import namedtuple
from functools import wraps
from os.path import exists
from typing import Callable, Literal, Union, List, Tuple, Mapping, Any

import numpy as np
from pandas import DataFrame
from pandas import read_sql_query as rsq
from sqlalchemy import create_engine, inspect, Table, MetaData
from sqlalchemy.exc import NoSuchTableError
from apsimNGpy.core.pythonet_config import *
from apsimNGpy.exceptions import TableNotFoundError
from pandas import DataFrame
from itertools import islice, repeat
from typing import Iterable, Iterator, List, Optional, TypeVar, Callable
import pandas as pd
from typing import Dict, Tuple, Hashable, List
from sqlalchemy.engine import Engine  # or use any DB-API connection

T = TypeVar("T")

from sqlalchemy.engine import Engine, Connection
from sqlalchemy.orm import Session

UNKNOWN_FLAG = 'UNKNOWN'


def _identify_db_object(obj):
    if isinstance(obj, (Engine, Connection, Session)):
        return "sqlalchemy"
    elif isinstance(obj, sqlite3.Connection) or (
            hasattr(obj, "cursor") and callable(obj.cursor)
    ):
        return "raw_sql"
    else:
        return UNKNOWN_FLAG


def detect_connection(obj):
    ob = _identify_db_object(obj)
    if ob != UNKNOWN_FLAG:
        return True


def delete_table(db, table_name):
    """deletes the table in a database.

    ⚠️ Proceed with caution: this operation is irreversible.
    """
    # database connection
    db = os.path.realpath(db)
    engine = create_engine(f"sqlite:///{db}")
    metadata = MetaData()
    try:
        # Load table
        table_to_drop = Table(f"{table_name}", metadata, autoload_with=engine)

        # Drop it
        table_to_drop.drop(engine)
    except NoSuchTableError:
        pass
    finally:
        engine.dispose(close=True)


def delete_all_tables(db: str) -> None:
    """
    Deletes all tables in the specified SQLite database.

    ⚠️ Proceed with caution: this operation is irreversible.

    Args:
        db (str): Path to the SQLite database file.
    """
    db_path = os.path.realpath(db)
    engine = create_engine(f"sqlite:///{db_path}")
    metadata = MetaData()
    try:
        # Reflect the current database schema
        metadata.reflect(bind=engine)

        # Drop all tables
        metadata.drop_all(bind=engine)
    except NoSuchTableError:
        pass
    finally:
        engine.dispose(close=True)


def dataview_to_dataframe(_model, reports):
    """
    Convert .NET System.Data.DataView to Pandas DataFrame.
    report (str, list, tuple) of the report to be displayed. these should be in the simulations
    :param apsimng model: CoreModel object or instance
    :return: Pandas DataFrame
    """

    from System.Data import DataView
    try:
        _model._DataStore.Open()
        pred = _model._DataStore.Reader.GetData(reports)
        dataview = DataView(pred)
        if dataview.Table:
            # Extract column names
            column_names = [col.ColumnName for col in dataview.Table.Columns]

            # Extract data from rows
            data = []
            for row in dataview:
                data.append([row[col] for col in column_names])  # Extract row values

            # Convert to Pandas DataFrame
            df = DataFrame(data, columns=column_names)
            return df
        else:
            logger.error("No DataView was found")
    finally:
        _model._DataStore.Close()


def read_with_query(db, query):
    """
    Executes an SQL query on a specified SQLite database and returns the result as a
    pandas DataFrame.

    Parameters
    ----------
    db : str
        Database file path or identifier to connect to.
    query : str
        SQL query string to execute. Must be a valid ``SELECT`` statement.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the results of the SQL query.

    Examples
    --------
    Define the database and the query

    .. code-block:: python

        database_path = 'your_database.sqlite'
        sql_query = 'SELECT * FROM your_table WHERE condition = values'

        # Get the query result as a DataFrame
        df = read_with_query(database_path, sql_query)

    Notes
    -----
    - Opens a connection to the SQLite database, executes the given query,
      loads the results into a DataFrame, and then closes the connection.
    - Ensure that the database path and query are correct and that the query
      is a proper SQL ``SELECT`` statement.
    - Uses `sqlite3` for the connection; confirm it is appropriate for your database.

    .. seealso::

       Related API: :meth:`~apsimNGpy.core_utils.database_utils.read_db_table`
    """

    # table = kwargs.get("table")
    with sqlite3.connect(db) as conn:
        df = rsq(query, conn)
        return df


def get_db_table_names(db):
    """
    Parameter
    -----------
    db : database name or path.

    return: list of table names
       All names ``SQL`` database table ``names`` existing within the database
    """
    d_b = f'sqlite:///{db}'
    # engine = create_engine(mssql+pymssql://sa:saPassword@localhost:52865/{d_b})')
    engine = create_engine(d_b)
    insp = inspect(engine)
    return insp.get_table_names()


def pd_save_todb(datas: dict, database, if_exists):
    engine = create_engine(f'sqlite:///{database}')
    try:
        table_names, data = datas

        data.to_sql(table_names, engine, if_exists=if_exists, index=False)
    finally:
        engine.dispose(close=True)


def pl_save_todb(datas: tuple, database: str, if_exists: str):
    engine = create_engine(f'sqlite:///{database}')
    try:
        table_name, data = datas

        # Convert Polars DataFrame to pandas before saving
        data.to_pandas().to_sql(table_name, engine, if_exists=if_exists, index=False)
    finally:
        engine.dispose(close=True)


def custom_remove_file(file):
    if os.path.exists(file):
        os.remove(file)


def read_db_table(db: Union[str, Path], report_name: str = None, sql_query=None):
    """
    Connects to a specified SQLite database, retrieves the entire contents of a
    specified table, and returns the results as a pandas DataFrame.

    Parameters
    ----------
    db : str | Path, database connection object
        Path to the SQLite database file.
    report_name : str
        Name of the table in the database from which to retrieve data.
    sql_query: str default is None
        if it is none, we assume a table

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing all records from the specified table.

    Examples
    --------
    >>> database_path = 'your_database.sqlite' # or connection object
    >>> table_name = 'your_table'
    >>> ddf = read_db_table(database_path, table_name)
    >>> print(ddf)

    Notes
    -----
    - Establishes a connection to the SQLite database, executes ``SELECT *`` on the
      specified table, loads the result into a DataFrame, and then closes the
      connection.
    - Ensure that the database path and table name are correct.
    - This function retrieves **all** records; use with caution for very large
      tables.
    """
    assert any([report_name, sql_query]), "Please provide at least a table name or a SQL query."
    # table = kwargs.get("table")
    if detect_connection(db):
        ENGINE = db
    else:
        DB = f'sqlite:///{db}'
        ENGINE = create_engine(DB)
    query = sql_query or f"SELECT * FROM {report_name}"
    try:

        df = rsq(query, ENGINE)

        return df
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            logger.error(f"Table '{report_name}' not found in the database.")
            available_tables = get_db_table_names(db)  # Assuming this function exists
            logger.warning(f"Available tables: {available_tables}")
        else:
            logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while reading table '{report_name}': {e}")
    finally:
        if hasattr(ENGINE,'dispose'):#sqlalchemy

            ENGINE.dispose(close=True)

        elif hasattr(ENGINE, 'close'):
            #raw sql
            ENGINE.close()
        gc.collect()


def load_database(path):
    assert exists(path), "error from__ (database_utils module) file path does not exist try a different=========="
    assert path.endswith(
        ".db"), "error from___ (database_utils module) the file path does not have .db extension======="
    path_info = namedtuple('db', ['path'])
    try:
        named_tuple = path_info(path=path)
        return named_tuple
    except Exception as e:
        print(repr(e))
        raise


def sql_data_from_df(df, con, table_name, chunksize=None, dtype=None,
                     if_exists='append', index=False, schema=None):
    sh = df.shape
    if sh:
        if sh[0] > 4000:
            chunksize = int(np.sqrt(sh[0]))
    df.to_sql(table_name, con, chunksize=chunksize, if_exists=if_exists, index=index, schema=schema, dtype=dtype)


SchemaKey = Tuple[Tuple[Hashable, str], ...]


def write_schema_grouped_tables(
        schema_to_df: Dict[SchemaKey, pd.DataFrame],
        engine: Engine,
        *,
        base_table_prefix: str = "group",
        schema_table_name: str = "_schema",
        chunksize=None, dtype=None,
        if_exists='append', index=False, schema=None
) -> None:
    """
    For each (schema, DataFrame) pair:
      - create a dedicated SQL table and insert the DataFrame,
      - record its schema and table name in a separate schema table.

    Parameters
    ----------
    schema_to_df : dict
        Mapping from schema signature to concatenated DataFrame.
        Schema signature format: ((column_name, dtype_str), ...).
    engine : sqlalchemy.engine.Engine or DB-API connection
        Database connection/engine to write to.
    base_table_prefix : str, optional
        Prefix for generated table names (e.g., 'apsim_group_1', 'apsim_group_2', ...).
    schema_table_name : str, optional
        Name of the schema metadata table.
    """
    schema_rows: List[dict] = []

    for i, (schema_key, df) in enumerate(schema_to_df.items(), start=1):
        # 1) Create a table name for this group
        table_name = f"{base_table_prefix}_{i}"

        # 2) Write the actual data table
        sql_data_from_df(df, engine, chunksize=chunksize, table_name=table_name, dtype=dtype,

                         if_exists=if_exists, index=index)

        # 3) Record the schema for this table
        # schema_key looks like: (('CheckpointID','int64'), ('Clock.Today','object'), ...)
        for col_order, (col_name, dtype_str) in enumerate(schema_key):
            schema_rows.append(
                {
                    "table_name": table_name,
                    "schema_group": i,  # optional grouping ID
                    "col_order": col_order,
                    "column_name": col_name,
                    "dtype": dtype_str,
                }
            )

    # 4) Build the schema DataFrame and write as a separate table
    schema_df = pd.DataFrame(schema_rows)

    schema_df.to_sql(
        schema_table_name,
        engine,
        if_exists="replace",  # it is expected to be One, so replace is appropriate
        index=False,
    )


def clear_table(db: Union[str, Path], table_name: str):
    """
    Deletes all rows from all user-defined tables in the given SQLite database.

    Parameters
    ----------
    db : str | Path
        Path to the SQLite database file.

    table_name : str
         Name of the target table to delete from the database `db`

    Returns
    -------
    None
        This function does not return a value.

    .. seealso::

       Related API: :meth:`~apsimNGpy.core_utils.database_utils.clear_all_tables`
    """

    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name}")
        conn.commit()


def clear_all_tables(db):
    """
    Deletes all rows from all user-defined tables in the given SQLite database.

    Parameters
    ----------
    db : str | Path
        Path to the SQLite database file.

    Returns
    -------
    None
        This function does not return a value.

    .. seealso::

       Related API: :meth:`~apsimNGpy.core_utils.database_utils.clear_table`
    """

    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()

        # Fetch all table names (excluding internal SQLite tables)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()

        # Clear all tables
        for (table_name,) in tables:
            cursor.execute(f"DELETE FROM '{table_name}'")

        conn.commit()


def check_column_value_exists(_db: os.PathLike, table_name: str, value_to_check: str, column_name: str, exists) -> bool:
    db = Path(_db)
    if db.is_file() and db.suffix == '.db':
        with sqlite3.connect(_db) as conn:
            cursor = conn.cursor()
            query = f"SELECT EXISTS(SELECT 1 FROM {table_name} WHERE {column_name} = ?)"

            # Execute the query
            try:
                cursor.execute(query, (value_to_check,))
                ans_exists = cursor.fetchone()[0]
                if ans_exists:
                    return True
            except TableNotFoundError as e:
                # expect this error to occur when the database is not yet created,
                return False


InsertFn = Callable[[str, DataFrame, str, str], None]  # (db_path, df, table, if_exists)


def _default_insert_fn(db: str, df: DataFrame, table: str, if_exists: str) -> None:
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
    df.to_sql(table, eng, if_exists=if_exists, index=False,chunksize=20)


def _to_dataframe(obj: Any) -> DataFrame:
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

    if isinstance(obj, DataFrame):
        return obj
    # list of dicts OR dict-of-columns
    if isinstance(obj, (list, tuple)) and (not obj or isinstance(obj[0], Mapping)):
        return DataFrame(list(obj))
    if isinstance(obj, Mapping):
        # dict-of-columns (values are list-like/scalars)
        return DataFrame(obj)
    raise TypeError("Cannot coerce object to DataFrame. Expected DataFrame, list[dict], or dict-of-columns.")


def _normalize_result(
        result: Any,
        default_table: str,
) -> List[Tuple[str, DataFrame]]:
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

    items: List[Tuple[str, DataFrame]] = []

    if result is None:
        return items  # no-op

    # Single DataFrame -> default table
    if isinstance(result, DataFrame):
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
    Examples:

        >>> from pandas import DataFrame
        >>> from apsimNGpy.core_utils.database_utils import write_results_to_sql, read_db_table
        >>> @write_results_to_sql(db_path="db.db", table="Report", if_exists="replace")
        ... def get_report():
        ...     # Return a DataFrame to be written to SQLite
        ...     return DataFrame({"x": [2], "y": [4]})

        >>> _ = get_report()  # executes and writes to db.db::Report
        >>> db = read_db_table("db.db", report_name="Report")
        >>> print(db.to_string(index=False))
         x  y
         2  4

    .. seealso::

          Related API:
          :meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.save_tosql`,
          :meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.insert_data`
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
                    del df, tbl
                    gc.collect()
                except Exception as exc:

                    raise RuntimeError(f"Failed to insert into table '{tbl}' in '{dbp_str}'.") from exc

            # return result

        return wrapper

    return decorator


def chunker(
        data: Iterable[T],
        *,
        chunk_size: Optional[int] = None,
        n_chunks: Optional[int] = None,
        pad: bool = False,
        fillvalue: Optional[T] = None) -> Iterator[List[T]]:
    """
    Yield chunks from `data`.

    Choose exactly one of:
      - `chunk_size`: yield consecutive chunks of length `chunk_size`
        (last chunk may be shorter unless `pad=True`)
      - `n_chunks`: split data into `n_chunks` nearly equal parts
        (sizes differ by at most 1)

    Args
    ----
    data : Iterable[T]
        The input data (list, generator, etc.)
    chunk_size : int, optional
        Fixed size for each chunk (>=1).
    n_chunks : int, optional
        Number of chunks to create (>=1). Uses nearly equal sizes.
    pad : bool, default False
        If True and using `chunk_size`, pad the last chunk to length `chunk_size`.
    fill value : T, optional
        Value to use when padding.

    Yields
    ------
    List[T]
        Chunks of the input data.

    Raises
    ------
    ValueError
        If neither or both of `chunk_size` and `n_chunks` are provided,
        or if provided values are invalid.
    """
    # exactly one of chunk_size / n_chunks
    if (chunk_size is None) == (n_chunks is None):
        raise ValueError("Provide exactly one of `chunk_size` or `n_chunks`.")

    if n_chunks is not None:
        if n_chunks <= 0:
            raise ValueError("`n_chunks` must be >= 1.")
        # Need length to distribute evenly
        seq = list(data)
        n = len(seq)
        base, rem = divmod(n, n_chunks)
        start = 0
        for i in range(n_chunks):
            size = base + (1 if i < rem else 0)
            yield seq[start:start + size]
            start += size
        return

    # chunk_size mode
    if chunk_size <= 0:
        raise ValueError("`chunk_size` must be >= 1.")
    it = iter(data)
    while True:
        chunk = list(islice(it, chunk_size))
        if not chunk:
            break
        if pad and len(chunk) < chunk_size:
            chunk.extend(repeat(fillvalue, chunk_size - len(chunk)))
        yield chunk


if __name__ == "__main__":
    #test
    @write_results_to_sql(db_path='db.db', table='Report')
    def get_report():
        return DataFrame(dict(x=2, y=4))


    ch = list(chunker(range(100), n_chunks=10))
    conn = create_engine('sqlite:///:memory:')
    try:
      assert detect_connection(conn), "detect connection not working with alchemy"
    finally:
       conn.dispose(close=True)
    with sqlite3.connect(":memory:") as sqLconn:
        assert detect_connection(sqLconn), "detect connection not working on sql raw connection"
