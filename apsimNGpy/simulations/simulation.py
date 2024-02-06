import time
from concurrent.futures import as_completed
from typing import Tuple, Any
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.parallel.safe import simulator_worker
from apsimNGpy.utililies.utils import select_process
from apsimNGpy.weather import daymet_bylocation_nocsv, daymet_bylocation
from apsimNGpy.manager.soilmanager import DownloadsurgoSoiltables, OrganizeAPSIMsoil_profile
from apsimNGpy.utililies.spatial import create_fishnet1, create_apsimx_sim_files, generate_random_points
from tqdm import tqdm


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
    # if replace weather
    sim_name = simulator_model.extract_simulation_name
    if kwargs.get('replace_weather', False):
        wname = model.strip('.apsimx') + '_w.met'
        wf = daymet_bylocation_nocsv(location, start, end, filename=wname)
        simulator_model.replace_met_file(wf, sim_name)
    # replace soil is true
    if kwargs.get("replace_soil", False):
        table = DownloadsurgoSoiltables(location)
        sp = OrganizeAPSIMsoil_profile(table, thickness=20, thickness_values=th)
        sp = sp.cal_missingFromSurgo()
        simulator_model.replace_downloaded_soils(sp, sim_name)
    # if replace management practices
    if kwargs.get("mgt_practices"):
        simulator_model.update_mgt(kwargs.get('mgt_practices'), sim_name)
    simulator_model.run(report_name=report)
    return simulator_model.results


def simulate_from_shape_file(wd, shape_file, model: Any, resolution, report, read_from_string=True, start=1990,
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
        random_grid_points: bolean. set this true to sample specified poitns per grid of your choice
        num_points: int,  set number of points

    """
    use_thread, ncores, num_points = kwargs.get('use_thread', True), kwargs.get('ncores', 3), kwargs.get('num_points',
                                                                                                         2)
    if kwargs.get('random_grid_points'):
        arr = generate_random_points(shape_file, resolution, ncores, num_points)
    else:
        arr = create_fishnet1(shape_file, lon_step=resolution, lat_step=resolution, ncores=kwargs.get('ncores', 4))
    df = create_apsimx_sim_files(wd, model, arr)
    thi = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
    th = kwargs.get("thickness_values", thi)  # in case it is not supplied, we take thi
    kwargs['start'] = start
    kwargs['end'] = end
    a = time.perf_counter()
    with select_process(use_thread, ncores) as tpool:
        futures = {tpool.submit(simulator_worker, df.loc[df['ID'] == i].squeeze(), kwargs): i for i in df['ID']}
        progress = tqdm(total=len(futures), position=0, leave=True,
                        bar_format=f'Running:' '{percentage:3.0f}% completed')
        # Iterate over the futures as they complete
        for future in as_completed(futures):
            yield future.result()
            progress.update(1)
        progress.close()
    print(f"running: {len(df['ID'])} locations took {time.perf_counter()-a} seconds")


