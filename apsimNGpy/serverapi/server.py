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

# related to server
clr.AddReference(r'C:\Program Files\APSIM2022.12.7130.0\bin\apsim-server.dll')
from Models.Core.Run import Runner
import APSIM.Server.IO
import socket

from APSIM.Server import Commands
import APSIM
import dataclasses
APSIM.Server.ApsimServer  # start again from here
from abc import ABC, abstractmethod


# context manager for the connection
class ConnectionManager:
    def __init__(self, port, ip_address):
        # todo Initialize  connection here
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = port
        self.ip_address = ip_address

    def __enter__(self):
        #todo  Start the connection or acquire resources
        try:
            self.client.connect(self.ip_address, self.port)
        except:
            pass

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            # An exception occurred within the 'with' block
            print(f"Exception Type: {exc_type}")
            print(f"Exception Value: {exc_value}")
        else:
            self.client.close()

    def close(self):
        pass
        # todo Implement connection closure here


class IConnectionManager(ABC):
    @abstractmethod
    def create_connection(self):
        pass


class LocalSocketConnection(IConnectionManager):
    def __init__(self, socket_name, verbose, protocol):
        self.socket_name = socket_name
        self.verbose = verbose
        self.protocol = protocol

    def create_connection(self):
        # todo Implement the connection creation for local mode here
        pass


class NetworkSocketConnection(IConnectionManager):
    def __init__(self, verbose, ip_address, port, backlog, protocol):
        self.verbose = verbose
        self.ip_address = ip_address
        self.port = port
        self.backlog = backlog
        self.protocol = protocol

    def create_connection(self):
        # todo Implement the connection creation for remote mode here
        pass


def create_connection(options):
    protocol = get_protocol()
    if options.local_mode:
        return LocalSocketConnection(options.socket_name, options.verbose, protocol)
    if options.remote_mode:
        return NetworkSocketConnection(options.verbose, options.ip_address, options.port, options.backlog, protocol)
    raise NotImplementedError("Unknown connection type. Use either local or remote mode.")


