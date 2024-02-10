from concurrent.futures import as_completed

import geopandas as gpd
import pandas as pd
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
from apsimNGpy.manager.soilmanager import OrganizeAPSIMsoil_profile, DownloadsurgoSoiltables
from apsimNGpy.core.weather import daymet_bylocation_nocsv
from apsimNGpy.parallel.process import custom_parallel
from apsimNGpy.parallel.safe import initialise

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
    print(CRS)
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


def random_points_in_polygon(number, polygon, seed=1):
    """
    Generates a specified number of random points within a given polygon.

    This function attempts to create a list of points that are guaranteed to be within
    the boundaries of the specified polygon. It uses a simple rejection sampling method
    where points are randomly generated within the bounding box of the polygon. Points
    that fall inside the polygon are kept until the desired number is reached.

    Parameters:
    - number (int): The number of random points to generate within the polygon.
    - polygon (shapely.geometry.polygon.Polygon): The polygon within which the random
      points are to be generated.
    - seed (int, optional): A seed for the random number generator to ensure reproducibility
      of the results. Defaults to 1.

    Returns:
    - list of shapely.geometry.point.Point: A list containing the generated shapely Point
      objects that fall within the specified polygon.

    Example:
    ```
    from shapely.geometry import Polygon, Point
    import random

    # Define a sample polygon (square in this case)
    polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])

    # Generate 5 random points within the polygon
    points = random_points_in_polygon(5, polygon, seed=42)

    # Print the generated points
    for point in points:
        print(point)
    ```

    Note:
    - The function's efficiency decreases as the complexity of the polygon increases,
      due to the nature of the rejection sampling method. For complex polygons or a high
      number of points, consider optimizing or using more sophisticated sampling methods.
    """
    random.seed(seed)
    points = []
    min_x, min_y, max_x, max_y = polygon.bounds
    i = 0
    while i < number:
        point = Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))
        if polygon.contains(point):
            points.append(point)
            i += 1
    return points


def sample_by_polygons(shp, k=1, filter_by=None, filter_value=None):
    """
    Generates a specified number of sample points within each polygon of a shapefile,
    optionally filtering the polygons based on a column value.

    This function reads a polygon shapefile and generates a user-defined number of random
    points within each polygon. It allows for an optional filtering of polygons based on
    a specified column and value. The distribution of points is weighted by the area of
    each polygon, ensuring that larger polygons receive a proportionately higher number
    of sample points. The function returns the coordinates of the generated points.

    Parameters:
    - shp (str): Path to the polygon shapefile (.shp).
    - k (int, optional): Base number of sample points to generate for each polygon.
      The actual number of points is adjusted based on the polygon's area. Defaults to 1.
    - filter_by (str, optional): Column name to filter the polygons. Only polygons
      matching the filter_value will be considered for sampling. Defaults to None.
    - filter_value (various, optional): Value in the filter_by column that the polygons
      must match to be included in the sampling. The type depends on the column's content.

    Returns:
    - numpy.ndarray: An array of tuples containing the (x, y) coordinates of each generated
      sample point within the polygons, adjusted to the WGS84 coordinate reference system.

    Note:
    - The function assumes the presence of a function `random_points_in_polygon` to generate
      points within a polygon, which is not defined within this docstring.
    - The output coordinates are converted to the WGS84 CRS for geospatial compatibility.
    """
    points = []

    # Load the shapefile as a GeoDataFrame
    gd = gpd.read_file(shp)
    total_area = gd.area.sum() / 10 ** 6
    print(f"The area is {total_area} square kilometers.")

    # Apply filtering if specified
    if filter_by and filter_value is not None:
        gd = gd[gd[filter_by] == filter_value]

    CRS = gd.crs  # Preserve the original CRS
    import math
    poi = []  # Placeholder for counting points per polygon

    # Generate points for each polygon
    for poly in gd['geometry']:
        area = poly.area / 10 ** 6
        weight = area / total_area
        new_k = math.ceil(area * k)  # Adjust k based on the area
        poi.append(new_k)
        print(f"Generating {new_k} points for a polygon.")
        pts = random_points_in_polygon(new_k, poly)
        points.extend(pts)

    points_gdf = gpd.GeoDataFrame(geometry=points, crs=CRS)
    gdf = points_gdf.to_crs("EPSG:4326")  # Convert to WGS84 CRS

    print(f"Total points generated: {np.sum(poi)}")
    return np.array([(point.x, point.y) for point in gdf.geometry])


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
        thi = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
        th = kwargs.get("thickness_values", thi)
        mod = ApsimModel(model, thickness_values=th, out_path=out_path_name)
        if kwargs.get('replace_weather', True):
            wf = daymet_bylocation_nocsv(location, start=start, end=end, filename=wname)
            sim_name = mod.extract_simulation_name
            mod.replace_met_file(wf, sim_name)
        if kwargs.get("verbose"):
            print("downloading and replacing soils now")
        if replace_soils:
            table = DownloadsurgoSoiltables(location)
            if isinstance(table, pd.DataFrame):
                sp = OrganizeAPSIMsoil_profile(table, thickness=20, thickness_values=th)
                sp = sp.cal_missingFromSurgo()
                if sp[0].isna().any().any() or sp[1].isna().any().any() or sp[2].isna().any().any():
                    print(f"soils not replaced at {location}")
                    return None
                else:
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


def create_and_run_sim_objects(wd, shp_file, resolution, num_points, model_file, reports_names, cores=10, **kwargs):
    """

    Args:
        wd: working directory
        shp_file: shape file of the target area
        model_file: APSIM model string path
        reports_names:str or list names of the data in the simulation model
        **kwargs:
           Test: bool. set to true to try out 10 sample before simulation
           run_process: set too false to run in parallel
           select_process; set too False to use multiple process
           'replace_weather'

    :param shp_file:
    :param resolution:int. square qrid resolution
    :param num_points:int for random sampling

    """
    print(f"Here is your extra arguments: {kwargs}")
    ap = generate_random_points(shp_file, resolution, 10, num_points)
    if kwargs.get('test'):
        k = 10
        random_indices = np.random.choice(ap.shape[0], size=k, replace=False)

        # Use the random indices to select rows from ap
        arr = ap[random_indices]
    else:
        arr = ap
    print("Downloading weather files")
    ap = create_apsimx_sim_files(wd, model_file, arr)
    # first we replace soils, then we
    objs = download_weather(ap, 1990, 2021, report_names='Carbon', ncores=cores, verbose=False, report=False,
                            use_thread=kwargs.get('select_process', True),
                            replace_soils=False, replace_weather=True)

    weathers = list(objs)

    print("\nDownloading soils now please wait")
    objs = download_weather(ap, 1990, 2021, report_names='Carbon', verbose=False, ncores=cores, report=False,
                            use_thread=kwargs.get('select_process', True),
                            replace_soils=True)
    soils = list(objs)
    data = [s for s in soils if s in weathers and s is not None]
    print(f"\nrunning the {len(data)} simulations now.....")
    sim = custom_parallel(initialise, data, reports_names, ncores=cores, use_thread=kwargs.get('run_process', True))
    return list(sim)


if __name__ == '__main__':
    wd = r'C:\Users\rmagala'
    fb401 = r'D:\ACPd\Long deek401 simulations\FB401.shp'
    df = create_fishnet1(shp, ncores=10, use_thread=True)
    gd = df
    bc_model = r'D:\ACPd\Bear creek simulations\ML_bear_creek 20240206.apsimx'
    fb = gpd.read_file(fb401)
    lp = sample_by_polygons(fb401, k=4, filter_by='isAG', filter_value=1)
    # data = create_and_run_sim_objects(wd, shp, 500, 2, maize, 'Carbon', test=False, run_process=False,
    #                                   select_process=True, cores=13)
    # # sims = run_created_files(data, "Carbon", cores = 15, use_threads = False)
    # # dat = custom_parallel(run_simPle, data, "Carbon", ncores=14, use_thread=True)
    # # dd = list(dat)
    # from joblib import dump, load
    #
    # # dat = load('sims')
    # # ap = ApsimModel(data[8])
    # # dump(data, 'sims')
    # # mod = [model.run(report_name='Carbon') for model in mop]
