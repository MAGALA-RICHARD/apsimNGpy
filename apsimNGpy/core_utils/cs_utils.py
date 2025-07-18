import os
from pathlib import Path

# Define the path to the config file using pathlib for better cross-platform support
DLL_DIR = str(Path(__file__).parent.parent / 'dll')


def start_pythonnet():
    import pythonnet
    try:
        if pythonnet.get_runtime_info() is None:
            return pythonnet.load("coreclr")
    except:
        print("dotnet not found, trying alternate runtime")
        return pythonnet.load()


start_pythonnet()
import clr

clr.AddReference(os.path.join(DLL_DIR, 'CastBridge'))
from CastBridge import CastHelper