"""
Interface to APSIM simulation models using Python.NET build on top of a Matti Pastell farmingpy framework.
"""
import os
import sqlite3
import sys
import pandas as pd
from apsimNGpy.core.pythonet_config import LoadPythonnet, aPSim_PATH
apsim_model = aPSim_PATH
loader = LoadPythonnet()()
from System.Collections.Generic import *
from System import *
from pathlib import Path
import Models
from System import *
from System.Collections.Generic import *

FAILED_RUNS = []

sys.path.append(os.path.realpath(apsim_model))


def run_helper(data_store, IModel, results=True, multithread=True, simulations=None):
    """
    Runs a simulation:
    """
    run_type_enum = Models.Core.Run.Runner.RunTypeEnum
    run_type = run_type_enum.MULTITHREAD if multithread else run_type_enum.SINGLETHREAD

    data_store.Dispose()  # start by cleaning the datastore
    data_store.DataStore.Open()

    if simulations is None:
        runmodel = Models.Core.Run.Runner(IModel, True, False, False, None, run_type)
        e = runmodel.Run()
    else:
        sims = IModel.FindAllInScope[Models.Core.Simulation]()
        # Runner needs C# list
        cs_sims = List[Models.Core.Simulation]()
        for s in sims:
            cs_sims.Add(s)
            runmodel = Models.Core.Run.Runner(cs_sims, True, False, False, None, runtype)
            e = runmodel.Run()

        if len(e) > 0:  # this function is not doing much.
            print(e[0].ToString())


def run(named_tuple_data, results=True, multithread=True, simulations=None):
    """
    # TODO generally when people see a method call run, they thing of multithreading.
    # it looks like this is for a simulation of some sort.
    Run apsimx model in the simulations. the method first cleans the existing database.

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
    data_store, IModel = named_tuple_data.DataStore, named_tuple_data.IModel
    try:
        run_helper(data_store, IModel, results=results, multithread=multithread, simulations=simulations)
    except Exception as e:
        logger.exception(repr(e))
    finally:
        data_store.close()

    if results:
        from apsimNGpy.utilities.run_utils import read_simulation
        data = read_simulation(data_store)
        return data


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
