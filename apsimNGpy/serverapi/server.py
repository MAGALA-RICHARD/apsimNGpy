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
# TODO this file is redundant now. Everything that was relevant here has been moved to the settings.py file


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


