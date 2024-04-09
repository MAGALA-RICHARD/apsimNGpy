import os
from os.path import join as opj
from datetime import datetime
import datetime
import urllib
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


def generate_unique_name(base_name, length=6):
    # TODO this function has 4 duplicates
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=length))
    unique_name = base_name + '_' + random_suffix
    return unique_name


# from US_states_abbreviation import getabreviation
def get_iem_bystation(dates, station, path, mettag):
    '''
      Dates is a tupple/list of strings with date ranges
      
      an example date string should look like this: dates = ["01-01-2012","12-31-2012"]
      
      if station is given data will be downloaded directly from the station the default is false.
      
      mettag: your prefered tag to save on filee
      '''
    # access the elements in the metdate class above
    wdates = metdate(dates)
    stationx = station[:2]
    state_clim = stationx + "CLIMATE"
    str0 = "http://mesonet.agron.iastate.edu/cgi-bin/request/coop.py?network="
    str1 = str0 + state_clim + "&stations=" + station
    str2 = str1 + "&year1=" + wdates.year_start + "&month1=" + wdates.startmonth + "&day1=" + wdates.startday + "&year2=" + wdates.year_end + "&month2=" + wdates.endmonth + "&day2=" + wdates.endday
    str3 = (str2 + "&vars%5B%5D=apsim&what=view&delim=comma&gis=no")
    url = str3
    rep = requests.get(url)
    if rep.ok:
        metname = station + mettag + ".met"
        os.chdir(path)
        if not os.path.exists('weatherdata'):
            os.mkdir('weatherdata')
        pt = os.path.join('weatherdata', metname)

        with open(pt, 'wb') as metfile1:
            # dont forget to include the file extension name
            metfile1.write(rep.content)
            rep.close()
            metfile1.close()
            print(rep.content)
    else:
        print("Failed to download the data web request returned code: ", rep)


class metdate:
    def __init__(self, dates):
        self.startdate = dates[0]
        self.lastdate = dates[1]
        self.startmonth = dates[0][:2]
        self.endmonth = dates[1][:2]
        self.year_start = dates[0].split("-")[2]
        self.year_end = dates[1].split("-")[2]
        import datetime
        self.startday = datetime.datetime.strptime(dates[0], '%m-%d-%Y').strftime('%j')
        self.endday = datetime.datetime.strptime(dates[1], '%m-%d-%Y').strftime('%j')


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


def daymet_bylocation(lonlat, start, end, cleanup=True, filename=None):
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


def daymet_bylocation_nocsv(lonlat, start, end, cleanup=True, filename=None):
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
            outFname = "w" + filename + conn.headers["Content-Disposition"].split("=")[-1]
            text_str = conn.content
            conn.close()
            #  read the downloaded data to a data frame
            # Create an in-memory binary stream
            text_stream = io.BytesIO(text_str)
            # Read the data into a DataFrame
            dmett = pd.read_csv(text_stream, delimiter=',', skiprows=6)
            # dmett = pd.read_csv(outFname, delimiter=',', skiprows=7)
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


# dowload weather data from nasapower
def getnasa(lonlat, start, end):
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


import pandas as pd
import numpy as np
from scipy import interpolate
import copy


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
    # Handle deep copy option
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


def getnasa_df(lonlat, start, end):
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
    if source == 'daymet' and _is_within_USA_mainland(lonlat):
        file_name = "daymet_" + filename
        return daymet_bylocation_nocsv(lonlat, start=start, end=end, filename=file_name)
    elif source == 'nasapower':
        file_name = "nasapower_" + filename
        return met_nasapower(lonlat, start, end, fname=file_name)
    else:
        raise ValueError(f"Invalid source: {source} according to supplied {lonlat} lon_lat values try nasapower instead")


if __name__ == '__main__':
    # imputed_df = impute_data(df, method="approx", verbose=True, copy=True)
    kampala = 35.582520, 0.347596
    df = getnasa_df(kampala, 2000, 2020)
    imputed_df = impute_data(df, method="mean", verbose=True, copy=True)
    hf = met_nasapower(kampala, end=2020, fname='kampala_new.met')
    wf = get_weather(kampala, start=1990, end=2020, source='daymet', filename='kampala_new.met')
