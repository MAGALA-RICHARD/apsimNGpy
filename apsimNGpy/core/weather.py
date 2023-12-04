import os
from os.path import join as opj
from datetime import datetime
import datetime
import requests
import copy
import random
import json
import pandas as pd
import statistics
import numpy as np
import string
from io import StringIO
import io


def generate_unique_name(base_name, length=6):
    # TODO this function is duplicated everywhere.
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
    wdates = _MetDate(dates)
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


class _MetDate:
    """
    This class organises the data for IEM weather download
    """
    def __init__(self, dates):
        self.startdate = dates[0]
        self.lastdate = dates[1]
        self.startmonth = dates[0][:2]
        self.endmonth = dates[1][:2]
        self.year_start = dates[0].split("-")[2]
        self.year_end = dates[1].split("-")[2]
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
    return new_dict[x]



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

    datecheck = daterange(start, end)
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
        return self.write_edited_met(old = self.weather, daf = df, filename=fname)

    def check_met(self):
        df = self._edit_apsim_met()
        rain = np.array(df['rain'])
        ch = np.any(rain <= 0)
        if True in ch:
            print(f'the met file has some negative values {ch}')


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


def write_edited_met(old, daf, filename="edited_met.met"):
    existing_lines = []
    with open(old, 'r+') as file:
        for i, line in enumerate(file):
            existing_lines.append(line)
            if 'MJ' in line and 'mm' in line and 'day in line':
                print(line)
                break
    # iterate through the edited data frame met
    headers = ['year', 'day', 'radn', 'maxt', 'mint', 'rain', 'vp', 'swe']
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
P
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
