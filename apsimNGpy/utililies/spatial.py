import geopandas as gpd
import utils
import numpy as np
from apsimNGpy.utililies.utils  import select_process
from shapely.geometry import Polygon
import random
from shapely.geometry import Point
from shapely.ops import unary_union

WGS84 = 'epsg:4326'
shp = r'D:\ACPd\Bear creek simulations\bearcreek_shape\bearcreek.shp'


def create_polygon1(args):
    lon, lat, lon_step, lat_step = args
    return Polygon([(lon, lat), (lon + lon_step, lat), (lon + lon_step, lat + lat_step), (lon, lat + lat_step)])


def create_fishnet1(pt, lon_step=200, lat_step=200, ncores=3, use_thread=True, **kwargs):
    """

    Args:
        pt: shape or point feature class layer
        lon_step: height of the polygon
        lat_step: width of the polygon
        ncores: number of cores to use
        use_thread: if True, threads will be used if false processes will be used
        **kwargs: use key word Return = gdf to return geponadas data frame otherwise if not supplied to will retrun an arrya

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
def generate_random_points(pt, resolution,  ncores, num_points):
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
        points_gdf = gpd.GeoDataFrame(geometry=all_points)# Add the points to the list
        GDF = points_gdf
    return np.array([(point.x, point.y) for point in GDF.geometry])


if __name__ == '__main__':

        df = create_fishnet1(shp, ncores=10, use_thread=True)
        gdf = df
        ap = generate_random_points(shp, 500, 10, 3)
