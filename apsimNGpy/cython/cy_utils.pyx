# circle_area.pyx
cimport numpy as np
import numpy as np
import cython
from cython.parallel import prange

from scipy.spatial.distance import  cdist
cpdef area_of_circle(double r):
    cdef double pi = 3.141592653589793
    return pi * r * r
cpdef number_of_cells(double r, double cell_size):
    cdef double circle_area = area_of_circle(r)
    cdef double cell_area = cell_size * cell_size
    return int(circle_area / cell_area)
cdef split_single(np.ndarray[double] ar, int chunk_size):
    num_chunks = int(len(ar) / chunk_size)
    indices = range(chunk_size, len(ar), num_chunks)
    return np.array_split(ar, indices)
cdef split_mult_D_array(np.ndarray[double, ndim=2] ar, int chunk_size):
    num_chunks = int(len(ar) / chunk_size)
    print("number of chunks is:  ", num_chunks)
    indices = range(chunk_size, len(ar), num_chunks)
    return np.vsplit(ar, indices)
@cython.boundscheck(False)  # Turn off bounds-checking for entire function
@cython.wraparound(False)  # Turn off negative index wrapping for entire function
cdef euclidean_distance_single_to_many(double[:] point, np.ndarray[double, ndim=2] points):
    cdef int i, j
    cdef int num_points = points.shape[0]
    cdef double dist, temp_diff
    cdef double[:] result = np.empty(num_points, dtype=np.float64)

    for i in range(num_points):
        dist = 0.0
        for j in range(points.shape[1]):
            temp_diff = point[j] - points[i, j]
            dist += temp_diff * temp_diff
        result[i] = dist**0.5
    return np.asarray(result)
@cython.boundscheck(False)  # Turn off bounds-checking for entire function
@cython.wraparound(False)  # Turn off negative index wrapping for entire function
cdef np.ndarray access_value_python(np.ndarray[np.float64_t, ndim=2] arr, int i):
    return arr[i, :]

@cython.boundscheck(False)  # Turn off bounds-checking for entire function
@cython.wraparound(False)  # Turn off negative index wrapping for entire function
cpdef ecdx(np.ndarray[double, ndim=2] points1, np.ndarray[double, ndim=2] points2):
    cdef double[:, :] arr1 = points1
    cdef double[:, :] arr2 =points1
    cdef int i, j, k
   #cdef double pts
    cdef int id0 =0
    cdef int id1 = 1
    cdef np.ndarray ac, pts, arp
    cdef int num_points1 = points1.shape[0]
    for i in range(num_points1):
            pts = points1[5, :]
            ac = euclidean_distance_single_to_many(pts, points2)
            arp = np.hstack(ac)
    return np.asarray(arp)
cpdef calculate_in_chunk(np.ndarray[double, ndim=2] Array, np.ndarray[double] foraging_suitability, int foraging_distance, int resolution):
    cdef int num_cells, leg
    cdef np.ndarray cd, arp, cod_distance, numerator, denominator, FQ, forage
    cdef int ax = 1
    cdef int neg = -1
    num_cells = number_of_cells(foraging_distance, resolution)
    foraging_aray = split_single(foraging_suitability, num_cells)
    arr = split_mult_D_array(Array, num_cells)
    #self.p = [cdist(i, i)*-1 for i in arr]
    leg = len(arr)
    for i in range(leg):
        forage = foraging_aray[i]
        # reshape the foraging array after the calculations
        cd = cdist(arr[i], arr[i]) * neg
        cod_distance =  np.exp( ((cd) / foraging_distance))
        num = cod_distance * foraging_aray[i]  #/cod_distance
        numerator, denominator = np.sum(num, axis =ax), np.sum(cod_distance, axis =ax)
        FQ = np.divide(numerator, denominator)
        arp = np.hstack(FQ)
        return np.asarray(arp)
import numpy as np
import rasterio

def mean_filter(raster_data, window_size=3):
    """
    Apply a mean filter to a 2D numpy array (raster data).
    """
    padding = window_size // 2
    padded_data = np.pad(raster_data, ((padding, padding), (padding, padding)), mode='reflect')
    filtered_data = np.zeros_like(raster_data)

    for i in range(padded_data.shape[0] - window_size + 1):
        for j in range(padded_data.shape[1] - window_size + 1):
            window = padded_data[i:i + window_size, j:j + window_size]
            filtered_data[i, j] = np.mean(window)

    return filtered_data

# Read the raster data
with rasterio.open('path_to_raster.tif') as src:
    band1 = src.read(1)
    profile = src.profile

    # Apply the filter
    filtered_band = mean_filter(band1)

    # Save the filtered raster
    with rasterio.open('filtered_raster.tif', 'w', **profile) as dst:
        dst.write(filtered_band, 1)
cdef evaluate_crop(x):
    crops = ['F', 'U', 'X', 'T', 'G', 'R', 'P', 'I']
    for crop in crops:
        if crop in x:
            return False
    return True
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
           dt= ", ".join([crop_mapping[c] for c in arrr[i]])
           data[i] = dt
    return data