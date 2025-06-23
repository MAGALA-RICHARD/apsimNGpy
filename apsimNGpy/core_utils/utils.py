import logging
from collections import deque

import numpy as np
import glob
import os
from os.path import join as opj
import shutil
import random
import string
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.geometry import Point
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from threading import Thread
from scipy.optimize import curve_fit
from time import perf_counter
import pandas as pd
import time
from functools import cache
from pathlib import Path
from shapely import wkt

import functools
import traceback
import sys
from apsimNGpy.settings import logger
from platform import system
from subprocess import call, run, Popen
def select_process(use_thread, ncores):
    return ThreadPoolExecutor(ncores) if use_thread else ProcessPoolExecutor(ncores)

def open_file_in_window(filepath):
    if system() == 'Darwin':  # macOS
        call(['open', filepath])
    elif system() == 'Windows':  # Windows
        os.startfile(filepath)
    elif system() == 'Linux':  # Linux
        call(['xdg-open', filepath])
    else:
        raise OSError('Unsupported operating system')
# to avoid breaking old versions. am repeating it here


def open_apsimx_file_in_window(filepath, bin_path):
    """
    Opens the given .apsimx file using the APSIM Next Generation executable located in `bin_path`.

    Parameters:
        filepath (str): Path to the .apsimx file.
        bin_path (str): Path to the APSIM binaries (folder containing ApsimNG or ApsimNG.exe).

    Raises:
        FileNotFoundError: If the APSIM executable does not exist.
    """
    if system() == 'Windows':
        executor = os.path.join(bin_path, 'ApsimNG.exe')
    else:
        executor = os.path.join(bin_path, 'ApsimNG')

    if not os.path.exists(executor):
        raise FileNotFoundError(f"APSIM executable not found at: {executor}")

    try:
        process = Popen([executor, filepath])
        return process  # Return the running process if needed
    except Exception as e:
        raise RuntimeError(f"Failed to open file: {e}")


class KeyValuePair:
    def __init__(self, Key, Value):
        self.key = Key
        self.value = Value


def generate_unique_name(base_name, length=6):
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=length))
    unique_name = base_name + '_' + random_suffix
    return unique_name


def delete_simulation_files(path, patterns=None):
    """

        :param path: path where the target files are located
        :param patterns: a list of different file patterns to delete
        :return: none
        """
    if not patterns:
        patterns = ['*lat*lon*.csv', 'clones*.apsimx', 'F*.apsimx', '*.db-shm', '*.db-wal', '*.db', 'fish*.cpg',
                    'edit*.bak', 'FB_*.db', 'coh*.bak', 'fish*.shp', 'Daymet*.met']
    localfiles = [glob.glob1(path, pat) for pat in patterns]
    files_to_delete = []
    for file_group in localfiles:
        absolute_paths = [opj(path, file) for file in file_group]
        files_to_delete.extend(absolute_paths)
    for i in files_to_delete:
        try:
            os.remove(i)
        except (FileNotFoundError, PermissionError) as e:
            # print('error occured while deleting file:', repr(e))
            pass


# ____________________________________________________________
def upload_weather(path, specific_number):
    pattern = f'daymet_wf_{specific_number}.met'
    localfiles = glob.glob1(path, pattern)
    if len(localfiles) == 0:
        logger.info(f"weather file for: {specific_number} not found")
    else:
        absolute_paths = [opj(path, file) for file in localfiles]
        return absolute_paths[0]


def upload_apsimx_file(path, specific_number):
    pattern = f'spatial_ap_{specific_number}.apsimx'
    localfiles = glob.glob1(path, pattern)
    if len(localfiles) == 0:
        logger.info(f"apsimx file for: {specific_number} not found")
    else:
        absolute_paths = [opj(path, file) for file in localfiles]
        return absolute_paths[0]


def upload_apsimx_file_by_pattern(path, specific_number, pattern):
    localfiles = glob.glob1(path, pattern)
    if len(localfiles) == 0:
        print(f"apsimx file for: {specific_number} not found")
    else:
        absolute_paths = [opj(path, file) for file in localfiles]
        return absolute_paths[0]


def make_apsimx_clones(base_file, number_of_clones):
    path = opj(os.getcwd(), 'apsimx_cloned')
    if os.path.exists(path):
        delete_simulation_files(path)
    if not os.path.exists(path):
        os.mkdir(path)
    files = []

    try:
        for i in range(number_of_clones):
            file_path = opj(path, generate_unique_name(f"clones_{i}")) + ".apsimx"
            files.append(file_path)
            shutil.copy(base_file, file_path)
        # check if there is any file that is not apsim
        for i in files:
            if not os.path.isfile(i) or not i.endswith('.apsimx'):
                files.remove(i)
                print(i, ": removed")
            yield i
    except Exception as e:
        print(repr(e))


def load_from_numpy(file):
    with open(file, 'rb') as f:
        ar = np.load(f, allow_pickle=True)
    return ar


def get_data_element(data, column_names, indexid):
    """_summary_

        Args:
            data (_array or dataframe_): _description_
            column_names (_type_): _columns name in n dimensional array
            
            indexid (_type_): index of the data to return

        Raises:
            ValueError: _erros if the column is not in the data

        Returns:
            data corresponding to the index id or position in the array
        """

    # Define a dictionary mapping statistic names to corresponding functions
    stat_functions = {
        'OBJECTID': lambda x: x[indexid],
        'FBndID': lambda x: x[indexid],
        'isAG': lambda x: x[indexid],
        'Shape': lambda x: x[indexid],
        'CropRotatn': lambda x: x[indexid]

    }

    # Get the desired statistic function from the dictionary
    func = stat_functions.get(column_names)

    if func is None:
        raise ValueError("Invalid column names. Supported are Shape, OBJECTID, FBndID, isAG and CropRotatn")

    # Calculate the desired statistic for the specified column
    result = func(data[column_names])

    return result


evaluate_crop = lambda x: not any(crop in x for crop in ['F', 'U', 'X', 'T', 'G', 'R', 'P', 'I'])
crop_mapping = {'C': 'Maize', 'B': 'Soybean', 'W': 'Wheat'}


def organize_crop_rotations(arrr):
    """_summary_

    Args:
        arrr (array_): _description_

    Returns:
        return concatenated crop rotation names
    """
    data = {}
    list_data = [list(y) for y in arrr]
    for i in range(len(list_data)):
        if all([evaluate_crop(crop) for crop in arrr[i]]):
            dt = ", ".join([crop_mapping[c] for c in arrr[i]])
            data[i] = dt
    return data


def split_and_replace(data):
    crop_mapping = {'C': 'Maize', 'B': 'Soybean', 'U': 'Unknown', 'P': 'Potato'}
    rows = data.strip().split('\n')
    result = []
    for row in rows:
        row_data = [crop_mapping[c] for c in row]
        result.append(", ".join(row_data))
        print(result)
    return "".join(result)


def convert_negative_to_positive(arr, column_index):
    # Check if all values in the specified column are negative
    for i in column_index:
        # Convert all negative values to positive
        arr[:, i] = np.abs(arr[:, i])
        print(f"changing column {i} to postive")
    return arr


def split_and_replace(data):
    """
    Replaces rows in the 'CropRotatn' column of the input structured array ('data')
    with calculated values based on a mapping ('crop_mapping').

    Parameters:
        data (numpy structured array): A structured array with a 'CropRotatn' column.

    Returns:
        numpy array: A new column containing calculated values for rows that do not meet the condition,
                     and 'none' for rows that meet the condition.
    """

    # Crop mapping dictionary to replace crop codes with crop names
    crop_mapping = {'C': 'Maize', 'B': 'Soybean', 'W': 'Wheat'}

    # Use np.vectorize() to apply np.char.find() on the specified columns
    find_func = np.vectorize(lambda x: not any(crop in x for crop in ['F', 'U', 'X', 'T', 'G', 'R', 'P', 'I']))
    valid_indices = np.where(find_func(data['CropRotatn']))[0]

    # Initialize a new column with 'none'
    new_column = np.array(['none'] * len(data), dtype=object)

    # Calculate and populate new_column for the rows that do not meet the condition
    new_column[valid_indices] = [", ".join([crop_mapping[c] for c in row]) for row in data['CropRotatn'][valid_indices]]

    return new_column


def convert_fc_to_numpy(fc):
    # Replace 'path_to_shapefile.shp' with the actual path to your feature class
    path_to_shapefile = fc

    # Read the shapefile into a GeoDataFrame
    gdf = gpd.read_file(path_to_shapefile)
    # Check the GeoDataFrame to ensure it was read correctly
    print(gdf.head())
    atn = ['FBndID', 'Acres', 'isAG', 'updateYr', 'Shape_Leng', 'Shape_Area']
    numpy_array = gdf[atn].to_numpy()

    # Now you have your attribute data as a NumPy array
    print(numpy_array)
    return numpy_array


def get_centroid(polygon):
    gdf = gpd.read_file(polygon)
    # Union all geometries in the GeoDataFrame
    unified_geometry = unary_union(gdf['geometry'])
    # Calculate centroid of the unified geometry
    centroid = unified_geometry.centroid
    centroid_gdf = gpd.GeoDataFrame(index=[0], crs=gdf.crs, geometry=[Point(centroid.x, centroid.y)])
    # Replace 'EPSG:4326' with the EPSG code of your target CRS
    reprojected_centroid_gdf = centroid_gdf.to_crs('EPSG:4326')
    lonlat = reprojected_centroid_gdf['geometry'].x[0], reprojected_centroid_gdf['geometry'].y[0]
    return lonlat


def create_polygon(lat, lon, lon_step, lat_step):
    return Polygon([(lon, lat), (lon + lon_step, lat), (lon + lon_step, lat + lat_step), (lon, lat + lat_step)])


def create_fishnet(min_lat, min_lon, max_lat, max_lon, lon_step, lat_step):
    lats = np.arange(min_lat, max_lat, lat_step)
    lons = np.arange(min_lon, max_lon, lon_step)

    polygons = []
    with ThreadPoolExecutor(max_workers=18) as executor:  # Adjust max_workers as needed
        x = 0
        for lon in lons:
            x += 1
            print(x)
            for lat in lats:
                print(x)
                future = executor.submit(create_polygon, lat, lon, lon_step, lat_step)
                polygons.append(future.result())

    gdf = gpd.GeoDataFrame({'geometry': polygons})


crs = "EPSG:4326"


def create_polygon1(args):
    lon, lat, lon_step, lat_step = args
    return Polygon([(lon, lat), (lon + lon_step, lat), (lon + lon_step, lat + lat_step), (lon, lat + lat_step)])


def create_fishnet1(pt, lon_step=20, lat_step=20, ncores=2, process=False):
    gdf_shape = gpd.read_file(pt)
    CRS = gdf_shape.crs
    print(crs)
    min_lon, min_lat, max_lon, max_lat = gdf_shape.total_bounds
    lats = np.arange(min_lat, max_lat, lat_step)
    lons = np.arange(min_lon, max_lon, lon_step)
    polygons = []

    with select_process(process, ncores) as executor:
        args = [(lon, lat, lon_step, lat_step) for lon in lons for lat in lats]
        polygons = list(executor.map(create_polygon1, args))
    gdf = gpd.GeoDataFrame({'geometry': polygons}, crs=CRS)
    gdf_clip = gpd.clip(gdf, gdf_shape)

    return gdf_clip


def convert_geopoint_to_array(geoseries):
    # Assuming 'geoseries' is your GeoSeries of Point geometries

    # Extract the x and y coordinates
    x_coords = geoseries.geometry.x
    y_coords = geoseries.geometry.y

    # Stack the coordinates into a 2D array
    coords_array = np.column_stack((x_coords, y_coords))

    return coords_array


import numpy as np
import math


def split_arr(ar, chunk_size):
    num_chunks = math.ceil(len(ar) / chunk_size)
    indices = range(chunk_size, len(ar), num_chunks)
    return np.vsplit(ar, indices)


def moving_average(iterable, n=3):
    import itertools
    # moving_average([40, 30, 50, 46, 39, 44]) --> 40.0 42.0 45.0 43.0
    # https://en.wikipedia.org/wiki/Moving_average
    it = iter(iterable)
    d = deque(itertools.islice(it, n - 1))
    d.appendleft(0)
    s = sum(d)
    for elem in it:
        s += elem - d.popleft()
        d.append(elem)
        yield s / n


def Cache(func):
    """

    This is a function decorator for class attributes. It just remembers the result of the FIRST function call
    and returns this from there on.
    """

    func_name = func.__name__

    def wrapper(self, *args, use_cache=True, set_cache=True, **kwargs):

        if "cache" not in self.__dict__:
            self.__dict__["cache"] = {}

        cache = self.__dict__["cache"]

        if use_cache and func_name in cache:
            return cache[func_name]
        else:

            obj = func(self, *args, **kwargs)

            if set_cache:
                cache[func_name] = obj

            return obj

    return wrapper


def add_wheat(string_object, word_to_insert="Wheat"):
    result = []
    words = string_object.split(', ')
    last_target_index = -1
    target_words = [words[0]] + ["Soybean"]
    ["Maize", "Soybean"]
    # Iterate through the words in the list
    for i, word in enumerate(words):
        result.append(word)  # Add the current word to the result list
        # Check if the current word is one of the target words
        if word in target_words and len(
                words) - 1 > i > last_target_index and word_to_insert not in string_object:
            result.append(word_to_insert)  # Add the word to insert after the target word
            last_target_index = i  # Update the last target word index
    return result


def assign_management_practices(locations, object_ids, num_practices):
    if len(locations) != len(object_ids):
        raise ValueError("The 'locations' and 'object_ids' arrays must have the same length.")
    watershed_data = []
    for location, obj_id in zip(locations, object_ids):
        # Generate a random management practice ID between 1 and num_practices
        management_practice_id = random.randint(1, num_practices)
        # Append the location, objectID, and management practice ID to the watershed_data
        watershed_data.append({"location": location, "objectID": obj_id, "practiceID": management_practice_id})
    return watershed_data


def idex_excutor(self, x):  # We supply x from the rotations idex which inherits objectid
    try:
        a = time.perf_counter()
        print(f"downloading for: {x}")
        data_dic = {}
        fn = "daymet_wf_" + str(x) + '.met'
        cod = pol_object.record_array["Shape"][x]

        filex = weather.daymet_bylocation_nocsv(cod, start=1998, end=2020, cleanup=False, filename=fn)
        return filex
    except Exception as e:
        # raise
        print(e, "has occured")
        try:
            print("trying again")
            filex = weather.daymet_bylocation_nocsv(cod, start=1998, end=2000, cleanup=True, filename=fn)
            return filex
        except:
            print("unresolved errors at the momentt try again")


def threaded_weather_download(self, iter_arable):
    threads = []
    for idices in iter_arable:
        thread = Thread(target=self.idex_excutor, args=(idices,))
        threads.append(thread)
        thread.start()
    # Wait for all threads to finish
    for thread in threads:
        thread.join()



# we can constrain the sample size of each management practice every time we sample
def collect_runfiles(path2files, pattern="*.apsimx"):
    """_summary_

    Args:
        path2files (_type_): path to the apsimx or database file_
        pattern (str, optional) or lists of strings: file pattern. Defaults to "*.apsimx".

    Returns:
        _type_: _description_
    """
    lp = []
    if not isinstance(pattern, list):
        pattern = [pattern]
    for i in pattern:
        list_files = glob.glob1(path2files, i)
        lp += list_files
    files = [os.path.join(path2files, i) for i in lp]
    assert len(lp) != [], "No files found please try another path or file pattern"
    for i in files:
        yield i


def decreasing_exponential_function(x, a, b):  # has potential to cythonize
    """
    Compute the decreasing exponential function y = a * e^(-b * x).

    Parameters:
        x (array-like): Input values.
        a (float): Amplitude or scaling factor.
        b (float): Exponential rate.

    Returns:
        numpy.ndarray: The computed decreasing exponential values.
    """
    func = a * np.exp(-b * x)
    return func


def optimize_exponetial_data(x_data, y_data, initial_guess=[0.5, 0.5],
                             bounds=([0.1, 0.01], [np.inf, np.inf])):  # defaults for carbon

    best_fit_params, _ = curve_fit(decreasing_exponential_function, x_data, y_data, p0=initial_guess,
                                   bounds=bounds)
    a_fit, b_fit = best_fit_params
    predicted = decreasing_exponential_function(x_data, a_fit, b_fit)
    return predicted


def area_of_circle(r):
    pi = 3.141592653589793
    return pi * r * r


def number_of_cells(r, cell_size):
    circle_area = area_of_circle(r)
    cell_area = cell_size * cell_size
    return int(circle_area / cell_area)


def timer(func):
    @functools.wraps(func)  # Preserves metadata
    def wrapper(*args, **kwargs):
        start_time = perf_counter()
        result = func(*args, **kwargs)
        end_time = perf_counter()
        elapsed_time = end_time - start_time
        logger.info(f"{func.__name__} took {elapsed_time:.4f} seconds to execute.")
        return result
    return wrapper


def filter_df(df, **kwargs):
    """
    Filter a DataFrame based on values in specified columns.

    Args:
        df (pd.DataFrame): The DataFrame to be filtered.
        **kwargs: Keyword arguments where the key is the column name and the value is the value to filter on.

    Returns:
        pd.DataFrame: The filtered DataFrame.

    Example:
        filtered_df = filter_dataframe(df, Age=30, City='Los Angeles')
    """

    mask = pd.Series(True, index=df.index)

    #
    for column, value in kwargs.items():
        mask &= (df[column] == value)


    filtered_df = df[mask]
    return filtered_df


def convert_df_to_gdf(df, CRS):
    """
    Converts a pandas DataFrame to a GeoPandas GeoDataFrame with specified CRS.

    This function assumes that the input DataFrame contains a column named 'geometry'
    with WKT (Well-Known Text) representations of geometric objects. It converts these
    textual geometry representations into GeoPandas geometry objects and sets the
    coordinate reference system (CRS) for the resulting GeoDataFrame.

    Parameters:
    - df (pandas.DataFrame): The input DataFrame to convert. Must include a 'geometry'
      column with WKT representations of the geometries.
    - CRS (str or dict): The coordinate reference system to set for the GeoDataFrame.
      Can be specified as a Proj4 string, a dictionary of Proj parameters, an EPSG
      code, or a WKT string.

    Returns:
    - gpd.GeoDataFrame: A GeoDataFrame created from the input DataFrame with geometries
      converted from WKT format and the specified CRS.

    Example:
    ```
    import pandas as pd
    import geopandas as gpd
    from shapely import wkt

    # Sample DataFrame with WKT geometries
    data = {'geometry': ['POINT (12 34)', 'LINESTRING (0 0, 1 1, 2 1, 2 2)'],
            'value': [1, 2]}
    df = pd.DataFrame(data)

    # Convert DataFrame to GeoDataFrame with an EPSG code for CRS
    gdf = convert_df_to_gdf(df, CRS='EPSG:4326')
    ```

    Note:
    The 'wkt' module from 'shapely' needs to be imported to convert geometries from WKT.
    """
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, crs=CRS)
    return gdf


def bounding_box_corners(center_point, radius):
    from geopy.distance import geodesic
    """
        Generates a bounding box around a center point within a specified radius and returns all four corners.

        Parameters:
        - center_point: tuple of (latitude, longitude)
        - radius: radius in meters

        Returns:
        - A dictionary with the coordinates of the 'north_east', 'south_east', 'south_west', and 'north_west' corners of the bounding box.
        """

    # Calculate the north, south, east, and west points by applying the radius distance to the center point
    north = geodesic(meters=radius).destination(center_point, bearing=0)
    south = geodesic(meters=radius).destination(center_point, bearing=180)
    east = geodesic(meters=radius).destination(center_point, bearing=90)
    west = geodesic(meters=radius).destination(center_point, bearing=270)

    # Calculate corners by combining the north/south with east/west
    # we wanted to be intuitive in the direction calculation but let' reverse it'
    north_east = (east.longitude, north.latitude)
    south_east = (east.longitude, south.latitude)
    south_west = (west.longitude, south.latitude)
    north_west = (west.longitude, north.latitude)

    ne = north_east
    sw = south_east
    se = south_west
    nw = north_west
    return ne, se, sw, nw


class WDir:
    def __init__(self, path_dir=None):
        assert path_dir, "path dir_path is required"
        self.initial_path = Path(path_dir)

    def path(self, name=None):
        """

        :param name: name of the new file
        :return: realpath for the new file name
        """
        assert name, "name is required"
        return os.path.realpath(self.initial_path.joinpath(name))

    def mkdir(self, name):
        new_dir = self.initial_path.joinpath(name)
        new_dir.mkdir(exist_ok=True)
        return new_dir

    def make_this_cwd(self):
        wd = os.path.realpath(self.initial_path)
        if os.getcwd() != wd:
            os.chdir(os.path.realpath(self.initial_path))
        else:
            logger.warning(f"this path: {wd} is already the current working dir_path")


def exception_handler(re_raise=False):
    """A decorator to handle exceptions with an option to re-raise them.

    Args:
    re_raise (bool): If True, re-raises the caught exception after logging.
                     If False, logs the exception and suppresses it.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                # Extract unformatted stack traces as a tuple
                trace_back = traceback.extract_tb(exc_traceback)
                # Format stacktrace
                stack_trace = list()

                for trace in trace_back:
                    stack_trace.append("File : %s , Line : %d, Func.Name : %s, Message : %s" % (
                        trace[0], trace[1], trace[2], trace[3]))

                logger.error(f"Exception occurred in {func.__name__}: {e}")
                print("Error details : ")
                logger.info("\n".join(stack_trace))

                if re_raise:
                    raise

                return None

        return wrapper

    return decorator


def flatten_nested_list(nested_list, deep=True):
    """
    this will recursively flatten a nested list
    :param nested_list:  to flatten
    :return: a list with nested flattened values
    """
    flattened = []
    for item in nested_list:

        if isinstance(item, (tuple, list, set)):
            # Recursively flatten the sublist
            flattened.extend(flatten_nested_list(item))
        else:
            # If the item is not a list, append it to the flattened list
            flattened.append(item)
    return flattened


def flatten_dict(nested_dict, parent_key='', separator='.'):
    flattened = {}
    for key, value in nested_dict.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        if isinstance(value, dict):
            # Recursively flatten the sub-dictionary
            flattened.update(flatten_dict(value, new_key, separator=separator))
        else:
            # Add the current key-value pair to the flattened dictionary
            flattened[new_key] = value
    return flattened


if __name__ == '__main__':
    ...
