"""
Interface to APSIM simulation models using Python.NET build on top of Matti Pastell farmingpy framework.
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
import sqlite3


def read_with_query(db, query):
    """
        Executes a SQL query on a specified database and returns the result as a Pandas DataFrame.

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
            sql_query = 'SELECT * FROM your_table WHERE condition = value'

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


def read_db_table(db, table):
    """
        Connects to a specified database, retrieves the entire contents of a specified table,
        and returns the results as a Pandas DataFrame.

        Args:
            db (str): The database file path or identifier to connect to.
            table (str): The name of the table in the database from which to retrieve data.
        Returns:
            pandas.DataFrame: A DataFrame containing all the records from the specified table.

        The function establishes a connection to the specified SQLite database, constructs and executes a SQL query
        to select all records from the specified table, fetches the results into a DataFrame, then closes the database connection.

        Example:
            # Define the database and the table name
            database_path = 'your_database.sqlite'
            table_name = 'your_table'

            # Get the table data as a DataFrame
            df = read_db_table(database_path, table_name)

            # Work with the DataFrame
            print(df)

        Note:
            - Ensure that the database path and table name are correct.
            - The function uses 'sqlite3' for connecting to the database; make sure it is appropriate for your database.
            - This function retrieves all records from the specified table. Use with caution if the table is very large.
        """
    # table = kwargs.get("table")
    conn = sqlite3.connect(db)
    query = f"SELECT * FROM {table}"
    df = rsq(query, conn)
    conn.close()
    return df


def load_database(path):
    assert exists(path), "error from__ (database_utils module) file path does not exist try a different=========="
    assert path.endswith(
        ".db"), "error from___ (database_utils module) the file path does not have .db extension======="
    path_info = namedtuple('db', ['path'])
    try:
        named_tuple = path_info(path=path)
        return named_tuple
    except Exception as e:
        print(repr(e))  # this error will be logged to the folder logs in the current working directory
        raise


def _read_simulation(datastore, report_name=None):
    '''
    returns all data frame the available report tables

    TODO this file is duplicated in runner/database_utils.py i did want to reimport it there
    '''
    conn = connect(datastore)
    conn.text_factory = lambda b: b.decode(errors='ignore')
    cursor = conn.cursor()

    # reading all table names

    table_names = [a for a in cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]

    table_list = []
    for i in table_names:
        table_list.append(i[0])
        # remove these
    # print(table_list)
    # rm = ['_InitialConditions', '_Messages', '_Checkpoints', '_Units']
    # for i in rm:
    #     if i in table_list:
    #         table_list.remove(i)
    #         # start selecting tables
    select_template = 'SELECT * FROM {table_list}'

    # create data fram dictionary to keep all the tables
    dataframe_dict = {}

    for tname in table_list:
        query = select_template.format(table_list=tname)
        dataframe_dict[tname] = read_sql(query, conn)
    # close the connection cursor
    conn.close()
    dfl = len(dataframe_dict)
    if len(dataframe_dict) == 0:
        print("the data dictionary is empty. no data has been returned")
        # else:
        # remove elements
        # print(f"{dfl} data frames has been returned")

    if report_name:
        return dataframe_dict[report_name]
    else:
        return dataframe_dict


def convert_data(data):
    data['Nitrogen'] = data['Nitrogen'].astype(int)
    ky = list(data.columns)
    if "Residue" in ky:
        data['Residue'] = data['Residue'].astype(float)
    return data


def query_data(df, N, R=None):
    if R:
        dat = df.loc[(df['Nitrogen'] == N) & (df['Residue'] == R)]
        # dat = df.query(f"Nitrogen== {N} and Residue == {R}")
    else:
        dat = df.loc[(df['Nitrogen'] == N)]
    return dat


# def query_data(df, N, R = None):
#     #data  = df.to_records(index=False)
#     if R:
#         dat =df.query(f'Nitrogen == {N} and Residue =={R}')
#         #dat = df.query(f"Nitrogen== {N} and Residue == {R}")
#     else:
#        dat = df.query(f'Nitrogen == {N}')
#     return dat

def excute_query_data(fileinput, N, R=None):
    # we load apsimx file with .apsimx file extension because we want its corresponding data base
    try:
        meta = load_database(fileinput)
        data = _read_simulation(meta.path)
        carbon = convert_data(data['Carbon'])
        # we query the data base by Residue and Nitrogen
        maizer, annual = convert_data(data["MaizeR"]), convert_data(data["Annual"])
        df_maize_yield, df_annual, df_carbon = query_data(maizer, N, R), query_data(annual, N, R), query_data(carbon, N,
                                                                                                              R)
        mean_n20 = np.mean(df_annual['TopN2O'])
        MineralN = np.mean(df_annual['MineralN'])
        leached_N = np.mean(df_annual['CumulativeAnnualLeaching'])
        carbon = np.mean(df_carbon['changeincarbon']) * -1
        Myield = np.mean(df_maize_yield['Yield'])
        prof_maize = Myield / 25.40 * 4.6650
        revenue = prof_maize
        Ncost = 1.8291246 * N
        profit = revenue - Ncost
        ghg_co2_co2eq = -1 * carbon * 44 / 128 * 1
        ghg_n02_co2eq = mean_n20 * 44 / 28 * 298
        co2_eq = ghg_co2_co2eq + ghg_n02_co2eq
        data = meta.path, mean_n20, carbon * -1, MineralN, leached_N, profit * -1, co2_eq, Myield * -1
        return data
    except Exception as e:
        print(repr(e))


def excute_querry_in_pool(data):
    """
    :param data: tuple of path and N amountd
    :return: tuple
    """
    meta_data = namedtuple('db', ['path', 'N'])
    generate_data = meta_data(path=data[0], N=data[1])
    dt = excute_query_data(fileinput=generate_data.path, N=generate_data.N)
    return dt


def read_data_in_parallel(aps_list, Nitrogen, Residue=None):
    """
    :param aps_list: list of apsimx data bases
    :param Nitrogen: integer
    :param Residue:  float
    :return: pandas data frame
    """
    read_partial = partial(excute_query_data, N=Nitrogen, R=Residue)
    with ProcessPoolExecutor(max_workers=8) as tpool:
        tp = tpool.map(read_partial, aps_list)
        tp = [i for i in tp if i is not None]
        data = pd.DataFrame(list(tp))
    return data.mean(0, numeric_only=True)


