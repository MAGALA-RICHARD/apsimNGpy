from concurrent.futures import as_completed

import numpy as np
from typing import Tuple, Any
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.base_data import LoadExampleFiles
from pathlib import Path

from apsimNGpy.utililies.utils import select_process
from apsimNGpy.weather import daymet_bylocation_nocsv, daymet_bylocation
from apsimNGpy.manager.soilmanager import DownloadsurgoSoiltables, OrganizeAPSIMsoil_profile
from apsimNGpy.utililies.spatial import create_fishnet1, create_apsimx_sim_files
from tqdm import tqdm

wd = Path.home()
from os.path import basename

maize = LoadExampleFiles(wd).get_maize

lon = -91.620369, 43.034534


def simulate_single_point(model: Any, location: Tuple[float, float], report, read_from_string=True, start=1990,
                          end=2020,
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

        replace_weather: Set this boolean to true to download and replace the weather data based on the specified location.

        replace_soil: Set this boolean to true to download and replace the soil data using the given location details.

        mgt_practices: Provide a list of management decissions

    """
    thi = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
    th = kwargs.get("thickness_values", thi)  # in case it is not supplied, we take thi
    simulator_model = ApsimModel(
        model, copy=kwargs.get('copy'), read_from_string=read_from_string, lonlat=location, thickness_values=th)

    sim_name = simulator_model.extract_simulation_name
    if kwargs.get('replace_weather', False):
        wname = model.strip('.apsimx') + '_w.met'
        wf = daymet_bylocation_nocsv(location, start, end, filename=wname)
        simulator_model.replace_met_file(wf, sim_name)

    if kwargs.get("replace_soil", False):
        table = DownloadsurgoSoiltables(location)
        sp = OrganizeAPSIMsoil_profile(table, thickness=20, thickness_values=th)
        sp = sp.cal_missingFromSurgo()
        simulator_model.replace_downloaded_soils(sp, sim_name)

    if kwargs.get("mgt_practices"):
        simulator_model.update_mgt(kwargs.get('mgt_practices'), sim_name)
    simulator_model.run(report_name=report)
    return simulator_model.results


def simulate_single_from_shape_file(wd, shape_file, model: Any, resolution, report, read_from_string=True, start=1990,
                                    end=2020,
                                    soil_series: str = 'domtcp', **kwargs):
    arr = create_fishnet1(shape_file, lon_step=resolution, lat_step=resolution, ncores=3)
    """
    Run a simulation of a given crop.
     model: Union[str, Simulations],
     location: longitude and latitude to run from, previously lonlat
     soil_series: str
     wd: pathlike stirng
     kwargs:
        copy: bool = False, out_path: str = None, read_from_string=True,

        soil_series: str = 'domtcp', thickness: int = 20, bottomdepth: int = 200,

        thickness_values: list = None, run_all_soils: bool = False

        report_name: str specifies the report or table name in the simulation, for which to read the reasults

        replace_weather: Set this boolean to true to download and replace the weather data based on the specified location.

        replace_soil: Set this boolean to true to download and replace the soil data using the given location details.

        mgt_practices: Provide a list of management decissions
        
        ncores: set the number of cores
        use_thread: set true to run in parallel processing

    """
    arr = create_fishnet1(shape_file, lon_step=resolution, lat_step=resolution, ncores=kwargs.get('ncores', 4))
    df = create_apsimx_sim_files(wd, model, arr)
    thi = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
    th = kwargs.get("thickness_values", thi)  # in case it is not supplied, we take thi

    use_thread, ncores = kwargs.get('use_thread', False), kwargs.get('ncores', 3)

    def worker(row):
        ID = row['ID']
        model = row['file_name']
        simulator_model = ApsimModel(
            model, copy=kwargs.get('copy'), read_from_string=read_from_string, lonlat=None, thickness_values=th)
        sim_names = simulator_model.extract_simulation_name
        location = row['location']

        if kwargs.get('replace_weather', False):
            wname = model.strip('.apsimx') + '_w.met'
            wf = daymet_bylocation_nocsv(arr[location], start, end, filename=wname)
            simulator_model.replace_met_file(wf, sim_names)

        if kwargs.get("replace_soil", False):
            table = DownloadsurgoSoiltables(location)
            sp = OrganizeAPSIMsoil_profile(table, thickness=20, thickness_values=th)
            sp = sp.cal_missingFromSurgo()
            simulator_model.replace_downloaded_soils(sp, sim_names)

        if kwargs.get("mgt_practices"):
            simulator_model.update_mgt(kwargs.get('mgt_practices'), sim_names)
        simulator_model.run(report_name=report)
        return simulator_model.results

    with select_process(use_thread, ncores) as tpool:
        futures = {tpool.submit(worker, df.loc[df['ID'] == i].squeeze()): i for i in df['ID']}
        progress = tqdm(total=len(futures), position=0, leave=True,
                        bar_format=f'Running:' '{percentage:3.0f}% completed')
        # Iterate over the futures as they complete
        for future in as_completed(futures):
            yield future.result()
            progress.update(1)
        progress.close()


md = {"Name": 'PostharvestillageMaize', 'Fraction': 0.001
      }
if __name__ == '__main__':
        pp = simulate_single_point(maize, lon, replace_weather=True, replace_soil=True, mgt_practices=md, report='MaizeR')
        shp = r'D:\ACPd\Bear creek simulations\bearcreek_shape\bearcreek.shp'
        wd = r'C:\Users\rmagala'
        lp = simulate_single_from_shape_file(wd, shp, maize, 1000, report = 'MaizeR')
        lip = list(lp)