"""
Interface to APSIM simulation models using Python.NET build on top of a Matti Pastell farmingpy framework.
"""
import os
import pandas as pd
import pathlib
import pythonnet
import shutil
import sqlite3
import sys
import warnings
import pythonnet
from apsimNGpy.core.pythonet_config import LoadPythonnet, APSIM_PATH

apsim_model = APSIM_PATH
loader = LoadPythonnet()()
from os.path import realpath
import warnings
from System.Collections.Generic import *
from Models.Core import Simulations
from System import *
from Models.PMF import Cultivar
from Models import Options
from pathlib import Path
import Models
from System import *
from collections import namedtuple
import json
from System.Collections.Generic import *

FAILED_RUNS = []

sys.path.append(os.path.realpath(apsim_model))


def _read_simulation(datastore, report_name=None):
    """ returns all data frame the available report tables"""
    conn = sqlite3.connect(datastore)
    try:
        cursor = conn.cursor()

        # reading all table names

        table_names = [a for a in cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]

        table_list = []
        for i in table_names:
            table_list.append(i[0])
            # remove these
        rm = ['_InitialConditions', '_Messages', '_Checkpoints', '_Units']
        for i in rm:
            if i in table_list:
                table_list.remove(i)
                # start selecting tables
        select_template = 'SELECT * FROM {table_list}'

        # create data fram dictionary to keep all the tables
        dataframe_dict = {}

        for tname in table_list:
            query = select_template.format(table_list=tname)
            dataframe_dict[tname] = pd.read_sql(query, conn)
        # close the connection cursor

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
    finally:
        conn.close()


def run(named_tuple_data, results=True, multithread=True):
    """Run apsimx model in the simulations. the method first cleans the existing database.

     This is the safest way to run apsimx files in parallel
     as named tuples are immutable so the chances of race conditioning are very low

        Parameters
        ----------
        simulations (__str_), optional
            List of simulation names to run, if `None` runs all simulations, by default `None`.

        :multithread (bool), optional
            If `True` APSIM uses multiple threads, by default `True`

        results (bool), optional: if True, the results will be returned else the function execute without returning anything
        """
    if multithread:
        runtype = Models.Core.Run.Runner.RunTypeEnum.MultiThreaded
    else:
        runtype = Models.Core.Run.Runner.RunTypeEnum.SingleThreaded
    try:

        named_tuple_data.DataStore.Dispose()
        named_tuple_data.DataStore.Open()
        runmodel = Models.Core.Run.Runner(named_tuple_data.IModel, True, False, False, None, runtype)
        e = runmodel.Run()
        if results:
            data = _read_simulation(named_tuple_data.datastore)

            return data
    except Exception as e:
        raise
    finally:
        named_tuple_data.DataStore.Close()


def run_model(named_tuple_model, results=False, clean_up =False):
    """

    :param results (bool) for return results
    :param named_tuple_model: named tuple from model_loader
    :param clean_up (bool), deletes the files associated with the Apsim model. there is no need to worry about this
    because everything is compied in the model_loader
    :return: a named tuple objects populated with the results if results is True
    """
    try:
        res = run(named_tuple_model, results=results)
        if clean_up:
            Path(named_tuple_model.path).unlink(missing_ok=True)
        return res
    except Exception as e:
        print(f"{type(e)} has occured::::")
        print(f"apsimNGpy had issues running file {named_tuple_model.path} : because of {repr(e)}")


if __name__ == "__main__":
    pp = r'D:\ndata/sw.apsimx'
