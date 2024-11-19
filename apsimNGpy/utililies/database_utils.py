"""
Interface to APSIM simulation models using Python.NET 
"""
import sqlite3
from collections import namedtuple
from os.path import exists

from pandas import errors
from pandas import read_sql_query as rsq
from sqlalchemy import create_engine, inspect

logger = logging.getLogger(__name__)


def get_db_table_names(sqlite_db):
    """

    :param sqlite_db: database name or path
    :return: all names sql database table names existing within the database
    """
    sqlite_db = f'sqlite:///{sqlite_db}'
    # engine = create_engine(mssql+pymssql://sa:saPassword@localhost:52865/{d_b})')
    engine = create_engine(sqlite_db)
    insp = inspect(engine)
    return insp.get_table_names()


def _read_table(conn, table_name):
    """
    It gets a connection and records a table using that live connection
    conn: A live database connection. This is a bit of a premature optimization.
    We do not wish to open and close many connections just in case we wish to read multiple tables.
    table_name: str
    The name of the table to read.
    Returns a pandas dataframe with the data. This function must be wrapped in appropriate error
    """
    query = f"SELECT * FROM {table_name}"
    return rsq(query, conn)


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
    try:
        # conn = sqlite3.connect(db)
        with sqlite3.connect(db) as conn:
            return _read_table(conn, report_name)
    except errors.DatabaseError as ed:
        # print(repr(ed))
        # print(f" Seems like the specified table name: {report_name} does not exists in {db} data base")
        if exists(db):
            print(f"report_name(s) should be any of the following:: {get_db_table_names(db)}")
        raise errors.DatabaseError(f"{str(ed)} occurred")


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
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Clear all tables
        for table in tables:
            cursor.execute(f"DELETE FROM {table[0]}")

        conn.commit()


def read_sqlite_simulation_data(sqlite_db, table_names=None):
    """
    Reads all the data from an sql database and returns a dataframe
    """
    # from .database_utils import get_db_table_names, _read_table

    # note a string is also iterable
    if table_names is None:
        table_names = get_db_table_names(sqlite_db)  # is a simple list of table names
        to_exclude = ['_InitialConditions', '_Messages', '_Checkpoints', '_Units']
        tables_to_read = [table_name for table_name in table_names if table_name not in to_exclude]
    elif isinstance(table_names, str):
        tables_to_read = [table_names]
    else:
        assert isinstance(table_names, Iterable)
        tables_to_read = table_names

    dataframe_dict = {}
    # Don't catch errors when you do not need. Minimize the number of times you do try catch.
    # In other words, write code that fails and fails fast. That's the best way to get working code fast.
    with sqlite3.connect(sqlite_db) as conn:
        for table in tables_to_read:
            dataframe_dict[table] = _read_table(conn, table)
        return dataframe_dict


def read_simulation_results(datastore, report_name=None):
    """ returns all data frame the available report tables"""
    dataframe_dict = read_sqlite_simulation_data(datastore, table_names=report_name)
    if len(dataframe_dict) == 0:
        logger.info("the data dictionary is empty. no data has been returned")
    if report_name is not None and report_name in dataframe_dict:
        return dataframe_dict[report_name]
    return dataframe_dict
