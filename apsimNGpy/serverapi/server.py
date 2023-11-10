"""
Interface to APSIM simulation models using Python.NET build on top of Matti Pastell farmingpy framework.
"""
import matplotlib.pyplot as plt
import random, logging, pathlib
import string
from typing import Union
import pythonnet
import os, sys, datetime, shutil, warnings
import numpy as np
import pandas as pd
from os.path import join as opj
import sqlite3
import json
from pathlib import Path
import apsimNGpy.manager.weathermanager as weather
from apsimNGpy.manager.soilmanager import DownloadsurgoSoiltables, OrganizeAPSIMsoil_profile
from apsimNGpy.utililies.pythonet_config import get_apsimx_model_path, get_apsim_path

try:
    if pythonnet.get_runtime_info() is None:
        pythonnet.load("coreclr")
except:
    print("dotnet not found ,trying alternate runtime")
    pythonnet.load()

import clr
from os.path import join as opj

# logs folder
Logs = "Logs"
basedir = os.getcwd()
log_messages = opj(basedir, Logs)
if not os.path.exists(log_messages):
    os.mkdir(log_messages)

datime_now = datetime.datetime.now()
timestamp = datime_now.strftime('%a-%m-%y')
logfile_name = 'log_messages' + str(timestamp) + ".log"
log_paths = opj(log_messages, logfile_name)
# f"log_messages{datetime.now().strftime('%m_%d')}.log"
logging.basicConfig(filename=log_paths, level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

try:
    apsim_model = os.path.realpath(get_apsimx_model_path())
except:
    apsim_model = get_apsim_path()

sys.path.append(apsim_model)

try:
    clr.AddReference("Models")
except:
    print("Looking for APSIM")
    apsim_path = shutil.which("Models")
    if apsim_path is not None:
        apsim_path = os.path.split(os.path.realpath(apsim_path))[0]
        sys.path.append(apsim_path)
    clr.AddReference("Models")

clr.AddReference("System")
from System.Collections.Generic import *
from Models.Core import Simulations
from System import *
from Models.PMF import Cultivar
from Models import Options
from Models.Core.ApsimFile import FileFormat
from Models.Climate import Weather
from Models.Soils import Solute, Water, Chemical
from Models.Soils import Soil, Physical, SoilCrop, Organic
import Models
from Models.PMF import Cultivar
import threading
import time
clr.AddReference(r'C:\Program Files\APSIM2022.12.7130.0\bin\apsim-server.dll')
from APSIM.Server import Commands
import APSIM

APSIM.Server.ApsimServer # statrt again from here
# decorator to monitor performance
def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        print(f"{func.__name__} took {elapsed_time:.4f} seconds to execute.")
        return result

    return wrapper


