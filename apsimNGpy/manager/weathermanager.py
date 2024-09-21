import os
from os.path import join as opj
from datetime import datetime
import datetime
import urllib
from pathlib import Path
from typing import Union

from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception, retry_if_exception_type
import requests
import random
import json
import pandas as pd
import time
import statistics
from progressbar import ProgressBar
import progressbar
import numpy as np
import string
import io
from scipy import interpolate
import copy
import requests
from datetime import datetime
import string
from io import StringIO
import io
import os
from scipy import interpolate
from scipy.interpolate import UnivariateSpline
import logging

from datetime import datetime
import pandas as pd
import numpy as np
from scipy import interpolate
import copy
import warnings

# we only need to retry if any of these error occured, the rest we dont need to know
NETWORK_EXCEPTIONS = (requests.ConnectionError, requests.Timeout, requests.RequestException)


def try_many_times(k_times):
    if k:
        return retry(stop=stop_after_attempt(k_times), wait=wait_fixed(0.5),
                     retry=retry_if_exception_type(NETWORK_EXCEPTIONS))


def generate_unique_name(base_name, length=6):
    # TODO this function has 4 duplicates
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=length))
    unique_name = base_name + '_' + random_suffix
    return unique_name


# from US_states_abbreviation import getabreviation

# let us manage network issues more gracefully
@retry(stop=stop_after_attempt(3), wait=wait_fixed(0.5), retry=retry_if_exception_type(NETWORK_EXCEPTIONS))
def get_iem_by_station(dates_tuple, station, path, met_tag):
    '''
      Dates is a tupple/list of strings with date ranges
      
      an example date string should look like this: dates = ["01-01-2012","12-31-2012"]
      
      if station is given data will be downloaded directly from the station the default is false.
      
      mettag: your prefered tag to save on filee
      '''
    # access the elements in the metdate class above
    weather_dates = MetDate(dates_tuple)
    stationX = station[:2]
    state_clim = stationX + "CLIMATE"
    str0 = "http://mesonet.agron.iastate.edu/cgi-bin/request/coop.py?network="
    str1 = str0 + state_clim + "&stations=" + station
    str2 = str1 + "&year1=" + weather_dates.year_start + "&month1=" + weather_dates.start_month + "&day1=" + weather_dates.start_day + "&year2=" + weather_dates.year_end + "&month2=" + weather_dates.end_month + "&day2=" + weather_dates.end_day
    str3 = (str2 + "&vars%5B%5D=apsim&what=view&delim=comma&gis=no")
    url = str3
    rep = requests.get(url)
    if rep.ok:
        met_name_of_file = station + met_tag + ".met"
        os.chdir(path)
        if not os.path.exists('weatherdata'):
            os.mkdir('weatherdata')
        pt = os.path.join('weatherdata', met_name_of_file)

        with open(pt, 'wb') as met_fileX:
            # remember to include the file extension name
            met_fileX.write(rep.content)
            rep.close()
            met_fileX.close()
            print(rep.content)
    else:
        print("Failed to download the data web request returned code: ", rep)


class MetDate:
    def __init__(self, dates):
        self.start_date = dates[0]
        self.end_date = dates[1]
        self.start_month = dates[0][:2]
        self.end_month = dates[1][:2]
        self.year_start = dates[0].split("-")[2]
        self.year_end = dates[1].split("-")[2]
        import datetime
        self.start_day = datetime.datetime.strptime(dates[0], '%m-%d-%Y').strftime('%j')
        self.end_day = datetime.datetime.strptime(dates[1], '%m-%d-%Y').strftime('%j')


dates = ['01-01-2000', '12-31-2020']

states = {
    'AK': 'Alaska',
    'AL': 'Alabama',
    'AR': 'Arkansas',
    'AZ': 'Arizona',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DC': 'District of Columbia',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'HI': 'Hawaii',
    'IA': 'Iowa',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'MA': 'Massachusetts',
    'MD': 'Maryland',
    'ME': 'Maine',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MO': 'Missouri',
    'MS': 'Mississippi',
    'MT': 'Montana',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'NE': 'Nebraska',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NV': 'Nevada',
    'NY': 'New York',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VA': 'Virginia',
    'VT': 'Vermont',
    'WA': 'Washington',
    'WI': 'Wisconsin',
    'WV': 'West Virginia',
    'WY': 'Wyoming'
}

# flip the keys
new_dict = {}
for k, v in states.items():
    new_dict[v] = k


def getabreviation(x):
    ab = new_dict[x]
    return (ab)


# function to define the date ranges
def daterange(start, end):
    '''
  start: the starting year to download the weather data
  -----------------
  end: the year under which download should stop
  '''
    startdates = '01-01'
    enddates = '12-31'
    end = str(end) + "-" + enddates
    start = str(start) + "-" + startdates
    drange = pd.date_range(start, end)
    return (drange)


# check if a year is aleap year
def isleapyear(year):
    if (year % 400 == 0) and (year % 100 == 0) or (year % 4 == 0) and (year % 100 != 0):
        return (True)
    else:
        return (False)


# download radiation data for replacement
@retry(stop=stop_after_attempt(3), retry=retry_if_exception_type(NETWORK_EXCEPTIONS))
def get_nasarad(lonlat, start, end):
    lon = lonlat[0]
    lat = lonlat[1]
    pars = "ALLSKY_SFC_SW_DWN"
    rm = f'https://power.larc.nasa.gov/api/temporal/daily/point?start={start}0101&end={end}1231&latitude={lat}&longitude={lon}&community=ag&parameters={pars}&format=json&user=richard&header=true&time-standard=lst'
    data = requests.get(rm)
    dt = json.loads(data.content)
    df = pd.DataFrame(dt["properties"]['parameter'])
    if len(df) == len(daterange(start, end)):
        return df

    # fucntion to download data from daymet


@retry(stop=stop_after_attempt(2), retry=retry_if_exception_type(NETWORK_EXCEPTIONS))
def day_met_by_location(lonlat, start, end, cleanup=True, filename=None):
    '''collect weather from daymet solar radiation is replaced with that of nasapower
   ------------
   parameters
   ---------------
   start: Starting year
   
   end: Ending year
   
   lonlat: A tuple of xy cordnates
   
   Cleanup:  A bolean True or False default is true: deletes the excel file generated during the file write up
   
   ------------
   returns complete path to the new met file but also write the met file to the disk in the working directory
   '''
    # import pdb
    # pdb.set_trace()

    datecheck = daterange(start, end)
    if start < 1980 or end > 2021:
        print(
            "requested year preceeds valid data range! \n end years should not exceed 2021 and start year should not be less than 1980")
    else:
        base_url = 'https://daymet.ornl.gov/single-pixel/api/data?'
        latstr = 'lat=' + str(lonlat[1])
        lonstr = '&lon=' + str(lonlat[0])
        varss = ['dayl', 'prcp', 'srad', 'tmax', 'tmin', 'vp', 'swe']
        setyears = [str(year) for year in range(start, end + 1)]
        # join the years as a string
        years_in_range = ",".join(setyears)
        years_str = "&years=" + years_in_range
        varfield = ",".join(varss)
        var_str = "&measuredParams=" + varfield
        # join the string url together
        url = base_url + latstr + lonstr + var_str + years_str
        conn = requests.get(url, timeout=60)

        if not conn.ok:
            print("failed to connect to server")
        elif conn.ok:
            # print("connection established to download the following data", url)
            # outFname = conn.headers["Content-Disposition"].split("=")[-1]
            outFname = conn.headers["Content-Disposition"].split("=")[-1]
            text_str = conn.content
            outF = open(outFname, 'wb')
            outF.write(text_str)
            outF.close()
            conn.close()
            #       read the downloaded data to a data frame
            dmett = pd.read_csv(outFname, delimiter=',', skiprows=7)
            vp = dmett['vp (Pa)'] * 0.01
            # calcuate radn
            radn = dmett['dayl (s)'] * dmett['srad (W/m^2)'] * 1e-06
            # re-arrange data frame
            year = np.array(dmett['year'])
            day = np.array(dmett['yday'])
            radn = np.array(radn)
            maxt = np.array(dmett['tmax (deg c)'])
            mint = np.array(dmett['tmin (deg c)'])
            rain = np.array(dmett['prcp (mm/day)'])
            vp = np.array(vp)
            swe = np.array(dmett['swe (kg/m^2)'])
            df = pd.DataFrame(
                {'year': year, 'day': day, 'radn': radn, 'maxt': maxt, 'mint': mint, 'rain': rain, 'vp': vp,
                 'swe': swe})
            # bind the frame
            # calculate mean annual applitude in mean monthly temperature (TAV)
            ab = [a for a in setyears]
            # split the data frame
            ab = [x for _, x in df.groupby(df['year'])]
            df_bag = []
            # constants to evaluate the leap years
            leapfactor = 4
            for i in ab:
                if (all(i.year % 400 == 0)) and (all(i.year % 100 == 0)) or (all(i.year % 4 == 0)) and (
                        all(i.year % 100 != 0)):
                    x = i[['year', 'radn', 'maxt', 'mint', 'rain', 'vp', 'swe', ]].mean()
                    year = round(x.iloc[0], 0)
                    day = round(366, 0)
                    new_row = pd.DataFrame(
                        {'year': [year], 'day': [day], 'radn': [0], 'maxt': [0], 'mint': [0], 'rain': [0], 'vp': [0],
                         'swe': [0]})
                    df_bag.append(pd.concat([i, new_row], ignore_index=True))

                    continue
                else:
                    df_bag.append(i)
                    frames = df_bag
            newmet = pd.concat(frames)
            newmet.index = range(0, len(newmet))
            # repalce radn data
            rad = get_nasarad(lonlat, start, end)
            newmet["radn"] = rad.ALLSKY_SFC_SW_DWN.values
            if len(newmet) != len(datecheck):
                print('date discontinuities still exisists')
            else:
                # print("met data is in the range of specified dates no discontinuities")
                rg = len(newmet.day.values) + 1
                # newmet  = pd.concat(newmet)
                mean_maxt = newmet['maxt'].mean(skipna=True, numeric_only=None)
                mean_mint = newmet['mint'].mean(skipna=True, numeric_only=None)
                AMP = round(mean_maxt - mean_mint, 2)
                tav = round(statistics.mean((mean_maxt, mean_mint)), 2)
                tile = conn.headers["Content-Disposition"].split("=")[1].split("_")[0]
                fn = conn.headers["Content-Disposition"].split("=")[1].replace("csv", 'met')
                if not filename:
                    shortenfn = generate_unique_name("Daymet") + '.met'
                else:
                    shortenfn = filename
                if not os.path.exists('weatherdata'):
                    os.makedirs('weatherdata')
                fn = shortenfn
                fname = os.path.join('weatherdata', fn)
                headers = ['year', 'day', 'radn', 'maxt', 'mint', 'rain', 'vp', 'swe']
                header_string = " ".join(headers) + "\n"
                # close and append new lines
                with open(fname, "a") as f2app:
                    f2app.writelines([f'!site: {tile}\n', f'latitude = {lonlat[1]} \n', f'longitude = {lonlat[0]}\n',
                                      f'tav ={tav}\n', f'amp ={AMP}\n'])
                    f2app.writelines([header_string])
                    f2app.writelines(['() () (MJ/m2/day) (oC) (oC) (mm) (hPa) (kg/m2)\n'])
                    # append the weather data
                    data_rows = []
                    for index, row in newmet.iterrows():
                        current_row = []
                        for header in headers:
                            current_row.append(str(row[header]))
                        current_str = " ".join(current_row) + '\n'
                        data_rows.append(current_str)

                    f2app.writelines(data_rows)

                if cleanup:
                    if os.path.isfile(os.path.join(os.getcwd(), outFname)):
                        os.remove(os.path.join(os.getcwd(), outFname))
                return fname  # fname


def get_met_from_day_met(lonlat, start, end, filename=None, retry_number=1, **kwa):
    """collect weather from daymet solar radiation is replaced with that of nasapower
    ------------
    parameters
    ---------------
    retry_number
    filename
    start: Starting year

    end: Ending year

    lonlat: A tuple of xy cordnates

    Cleanup:  A bolean True or False default is true: deletes the excel file generated during the file write up

    ------------
    returns a complete path to the new met file but also write the met file to the disk in the working directory
    :keyword timeout specifies the waiting time
    :keyword wait: the time in secods to try for every retry in case of network errors
    Example:
      # Assuming the function is imported:
          >>> from apsimNGpy.manager.weathermanager import get_met_from_day_met
          >>> wf = get_met_from_day_met(lonlat=(-93.04, 42.01247), start=2000, end=2020, filename='daymet.met')

    """
    # import pdb
    # pdb.set_trace()

    check_date_range = daterange(start, end)
    if start < 1980 or end > 2021:
        print("requested year preceeds valid data range! \n"
              " end years should not exceed 2021 and start year should not be less than 1980")
    else:
        base_url = 'https://daymet.ornl.gov/single-pixel/api/data?'
        lat_str = 'lat=' + str(lonlat[1])
        lon_str = '&lon=' + str(lonlat[0])
        var_headers = ['dayl', 'prcp', 'srad', 'tmax', 'tmin', 'vp', 'swe']
        set_years = [str(year) for year in range(start, end + 1)]
        # join the years as a string
        years_in_range = ",".join(set_years)
        years_str = "&years=" + years_in_range
        var_field = ",".join(var_headers)
        var_str = "&measuredParams=" + var_field
        # join the string url together
        url = base_url + lat_str + lon_str + var_str + years_str

        def connect():
            """
            just to allow users enter number retries and reduce overhead incase no retry is needed
            Returns
            -------

            """
            try:
                _conn = requests.get(url, timeout=kwa.get('timeout', 50))
                return _conn
            # We want to retry only if the network exceptions defined above occur not value errors or type errors and
            # so forth
            except NETWORK_EXCEPTIONS:
                raise

        if retry_number and isinstance(retry_number, int):
            # Apply the retry decorator to the connect function
            connect_with_retry = retry(wait=wait_fixed(kwa.get('wait', 0.5)),
                                       stop=stop_after_attempt(retry_number),
                                       )(connect)
            connector = connect_with_retry()
        else:
            connector = connect()
        if not connector.ok:
            print("failed to connect to server")
        elif connector.ok:
            out_file_name = "w" + filename + connector.headers["Content-Disposition"].split("=")[-1]
            text_str = connector.content
            connector.close()
            #  read the downloaded data to a data frame
            # Create an in-memory binary stream
            text_stream = io.BytesIO(text_str)
            # Read the data into a DataFrame
            day_met_read = pd.read_csv(text_stream, delimiter=',', skiprows=6)
            vp = day_met_read['vp (Pa)'] * 0.01
            # calculate radiation
            radiation = day_met_read['dayl (s)'] * day_met_read['srad (W/m^2)'] * 1e-06
            # re-arrange data frame
            year = np.array(day_met_read['year'])
            day = np.array(day_met_read['yday'])
            radiation = np.array(radiation)
            max_temp = np.array(day_met_read['tmax (deg c)'])
            mint = np.array(day_met_read['tmin (deg c)'])
            rain = np.array(day_met_read['prcp (mm/day)'])
            vp = np.array(vp)
            swe = np.array(day_met_read['swe (kg/m^2)'])
            _data_frame = pd.DataFrame(
                {'year': year, 'day': day, 'radn': radiation, 'maxt': max_temp, 'mint': mint, 'rain': rain, 'vp': vp,
                 'swe': swe})
            # bind the frame
            # calculate mean annual amplitude in mean monthly temperature (TAV)
            ab = [a for a in set_years]
            # split the data frame
            ab = [x for _, x in _data_frame.groupby(_data_frame['year'])]
            df_bag = []
            # constants to evaluate the leap years
            leap_factor = 4
            for i in ab:
                if (all(i.year % 400 == 0)) and (all(i.year % 100 == 0)) or (all(i.year % 4 == 0)) and (
                        all(i.year % 100 != 0)):
                    x = i[['year', 'radn', 'maxt', 'mint', 'rain', 'vp', 'swe', ]].mean()
                    year = round(x.iloc[0], 0)
                    day = round(366, 0)
                    new_row = pd.DataFrame(
                        {'year': [year], 'day': [day], 'radn': [0], 'maxt': [0], 'mint': [0], 'rain': [0], 'vp': [0],
                         'swe': [0]})
                    df_bag.append(pd.concat([i, new_row], ignore_index=True))

                    continue
                else:
                    df_bag.append(i)
                    frames = df_bag
            new_met = pd.concat(frames)
            new_met.index = range(0, len(new_met))
            # replace radiation data
            rad = get_nasarad(lonlat, start, end)
            new_met["radn"] = rad.ALLSKY_SFC_SW_DWN.values
            if len(new_met) != len(check_date_range):
                print('date discontinuities still exists')
            else:
                rg = len(new_met.day.values) + 1
                mean_max_temp = new_met['maxt'].mean(skipna=True, numeric_only=None)
                mean_mint = new_met['mint'].mean(skipna=True, numeric_only=None)
                AMP = round(mean_max_temp - mean_mint, 2)
                tav = round(statistics.mean((mean_max_temp, mean_mint)), 2)
                tile = connector.headers["Content-Disposition"].split("=")[1].split("_")[0]
                fn = connector.headers["Content-Disposition"].split("=")[1].replace("csv", 'met')
                if not filename:
                    short_file_name = generate_unique_name("Daymet") + '.met'
                else:
                    short_file_name = filename
                if not os.path.exists('weatherdata'):
                    os.makedirs('weatherdata')
                fn = short_file_name
                file_name_path = os.path.join('weatherdata', fn)
                headers = ['year', 'day', 'radn', 'maxt', 'mint', 'rain', 'vp', 'swe']
                header_string = " ".join(headers) + "\n"
                # close and append new lines
                with open(file_name_path, "a") as f2app:
                    f2app.writelines([f'!site: {tile}\n', f'latitude = {lonlat[1]} \n', f'longitude = {lonlat[0]}\n',
                                      f'tav ={tav}\n', f'amp ={AMP}\n'])
                    f2app.writelines([header_string])
                    f2app.writelines(['() () (MJ/m2/day) (oC) (oC) (mm) (hPa) (kg/m2)\n'])
                    # append the weather data
                    data_rows = []
                    for index, row in new_met.iterrows():
                        current_row = []
                        for header in headers:
                            current_row.append(str(row[header]))
                        current_str = " ".join(current_row) + '\n'
                        data_rows.append(current_str)

                    f2app.writelines(data_rows)

                if os.path.isfile(os.path.join(os.getcwd(), out_file_name)):
                    os.remove(os.path.join(os.getcwd(), out_file_name))
                return file_name_path  # fname


# download weather data from nasa power
def get_nasa(lonlat, start, end):
    lon = lonlat[0]
    lat = lonlat[1]
    param = ["T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR", "RH2M", "WS2M"]
    pars = ",".join(param)
    rm = f'https://power.larc.nasa.gov/api/temporal/daily/point?start={start}0101&end={end}1231&latitude={lat}&longitude={lon}&community=ag&parameters={pars}&format=json&user=richard&header=true&time-standard=lst'
    data = requests.get(rm)
    dt = json.loads(data.content)
    df = pd.DataFrame(dt["properties"]['parameter'])
    return df


def calculate_tav_amp(df):
    mean_maxt = df['maxt'].mean(skipna=True, numeric_only=None)
    mean_mint = df['mint'].mean(skipna=True, numeric_only=None)
    AMP = round(mean_maxt - mean_mint, 2)
    tav = round(np.mean([mean_maxt, mean_mint]), 3)
    return tav, AMP


def create_met_header(fname, lonlat, tav, AMP, site=None):
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
    Imputes missing data in a pandas DataFrame using specified interpolation or mean value.

    Parameters:
    - met (pd.DataFrame): DataFrame with missing values.
    - method (str, optional): Method for imputing missing values ("approx", "spline", "mean"). Default is "mean".
    - verbose (bool, optional): If True, prints detailed information about the imputation. Default is False.
    - **kwargs (dict, optional): Additional keyword arguments including 'copy' (bool) to deep copy the DataFrame.

    Returns:
    - pd.DataFrame: DataFrame with imputed missing values.
    """

    if kwargs.get('copy', False):
        met = copy.deepcopy(met)

    if not isinstance(met, pd.DataFrame):
        raise ValueError("The 'met' parameter must be a pandas DataFrame.")

    valid_methods = ["approx", "spline", "mean"]
    if method not in valid_methods:
        raise ValueError(f"Invalid method '{method}'. Valid options are {valid_methods}.")

    def vprint(*args):
        """Conditional print based on verbose flag."""
        if verbose:
            print(*args)

    # Impute values based on the specified method
    for col_name in met.columns:
        if met[col_name].isna().any():
            vprint(f"Imputing missing values in column '{col_name}' using '{method}' method.")
            if method in ["approx", "spline"]:
                # Prepare for interpolation
                valid = met[~met[col_name].isna()]
                indices = np.arange(len(met))
                if method == "approx":
                    interp_func = interpolate.interp1d(valid.index, valid[col_name], bounds_error=False,
                                                       fill_value="extrapolate")
                else:  # spline
                    interp_func = interpolate.UnivariateSpline(valid.index, valid[col_name], s=0, ext=3)
                imputed_values = interp_func(indices)
                met[col_name] = imputed_values
            else:  # mean
                mean_value = met[col_name].mean(skipna=True)
                met[col_name].fillna(mean_value, inplace=True)

    return met


def separate_date(date_str):
    # Ensure the date string is of the correct format

    # Extracting year, month, and day
    year = date_str[:4]
    month = date_str[4:6]
    day = date_str[6:]

    return year, month, day


@retry(stop=stop_after_attempt(2), wait=wait_fixed(0.5), retry=retry_if_exception_type(NETWORK_EXCEPTIONS))
def get_nasa_data(lonlat, start, end):
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


def get_met_nasa_power(lonlat, start=1990, end=2000, fname='get_met_nasa_power.met'):
    df = get_nasa_data(lonlat, start, end)
    tav, AMP = calculate_tav_amp(df)
    create_met_header(fname, lonlat, tav, AMP, site=None)
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


def _is_within_USA_mainland(lonlat):
    lon_min, lon_max = -125.0, -66.9  # Approximate longitudes for the west and east coasts
    lat_min, lat_max = 24.4, 49.4  # Approximate latitudes for the southern and northern borders

    # Check if given coordinates are within the bounding box
    if lon_min <= lonlat[0] <= lon_max and lat_min <= lonlat[1] <= lat_max:
        return True
    else:
        return False


def get_weather(lonlat, start=1990, end=2000, source='daymet', filename='__met_.met'):
    """collects data from various sources
    only nasapower and dayment are currently supported sources,so it will raise an error if mesonnet is suggested
    Note if you not in mainland USA, please don't pass source = 'dayment' as it will raise an error due to geographical scope
    >> example
    >>> from apsimNGpy.manager.weathermanager import get_weather
    >>> from apsimNGpy.core.base_data import load_default_simulations
    We are going to collect data from my hometown Kampala
    >>> kampala_loc = 35.582520, 0.347596
    # Notice it return a path to the downloaded weather file
    >>> met_file = get_weather(kampala_loc, start=1990, end=2020, source='nasa', filename='kampala_new.met')
    >>> print(met_file)
    # next we can pass this weather file to apsim model
    >>> maize_model = load_default_simulations(crop = 'maize')
    >>> maize_model.replace_met_file(weather_file = met_file)

    """

    if source == 'daymet' and _is_within_USA_mainland(lonlat):
        file_name = "daymet_" + filename
        return get_met_from_day_met(lonlat, start=start, end=end, filename=file_name)
    elif source == 'nasa':
        file_name = "nasa_" + filename
        return get_met_nasa_power(lonlat, start, end, fname=file_name)
    else:
        raise ValueError(
            f"Invalid source: {source} according to supplied {lonlat} lon_lat values try 'nasa' instead")


def read_apsim_met(met_path, skip=5, index_drop=0, separator=' '):
    try:
        data = pd.read_csv(met_path, skiprows=skip, delim_whitespace=True)
        return data.drop(0)

    except Exception as e:
        print(repr(e))


def write_edited_met(old: Union[str, Path], daf: pd.DataFrame, filename: str = "edited_met.met") -> str:
    """

    Parameters
    ----------
    old; pathlinke to original met file

    old
    daf: new data in the form of a pandas dataframe
    filename; file name to save defaults to edited_met.met

    Returns
    -------
    new path to the saved file
    """
    existing_lines = []
    with open(old, 'r+') as file:
        for i, line in enumerate(file):
            existing_lines.append(line)
            if 'MJ' in line and 'mm' in line and 'day in line':
                print(line)
                break
    # iterate through the edited data frame met
    headers = daf.columns.to_list()
    for index, row in daf.iterrows():
        current_row = []
        for header in headers:
            current_row.append(str(row[header]))
        current_str = " ".join(current_row) + '\n'
        existing_lines.append(current_str)
    fname = os.path.join(os.path.dirname(old), filename)
    if os.path.exists(fname):
        os.remove(fname)
    with open(fname, "a") as df_2met:
        df_2met.writelines(existing_lines)
    return fname


def merge_columns(df1_main, common_column, df2, fill_column, df2_colummn):
    """
    Parameters:
    df_main (pd.DataFrame): The first DataFrame to be merged and updated.
    common_column (str): The name of the common column used for merging.
    df2 (pd.DataFrame): The second DataFrame to be merged with 'df_main'.
    fill_column (str): The column in 'edit' to be updated with values from 'df2_column'.
    df2_column (str): The column in 'df2' that provides replacement values for 'fill_column'.

    Returns:
    pd.DataFrame: A new DataFrame resulting from the merge and update operations.
    """
    try:
        df = df1_main.merge(df2, on=common_column, how='left')
        dm_copy = copy.deepcopy(df)
        dm_copy[df2_colummn].fillna(dm_copy[fill_column], inplace=True)
        dm_copy[fill_column] = dm_copy[df2_colummn]
        # dm_copy.drop(columns=[df2_colummn], inplace=True)
        dm_copy.reset_index()
        return dm_copy
    except Exception as e:
        print(repr(e))


def validate_met(met):
    import datetime
    if not isinstance(met, pd.DataFrame):
        raise ValueError("object should be of class 'DataFrame'")

    if met.empty:
        raise ValueError("No rows of data present in this object.")

    expected_colnames = ['year', 'day', 'radn', 'maxt', 'mint', 'rain']  # Add more as per your actual data structure
    if len(met.columns) != len(expected_colnames) or not all(met.columns == expected_colnames):
        print("Names in DataFrame:", met.columns)
        logging.warning("Expected column names", expected_colnames)
        warnings.warn("Number of columns in DataFrame does not match expected column names")
    for cols in met.columns:
        if cols == 'year':
            try:
                met = met[met['year'] != '!site:']
                met[cols] = met[cols].astype(int)
            except:
                met[cols] = met[cols].astype('float')
        else:
            try:
                met[cols] = met[cols].astype('float')
            except:
                pass
    if met['year'].isna().any():
        logging.warning(met[met['year'].isna()])
        warnings.warn("Missing values found for year")

    if met['year'].min() < 1900:
        logging.warning(met[met['year'] < 1900])
        warnings.warn(" minimum year is less than 1500")

    if met['year'].max() > 2024:
        logging.warning(met[met['year'] > 2024])
        warnings.warn("year is greater than 2024")

    # Add similar checks for other columns like 'day', 'mint', 'maxt', 'radn', 'rain'
    # Implement any specific checks as in your R function
    # Example for 'day':
    if met['day'].isna().any():
        print(met[met['day'].isna()])
        warnings.warn("Missing values found for day")

    if met['day'].min() < 1:
        print(met[met['day'] < 1])
        warnings.warn(" met starting day is less than 1")

    if met['day'].max() > 366:
        print(met[met['day'] > 366])
        warnings.warn("day is greater than 366")

    # Example for date checks
    if len(met) > 0:
        first_day = datetime.datetime(int(met.iloc[0]['year']), 1, 1) + pd.to_timedelta(met.iloc[0]['day'] - 1,
                                                                                        unit='d')
        last_day = datetime.datetime(int(met.iloc[-1]['year']), 1, 1) + pd.to_timedelta(met.iloc[-1]['day'] - 1,
                                                                                        unit='d')
        expected_dates = pd.date_range(start=first_day, end=last_day, freq='D')
        if len(met) < len(expected_dates):
            warnings.warn(f"{len(expected_dates) - len(met)} date discontinuities found. Consider checking data.")
    check_rain = met[met['rain'] > 95]
    rad_high = met[met['radn'] > 41]
    if not rad_high.empty:
        print(rad_high)
        warnings.warn("radiation is too high")
    if not check_rain.empty:
        warnings.warn('probably rain is too high')
        print(met[met['rain'] > 95])

    def check_missing(col):
        if met[col].isna().any():
            warnings.warn(f"{col}: has missing values_****___")
            print(met[col].isna())

    check_radn = met[met['radn'] < 0]
    if not check_radn.empty:
        logging.warning('probably radiation is too low or missing')
        print(met[met['radn'] < 0])

    # Temperature checks could be similar, comparing 'maxt' and 'mint'
    # Radiation, rain, and other checks as per the original function's logic
    for cols in met.columns:
        check_missing(cols)
    min_t = met[met['mint'] < -60]
    if not min_t.empty:
        warnings.warn("min temp is too low")
        print(min_t)

    min_t_high = met[met['mint'] > 40]
    if not min_t_high.empty:
        warnings.warn('Minimum temp is too high')
        print(min_t_high)
    maxt = met[met['maxt'] < -60]
    if not maxt.empty:
        warnings.warn("max temp is too low")
        print(maxt)
    maxt_high = met[met['maxt'] > 60]
    if not maxt_high.empty:
        print("max temp is too high")
        print(maxt_high)
    if len(daterange(met.year.min(), met.year.max())) != len(met):
        warnings.warn('daterange is not standard')
    else:
        print('daterange matched expected')


from datetime import datetime, timedelta


def day_of_year_to_date(year, day_of_year):
    """
    Convert day of the year to a date.

    Parameters:
    -----------
    year : int
        The year to which the day of the year belongs.
    day_of_year : int
        The day of the year (1 to 365 or 366).

    Returns:
    --------
    datetime.date
        The corresponding date.
    """
    return datetime(year, 1, 1) + timedelta(days=day_of_year - 1)


def impute_missing_leaps(dmet, fill=0):
    dmet['year'] = dmet['year'].astype(int)
    dmet['day'] = dmet['day'].astype(int)
    datee = [day_of_year_to_date(_year, day) for _year, day in zip(dmet.year, dmet.day)]

    # Create a copy and set the date as the index
    dmett = dmet.copy()
    dmett['datee'] = pd.to_datetime(datee)
    dmett.set_index('datee', inplace=True)
    indexDate = pd.date_range(start=dmett.index.min(), end=dmett.index.max(), freq='D')
    check = daterange(dmett.year.min(), dmett.year.max())
    # Reindex the DataFrame to include all dates in the range
    df_daily = dmett.reindex(check)
    df_fill = df_daily.fillna(fill).copy(deep=True)
    df_fill['day'] = df_fill.index.day
    df_fill['year'] = df_fill.index.year
    # Optionally, fill missing values (for example, with the mean of the column)

    return df_fill


if __name__ == '__main__':
    # imputed_df = impute_data(df, method="approx", verbose=True, copy=True)
    kampala = 35.582520, 0.347596
    df = get_nasa_data(kampala, 2000, 2020)
    # imputed_df = impute_data(df, method="mean", verbose=True, copy=True)
    hf = get_met_nasa_power(kampala, end=2020, fname='kampala_new.met')
    wf = get_weather(kampala, start=1990, end=2020, source='nasa', filename='kampala_new.met')
    import time

    a = time.perf_counter()
    get_met_from_day_met(lonlat=(-93.04, 42.01247), start=2000, end=2020, filename='daymet.met')
    b = time.perf_counter()
    print(b - a)
