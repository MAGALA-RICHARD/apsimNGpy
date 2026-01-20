import sqlite3
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


def get_key(db, value, table_name=None):
    """
    get the last completed simulation key and return None if databse is empty or key not found
    @param db: database path
    @param value: key to return
    @return: any value type matching the entered values
    """
    if table_name is None:
        table_name = database_info.table_name
    try:
        engine = create_engine(f"sqlite:///{db}") if isinstance(db, (Path, str)) else db
        with engine.connect() as conn:
            if table_name not in inspect(conn).get_table_names():
                return None

            row = conn.execute(
                text('SELECT 1 FROM completed WHERE "ID" = :v LIMIT 1'),
                {"v": value},
            ).fetchone()

            return value if row else None
    except  OperationalError:
        return None


def register_key(key, db, table_column=None, if_exists='append', table_name=None):
    """store completed simulation key or value"""
    if table_column is None:
        table_column = database_info.table_column
    if table_name is None:
        table_name = database_info.table_name
    out = DataFrame([{f"{table_column}": key}])
    out[table_column] = out[table_column].astype(type(key))
    write_df_to_sql(out, db_or_con=db, table_name=table_name, if_exists=if_exists,
                    chunk_size=None,
                    index=False)
    return db


def clear_db(db, table_name=None):
    """drops table for the next clean session"""
    if table_name is None:
        table_name = database_info.table_name
    drop_table(db=db, table_name=table_name)


@dataclass(slots=True, frozen=False)
class JobTracker:
    db: str | Path
    completed_table: str
    completed_column: str = "__ID__"

    def __hash__(self) -> int:
        """
        Hash based on immutable, normalized identifiers.
        """
        db_key = str(Path(self.db).resolve()) if isinstance(self.db, (str, Path)) else str(self.db)
        return hash((db_key, self.completed_table, self.completed_column))

    def all_tasks_done(self) -> None:
        """
        Drop the completed-tasks table to prepare for a clean session.
        """
        drop_table(db=self.db, table_name=self.completed_table)

    def register_task_done(self, key, if_exists: str = "append") -> None:
        """
        Record a completed task key in the database.
        """
        col = self.completed_column
        out = DataFrame([{col: key}])
        out[col] = out[col].astype(type(key))

        write_df_to_sql(
            out,
            db_or_con=self.db,
            table_name=self.completed_table,
            if_exists=if_exists,
            chunk_size=None,
            index=False,
        )

    def get_done_task(self, task_value):
        """
        Check whether a task value has already been completed.

        Returns
        -------
        task_value or None
            Returns the task value if found, otherwise None.
        """
        try:
            with sqlite3.connect(self.db) as con:
                cursor = con.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                    (self.completed_table,),
                )
                if cursor.fetchone() is None:
                    return None

                query = f"""
                    SELECT 1
                    FROM "{self.completed_table}"
                    WHERE "{self.completed_column}" = ?
                    LIMIT 1"""
                row = con.execute(query, (task_value,)).fetchone()
                return task_value if row else None

        except sqlite3.OperationalError:
            return None
