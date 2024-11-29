# This API documentation is generated automatically. The official documentation has not been released by apsimNGpy team

# apsimNGpy API documentation

# Module: base_data

## base_data._get_maize_NF_experiment

```python
_get_maize_NF_experiment(file_path: unknown)

copies the apsimx data from 'EXPERIMENT.apsimx' file
returns the path
```

## base_data.__init__

```python
__init__(self: unknown, path: unknown)

LoadExampleFiles constructor.

Args:
path (str): The path where default example files will be copied to.

Raises:
NameError: If the specified path does not exist.
```

## base_data.get_maize_with_cover_crop

```python
get_maize_with_cover_crop(self: unknown)

Get the example data for maize with a cover crop.

Returns:
path (str): The example data for maize with a cover crop.
        
```

## base_data.get_experiment_nitrogen_residue

```python
get_experiment_nitrogen_residue(self: unknown)

Get the example data for an experiment involving nitrogen residue.

Returns:
path (str): The example data for the nitrogen residue experiment.
```

## base_data.get_get_experiment_nitrogen_residue_NT

```python
get_get_experiment_nitrogen_residue_NT(self: unknown)

Get the example data for an experiment involving nitrogen residue with no-till.

Returns:
path (str): The example data for the nitrogen residue experiment with no-till.
```

## base_data.get_swim

```python
get_swim(self: unknown)

Get the example data for the SWIM model.

Returns:
path (str): The example data for the SWIM model.
```

## base_data.get_maize

```python
get_maize(self: unknown)

Get the example data for the maize model.

Returns:
path (str): The example data for the maize model.
```

## base_data.get_maize_no_till

```python
get_maize_no_till(self: unknown)

Get the example data for the maize model with no-till.

Returns:
path (str): The example data for the maize model with no-till.
```

## base_data.get_maize_model

```python
get_maize_model(self: unknown)

Get a SoilModel instance for the maize model.

Returns: SoilModel: An instance of the SoilModel class for the maize model. Great for optimisation,
where you wat a model always in memory to reducing laoding overload
```

## base_data.get_maize_model_no_till

```python
get_maize_model_no_till(self: unknown)

Get a SoilModel instance for the maize model with no-till.

Returns: SoilModel: An instance of the SoilModel class for the maize model with no-till. Great for
optimisation, where you wat a model always in memory to reducing laoding overload
```

## base_data.get_example

```python
get_example(self: unknown, crop: unknown)

Get an APSIM example file path for a specific crop model.

This function copies the APSIM example file for the specified crop model to the target path,
creates a SoilModel instance from the copied file, replaces its weather file with the
corresponding weather file, and returns the SoilModel instance.

Args:
crop (str): The name of the crop model for which to retrieve the APSIM example.

Returns: SoilModel: An instance of the SoilModel class representing the APSIM example for the specified crop
model. the path of this model will be your current working directory

Raises:
OSError: If there are issues with copying or replacing files.
```

## base_data.get_all

```python
get_all(self: unknown)

This return all files from APSIM default examples in the example folder. But for what?
```

# Module: apsim

## apsim.Modul: Module

```python
Interface to APSIM simulation models using Python.NET
author: Richard Magala
email: magalarich20@gmail.com
```

## apsim._replace_initial_chemical_values

```python
_replace_initial_chemical_values(self: unknown, name: unknown, values: unknown, simulations: unknown)

_summary_

Args:
    name (str): of the solutes e.g  NH4
    values (array): _values with equal lengths as the existing other variable
    simulations (str): simulation name in the root folder
```

## apsim.get_initial_no3

```python
get_initial_no3(self: unknown, simulation: unknown)

Get soil initial NO3 content
```

## apsim.get_unique_soil_series

```python
get_unique_soil_series(self: unknown)

this function collects the unique soil types

Args:
    lonlat (_tuple_): longitude and latitude of the target location
```

## apsim.relace_initial_carbon

```python
relace_initial_carbon(self: unknown, values: unknown, simulation_names: unknown)

Replaces initial carbon content of the organic module

Args:
    values (_list_): liss of initial vlaues with length as the soil profile in the simulation file_
    simulation_names (_str_): Name of the simulation in the APSIM  file
```

## apsim._change_met_file

```python
_change_met_file(self: unknown, lonlatmet: unknown, simulation_names: unknown)

_similar to class weather management but just in case we want to change the weather within the subclass
# uses exisitng start and end years to download the weather data
```

## apsim.run_edited_file

```python
run_edited_file(self: unknown, simulations: unknown, clean: unknown, multithread: unknown)

Run simulations in this subclass if we want to clean the database, we need to
 spawn the path with one process to avoid os access permission eros


Parameters
----------
simulations, optional
    List of simulation names to run, if `None` runs all simulations, by default `None`.
clean, optional
    If `True` remove existing database for the file before running, by default `True`
multithread, optional
    If `True` APSIM uses multiple threads, by default `True`
```

## apsim.spin_up

```python
spin_up(self: unknown, report_name: str, start: unknown, end: unknown, spin_var: unknown)

Perform a spin-up operation on the APSIM model.

This method is used to simulate a spin-up operation in an APSIM model. During a spin-up, various soil properties or
variables may be adjusted based on the simulation results.

Parameters:
----------
report_name : str, optional (default: 'Report')
    The name of the APSIM report to be used for simulation results.
start : str, optional
    The start date for the simulation (e.g., '01-01-2023'). If provided, it will change the simulation start date.
end : str, optional
    The end date for the simulation (e.g., '3-12-2023'). If provided, it will change the simulation end date.
spin_var : str, optional (default: 'Carbon'). the difference between the start and end date will determine the spin-up period
    The variable representing the type of spin-up operation. Supported values are 'Carbon' or 'DUL'.

Returns:
-------
self : ApsimModel
    The modified ApsimModel object after the spin-up operation.
```

# Module: core

## core.Modul: Module

```python
Interface to APSIM simulation models using Python.NET
author: Richard Magala
email: magalarich20@gmail.com
```

## core.Class: APSIMNG

```python
Modify and run Apsim next generation simulation models.
```

## core.__init__

```python
__init__(self: unknown, model: Union[str, Simulations], copy: unknown, out_path: unknown, read_from_string: unknown)

Parameters
----------

model
    Path to .apsimx file
copy, optional
    If `True` a copy of original simulation will be created on init, by default True.
out_path, optional
    Path of modified simulation, if `None` will be set automatically.
read_from_string (boolean) if True file will be uploaded to memory through json module most preffered, otherwise we can read from file
```

## core.save_edited_file

```python
save_edited_file(self: unknown, outpath: unknown)

Save the model

Parameters
----------
out_path, optional
    Path of output .apsimx file, by default `None`
```

## core.run

```python
run(self: unknown, simulations: unknown, clean: unknown, multithread: unknown)

Run apsim model in the simulations

Parameters
----------
simulations (__str_), optional
    List of simulation names to run, if `None` runs all simulations, by default `None`.
clean (_-boolean_), optional
    If `True` remove existing database for the file before running, deafults to False`
multithread, optional
    If `True` APSIM uses multiple threads, by default `True`
```

## core.clone_simulation

```python
clone_simulation(self: unknown, target: unknown, simulation: unknown)

Clone a simulation and add it to Model

Parameters
----------
target
    target simulation name
simulation, optional
    Simulation name to be cloned, of None clone the first simulation in model
```

## core.remove_simulation

```python
remove_simulation(self: unknown, simulation: unknown)

Remove a simulation from the model

Parameters
----------
simulation
    The name of the simulation to remove
```

## core.extract_simulation_name

```python
extract_simulation_name(self: unknown)

print or extract a simulation name from the model

Parameters
----------
simulation
    The name of the simulation to remove
```

## core.clone_zone

```python
clone_zone(self: unknown, target: unknown, zone: unknown, simulation: unknown)

Clone a zone and add it to Model

Parameters
----------
target
    target simulation name
zone
    Name of the zone to clone
simulation, optional
    Simulation name to be cloned, of None clone the first simulation in model
```

## core.find_zones

```python
find_zones(self: unknown, simulation: unknown)

Find zones from a simulation

Parameters
----------
simulation
    simulation name

Returns
-------
    list of zones as APSIM Models.Core.Zone objects
```

## core.extract_report_names

```python
extract_report_names(self: unknown)

returns all data frame the available report tables
```

## core._read_simulation

```python
_read_simulation(self: unknown, report_name: unknown)

returns all data frame the available report tables
```

## core._read_external_simulation

```python
_read_external_simulation(datastore: unknown, report_name: unknown)

returns all data frame the available report tables
```

## core._cultivar_params

```python
_cultivar_params(self: unknown, cultivar: unknown)

returns all params in a cultivar
```

## core.get_crop_replacement

```python
get_crop_replacement(self: unknown, Crop: unknown)

:param Crop: crop to get the replacement
:return: System.Collections.Generic.IEnumerable APSIM plant object
```

## core.edit_cultivar

```python
edit_cultivar(self: unknown, CultvarName: unknown, commands: tuple, values: tuple)

:param CultvarName: name of the cultvar e.g laila

:param command: python tuple of strings.
          example: ('[Grain].MaximumGrainsPerCob.FixedValue', "[Phenology].GrainFilling.Target.FixedValue ")
values: corresponding values for each command e.g ( 721, 760)
:return:
```

## core.collect_specificreport

```python
collect_specificreport(results: unknown, report_names: unknown, var_names: unknown, stat: unknown)

_summary_

Args:
    results (_dict_): diction of apsim results table generated by run method
    report_names (_str_): _report name_
    var_names (_list_): _description_
    Statistic (_list_): how to summary the data supported versions are mean, median, last ,start standard deviation
    statistics and var names should be the order ['yield', 'carbon'] and ['mean', 'diff'], where mean for yield and diff for carbon, respectively
```

## core.update_cultivar

```python
update_cultivar(self: unknown, parameters: unknown, simulations: unknown, clear: unknown)

Update cultivar parameters

Parameters
----------
parameters
    Parameter = value dictionary of cultivar paramaters to update.
simulations, optional
    List of simulation names to update, if `None` update all simulations.
clear, optional
    If `True` remove all existing parameters, by default `False`.
```

## core.examine_management_info

```python
examine_management_info(self: unknown, simulations: unknown)

this will show the current management scripts in the simulation root

Parameters
----------
simulations, optional
    List of simulation names to update, if `None` show all simulations. if you are not sure,

    use the property decorator 'extract_simulation_name
```

## core.change_som

```python
change_som(self: unknown, simulations: unknown, inrm: int, icnr: int)

     Change Surface Organic Matter (SOM) properties in specified simulations.

Parameters:
    simulations (str ort list): List of simulation names to target (default: None).
    inrm (int): New value for Initial Residue Mass (default: 1250).
    icnr (int): New value for Initial Carbon to Nitrogen Ratio (default: 27).

Returns:
    self: The current instance of the class.
    
```

## core.update_management_decissions

```python
update_management_decissions(self: unknown, management: unknown, simulations: unknown, reload: unknown)

Update management, handles multiple managers in a loop

Parameters
----------
management: a list of dictionaries of management paramaters or a dictionary with keyvarlue pairs of parameters and associated values, respectivelyto update. examine_management_info` to see current values.
make a dictionary with 'Name' as the for the of  management script
simulations, optional
    List of simulation names to update, if `None` update all simulations not recommended.
reload, optional
    _description_ defaults to True
```

## core.update_mgt

```python
update_mgt(self: unknown, management: unknown, simulations: unknown)

Update management, handles one manager at a time

Parameters
----------
management

    Parameter = value dictionary of management paramaters to update. examine_management_info` to see current values.
    make a dictionary with 'Name' as the for the of  management script
simulations, optional
    List of simulation names to update, if `None` update all simulations not recommended.
```

## core.extract_user_input

```python
extract_user_input(self: unknown, manager_name: unknown)

Get user_input of a given model manager script
returns;  a dictionary
```

## core.change_simulation_dates

```python
change_simulation_dates(self: unknown, start_date: unknown, end_date: unknown, simulations: unknown)

Set simulation dates. this is important to run this method before run the weather replacement method as
the date needs to be alligned into weather

Parameters
-----------------------------------
start_date, optional
    Start date as string, by default `None`
end_date, optional
    End date as string, by default `None`
simulations, optional
    List of simulation names to update, if `None` update all simulations
```

## core.extract_dates

```python
extract_dates(self: unknown, simulations: unknown)

Get simulation dates in the model

Parameters
----------
simulations, optional
    List of simulation names to get, if `None` get all simulations
Returns
-------
    Dictionary of simulation names with dates
```

## core.extract_start_end_years

```python
extract_start_end_years(self: unknown, simulations: unknown)

Get simulation dates

Parameters
----------
simulations, optional
    List of simulation names to get, if `None` get all simulations
Returns
-------
    Dictionary of simulation names with dates
```

## core.show_met_file_in_simulation

```python
show_met_file_in_simulation(self: unknown)

Show weather file for all simulations
```

## core.change_report

```python
change_report(self: unknown, command: str, report_name: unknown, simulations: unknown, set_DayAfterLastOutput: unknown)

    Set APSIM report variables for specified simulations.

This function allows you to set the variable names for an APSIM report
in one or more simulations.

Parameters
----------
command : str
    The new report string that contains variable names.
report_name : str
    The name of the APSIM report to update defaults to Report.
simulations : list of str, optional
    A list of simulation names to update. If `None`, the function will
    update the report for all simulations.

Returns
-------
None
```

## core.get_report

```python
get_report(self: unknown, simulation: unknown)

Get current report string

Parameters
----------
simulation, optional
    Simulation name, if `None` use the first simulation.
Returns
-------
    List of report lines.
```

## core.extract_soil_physical

```python
extract_soil_physical(self: unknown, simulation: unknown)

Find physical soil

Parameters
----------
simulation, optional
    Simulation name, if `None` use the first simulation.
Returns
-------
    APSIM Models.Soils.Physical object
```

## core.extract_any_soil_physical

```python
extract_any_soil_physical(self: unknown, parameter: unknown, simulation: unknown)

extracts soil physical parameters in the simulation

Args:
    parameter (_string_): string e.g DUL, SAT
    simulation (string, optional): Targeted simulation name. Defaults to None.
---------------------------------------------------------------------------
returns an array of the parameter values
```

## core.replace_any_soil_physical

```python
replace_any_soil_physical(self: unknown, parameter: str, param_values: unknown, simulation: str)

relaces specified soil physical parameters in the simulation

______________________________________________________
Args:
    parameter (_string_, required): string e.g DUL, SAT. open APSIMX file in the GUI and examne the phyicals node for clues on the parameter names
    simulation (string, optional): Targeted simulation name. Defaults to None.
    param_values (array, required): arrays or list of values for the specified parameter to replace
```

## core.extract_soil_organic

```python
extract_soil_organic(self: unknown, simulation: unknown)

Find physical soil

Parameters
----------
simulation, optional
    Simulation name, if `None` use the first simulation.
Returns
-------
    APSIM Models.Soils.Physical object
```

## core.extract_any_solute

```python
extract_any_solute(self: unknown, parameter: str, simulation: unknown)

Parameters
____________________________________
parameter: parameter name e.g NO3
simulation, optional
    Simulation name, if `None` use the first simulation.
returns
___________________
the solute array or list
```

## core.replace_any_solute

```python
replace_any_solute(self: unknown, parameter: str, values: list, simulation: unknown)

# replaces with new solute

Parameters
____________________________________
parameter: paramter name e.g NO3
values: new values as a list to replace the old ones
simulation, optional
    Simulation name, if `None` use the first simulation.
```

## core.extract_any_soil_organic

```python
extract_any_soil_organic(self: unknown, parameter: unknown, simulation: unknown)

extracts any specified soil  parameters in the simulation

Args:
    parameter (_string_, required): string e.g Carbon, FBiom. open APSIMX file in the GUI and examne the phyicals node for clues on the parameter names
    simulation (string, optional): Targeted simulation name. Defaults to None.
    param_values (array, required): arrays or list of values for the specified parameter to replace
```

## core.replace_any_soil_organic

```python
replace_any_soil_organic(self: unknown, parameter: unknown, param_values: unknown, simulation: unknown)

replaces any specified soil  parameters in the simulation

Args:
    parameter (_string_, required): string e.g Carbon, FBiom. open APSIMX file in the GUI and examne the phyicals node for clues on the parameter names
    simulation (string, optional): Targeted simulation name. Defaults to None.
    param_values (array, required): arrays or list of values for the specified parameter to replace
```

## core.extract_crop_soil_water

```python
extract_crop_soil_water(self: unknown, parameter: unknown, crop: unknown, simulation: unknown)

_summary_

Args:
    parameter (_str_): crop soil water parameter names e.g. LL, XF etc
    crop (str, optional): crop name. Defaults to "Maize".
    simulation (_str_, optional): _target simulation name . Defaults to None.

Returns:
    _type_: _description_
```

## core.replace_crop_soil_water

```python
replace_crop_soil_water(self: unknown, parameter: unknown, param_values: unknown, crop: unknown, simulation: unknown)

_summary_

Args:
    parameter (_str_): crop soil water parameter names e.g. LL, XF etc
    crop (str, optional): crop name. Defaults to "Maize".
    simulation (_str_, optional): _target simulation name . Defaults to None.
     param_values (_list_ required) values of LL of istance list or 1-D arrays

Returns:
    doesn't return anything it mutates the specified value in the soil simulation object
```

## core.find_simulations

```python
find_simulations(self: unknown, simulations: unknown)

Find simulations by name

Parameters
----------
simulations, optional
    List of simulation names to find, if `None` return all simulations
Returns
-------
    list of APSIM Models.Core.Simulation objects
```

## core.set_swcon

```python
set_swcon(self: unknown, swcon: unknown, simulations: unknown)

Set soil water conductivity (SWCON) constant for each soil layer.

Parameters
----------
swcon
    Collection of values, has to be the same length as existing values.
simulations, optional
    List of simulation names to update, if `None` update all simulations
```

## core.get_swcon

```python
get_swcon(self: unknown, simulation: unknown)

Get soil water conductivity (SWCON) constant for each soil layer.

Parameters
----------
simulation, optional
    Simulation name.
Returns
-------
    Array of SWCON values
```

## core.plot_objectives

```python
plot_objectives(self: unknown, x: unknown)

:param x: x variable to go on the x- axis
:param args: y variables to plotted against the x variable, e.g 'Maize yield'
:param kwargs: key word argument specifying the report name e.g report = "Annual"
:return: graph
```

## core.extract_soil_profile

```python
extract_soil_profile(self: unknown, simulation: unknown)

Get soil definition as dataframe

Parameters
----------
simulation, optional
    Simulation name.
Returns
-------
    Dataframe with soil definition
```

## core.replace_soil_organic

```python
replace_soil_organic(self: unknown, organic_name: unknown, simulation_name: unknown)

replace the organic module comprising Carbon , FBIOm, FInert/ C/N

Args:
    organic_name (_str_): _description_
    simulation (_str_, optional): _description_. Defaults to None.
```

## core.set_initial_nh4

```python
set_initial_nh4(self: unknown, values: unknown, simulations: unknown)

Set soil initial NH4 content

Parameters
----------
values
    Collection of values, has to be the same length as existing values.
simulations, optional
    List of simulation names to update, if `None` update all simulations
```

## core.get_initial_urea

```python
get_initial_urea(self: unknown, simulation: unknown)

Get soil initial urea content
```

## core.set_initial_urea

```python
set_initial_urea(self: unknown, values: unknown, simulations: unknown)

Set soil initial urea content

Parameters
----------
values
    Collection of values, has to be the same length as existing values.
simulations, optional
    List of simulation names to update, if `None` update all simulations
```

# Module: weather

## weather.get_iem_bystation

```python
get_iem_bystation(dates: unknown, station: unknown, path: unknown, mettag: unknown)

Dates is a tupple/list of strings with date ranges

an example date string should look like this: dates = ["01-01-2012","12-31-2012"]

if station is given data will be downloaded directly from the station the default is false.

mettag: your prefered tag to save on filee
```

## weather.Class: _MetDate

```python
This class organises the data for IEM weather download
```

## weather.daterange

```python
daterange(start: unknown, end: unknown)

start: the starting year to download the weather data
-----------------
end: the year under which download should stop
```

## weather.daymet_bylocation

```python
daymet_bylocation(lonlat: unknown, start: unknown, end: unknown, cleanup: unknown, filename: unknown)

collect weather from daymet solar radiation is replaced with that of nasapower
------------
parameters
---------------
start: Starting year

end: Ending year

lonlat: A tuple of xy cordnates

Cleanup:  A bolean True or False default is true: deletes the excel file generated during the file write up

------------
returns complete path to the new met file but also write the met file to the disk in the working directory
```

## weather.daymet_bylocation_nocsv

```python
daymet_bylocation_nocsv(lonlat: unknown, start: unknown, end: unknown, cleanup: unknown, filename: unknown)

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
```

## weather.Class: EditMet

```python
This class edits the weather files
```

## weather.merge_columns

```python
merge_columns(df1_main: unknown, common_column: unknown, df2: unknown, fill_column: unknown, df2_colummn: unknown)

Parameters:
df_main (pd.DataFrame): The first DataFrame to be merged and updated.
common_column (str): The name of the common column used for merging.
df2 (pd.DataFrame): The second DataFrame to be merged with 'df_main'.
fill_column (str): The column in 'edit' to be updated with values from 'df2_column'.
df2_column (str): The column in 'df2' that provides replacement values for 'fill_column'.

Returns:
pd.DataFrame: A new DataFrame resulting from the merge and update operations.
```

## weather._edit_apsim_met

```python
_edit_apsim_met(self: unknown)

converts the weather file into a pandas dataframe by removing specified rows.
It is easier to edit  a pandas data frame than a text file

Returns:
- pandas.DataFrame: A DataFrame containing the modified APSIM weather data.

Example:
```

## weather.write_edited_met

```python
write_edited_met(self: unknown, old: unknown, daf: unknown, filename: unknown)

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
```

## weather.met_replace_var

```python
met_replace_var(self: unknown, parameter: unknown, values: unknown)

in case we want to change some columns or rows in the APSIM met file
this function replace specific data in the APSIM weather file with new values.

This method allows for the replacement of specific columns or rows in the APSIM weather file by providing a
'parameter' (column name) and a list of 'values' to replace the existing data.

Args:
- parameter (str): The name of the column (parameter) to be replaced.
- values (list, array or pandas series):  values to replace the existing data in the specified column.

Returns:
- str: The path to the newly created APSIM weather file with the replaced data.
```

# Module: soilmanager

## soilmanager.DownloadsurgoSoiltables

```python
DownloadsurgoSoiltables(lonlat: unknown, select_componentname: unknown, summarytable: unknown)

TODO this is a duplicate File. Duplicate of soils/soilmanager
Downloads SSURGO soil tables

parameters
------------------
lon: longitude 
lat: latitude
select_componentname: any componet name within the map unit e.g 'Clarion'. the default is None that mean sa ll the soil componets intersecting a given locationw il be returned
  if specified only that soil component table will be returned. in case it is not found the dominant componet will be returned with a caveat meassage.
    use select_componentname = 'domtcp' to return the dorminant component
summarytable: prints the component names, their percentages
```

## soilmanager.set_depth

```python
set_depth(depththickness: unknown)

  parameters
  depththickness (array):  an array specifying the thicknness for each layer
  nlayers (int); number of layers just to remind you that you have to consider them
  ------
  return
bottom depth and top depth in a turple
  
```

## soilmanager.Replace_Soilprofile

```python
Replace_Soilprofile(apsimxfile: unknown, path2apsimx: unknown, series: unknown, lonlat: unknown, crop: unknown)

Replaces APASIMX soil properties

parameters
------------
apsimxfile: apsimx file name string with the extension .apsimx
path2apsimx: path string to apsimx file
lonlat a tupple or a list with the longitude and latitude in the order as the name
```

## soilmanager.Replace_Soilprofile2

```python
Replace_Soilprofile2(path2apsimx: unknown, series: unknown, lonlat: unknown, filename: unknown, gridcode: unknown, Objectid: unknown, crop: unknown)

Replaces APASIMX soil properties

parameters
------------
apsimxfile: apsimx file name string with the extension .apsimx
path2apsimx: path string to apsimx file
lonlat a tupple or a list with the longitude and latitude in the order as the name
```

## soilmanager.__init__

```python
__init__(self: unknown, sdf: unknown, thickness: unknown, thickness_values: unknown, bottomdepth: unknown)

_summary_

Args:
    sdf (pandas data frame): soil table downloaded from SSURGO_
    thickness double: _the thickness of the soil depth e.g 20cm_
    bottomdepth (int, optional): _description_. Defaults to 200.
    thickness_values (list or None) optional if provided extrapolation will be based on those vlue and should be the same length as the existing profile depth
 
```

## soilmanager.decreasing_exponential_function

```python
decreasing_exponential_function(self: unknown, x: unknown, a: unknown, b: unknown)

Compute the decreasing exponential function y = a * e^(-b * x).

Parameters:
    x (array-like): Input values.
    a (float): Amplitude or scaling factor.
    b (float): Exponential rate.

Returns:
    numpy.ndarray: The computed decreasing exponential values.
```

# Module: weathermanager

## weathermanager.get_iem_bystation

```python
get_iem_bystation(dates: unknown, station: unknown, path: unknown, mettag: unknown)

Dates is a tupple/list of strings with date ranges

an example date string should look like this: dates = ["01-01-2012","12-31-2012"]

if station is given data will be downloaded directly from the station the default is false.

mettag: your prefered tag to save on filee
```

## weathermanager.daterange

```python
daterange(start: unknown, end: unknown)

start: the starting year to download the weather data
-----------------
end: the year under which download should stop
```

## weathermanager.daymet_bylocation

```python
daymet_bylocation(lonlat: unknown, start: unknown, end: unknown, cleanup: unknown, filename: unknown)

collect weather from daymet solar radiation is replaced with that of nasapower
------------
parameters
---------------
start: Starting year

end: Ending year

lonlat: A tuple of xy cordnates

Cleanup:  A bolean True or False default is true: deletes the excel file generated during the file write up

------------
returns complete path to the new met file but also write the met file to the disk in the working directory
```

## weathermanager.daymet_bylocation_nocsv

```python
daymet_bylocation_nocsv(lonlat: unknown, start: unknown, end: unknown, cleanup: unknown, filename: unknown)

collect weather from daymet solar radiation is replaced with that of nasapower
------------
parameters
---------------
start: Starting year

end: Ending year

lonlat: A tuple of xy cordnates

Cleanup:  A bolean True or False default is true: deletes the excel file generated during the file write up

------------
returns complete path to the new met file but also write the met file to the disk in the working directory
```

