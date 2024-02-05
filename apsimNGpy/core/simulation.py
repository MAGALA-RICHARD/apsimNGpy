from typing import Tuple, Any
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.base_data import LoadExampleFiles
from pathlib import Path
from apsimNGpy.weather import daymet_bylocation_nocsv, daymet_bylocation

wd = Path.home()
from os.path import basename

maize = LoadExampleFiles(wd).get_maize

lon = -91.620369, 43.034534


def simulate(model: Any, location: Tuple[float, float], read_from_string=True, start=1990, end=2020,
             soil_series: str = 'domtcp', **kwargs):
    """
    Run a simulation of a given crop.
     model: Union[str, Simulations],
     location: longitude and latitude to run from, previously lonlat
     soil_series: str
     kwargs:
        copy: bool = False, out_path: str = None, read_from_string=True,
        soil_series: str = 'domtcp', thickness: int = 20, bottomdepth: int = 200,
        thickness_values: list = None, run_all_soils: bool = False
        report_name: str specifies the report or table name in the simulation, for which to read the reasults
        replace_weather: bool if true,weather is downloaded using the specified location and itis replaced

    """

    simulator_model = ApsimModel(
        model, copy=kwargs.get('copy'), read_from_string=read_from_string, lonlat=location)

    report_name = kwargs.get("report_name")
    sim_name = simulator_model.extract_simulation_name
    if kwargs.get('replace_weather', False):
        wname = 'w' + model.strip('apsimx') + ".met"
        wf = daymet_bylocation_nocsv(location, start, end, filename='wname.met')
        ApsimModel.replace_met_file(wf, sim_name)
    met = simulator_model.show_met_file_in_simulation()
    print(met)
    simulator_model.run()
    return simulator_model.results


import os
# pp = simulate(maize, lon, replace_weather = True)
import os


def search(directory):
    am = []
    for root, dirs, files in os.walk(directory):

        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='latin-1') as f:
                    if 'nasa' in f.read():
                        print(file_path)
                        am.append(file_path)
    return am  # Return the path of the first .py file that contains 'nasapower'
    return None  # Return None if 'nasapower' is not found in any .py files


# Usage
directory_to_search = r"C:\Users\rmagala\Box\apsimNGpy"
result = search(directory_to_search)
if result:
    print(f"Found 'nasapower' in: {result}")
else:
    print("Did not find 'nasapower' in any .py files.")
