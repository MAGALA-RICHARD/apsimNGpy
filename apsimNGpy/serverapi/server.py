"""
Interface to APSIM simulation models using Python.NET build on top of Matti Pastell farmingpy framework.
"""
from pathlib import Path
import pythonnet
import os, sys, datetime, shutil, warnings
import socket
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
from apsimNGpy.base.base_data import LoadExampleFiles

data = LoadExampleFiles(Path.home())
maize = data.get_maize
# related to server
clr.AddReference(r'C:\Program Files\APSIM2022.12.7130.0\bin\apsim-server.dll')
from Models.Core.Run import Runner
import APSIM
import APSIM.Server.IO
import socket

from APSIM.Server import Commands
import APSIM
import dataclasses

sims = Simulations()
run = Runner(sims)
JOBSERVERRUNNER = APSIM.Server.ServerJobRunner()
RUN = APSIM.Server.ServerJobRunner.Run
APSIM.Server.ServerJobRunner.Dispose

com = APSIM.Server.Cli.GlobalServerOptions()
com.File = data.get_maize
com.Verbose = True
com.NativeMode = True
com.LocalMode = True
com.RemoteMode = False
com.IPAddress = '10.24.22.192'


def _apsim_server(file):
    sims = FileFormat.ReadFromFile[Models.Core.Simulations](file, None, False)
    sims.FindChild[Models.Storage.DataStore]().UseInMemoryDB = True;
    print(sims.FindChild[Models.Storage.DataStore]().UseInMemoryDB)
    runner = Runner(sims)
    runner.Use(JOBSERVERRUNNER)
    return runner


def _connect_to_server(name):
    # The path to the Unix domain socket.
    pipe_prefix = "/tmp/CoreFxPipe_"
    pipe = pipe_prefix + name

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    address = pipe

    try:
        sock.connect(address)
    except Exception as e:
        print(f"Error connecting to the server: {str(e)}")
        return None

    return sock


def _connect_to_remote_server(ip_addr, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    address = (ip_addr, port)

    try:
        sock.connect(address)
    except Exception as e:
        print(f"Error connecting to the server: {str(e)}")
        return None

    return sock

from pathlib import Path
import os

# Get the path to the temporary directory
temp_dir = Path(os.environ.get('TEMP', os.environ.get('TMP')))

# Now you can work with the temp_dir as a Path object
print(temp_dir)

# You can list files in the temporary directory, for example:
for file in temp_dir.iterdir():
    print(file)

fip =r'C:\Users\rmagala\AppData\Local\Temp'
lp = os.listdir(fip)
for  i in lp:
    if 'bin' in i:
        print(i)
pm = os.path.join(fip, 'APSIMff535863-dc94-4abe-8dd6-02ceb31d52fd.xml')
os.startfile(pm)