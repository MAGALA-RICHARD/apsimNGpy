import os
import datetime
from pathlib import Path
import random
import json
import statistics
import requests
import string
from io import StringIO
import io
import logging

import pandas as pd
import numpy as np
from scipy import interpolate
import copy
import warnings

from ..utililies.utils import generate_unique_name


def get_iem_by_station(dates, station, path, mettag):
    """
      Dates is a tuple/list of strings with date ranges
      an example date string should look like this: dates = ["01-01-2012","12-31-2012"]
      if station is given data will be downloaded directly from the station the default is false.
      mettag: your preferred tag to save on file
      """
    # access the elements in the metdate class above
    wdates = MetDate(dates)
    stationx = station[:2]
    state_clim = stationx + "CLIMATE"
    iastate_weather_url = "https://mesonet.agron.iastate.edu/cgi-bin/request/coop.py?network="
    query_str = f"{state_clim}&stations={station}&year1={wdates.year_start}&month1={wdates.start_month}" \
                f"&day1={wdates.start_day}&year2={wdates.year_end}&month2={wdates.end_month}&day2={wdates.end_day}" \
                f"&vars%5B%5D=apsim&what=view&delim=comma&gis=no"
    url = f"{iastate_weather_url}{query_str}"
    rep = requests.get(url)
    if rep.ok:
        met_name = station + mettag + ".met"
        os.chdir(path)
        if not os.path.exists('weatherdata'):
            os.mkdir('weatherdata')
        pt = os.path.join('weatherdata', met_name)

        with open(pt, 'wb') as met_file:
            # dont forget to include the file extension name
            met_file.write(rep.content)
            rep.close()
            met_file.close()


class MetDate:
    """
    This class organises the data for IEM weather download
    """

    def __init__(self, dates):
        self.start_date = dates[0]
        self.end_date = dates[1]
        self.start_month = dates[0][:2]
        self.end_month = dates[1][:2]
        self.year_start = dates[0].split("-")[2]
        self.year_end = dates[1].split("-")[2]
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


def get_abbreviation(x):
    ab = new_dict[x]
    return ab


# function to define the date ranges
def date_range(start, end):
    """
    start: the starting year to download the weather data
    -----------------
    end: the year under which download should stop
    """
    start_dates = '01-01'
    end_dates = '12-31'
    end = str(end) + "-" + end_dates
    start = str(start) + "-" + start_dates
    d_range = pd.date_range(start, end)
    return d_range


# check if a year is aleap year
def is_leap_year(year):
    if (year % 400 == 0) and (year % 100 == 0) or (year % 4 == 0) and (year % 100 != 0):
        return True
    else:
        return False


def get_nasa_rad(lonlat, start, end):
    # download radiation data for replacement
    lon = lonlat[0]
    lat = lonlat[1]
    pars = "ALLSKY_SFC_SW_DWN"
    nasa_rad_url = f'https://power.larc.nasa.gov/api/temporal/daily/point?start={start}' \
         f'0101&end={end}1231&latitude={lat}&longitude={lon}&community=ag&parameters={pars}' \
         f'&format=json&user=richard&header=true&time-standard=lst'
    data = requests.get(nasa_rad_url)
    dt = json.loads(data.content)
    df = pd.DataFrame(dt["properties"]['parameter'])
    if len(df) == len(date_range(start, end)):
        return df


def daymet_by_location(lonlat: str, start_year: int, end_year: int, clean_up: bool=True, file_name=None):
    """
    Collect weather from daymet solar radiation is replaced with that of nasapower
   ------------
   parameters
   ---------------
   start_year: Starting year
   end_year: Ending year
   lonlat: A tuple of gps coordinates of the location
   clean_up:  Deletes the excel file generated during the file write up default to true
   file_name: The name of the file to which the data will be written.
   ------------
   returns complete path to the new met file but also write the met file to the disk in the working directory
   """
    if start_year < 1980:
        raise ValueError("The database contains data only from 1980 onwards")

    current_year = datetime.datetime.now().year
    if end_year + 1 >= current_year:
        raise ValueError(f"The {current_year} weather data may not be stable, use at least 1 year before")

    datecheck = date_range(start_year, end_year)

    base_url = 'https://daymet.ornl.gov/single-pixel/api/data?'
    met_vars = ",".join(['dayl', 'prcp', 'srad', 'tmax', 'tmin', 'vp', 'swe'])
    weather_years = [str(year) for year in range(start_year, end_year + 1)]
    years_in_range = ",".join(weather_years)
        # join the years as a string

    query_str = f"lat={str(lonlat[1])}&lon={str(lonlat[0])}&measuredParams={met_vars}&years={years_in_range}"
    # join the string url together
    url = f"{base_url}{query_str}"
    conn = requests.get(url, timeout=60)

    if not conn.ok:
        # TODO refactor this function to handle the request in a separate function
        raise ValueError("failed to connect to server")
    elif conn.ok:
        out_filename = conn.headers["Content-Disposition"].split("=")[-1]
        text_str = conn.content
        with open(out_filename, 'wb') as out_file:
            out_file.write(text_str)
            # read the downloaded data to a data frame
            dmett = pd.read_csv(out_filename, delimiter=',', skiprows=7)
            vp = dmett['vp (Pa)'] * 0.01
            # calculate radiation
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
            # calculate mean annual amplitude in mean monthly temperature (TAV)
            ab = [a for a in weather_years]
            # split the data frame
            ab = [x for _, x in df.groupby(df['year'])]
            df_bag = []
            # constants to evaluate the leap years
            for i in ab:
                if is_leap_year(i.year):
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
            rad = get_nasa_rad(lonlat, start_year, end_year)
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
                if not file_name:
                    shortenfn = generate_unique_name("Daymet") + '.met'
                else:
                    shortenfn = file_name
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

                if clean_up:
                    if os.path.isfile(os.path.join(os.getcwd(), out_filename)):
                        os.remove(os.path.join(os.getcwd(), out_filename))
                return fname  # fname


def daymet_bylocation_nocsv(lonlat, start, end, cleanup=True, filename='daymet'):
    """
    collect weather from daymet. doesnt store data to csv
     solar radiation is replaced with that of nasapower
    ------------
    parameters
    ---------------
    start: Starting year

    end: Ending year

    lonlat: A tuple of xy cordnates

    Cleanup:  A bolean True or False default is true: deletes the excel file generated during the file write up

    ------------
    returns complete path to the new met file but also write the met file to the disk in the working directory
    """
    # import pdb
    # pdb.set_trace()

    datecheck = date_range(start, end)
    if start < 1980 or end > 2021:
        print(
            "requested year preceeds valid data range! \n end years should not exceed 2021 and start year should not "
            "be less than 1980")
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
            dmett = pd.read_csv(text_stream, delimiter=',', skiprows=7)
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
                    year = round(x[0], 0)
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
            rad = get_nasa_rad(lonlat, start, end)
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


class EditMet:
    """
    This class edits the weather files
    """

    def __init__(self, weather, skip=5, index_drop=0, separator=' '):
        self.skip = skip
        self.index_drop = index_drop
        self.seperator = separator
        self.weather = weather

    def _edit_apsim_met(self):
        """
        converts the weather file into a pandas dataframe by removing specified rows.
        It is easier to edit  a pandas data frame than a text file

        Returns:
        - pandas.DataFrame: A DataFrame containing the modified APSIM weather data.

        Example:
        """
        try:
            with open(self.weather, "r+") as f:
                string = f.read()
                data = pd.read_table(StringIO(string), sep=f"{self.seperator}", skiprows=self.skip)
                row_index = self.index_drop
                df = data.drop(row_index).reset_index()
                return df
        except Exception as e:
            print(repr(e))

    def write_edited_met(self, old, daf, filename="edited_met.met"):
        """
        Write an edited APSIM weather file using an existing file as a template.

        This function takes an existing APSIM weather file ('old'), replaces specific data rows with data from a DataFrame ('daf'),
        and writes the modified data to a new weather file ('filename').

        Args:
        - old (str): The path to the existing APSIM weather file used as a template.
        - daf (pandas.DataFrame): A DataFrame containing the edited weather data to be inserted.
        - filename (str, optional): The name of the new weather file to be created. Default is 'edited_met.met'.

        Returns:
        - str: The path to the newly created APSIM weather file.

        Example:
        ```python
        from your_module import write_edited_met

        # Specify the paths to the existing weather file and the edited data DataFrame
        existing_weather_file = "original_met.met"
        edited_data = pd.DataFrame(...)  # Replace with your edited data

        # Call the write_edited_met function to create a new weather file with edited data
        new_weather_file = write_edited_met(existing_weather_file, edited_data)

        # Use the new_weather_file path for further purposes
        ```

        Notes:
        - This function reads the existing APSIM weather file, identifies the location to insert the edited data,
          and then creates a new weather file containing the combined data.
        - The edited data is expected to be in the 'daf' DataFrame with specific columns ('year', 'day', 'radn', 'maxt', 'mint', 'rain', 'vp', 'swe').
        - The 'filename' parameter specifies the name of the new weather file to be created.
        - The function returns the path to the newly created weather file.

        """
        if not filename.endswith('.met'):
            raise NameError("file name should have  .met extension")
        existing_lines = []
        with open(old, 'r+') as file:
            for i, line in enumerate(file):
                existing_lines.append(line)
                if 'MJ' in line and 'mm' in line and 'day in line':
                    print(line)
                    break

        # Iterate through the edited DataFrame 'daf' and construct new data rows
        headers = ['year', 'day', 'radn', 'maxt', 'mint', 'rain', 'vp', 'swe']
        for index, row in daf.iterrows():
            current_row = []
            for header in headers:
                current_row.append(str(row[header]))
            current_str = " ".join(current_row) + '\n'
            existing_lines.append(current_str)

        fname = os.path.join(os.path.dirname(old), filename)

        # Remove the file if it already exists
        if os.path.exists(fname):
            os.remove(fname)

        # Write the edited data to the new weather file
        with open(fname, "a") as df_2met:
            df_2met.writelines(existing_lines)

        return fname

    def _read_line_from_file(self, line_number):
        with open(self.weather, 'r') as file:
            lines = file.readlines()
            if 0 <= line_number < len(lines):
                return lines[line_number]
            else:
                raise IndexError(f"Line number {line_number} is out of range.")

    def met_replace_var(self, parameter, values):
        """
        in case we want to change some columns or rows in the APSIM met file
        this function replace specific data in the APSIM weather file with new values.

        This method allows for the replacement of specific columns or rows in the APSIM weather file by providing a
        'parameter' (column name) and a list of 'values' to replace the existing data.

        Args:
        - parameter (str): The name of the column (parameter) to be replaced.
        - values (list, array or pandas series):  values to replace the existing data in the specified column.

        Returns:
        - str: The path to the newly created APSIM weather file with the replaced data.

        """
        df = self._edit_apsim_met()
        if len(df[parameter]) != len(values):
            raise ValueError("number of rows must be equal")
        if parameter not in df.columns:
            raise ValueError("column name not found")
        df['parameter'] = list(values)
        fname = os.path.join(os.path.dirname(self.weather), "edited_" + os.path.basename(self.weather))
        return self.write_edited_met(old=self.weather, daf=df, filename=fname)

    def check_met(self):
        df = self._edit_apsim_met()
        rain = np.array(df['rain'])
        ch = np.any(rain <= 0)
        if True in ch:
            print(f'the met file has some negative values {ch}')


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
        raise ValueError(
            f"Invalid source: {source} according to supplied {lonlat} lon_lat values try nasapower instead")

    def met_replace_var(self, parameter, values):
        """
        in case we want to change some columns or rows in the APSIM met file
        this function replace specific data in the APSIM weather file with new values.

        This method allows for the replacement of specific columns or rows in the APSIM weather file by providing a
        'parameter' (column name) and a list of 'values' to replace the existing data.

        Args:
        - parameter (str): The name of the column (parameter) to be replaced.
        - values (list, array or pandas series):  values to replace the existing data in the specified column.

        Returns:
        - str: The path to the newly created APSIM weather file with the replaced data.

        """
        df = self._edit_apsim_met()
        if len(df[parameter]) != len(values):
            raise ValueError("number of rows must be equal")
        if parameter not in df.columns:
            raise ValueError("column name not found")
        df['parameter'] = list(values)
        fname = os.path.join(os.path.dirname(self.weather), "edited_" + os.path.basename(self.weather))
        return self.write_edited_met(old=self.weather, daf=df, filename=fname)


def read_apsim_met(met_path, skip=5, index_drop=0, separator=' '):
    try:
        with open(met_path, "r+") as f:
            string = f.read()
            data = pd.read_csv(StringIO(string), sep=f"{separator}", skiprows=skip)
            row_index = index_drop
            df = data.drop(row_index).reset_index()
            return df
    except Exception as e:
        print(repr(e))


def write_edited_met(old: [str, Path], daf: pd.DataFrame, filename: str = "edited_met.met") -> str:
    """

    Parameters
    ----------
    old; pathlinke to original met file

    daf: new data inform of a pandas dataframe
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
    # headers = ['year', 'day', 'radn', 'maxt', 'mint', 'rain', 'vp', 'swe']
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
    if len(date_range(met.year.min(), met.year.max())) != len(met):
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
    check = date_range(dmett.year.min(), dmett.year.max())
    # Reindex the DataFrame to include all dates in the range
    df_daily = dmett.reindex(check)
    df_fill = df_daily.fillna(fill).copy(deep=True)
    df_fill['day'] = df_fill.index.day
    df_fill['year'] = df_fill.index.year
    # Optionally, fill missing values (for example, with the mean of the column)

    return df_fill


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


if __name__ == '__main__':
    # imputed_df = impute_data(df, method="approx", verbose=True, copy=True)
    kampala = 35.582520, 0.347596
    df = getnasa_df(kampala, 2000, 2020)
    imputed_df = impute_data(df, method="mean", verbose=True, copy=True)
    hf = met_nasapower(kampala, end=2020, fname='kampala_new.met')
    wf = get_weather(kampala, start=1990, end=2020, source='daymet', filename='kampala_new.met')
