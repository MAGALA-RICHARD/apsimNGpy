
import numpy as np
from scipy.spatial.distance import  cdist
def area_of_circle(r):
    pi = 3.141592653589793
    return pi * r * r
def number_of_cells(r, cell_size):
    circle_area = area_of_circle(r)
    cell_area = cell_size * cell_size
    return int(circle_area / cell_area)
def split_single(ar, chunk_size):
    num_chunks = int(len(ar) / chunk_size)
    indices = range(chunk_size, len(ar), num_chunks)
    return np.array_split(ar, indices)
def split_mult_D_array(ar, chunk_size):
    num_chunks = int(len(ar) / chunk_size)
    print("number of chunks is:  ", num_chunks)
    indices = range(chunk_size, len(ar), num_chunks)
    return np.vsplit(ar, indices)
 # Turn off negative index wrapping for entire function
def euclidean_distance_single_to_many(point, points):
    num_points = points.shape[0]
    for i in range(num_points):
        dist = 0.0
        for j in range(points.shape[1]):
            temp_diff = point[j] - points[i, j]
            dist += temp_diff * temp_diff
        result[i] = dist**0.5
    return results

def  access_value_python( arr,  i):
    return arr[i, :]

def ecdx(points1, points2):
    arr1 = points1
    arr2 =points1
    num_points1 = points1.shape[0]
    for i in range(num_points1):
            pts = points1[5, :]
            ac = euclidean_distance_single_to_many(pts, points2)
            arp = np.hstack(ac)
    return arp
def calculate_in_chunk(Array, foraging_suitability,  foraging_distance, resolution):
    num_cells = number_of_cells(foraging_distance, resolution)
    foraging_aray = split_single(foraging_suitability, num_cells)
    arr = split_mult_D_array(Array, num_cells)
    #self.p = [cdist(i, i)*-1 for i in arr]
    leg = len(arr)
    for i in range(leg):
        forage = foraging_aray[i]
        # reshape the foraging array after the calculations
        cd = cdist(arr[i], arr[i]) * -1
        cod_distance =  np.exp( ((cd) / foraging_distance))
        num = cod_distance * foraging_aray[i]  #/cod_distance
        numerator, denominator = np.sum(num, axis =ax), np.sum(cod_distance, axis =ax)
        FQ = np.divide(numerator, denominator)
        arp = np.hstack(FQ)
        return arp

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

