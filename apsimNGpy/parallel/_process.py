from pathlib import Path
from sqlalchemy.exc import OperationalError, NoSuchTableError

from pandas import DataFrame
from apsimNGpy.core_utils.database_utils import drop_table
from apsimNGpy.core_utils.database_utils import write_df_to_sql
from sqlalchemy import create_engine, text, inspect
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TableInfo:
    table_name: str = 'completed'
    table_column: str = "ID"
    if_exists: str = 'append'


database_info = TableInfo()


def get_key(db, value):
    """
    get the last completed simulation key and return None if databse is empty or key not found
    @param db: database path
    @param value: key to return
    @return: any value type matching the entered values
    """
    try:
        engine = create_engine(f"sqlite:///{db}") if isinstance(db, (Path, str)) else db
        with engine.connect() as conn:
            if database_info.table_name not in inspect(conn).get_table_names():
                return None

            row = conn.execute(
                text('SELECT 1 FROM completed WHERE "ID" = :v LIMIT 1'),
                {"v": value},
            ).fetchone()

            return value if row else None
    except  OperationalError:
        return None


def write_key(key, db):
    """store completed simulation key or value"""
    out = DataFrame([{f"{database_info.table_column}": int(key)}])
    out[database_info.table_column] = out[database_info.table_column].astype(int)
    write_df_to_sql(out, db_or_con=db, table_name=database_info.table_name, if_exists=database_info.if_exists,
                    chunk_size=None,
                    index=False)
    return db


def clear_db(db):
    """drops table for the next clean session"""
    drop_table(db=db, table_name=database_info.table_name)
