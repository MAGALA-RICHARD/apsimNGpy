import os

import pandas as pd
import numpy as np
from scipy import interpolate
from scipy.interpolate import UnivariateSpline
from apsimNGpy.core.base_data import LoadExampleFiles, Path
import copy
import json
import requests
from datetime import datetime

wd = Path.home()
os.chdir(wd)
# maize = LoadExampleFiles(wd).get_maize_model
import numpy as np
# TODO; this is not a good name for this file.
lon = -93.620369, 42.034534


def calculate_tav_amp(df):
    mean_maxt = df['maxt'].mean(skipna=True, numeric_only=None)
    mean_mint = df['mint'].mean(skipna=True, numeric_only=None)
    AMP = round(mean_maxt - mean_mint, 2)
    tav = round(np.mean([mean_maxt, mean_mint]), 3)
    return tav, AMP


def create_met_header(fname, lonlat, tav, AMP, site= None):
    if not site:
        site = 'Not stated'
    if os.path.isfile(fname):
        os.remove(fname)
    headers = ['year', 'day', 'radn', 'maxt', 'mint', 'rain']
    header_string = " ".join(headers) + "\n"
    # close and append new lines
    with open(fname, "a") as f2app:
        f2app.writelines(
            [f'!site: {site}\n', f'latitude = {lonlat[1]} \n', f'longitude = {lonlat[0]}\n', f'tav ={tav}\n',
             f'amp ={AMP}\n'])
        f2app.writelines([header_string])
        f2app.writelines(['() () (MJ/m2/day) (oC) (oC) (mm)\n'])


def impute_data(met, method="mean", verbose=False, **kwargs):
    """
       Handles missing data in a pandas DataFrame by imputing missing values based on the specified method.

       Parameters:
       - met (pd.DataFrame): The DataFrame containing data with missing values.
       - method (str, optional): Method used for imputing missing values. Options: "approx", "spline", "mean". Default is "mean".
       - verbose (bool, optional): If True, prints information about the imputation process. Default is False.
       - **kwargs (dict, optional): Additional keyword arguments. Currently supports:
           - copy (bool): If True, makes a deep copy of the DataFrame before imputation. Default is False.

       Behavior and Methods:
       - Deep Copy: Creates a deep copy of the DataFrame if 'copy=True' to prevent changes to the original data.
       - Input Validation: Checks if the input is a pandas DataFrame and if the specified method is valid.
       - Missing Value Imputation: Imputes missing values in the DataFrame based on the specified method:
           - "approx": Linear interpolation.
           - "spline": Spline interpolation, useful for non-linear data.
           - "mean": Fills missing values with the mean of the column.
       - Verbose Output: Provides detailed information about the imputation process if 'verbose=True'.

       Returns:
       - pd.DataFrame: The DataFrame with missing values imputed.

       Usage:
       df = pd.read_csv('your_file.csv')  # Load your data
       imputed_df = impute_data(df, method="mean", verbose=True, copy=True)
       """
    cope = kwargs.get('copy')
    if cope:
        met = copy.deepcopy(met)
    if not isinstance(met, pd.DataFrame):
        raise ValueError("met should be a pandas DataFrame")

    methods = ["approx", "spline", "mean"]
    if method not in methods:
        raise ValueError(f"method should be one of {methods}")

    # Function to print if verbose is True
    def vprint(*args):
        if verbose:
            print(*args)

    # Impute first and last row if all their values are NA
    if met.iloc[0].isna().all():
        vprint("Imputing first row with mean as all values are NA")
        met.iloc[0] = met.mean(skipna=True)

    if met.iloc[-1].isna().all():
        vprint("Imputing last row with mean as all values are NA")
        met.iloc[-1] = met.mean(skipna=True)

    # Iterate through each column
    for col_name, column in met.items():
        na_indices = column[column.isna()].index
        try:
            # If column has missing values
            if na_indices.any():
                vprint(f"Missing values for {col_name}")
                # Interpolate or fill with mean
                match method:
                    # Prepare valid indices and values for interpolation
                    case "approx":
                        valid_indices = column[~column.isna()].index
                        valid_values = column[~column.isna()]
                        f = interpolate.interp1d(valid_indices, valid_values, bounds_error=False)
                        imputed_values = pd.Series(f(na_indices), index=na_indices)
                    case 'spline':
                        valid_indices = column[~column.isna()].index
                        valid_values = column[~column.isna()]
                        f = interpolate.UnivariateSpline(valid_indices, valid_values, s=0)

                        imputed_values = pd.Series(f(na_indices), index=na_indices)
                    case 'mean':
                        mean_value = column.mean(skipna=True)
                        imputed_values = pd.Series(mean_value, index=na_indices)
                # Fill NA values in the column with imputed values
                met[col_name].fillna(imputed_values, inplace=True)
        except Exception as e:
            error_message = str(e)
            if "(m>k) failed for hidden m: fpcurf0:m=0" in error_message:
                vprint(f"Specific dfitpack error encountered in {col_name}: {error_message}: **")
                vprint(f"While imputing [{col_name}], {method} method failed trying mean instead")
                # Handle the specific dfitpack error, e.g., by using mean imputation
                mean_value = column.mean(skipna=True)
                met[col_name].fillna(mean_value, inplace=True)
            else:
                vprint(f"An unexpected error occurred while imputing {col_name}: {e}")
                vprint(f"While imputing [{col_name}], {method} method, failed trying mean instead")
                # Handle other general exceptions
                # Fallback to mean or another method if interpolation fails
                mean_value = column.mean(skipna=True)
                met[col_name].fillna(mean_value, inplace=True)

    return met


def separate_date(date_str):
    # Ensure the date string is of the correct format
    # TODO introduce the use of the dateutils package. delete this function
    # Extracting year, month, and day
    year = date_str[:4]
    month = date_str[4:6]
    day = date_str[6:]

    return year, month, day


def getnasa_df(lonlat, start, end):
    # TODO This function name is likely duplicated
    lon = lonlat[0]
    lat = lonlat[1]
    param = ["T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR", "RH2M", "WS2M"]
    # dictionary
    """
    "PRECTOTCORR": Corrected Total Precipitation
    "WS2M" : wind speed at 2 meters
    RH2M: Relative Humidity at 2 Meters
    ALLSKY_SFC_SW_DWN: All Sky Surface Shortwave Downward Irradiance
    """
    pars = ",".join(param)
    rm = f'https://power.larc.nasa.gov/api/temporal/daily/point?start={start}0101&end={end}1231&latitude={lat}&longitude={lon}&community=ag&parameters={pars}&format=json&user=richard&header=true&time-standard=lst'
    data = requests.get(rm)
    dt = json.loads(data.content)
    fd = {}
    headers = ['year', 'day', 'radn', 'maxt', 'mint', 'rain', 'vp', 'swe']
    df = pd.DataFrame(dt["properties"]['parameter'])
    fd['year'] = [date_str[:4] for date_str in df.index]
    date_object = [datetime.strptime(date_str, '%Y%m%d') for date_str in df.index]
    fd['day'] = [date_obj.timetuple().tm_yday for date_obj in date_object]
    fd['radn'] = df.ALLSKY_SFC_SW_DWN
    fd['maxt'] = df.T2M_MAX
    fd['mint'] = df.T2M_MIN
    fd['rain'] = df.PRECTOTCORR
    df = pd.DataFrame(fd)
    return df


def met_nasapower(lonlat, start=1990, end=2000, fname='met_nasapower.met'):
    df = getnasa_df(lonlat, start, end)
    tav, AMP = calculate_tav_amp(df)
    create_met_header(fname, lonlat, tav, AMP, site = None)
    data_rows = []
    headers = ['year', 'day', 'radn', 'maxt', 'mint', 'rain']
    for index, row in df.iterrows():
        current_row = []
        for header in headers:
            current_row.append(str(row[header]))
        current_str = " ".join(current_row) + '\n'
        data_rows.append(current_str)
    with open(fname, "a") as f2app:
        f2app.writelines(data_rows)
    return fname


if __name__ == '__main__':
    # imputed_df = impute_data(df, method="approx", verbose=True, copy=True)
    kampala = 32.582520, 0.347596
    df = getnasa_df(kampala, 2000, 2020)
    imputed_df = impute_data(df, method="approx", verbose=True, copy=True)
    hf = met_nasapower(kampala, end=2020, fname='kampala_new.met')
