"""
Interface to APSIM simulation models using Python.NET 
"""
from collections import namedtuple
from os.path import exists
from sqlite3 import connect
from pandas import read_sql
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial
import pandas as pd
from pandas import read_sql_query as rsq
from pandas import errors
from sqlalchemy import create_engine
from os.path import exists

import sqlite3


def read_with_query(db, query):
    """
        Executes an SQL query on a specified database and returns the result as a Pandas DataFrame.

        Args:
        db (str): The database file path or identifier to connect to.
        query (str): The SQL query string to be executed. The query should be a valid SQL SELECT statement.

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
    df = rsq(query, conn)
    conn.close()
    return df
def get_db_table_names(d_b):
    """

    :param d_b: database name or path
    :return: all names sql database table names existing within the database
    """
    d_b = f'sqlite:///{d_b}'
    #engine = create_engine(mssql+pymssql://sa:saPassword@localhost:52865/{d_b})')
    engine = create_engine(d_b)
    return engine.table_names()


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

        Example:
            # Define the database and the table name
            database_path = 'your_database.sqlite'
            table_name = 'your_table'

            # Get the table data as a DataFrame
            >>>> df = read_db_table(database_path, table_name)

            # Work with the DataFrame
           >>>> print(df)

        Note:
            - Ensure that the database path and table name are correct.
            - The function uses 'sqlite3' for connecting to the database; make sure it is appropriate for your database.
            - This function retrieves all records from the specified table. Use with caution if the table is very large.
            
        """
    # table = kwargs.get("table")
    try:
        conn = sqlite3.connect(db)
        query = f"SELECT * FROM {report_name}"
        df = rsq(query, conn)
        conn.close()
        return df
    except errors.DatabaseError as ed:
        print(repr(ed))
        print(f" Seems like the specified table name: {report_name} does not exists in {db} data base")
        if exists(db):
           print(f"report_name(s) should be any of the following:: {get_db_table_names(db)}")


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

