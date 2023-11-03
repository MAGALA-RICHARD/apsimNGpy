import os
import sys
import numpy as np
from os.path import join as opj
from multiprocessing import Pool
import pandas as pd
import time
import geopandas as gpd
import math

root = os.path.dirname(os.path.realpath(__file__))
path = opj(root, 'manager')
path_utilities = opj(root, 'utililies')
import utils

sys.path.append(path_utilities)
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import copy
from scipy.spatial.distance import cdist
import pyproj
from utils import get_centroid
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.geometry import Point
from tqdm import tqdm

lock = threading.Lock()


class PollinationBase:
    np.set_printoptions(precision=4)

    def __init__(self, in_landuseclass, field, method='euclidean', resoln=100,
                 SR=None, foraging_distance=700):
        """
            Initialize the RasterManagement object.

            Args:
                
            """
        self.layer = in_landuseclass
        self.method = method
        self.resolution = resoln
        self.SR = SR
        self.Field = field
        self.foraging_distance = foraging_distance

    def find_unique_classes(self):
        self.gdf = gpd.read_file(self.layer)
        self.UniqueClasses = self.gdf[self.Field].unique()
        return self

    @staticmethod
    def convert_centroid_lonlat(gdf):
        from pyproj import Proj, Transformer, transform
        # Load your GeoDataFrame (replace 'gdf_file.shp' with your file path)
        # Define the projected CRS (e.g., UTM Zone 33N)
        projected_crs = gdf.crs
        # Define the target geographic CRS (EPSG 4326 for lon/lat)
        geographic_crs = Proj(init='epsg:4326')

        def xy_to_lonlat(x, y):
            t = Transformer.from_crs(projected_crs, "epsg:4326", always_xy=True)
            lon, lat = t.transform(x, y)
            return lon, lat

        # Apply the conversion function to each centroid
        ap = gdf.geometry.centroid.apply(lambda geom: xy_to_lonlat(geom.x, geom.y))
        return ap

    @staticmethod
    def create_polygon1(args):
        lon, lat, lon_step, lat_step = args
        return Polygon([(lon, lat), (lon + lon_step, lat), (lon + lon_step, lat + lat_step), (lon, lat + lat_step)])

    @staticmethod
    def create_fishnet1(pt, lon_step=30, lat_step=30):
        gdf_shape = gpd.read_file(pt)
        CRS = gdf_shape.crs
        min_lon, min_lat, max_lon, max_lat = gdf_shape.total_bounds
        lats = np.arange(min_lat, max_lat, lat_step)
        lons = np.arange(min_lon, max_lon, lon_step)
        polygons = []
        with ThreadPoolExecutor(20) as executor:
            args = [(lon, lat, lon_step, lat_step) for lon in lons for lat in lats]
            polygons = list(executor.map(PollinationBase.create_polygon1, args))
        gdf = gpd.GeoDataFrame({'geometry': polygons}, crs=CRS)
        gdf_clip = gpd.clip(gdf, gdf_shape)
        return gdf_clip

    @staticmethod
    def convert_geopoint_to_array(geoseries):
        # Assuming 'geoseries' is your GeoSeries of Point geometries

        # Extract the x and y coordinates
        x_coords = geoseries.geometry.x
        y_coords = geoseries.geometry.y

        # Stack the coordinates into a 2D array
        coords_array = np.column_stack((x_coords, y_coords))

        return coords_array

    @staticmethod
    def split_mult_D_array(ar, chunk_size):
        num_chunks = math.ceil(len(ar) / chunk_size)
        print("number of chunks is:  ", num_chunks)
        indices = range(chunk_size, len(ar), num_chunks)
        return np.vsplit(ar, indices)

    @staticmethod
    def split_single(ar, chunk_size):
        num_chunks = math.ceil(len(ar) / chunk_size)
        indices = range(chunk_size, len(ar), num_chunks)
        return np.array_split(ar, indices)

    @property
    def get_fieldnames(self):
        gdf = gpd.read_file(self.layer)
        print(gdf.columns)

    def get_fishnets(self):
        self.FishNets = self.create_fishnet1(self.layer, self.resolution, self.resolution)
        land_gdf = self.find_unique_classes()
        print("joining fishnet with the main land cover class")
        self.joined = gpd.sjoin(self.FishNets, land_gdf.gdf, how='right', predicate='within')
        self.Centroids = self.joined.centroid
        self.lonlat = PollinationBase.convert_centroid_lonlat(self.joined)

        self.Array = self.convert_geopoint_to_array(self.Centroids).astype('float32')
        self.record_array = self.joined.drop(columns=['geometry'])
        self.record_array['OBJECTID'] = range(1, len(self.Array) + 1)
        print(len(self.lonlat))
        self.record_array["Shape"] = np.array(self.lonlat)
        self.record_array = self.record_array.to_records()
        return self

    def organise_suitability(self, foraging_csv_file, Nesting_csv, category_col="category", new_values_col='values'):
        """_summary_

          Args:
            foraging_csv_file (_str_): _csv file name describing foraging sutiability of the different land cover classess_
            category_col (str, optional): _class colname_. Defaults to "category".
            foraging_col (str, optional): _colname for foraging values_. Defaults to 'foraging'.
            nesting_col (str, optional): _colname for nesting values_. Defaults to 'nesting'.

          Returns:
            _array_: classified array like object
          """
        # df= pd.read_csv(os.path.join(back_dir, 'unique_mudcreek_landcover_classes.csv'))
        self.get_fishnets()
        landcover = np.array(self.joined[self.Field])
        global array
        array = landcover

        def replace(df):
            try:
                if not isinstance(df, pd.DataFrame):
                    df = pd.read_csv(df)
                assert category_col in df.columns, f"Category column name, '{category_col}'  not found in the provided data "
                assert new_values_col in df.columns, f"Column '{new_values_col}' provided does not exist in the data"
                self.old = np.array(df[category_col], dtype="U25")
                self.new = np.array(df[new_values_col], dtype='float64')
                # copy the array

                arrayc = copy.deepcopy(array)

                print(array.shape, "\n....")

                for i in range(len(self.old)):
                    np.place(arrayc, arrayc == self.old[i], [self.new[i]])

                nesting_array = np.transpose(arrayc)
                return nesting_array
            except Exception as e:
                print(repr(e))

        self.nesting_suitability = replace(Nesting_csv)
        self.foraging_suitability = replace(foraging_csv_file)
        print("_____________________________________________________________________________________________")

        return self

    def calculate_in_chunk(self):
        self.Array = self.Array.astype('double')
        self.num_cells = utils.number_of_cells(self.foraging_distance, self.resolution)
        foraging_aray = self.split_single(self.foraging_suitability, self.num_cells)
        arr = self.split_mult_D_array(self.Array, self.num_cells)
        # self.p = [cdist(i, i)*-1 for i in arr]
        self.FUQ = []
        distances = []
        print('calculating the foraging quality of cell')
        for forage, distances in zip(foraging_aray, arr):
            # reshape the foraging array after the calculations
            self.cod_distance = np.exp(cdist(distances, distances, 'euclidean') * -1 / self.foraging_distance)
            num = self.cod_distance * forage  # /cod_distance
            numerator, denominator = np.sum(num, axis=1), np.sum(self.cod_distance, axis=1)
            FQ = np.divide(numerator, denominator)
            self.FUQ.append(FQ)
        self.fqqx = np.hstack(self.FUQ).astype('double')
        self.fqq = np.round(self.fqqx, decimals=4)
        # thing sneed to change from here
        self.pollinator_supply = []
        self.pa = self.fqq * self.nesting_suitability
        pa_split = self.split_single(self.pa, self.num_cells)
        forage = self.split_single(self.foraging_suitability, self.num_cells)
        distances = self.split_mult_D_array(self.Array, self.num_cells)
        results = []
        print('calculating the pollination supply')
        for i, pa, F in zip(distances, pa_split, forage):
            cod_distance = np.exp(cdist(i, i) * -1 / self.foraging_distance)
            ps_num = pa * cod_distance
            psp = np.sum(ps_num, axis=1) / np.sum(cod_distance, axis=1)
            results.append(psp)
        self.pollinator_supply = np.hstack(results)
        # ps_num =i * m
        # polination supply denominator
        # ps =np.sum(ps_num, axis =1) / np.sum(distances[i], axis =1)
        # self.pollinator_supply.append(ps)
        return self
        # self.num = self.foraging_suitability*cd
        # self.num = self.foraging_suitability*cd

    def calculate_in_chunk_ps(self):
        import random
        random.seed(10000)
        self.Array = self.Array.astype('double')
        self.num_cells = utils.number_of_cells(self.foraging_distance, self.resolution)
        foraging_aray = self.split_single(self.foraging_suitability, self.num_cells)
        arr = self.split_mult_D_array(self.Array, self.num_cells)

        # Create a global lock

        def calculate_in_chunk_fq(idex):
            with lock:
                forage, distances = (foraging_aray[idex], arr[idex])
                # reshape the foraging array after the calculations
                self.cod_distance = np.exp(cdist(distances, distances, 'euclidean') * -1 / self.foraging_distance)
                num = self.cod_distance * forage  # /cod_distance
                numerator, denominator = np.sum(num, axis=1), np.sum(self.cod_distance, axis=1)
                FQ = np.divide(numerator, denominator)
                return FQ

        ideces = range(len(arr))
        with ThreadPoolExecutor(max_workers=2) as executor:
            ans = list(executor.map(calculate_in_chunk_fq, ideces))
            self.FQ = np.hstack(ans)
        self.pa = self.FQ * self.nesting_suitability
        pa_split = self.split_single(self.pa, self.num_cells)
        forage = self.split_single(self.foraging_suitability, self.num_cells)
        distances = self.split_mult_D_array(self.Array, self.num_cells)
        results = []

        def calcculate_ps_in_parallel(idex):
            with lock:
                forage, distances, pa = foraging_aray[idex], arr[idex], pa_split[idex]
                # for i, pa, F in zip(distances, pa_split, forage):
                cod_distance = np.exp(cdist(distances, distances) * -1 / self.foraging_distance)
                ps_num = pa * cod_distance
                psp = np.sum(ps_num, axis=1) / np.sum(cod_distance, axis=1)
                return psp

        with ThreadPoolExecutor(max_workers=2) as executor:
            ans = list(executor.map(calcculate_ps_in_parallel, ideces))
        self.pollinator_supply = np.hstack(ans)
        self.Normalised_pollination = self.pollinator_supply / self.FQ
        return self

    def calculate_aggregate(self):
        # self.p = [cdist(i, i)*-1 for i in arr]
        fr = self.split_single(self.foraging_suitability, self.num_cells)
        ideces = range(len(fr))
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = executor.map(self.calculate_in_chunk_mp, ideces)
            list(results)
        return self

    def trial(self):
        Array, foraging_suitability = self.Array.astype("double"), self.foraging_suitability.astype('double')
        self.cython = ch(Array, foraging_suitability, self.foraging_distance, self.resolution)
        return self

    def calculate_fq(self, cod):
        x, y = cod
        A = np.array([[x, y]])
        cd = cdist(A, self.Array, 'euclidean') * -1
        cod_dist = np.exp(((cd) / self.foraging_distance))
        num = np.multiply(cod_dist, self.foraging_suitability)
        # den = np.exp((cd)/self.foraging_distance)
        FQ = np.sum(num) / (np.sum(cod_dist))
        return FQ

    def calculate_pollnation_supply(self, cod):
        x, y = cod
        A = np.array([[x, y]])
        cd = cdist(A, self.Array, self.method) * -1
        cod_distance = np.exp(cd / self.foraging_distance)
        # pollination supply numerator
        self.fq = np.array([self.calculate_fq(i) for i in self.Array])
        self.pa = self.fq * self.nesting_suitability
        ps_num = self.pa * cod_distance
        # polination supply denominator
        PS = np.sum(ps_num) / np.sum(cod_distance)
        return PS

    def cal(self):
        self.PS = np.array([self.calculate_pollnation_supply(i) for i in self.Array])
        return self

    def calculalate(self):
        total_iterations = len(self.Array)
        self.FQ = np.array([self.calculate_fq(i) for i in self.Array])  # np.hstack(self.FUQ)
        self.PA = self.FQ * self.nesting_suitability
        # we need the pollinator abundance
        try:
            pollinator_supply = np.zeros(total_iterations)
            with tqdm(total=total_iterations, desc="Calculating pollination supply from nesting to foraging cells",
                      unit="cells") as pbar:
                for idx, cod in enumerate(self.Array):
                    A = np.array([[cod[0], cod[1]]])
                    cd = cdist(A, self.Array, self.method) * -1
                    cod_distance = np.exp(cd / self.foraging_distance)
                    # pollination supply numerator
                    ps_num = self.PA * cod_distance
                    # polination supply denominator
                    pollinator_supply[idx] = np.sum(ps_num) / np.sum(cod_distance)
                    pbar.update(1)
            self_original_pol_sup = np.reshape(pollinator_supply, (1, len(pollinator_supply)))
            print(self.FQ)
            self.Normalised_pollination = self_original_pol_sup * np.divide(self.foraging_suitability, self.FQ)
            self.normalised_poll = self.Normalised_pollination
            # neeed the PA defined inside here
            pa = self.PA.flatten()  # pollinator abundance
            ps = self_original_pol_sup.flatten()  # pollinator supply
            fq = self.FQ.flatten()  # foraging quality
            print(self.FQ.shape)

            # add new field and append the data
            FQ_name = "FQ"
            pa_abund = "PA"
            np_name = 'Nopo'
            field_type = "FLOAT"  # Specify the appropriate data type (e.g., "TEXT", "INTEGER", "FLOAT", etc.)
            field_names = [FQ_name, pa_abund, np_name, "NtNom"]
            # Add the field to the feature class

        except Exception as e:
            print(repr(e))
            raise

        return self


# test the fucntion
if __name__ == "__main__":
    os.chdir('D:\wd\GIS')
    np.set_printoptions(precision=2)
    a = time.perf_counter()
    ptt = r'D:\ENw_data\creek.shp'
    print(os.path.exists(ptt))
    path = r'C:\Users\rmagala\OneDrive\Pollination mapping\Pollination analysis\Scripts\forage.csv'
    back_dir = os.path.join(os.path.dirname(path), 'Sample data')
    test_results = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Testing data')
    if not os.path.exists(test_results):
        os.mkdir(test_results)
    os.chdir(test_results)
    sample_data = os.path.join(back_dir, 'Sample data')
    fc = r'D:\ACPd\Base_files\acpf_huc070801050305\acpf070801050305.gdb\FB070801050305'
    sample_data = os.path.join(path, 'Sample data')
    raster = r'C:\Users\rmagala\OneDrive\CRP 456 my final project\final+project+submission+files\final project submission files\Sample data\mudcreeklandcover.tif'

    # initialize the pollination object
    pp = PollinationBase(in_landuseclass=ptt, resoln=500, field="GenLU")
    for _ in range(2):
        pp.foraging_distance = 1100
        pm = pp.get_fishnets()
        print(pm.record_array)
        break
        pp.organise_suitability("classes.csv", "classes.csv")
        ws = r'D:\ACPd\Base_files\acpf_huc070801050305'
        pp.find_unique_classes()
        # pp.calculate_in_chunk()
        # profiler = cProfile.Profile()
        # profiler.enable()
        a = time.perf_counter()
        # pp.calculate_in_chunk()
        pp.calculalate()
        print(pp.normalised_poll)
        print(" single took: ", a - b, 'seconds')
        a = time.perf_counter()
        pp.calculate_in_chunk_ps()
        b = time.perf_counter()
        # print(pp.Normalised_pollination)
        print("pool_processor took: ", a - b, 'seconds')
        os.chdir(r'D:\wd\GIS')
        np.save(f'FB070801050305_resoln_{pp.resolution}.npy', pp.record_array)
        pat = os.path.join(os.getcwd(), f'FB070801050305_resoln_{pp.resolution}.csv')
        print(pat)
        pm = np.load(f'FB070801050305_resoln_{pp.resolution}.npy', allow_pickle=True)
        pp.get_fishnets()
