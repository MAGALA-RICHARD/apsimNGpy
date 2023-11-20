import sys
import os


def add_path(new_path):
    if not new_path in sys.path:
        sys.path += [new_path]
        print(f"{new_path} successfully added to the system")
    else:
        print("path is already added to the system")


from pathlib import Path


path = r'C:\raw_data\APSIM2022.12.7130.0\bin'
pm = write_path(path)
import json
json.load(pm)
import clr
import pythonnet

# # pythonnet.load()
# pythonnet.load("coreclr")
# add_path(path)
# import clr
#
# clr.AddReference("Models")
# import Models
