from concurrent.futures import as_completed

import geopandas as gpd
import pandas as pd
import utils
import numpy as np
from apsimNGpy.core import ApsimModel
from apsimNGpy.utililies.utils import select_process
from shapely.geometry import Polygon
import random
from shapely.geometry import Point
import os
from shutil import copy
from shapely.ops import unary_union
from apsimNGpy.core.base_data import LoadExampleFiles
from apsimNGpy.parallel.process import download_soil_tables
from tqdm import tqdm
import random
from manager.soilmanager import OrganizeAPSIMsoil_profile, DownloadsurgoSoiltables
from weather import daymet_bylocation_nocsv
from apsimNGpy.parallel.process import custom_parallel
from apsimNGpy.parallel.safe import run_simPle

maize = LoadExampleFiles().get_maize

WGS84 = 'epsg:4326'
shp = r'D:\ACPd\Bear creek simulations\bearcreek_shape\bearcreek.shp'


def create_polygon1(args):
    lon, lat, lon_step, lat_step = args
    return Polygon([(lon, lat), (lon + lon_step, lat), (lon + lon_step, lat + lat_step), (lon, lat + lat_step)])


def create_fishnet1(pt, lon_step=200, lat_step=200, ncores=3, use_thread=True, **kwargs):
    """

    Args: pt: shape or point feature class layer lon_step: height of the polygon lat_step: width of the polygon
    ncores: number of cores to use use_thread: if True, threads will be used if false processes will be used
    **kwargs: use key word Return = gdf to return GeoPandas data frame: this is show polygon coordinates otherwise if
    not supplied to will returun an array

    Returns: an array or geopandas data frame
    """
    gdf_shape = gpd.read_file(pt)
    CRS = gdf_shape.crs
    min_lon, min_lat, max_lon, max_lat = gdf_shape.total_bounds
    lats = np.arange(min_lat, max_lat, lat_step)
    lons = np.arange(min_lon, max_lon, lon_step)
    polygons = []

    with select_process(use_thread, ncores) as executor:
        args = [(lon, lat, lon_step, lat_step) for lon in lons for lat in lats]
        polygons = list(executor.map(create_polygon1, args))
    gdf = gpd.GeoDataFrame({'geometry': polygons}, crs=CRS)
    gdf_clip = gpd.clip(gdf, gdf_shape)
    gdf = gdf_clip.centroid
    gdf_transformed = gdf.to_crs(WGS84)
    if kwargs.get("Return", 'array') == 'array':
        return np.array([(point.x, point.y) for point in gdf_transformed])
    else:
        return gdf_clip


# Function to generate random points within a polygon
def generate_random_points(pt, resolution, ncores, num_points):
    """

    Args:
        pt: shape file
        resolution: resolution in meters
        ncores: number of cores to use
        num_points: number of points to sample in each grid

    Returns:

    """
    all_points = []

    def generate():
        min_x, min_y, max_x, max_y = poly.bounds
        points = []

        while len(points) < num_points:
            random_point = Point([random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
            if random_point.within(poly):
                points.append(random_point)
        return points

    gdf = create_fishnet1(pt, lon_step=resolution, lat_step=resolution, ncores=ncores, Return='gdf')
    df = gdf.to_crs(WGS84)
    for poly in df['geometry']:
        random_points = generate()  # Generate 3 random points
        all_points.extend(random_points)
        points_gdf = gpd.GeoDataFrame(geometry=all_points)  # Add the points to the list
        GDF = points_gdf
    return np.array([(point.x, point.y) for point in GDF.geometry])


def create_apsimx_sim_files(wd, model, iterable):
    """
    Creates copies of a specified APSIM model file for each element in the provided iterable,
    renaming the files to have unique identifiers based on their index in the iterable.
    The new files are saved in the specified working directory.

    Args:
    wd (str): The working directory where the new .apsimx files will be stored.
    model (str): The path to the .apsimx model file that will be copied.
    iterable (iterable): An iterable (e.g., list or range) whose length determines the number of copies made.

    Returns:
    dict: A dictionary where keys are indices from 0 to len(iterable)-1 and values are paths to the newly created .apsimx files.

    The function performs the following steps:
    1. Extracts the basename of the model file, removing the '.apsimx' extension to create a model suffix.
    2. Iterates over the `iterable`, creating a unique file name for each element by appending an index and '.apsimx' to the model suffix.
    3. Copies the original model file to the new file name in the specified working directory.
    4. Returns a dictionary mapping each index to the file path of the created .apsimx file.

    Example:
    >>wd = '/path/to/working/directory'
    >> model = '/path/to/original/model.apsimx'
    >> file_paths = create_apsimx_files(wd, model, range(5))
    >> print(file_paths)
    {0: '/path/to/working/directory/model_0.apsimx', 1: '/path/to/working/directory/model_1.apsimx', ...}
    """

    mod = model.strip('.apsimx')
    model_suffix = os.path.basename(mod)

    ids = range(len(iterable))
    files = [{'ID': i, 'location': iterable[i], 'file_name': os.path.join(wd, model_suffix) + f"_{i}.apsimx"} for i in
             ids]
    df = pd.DataFrame(files)
    [copy(model, df['file_name'][i]) for i in ids]
    return df


def download_weather(df, start, end, use_thread=True, ncores=10, replace_soils=True, **kwargs):
    """
       downloads and replace soil or weather files or both in parallel or threads
    Args:
        replace_soils: Set this to true to simulataneoursly downloand and replace soils
        df: data frame generated by 'create_apsimx_sim_files'
        start: start year of the simulation
        end:  end year of the simulation
        use_thread: if true threading will take place otherwise multiprocessing
        ncores: number of cores to use
    kwargs:
      verbose: bool, Set to True print current step
      thickness_values: list defining the soil layer thickness
      report : set to true to return results
      report_names; provide the required table names from apsimx model report
    Returns:

    """

    def worker(row):
        model = str(row['file_name']).strip('.apsimx')
        ID = row['ID']
        location = row['location']
        wname = f"{model}_{ID}.met"
        out_path_name = f"{model}_{ID}.apsimx"
        model = row['file_name']
        wf = daymet_bylocation_nocsv(location, start=start, end=end, filename=wname)
        thi = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
        th = kwargs.get("thickness_values", thi)
        mod = ApsimModel(model,  thickness_values=th, out_path=out_path_name)
        sim_name = mod.extract_simulation_name
        mod.replace_met_file(wf, sim_name)
        if kwargs.get("verbose"):
            print("downloading and replacing soils now")
        if replace_soils:
            table = DownloadsurgoSoiltables(location)
            sp = OrganizeAPSIMsoil_profile(table, thickness=20, thickness_values=th)
            sp = sp.cal_missingFromSurgo()
            mod.replace_downloaded_soils(sp, sim_name)
        if kwargs.get("report"):
            mod.run(report_name=kwargs.get('report_names'))
            return mod.results
        else:
            mod.save_edited_file(out_path_name)
            mod.clear()
            del mod
            return out_path_name

    with select_process(use_thread, ncores) as tpool:
        futures = {tpool.submit(worker, df.loc[df['ID'] == i].squeeze()): i for i in df['ID']}
        progress = tqdm(total=len(futures), position=0, leave=True,
                        bar_format=f'Running:' '{percentage:3.0f}% completed')
        # Iterate over the futures as they complete
        for future in as_completed(futures):
            yield future.result()
            progress.update(1)
        progress.close()
        # for future in as_completed(futures):


def create_sim_objects(wd, shp_file, model_file, reports_names, **kwargs):
    """

    Args:
        wd: working directory
        shp_file: shape file of the target area
        model_file: APSIM model string path
        reports_names: names of the data in the simulation model
        **kwargs:
           Test: bool. set to true to try out 10 sample before simulation
    Returns:

    """
    ap = generate_random_points(shp_file, 500, 10, 3)
    if kwargs.get('test'):
        k = 10
        random_indices = np.random.choice(ap.shape[0], size=k, replace=False)

        # Use the random indices to select rows from ap
        arr = ap[random_indices]
    else:
        arr = ap
    ap = create_apsimx_sim_files(wd, model_file, arr)
    objs = download_weather(ap, 1990, 2021, verbose=False, use_thread=True, replace_soils=True)

    mop = list(objs)
    return mop


if __name__ == '__main__':
    wd = r'C:\Users\rmagala'

    df = create_fishnet1(shp, ncores=10, use_thread=True)
    gdf = df

    data = create_sim_objects(wd, shp, maize, 'Carbon', test=True)
    # dat = custom_parallel(run_simPle, data, "Carbon", ncores=14, use_thread=True)
    # dd = list(dat)
    from joblib import dump, load
    dat = load('sims')
    ap = ApsimModel(dat[8])
    #dump(data, 'sims')
    # mod = [model.run(report_name='Carbon') for model in mop]
