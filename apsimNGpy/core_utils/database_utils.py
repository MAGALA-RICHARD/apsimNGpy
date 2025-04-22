"""
Interface to APSIM simulation models using Python.NET 
"""
import os
import sqlite3
from collections import namedtuple
from os.path import exists
from pathlib import Path
from apsimNGpy.core_utils.utils import timer
from pandas import errors
from pandas import read_sql_query as rsq
from sqlalchemy import create_engine, inspect
from apsimNGpy.core_utils.exceptions import TableNotFoundError
from apsimNGpy.settings import logger
from System.Data import DataView
from pandas import DataFrame

def dataview_to_dataframe(_model, reports):
    """
    Convert .NET System.Data.DataView to Pandas DataFrame.
    report (str, list, tuple) of the report to be displayed. these should be in the simulations
    :param apsimng model: CoreModel object or instance
    :return: Pandas DataFrame
    """
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
        Executes an SQL query on a specified database and returns the result as a Pandas DataFrame.

        Args:
        :db (str): The database file path or identifier to connect to.
        :query (str): The SQL query string to be executed. The query should be a valid SQL SELECT statement.

        Returns:
        pandas.DataFrame: A DataFrame containing the results of the SQL query.

        The function opens a connection to the specified SQLite database, executes the given SQL query,
        fetches the results into a DataFrame, then closes the database connection.

        Example:
            # Define the database and the query
            database_path = 'your_database.sqlite'
            sql_query = 'SELECT * FROM your_table WHERE condition = values'

            # Get the query result as a DataFrame
            df = read_with_query(database_path, sql_query)

            # Work with the DataFrame
            print(df)

        Note: Ensure that the database path and the query are correct and that the query is a proper SQL SELECT statement.
        The function uses 'sqlite3' for connecting to the database; make sure it is appropriate for your database.
        """
    # table = kwargs.get("table")
    conn = sqlite3.connect(db)
    try:
        df = rsq(query, conn)
        return df
    finally:
        conn.close()


def clear_dir(pat, exclude=None):
    if exclude is None:
        exclude = []
    files = []
    parts = ['apsimx', "db", 'db-shm', 'db-wal', 'csv', 'bak', 'met']
    patterns = [f'*.{i}' for i in parts if i not in exclude]

    for pattern in patterns:
        fi = list(Path(pat).rglob(pattern))
        files.extend(fi)
    for i in files:
        try:
            i.unlink(missing_ok=True)
        except PermissionError:
            ...


def get_db_table_names(d_b):
    """

    :param d_b: database name or path
    :return: all names sql database table names existing within the database
    """
    d_b = f'sqlite:///{d_b}'
    # engine = create_engine(mssql+pymssql://sa:saPassword@localhost:52865/{d_b})')
    engine = create_engine(d_b)
    insp = inspect(engine)
    return insp.get_table_names()


@timer
def read_db_table(db, report_name):
    """
        Connects to a specified database, retrieves the entire contents of a specified table,
        and returns the results as a Pandas DataFrame.

        Args:
            db (str): The database file path or identifier to connect to.
            report_name (str): name of the database table: The name of the table in the database from which to retrieve data.
        Returns:
            pandas.DataFrame: A DataFrame containing all the records from the specified table.

        The function establishes a connection to the specified SQLite database, constructs and executes a SQL query
        to select all records from the specified table, fetches the results into a DataFrame, then closes the database connection.

        Examples:
            # Define the database and the table name
            database_path = 'your_database.sqlite'
            table_name = 'your_table'

            # Get the table data as a DataFrame
            #>>>> ddf = read_db_table(database_path, table_name)

            # Work with the DataFrame
           #>>>> print(ddf)

        Note:
            - Ensure that the database path and table name are correct.
            - The function uses 'sqlite3' for connecting to the database; make sure it is appropriate for your database.
            - This function retrieves all records from the specified table. Use with caution if the table is very large.
            
        """
    # table = kwargs.get("table")
    DB = f'sqlite:///{db}'
    ENGINE = create_engine(DB)
    query = f"SELECT * FROM {report_name}"
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
        ENGINE.dispose(close=True)


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


def clear_table(db, table_name):
    """

    :param db: path to db
    :param table_name: name of the table to clear
    :return: None
    """
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name}")
        conn.commit()


def clear_all_tables(db):
    """
    
    :param db: path to database file
    :return: None
    """
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()

        # Fetch all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE ='table';")
        tables = cursor.fetchall()

        # Clear all tables
        for table in tables:
            cursor.execute(f"DELETE FROM {table[0]}")

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


if __name__ == "__main__":
    clear_dir(r'D:\package\src')
