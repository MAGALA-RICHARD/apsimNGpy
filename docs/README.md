# apsimNGpy API documentation
This apsimNGpy API documentation is generated automatically. The official documentation has not been released
# Module: config

```python
config.scan_dir_for_bin(path: str)
```
Recursively scans directories starting at the given path.
Stops scanning as soon as a directory named 'bin' is encountered and returns its path.

```python
config.scan_drive_for_bin()
```
This function uses scan_dir_for_bin to scan all drive directories.
for Windows only

```python
config.auto_detect_apsim_bin_path()
```
For Windows, this function scans all the drives. 
On macOS, we check the Applications folder, while on Linux, we look in `/usr/local`.
Additionally, we search the home directory, though it is unlikely to be a reliable source.



```python
config.get_apsim_bin_path()
```
Returns the path to the apsim bin folder from either auto-detection or from the path already supplied by the user
through the ```python apsimNgpyconfig.ini``` file in the user home directory. the location folder is called `APSIMNGpy_meta_data`.
This function is silent does not raise any exception but return empty string in all cases if the bin folder is not detected
:return:
a string path for the apsim bin path


```python
config.set_apsim_bin_path(path: [os.Pathlike, str])
```

Send your desired path to the aPSim binary folder to the config module
the path should end with bin as the parent directory of the aPSim Model.
- Please be careful with adding an uninstalled path, which does not have model.exe file or unix executable.
   It won't work and python with throw an error
```python
>> example from apsimNGpy.config import Config
# - check the current path

config = Config.get_apsim_bin_path()
 # set the desired path
>> Config.set_apsim_bin_path(path = '/path/to/APSIM*/bin')
```
## Class: Config

 The configuration class providing the leeway for the user to change the
global variables such as aPSim bin locations. it is deprecated. it has the following method similar as above
```python
set_apsim_bin_path(path: [os.Pathlike, str])
get_apsim_bin_path()
```

## Module: apsim

### Class ApsimModel
This class inherits all methods from APSIMNG class

```python
### Method: ApsimModel.adjust_dul
adjust_dul(simulations: Union[tuple, list])
```
- This method checks whether the soil SAT is above or below DUL and decreases DUL values accordingly
- Need to call this method everytime SAT is changed, or DUL is changed accordingly
:param simulations: str, name of the simulation where we want to adjust DUL and SAT according
:return:
ApsimModel model object

```python
Method: ApsimModel.replace_downloaded_soils

replace_downloaded_soils(soil_tables: Union[dict, list], simulation_names: Union[tuple, list])
```
Updates soil parameters and configurations for downloaded soil data in simulation models.

This method adjusts soil physical and organic parameters based on provided soil tables and applies these
adjustments to specified simulation models. Optionally, it can adjust the Radiation Use Efficiency (RUE)
based on a Carbon to Sulfur ratio (CSR) sampled from the provided soil tables.

Parameters: 
- soil_tables (list): A list containing soil data tables. Expected to contain: 
- [0]: DataFrame with physical soil parameters.
- [1]: DataFrame with organic
soil parameters.
- [2]: DataFrame with crop-specific soil parameters.


Returns:
- self: Returns an instance of the class for chaining methods.

This method directly modifies the simulation instances found by `find_simulations` method calls,
updating physical and organic soil properties, as well as crop-specific parameters like lower limit (LL),
drain upper limit (DUL), saturation (SAT), bulk density (BD), hydraulic conductivity at saturation (KS),
and more based on the provided soil tables.
- **kwargs: 

`set_sw_con`: Boolean, set the drainage coefficient for each layer

`adJust_kl`:: Bolean, adjust, kl based on productivity index

`CultvarName`: cultivar name which is in the sowing module for adjusting the rue

`tillage`: specify whether you will be carried to adjust some physical parameters



```python
Method: ApsimModel.run_edited_file

run_edited_file(simulations: Union[tuple, list], clean: bool, multithread: unknown)
```
Run simulations in this subclass if we want to clean the database, we need to
 spawn the path with one process to avoid os access permission errors


Parameters
----------
simulations, optional
    List of simulation names to run, if `None` runs all simulations, by default `None`.
clean, optional
    If `True` remove existing database for the file before running, by default `True`
multithread, optional
    If `True` APSIM uses multiple threads, by default `True`


### Method: ApsimModel.spin_up

```python
spin_up(report_name: str, start: int, end: int, spin_var: str, simulations: list)
```
Perform a spin-up operation on the aPSim model.

This method is used to simulate a spin-up operation in an aPSim model. During a spin-up, various soil properties or
variables may be adjusted based on the simulation results.

Parameters:
----------
report_name : str, optional (default: 'Report')
    The name of the aPSim report to be used for simulation results.
start : str, optional
    The start date for the simulation (e.g., '01-01-2023'). If provided, it will change the simulation start date.
end : str, optional
    The end date for the simulation (e.g., '3-12-2023'). If provided, it will change the simulation end date.
spin_var : str, optional (default: 'Carbon'). the difference between the start and end date will determine the spin-up period
    The variable representing the type of spin-up operation. Supported values are 'Carbon' or 'DUL'.

Returns:
-------
 ApsimModel object
    The modified ApsimModel object after the spin-up operation.
    you could call save_edited file and save it to your specified location, but you can also proceed with the simulation
```

# Module: base_data
The module for accessing the default dataset from APSIM model

## Function: load_default_simulations

```python
load_default_simulations(crop: str, path:  , simulations_object: bool)
```
Load default simulation model from aPSim folder
:param crop: string of the crop to load e.g. Maize, not case-sensitive
:param path: string of the path to copy the model
:param simulations_object: bool to specify whether to return apsimNGp.core simulation object defaults to True
:return: apsimNGpy.core.APSIMNG simulation objects
# Example
 load apsimNG object directly
```python
model = load_default_simulations('Maize', simulations_object=True)
```
 try running
```python
model.run(report_name='Report', get_dict=True)
```
 collect the results
```python
model.results.get('Report')
```
 Return the path only
```python
model =load_default_simulations('Maize', simulations_object=False)
```
#let's try to load non exisistent crop marize, which does exists
```python
model.load_default_simulations('Marize')
```
we get this warning
2024-11-19 16:18:55,798 - base-data - INFO - No crop named:' 'marize' found at 'C:/path/to/apsim/folder/Examples

### Function: load_default_sensitivity_model

```python
load_default_sensitivity_model(method: str, path: str, simulations_object: bool)
```
  Load default simulation model from aPSim folder
 :@param method: string of the sentitivity type to load e.g. "Morris" or Sobol, not case-sensitive
 :@param path: string of the path to copy the model
 :@param simulations_object: bool to specify whether to return apsimNGp.core simulation object defaults to True
 :@return: apsimNGpy.core.APSIMNG simulation objects
 # Example
 # load apsimNG object directly
```python
 >>> morris_model = load_default_sensitivity_model(method:str = 'Morris', simulations_object:bool=True)
```
 # let's try to laod non existient senstitivity model, which does exists
```python
 >>> load_default_sensitivity_model('Mmoxee')
```
we get this warning
2024-11-29 13:30:51,757 - settings - INFO - No sensitivity model for method:' 'morrirs' found at '~//APSIM2024.5.7493.0//Examples//Sensitivity'

# Module: core
The primary class for all apsim related simulations
### Class: APSIMNG

Modify and run APSIM Next Generation (APSIM NG) simulation models.

This class serves as the entry point for all apsimNGpy simulations and is inherited by the `ApsimModel` class.
It is designed to be used when you do not intend to replace soil profiles.

Parameters:
    model (os.PathLike): The file path to the APSIM NG model. This parameter specifies the model file to be used in the simulation.
    out_path (str, optional): The path where the output file should be saved. If not provided, the output will be saved with the same name as the model file in the current directory.
    out (str, optional): Alternative path for the output file. If both `out_path` and `out` are specified, `out` takes precedence. Defaults to `None`.

Keyword parameters:
    'copy' (bool, deprecated): Specify whether to clone the simulation file. This argument is deprecated as the simulation file is automatically cloned without requiring this parameter.

Note:
    The 'copy' keyword is no longer necessary and will be ignored in future versions.

## Method: APSIMNG.run_simulations

```python
core.APSIMNG.run_simulations(results: bool, reports: Union[tuple, list], clean_up: bool)
```
Run the simulation. Here we are using the self.model_info named tuple from model loader
:results : bool, optional if True, we return the results of the simulation
   else we just run, and the user can retrieve he results from the database using the data store path
reports: str, array like for returning the reports
clean_up : bool deletes the file on disk, by default False
returns results if results is True else None

## property APSIMNG.simulation_object
```python
core.APSIMNG.simulation_object(value: unknown)
```
Set the model if you don't want to initialize again
:param value:
- A value in this context is:
- A path to apsimx file, a str or pathlib Path object
- A dictionary (apsimx json file converted to a dictionary using the json module)
- apsimx simulation object already in memory



### property: APSIMNG.simulations

```python
core.APSIMNG.simulations
```
Retrieve simulation nodes in the APSIMx `Model.Core.Simulations` object.

We search all Models.Core.Simulation in the scope of Model.Core.Simulations. Please note the difference
Simulations is the whole json object Simulation is the node with the field zones, crops, soils and managers
any structure of apsimx file any structure can be handled

### property: APSIMNG.simulation_names

```python
core.APSIMNG.simulations_names
```
retrieves the name of the simulations in the APSIMx `Model.Core
@return: list of simulation names


### Method: APSIMNG.restart_model

```python
core.APSIMNG.restart_model(model_info:named_tuple)
```


 :param model_info: A named tuple object returned by `load_apx_model` from the `model_loader` module.

Notes:
- This parameter is crucial whenever we need to reinitialize the model, especially after updating management practices or editing the file.
- In some cases, this method is executed automatically.
- If `model_info` is not specified, the simulation will be reinitialized from `self`.

This function is called by `save_edited_file` and `update_mgt`.

:return: APSIMNG object


### Method: APSIMNG.save_edited_file

```python
core.APSIMNG.save_edited_file(out_path:[os.Pathlike, str], relaod:bool)
```
save_edited_file(out_path: unknown, reload: unknown)

Saves the model to the local drive.
Notes: - If `out_path` is None, the `save_model_to_file` function extracts the filename from the
`Model.Core.Simulation` object. - `out_path`, however, is given high priority. Therefore,
we first evaluate if it is not None before extracting from the file. - This is crucial if you want to
give the file a new name different from the original one while saving.

Parameters
- out_path (str): Desired path for the .apsimx file, by default, None.
- reload (bool): Whether to load the file using the `out_path` or the model's original file name.


### Method: APSIMNG.run

```python
core.APSIMNG.run(report_name: Union[tuple, list], simulations: Union[tuple, list], clean: bool, multithread: bool, verbose: bool, get_dict: bool, init_only: bool)
```
Run apsim model in the simulations

Parameters
----------
 :param report_name: str. defaults to APSIM defaults Report Name, and if not specified or Report Name not in the simulation tables, the simulator will
    execute the model and save the outcomes in a database file, accessible through alternative retrieval methods.

simulations (__list_), optional
    List of simulation names to run, if `None` runs all simulations, by default `None`.

:param clean (_-boolean_), optional
    If `True` remove an existing database for the file before running, deafults to False`

:param multithread: bool
    If `True` APSIM uses multiple threads, by default `True`
    :param simulations:

:param verbose: bool logger.infos diagnostic information such as false report name and simulation
:param get_dict: bool, return a dictionary of data frame paired by the report table names default to False
:param init_only, runs without returning the result defaults to 'False'.
returns
    instance of the class APSIMNG


### Method: APSIMNG.clone_simulation

```python
APSIMNG.clone_simulation.clone_simulation(target: str, simulation: Union[list, tuple])
```
Clone a simulation and add it to Model
Parameters
----------
target
     simulation name
simulation, optional
    Simulation name to be cloned, of None clone the first simulation in model


## Method: APSIMNG.remove_simulation

```python
remove_simulation(simulation: Union[tuple, list])
```
Remove a simulation from the model

Parameters
----------
simulation
    The name of the simulation to remove

### Method: APSIMNG.clone_zone

```python
core.APSIMNG.clone_zone(target: str, zone: str, simulation: Union[tuple, list])
```
Clone a zone and add it to Model

Parameters
----------
target
     simulation name
zone
    Name of the zone to clone
simulation, optional
    Simulation name to be cloned, of None clone the first simulation in model


## Method: APSIMNG.find_zones

```
core.APSIMNG.find_zones(simulation: Union[tuple, list])

Find zones from a simulation

Parameters
----------
simulation
     name

Returns
-------
    list of zones as APSIM Models.Core.Zone objects
```

### Method: APSIMNG.extract_report_names

```
returns all data frames the available report tables
@return: list of table names in the simulation
```

### Method: APSIMNG.replicate_file

```python
core.APSIMNG.replicate_file(k: int, path:  , tag: str)
```
Replicates a file 'k' times.

If a path is specified, the copies will be placed in that directory with incremented filenames.
If no path is specified, copies are created in the same directory as the original file, also with incremented filenames.

Parameters:
- self: The core.api.APSIMNG object instance containing 'path' attribute pointing to the file to be replicated.
- k (int): The number of copies to create.
- path (str, optional): The directory where the replicated files will be saved. Defaults to None, meaning the same directory as the source file.
- tag (str, optional): a tag to attached with the copies. Defaults to "replicate"
Returns:
- A list of paths to the newly created files if get_back_list is True else a generator is returned.


### Method: APSIMNG.get_crop_replacement

```python
core.APSIMNG.get_crop_replacement(Crop: unknown)
```
:param Crop: crop to get the replacement
:return: System.Collections.Generic.IEnumerable APSIM plant object


### Method: APSIMNG.edit_cultivar

```python
core. APSIMNG.edit_cultivar(CultivarName:str, commands:tuple, values:tuple)
```
Edits the parameters of a given cultivar. we don't need a simulation name for this unless if you are defining it in the
manager section, if that it is the case, see update_mgt

:param CultivarName: Name of the cultivar (e.g., 'laila').

:param commands: A tuple of strings representing the parameter paths to be edited.

Example: ('[Grain].MaximumGrainsPerCob.FixedValue', '[Phenology].GrainFilling.Target.FixedValue')

:param values: A tuple containing the corresponding values for each command (e.g., (721, 760)).
:return: None


### Method: APSIMNG.get_current_cultivar_name

```python
APSIMNG.get_current_cultivar_name(ManagerName: str)
```
@param ManagerName: script manager module in the zone
@return: returns the current cultivar name in the manager script 'ManagerName


## Method: APSIMNG.collect_specific_report

```python
core.APSIMNG.collect_specific_report(results: dict, report_names: str, var_names: str, stat:str)
```
_summary_

Args:
    results (_dict_): diction of apsim results table generated by run method
    report_names (_str_): _report name_
    var_names (_list_): _description_
    Statistic (_list_): how to summary the data supported versions are mean, median, last ,start standard deviation
    statistics and var names should be the order ['yield', 'carbon'] and ['mean', 'diff'], where mean for yield and diff for carbon, respectively


### Method: APSIMNG.update_cultivar

```python
core.APSIMNG.update_cultivar(parameters: dict, simulations: Union[list, tuple] = None, clear=False, **kwargs):
```
Update cultivar parameters

Parameters
----------
@param:parameters (__dict__) dictionary of cultivar parameters to update.
@param: simulations, optional
    List or tuples of simulation names to update if `None` update all simulations.
@param: clear, optional
    If `True` remove all existing parameters, by default `False`.


### Method: APSIMNG.examine_management_info

```python
core.APSIMNG.examine_management_info(simulations: Union[list, tuple])
```
this will show the current management scripts in the simulation root

Parameters
----------
simulations, optional
    List or tuple of simulation names to update, if `None` show all simulations. if you are not sure,

    use the property decorator 'extract_simulation_name


### Method: APSIMNG.change_som

```python
core.APSIMNG.change_som(*, simulations: Union[tuple, list] = None, inrm: int = 1250, icnr: int = 27, **kwargs):

````
     Change Surface Organic Matter (SOM) properties in specified simulations.

Parameters:
    simulations (str ort list): List of simulation names to target (default: None).
    inrm (int): New value for Initial Residue Mass (default: 1250).
    icnr (int): New value for Initial Carbon to Nitrogen Ratio (default: 27).

Returns:
    self: The current instance of the class.
    


### Method: APSIMNG.recompile_edited_model

```python

core.core.APSIMNG.recompile_edited_model(out_path: [str, os.PathLike])
```
@param out_path: os.PathLike object this method is called to convert the simulation object from ConverterReturnType to model like object
@return: self


### Method: APSIMNG.update_mgt

```python
core.APSIMNG.update_mgt(*, management: Union[dict, tuple],  simulations: [list, tuple] = None, out: [Path, str] = None, **kwargs)
```
Update management settings in the model. This method handles one management parameter at a time.

Parameters
----------
management : dict or tuple
    A dictionary or tuple of management parameters to update. The dictionary should have 'Name' as the key
    for the management script's name and corresponding values to update. Lists are not allowed as they are mutable
    and may cause issues with parallel processing. If a tuple is provided, it should be in the form (param_name, param_value).

simulations : list of str, optional
    List of simulation names to update. If `None`, updates all simulations. This is not recommended for large
    numbers of simulations as it may result in a high computational load.

out : str or pathlike, optional
    Path to save the edited model. If `None`, uses the default output path specified in `self.out_path` or
    `self.model_info.path`. No need to call `save_edited_file` after updating, as this method handles saving.

Returns
-------
self : Editor
    Returns the instance of the `Editor` class for method chaining.

Notes ----- - Ensure that the `management` parameter is provided in the correct format to avoid errors. -
This method does not perform validation on the provided `management` dictionary beyond checking for key
existence. - If the specified management script or parameters do not exist, they will be ignored.
using a tuple for a specifying management script, paramters is recommended if you are going to pass the function to  a multi-processing class fucntion


### Method: APSIMNG.preview_simulation

Preview the simulation file in the apsimNGpy object in the APSIM graphical user interface
@return: opens the simulation file


### Method: APSIMNG.extract_user_input

```python
core.APSIMNG.extract_user_input(manager_name: str)
```
Get user_input of a given model manager script
returns;  a dictionary of user input with the key as the script parameters and values as the inputs
- Example
_____________________________________________________
from apsimNGpy.core.base_data import load_default_simulations
model = load_default_simulations(crop = 'maize')
ui = model.extract_user_input(manager_name='Fertilise at sowing')
print(ui)
### output
{'Crop': 'Maize', 'FertiliserType': 'NO3N', 'Amount': '160.0'}


### Method: APSIMNG.change_simulation_dates

```python
change_simulation_dates(start_date: str, end_date: str, simulations: Union[tuple, list])
```
Set simulation dates. this is important to run this method before run the weather replacement method as
the date needs to be allowed into weather

Parameters
-----------------------------------
start_date, optional
    Start date as string, by default `None`
end_date, optional
    End date as string, by default `None`
simulations, optional
    List of simulation names to update, if `None` update all simulations
@note
one of the start_date or end_date parameters should at least no be None

@raise assertion error if all dates are None

@return None
### Example:
```python
from apsimNGpy.core.base_data import load_default_simulations

model = load_default_simulations(crop='maize')

model.change_simulation_dates(start_date='2021-01-01', end_date='2021-01-12')
#check if it was successful
changed_dates = model.extract_dates
print(changed_dates)
```
 # OUTPUT
   {'Simulation': {'start': datetime.date(2021, 1, 1),
    'end': datetime.date(2021, 1, 12)}}
@note
It is possible to target a specific simulation by specifying simulation name for this case the name is Simulations, so, it could appear as follows
 model.change_simulation_dates(start_date='2021-01-01', end_date='2021-01-12', simulation = 'Simulation')


## Method: APSIMNG.extract_dates

```python
extract_dates(simulations: list)
```
Get simulation dates in the model

Parameters
----------
simulations, optional
    List of simulation names to get, if `None` get all simulations
Returns
-------
    Dictionary of simulation names with dates
### Example
```python
from apsimNGpy.core.base_data import load_default_simulations

model = load_default_simulations(crop='maize')
changed_dates = model.extract_dates
print(changed_dates)
```
** OUTPUT
```python
   {'Simulation': {'start': datetime.date(2021, 1, 1),
    'end': datetime.date(2021, 1, 12)}}
```
@note
It is possible to target a specific simulation by specifying simulation name for this case the name is Simulations, so, it could appear as follows
model.change_simulation_dates(start_date='2021-01-01', end_date='2021-01-12', simulation = 'Simulation')


## Method: APSIMNG.extract_start_end_years

```python
extract_start_end_years(simulations: str)
```
Get simulation dates

Parameters
----------
simulations, optional
    List of simulation names to get, if `None` get all simulations
Returns
-------
    Dictionary of simulation names with dates


## Method: APSIMNG.show_met_file_in_simulation

```python
show_met_file_in_simulation(simulations: list) -> str
```
Show weather file for all simulations
@return
str 


## Method: APSIMNG.change_report

```python
```
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


### Method: APSIMNG.get_report

```python
get_report(simulation: unknown)
```
Get current report string

Parameters
----------
simulation, optional
    Simulation name, if `None` use the first simulation.
Returns
-------
    List of report lines.


### Method: APSIMNG.extract_soil_physical

```python
extract_soil_physical(simulations:  )
```
Find physical soil

Parameters
----------
simulation, optional
    Simulation name, if `None` use the first simulation.
Returns
-------
    APSIM Models.Soils.Physical object


### Method: APSIMNG.extract_any_soil_physical

```python
extract_any_soil_physical(parameter: unknown, simulations:  )
```
extracts soil physical parameters in the simulation

Args:
    parameter (_string_): string e.g DUL, SAT
    simulations (string, optional): Targeted simulation name. Defaults to None.
---------------------------------------------------------------------------
returns an array of the parameter values


### Method: APSIMNG.replace_any_soil_physical

```python
replace_any_soil_physical(*, parameter: str,
                                  param_values: [tuple, list],
                                  simulations: str = None,
                                  indices=None, **kwargs):
```
replaces specified soil physical parameters in the simulation
______________________________________________________ Args: parameter (_string_, required): string e.g. DUL,
SAT. open APSIMX file in the GUI and examine the physical node for clues on the parameter names simulation (        string, optional): Targeted simulation name. Defaults to None. param_values (array, required): arrays or list
of values for the specified parameter to replace index (int, optional):
if indices is None replacement is done with corresponding indices of the param values


### Method: APSIMNG.extract_soil_organic

```python
extract_soil_organic(simulation: tuple)
```
Find physical soil

Parameters
----------
simulation, optional
    Simulation name, if `None` use the first simulation.
Returns
-------
    APSIM Models.Soils.Physical object


### Method: APSIMNG.extract_any_solute

```python
extract_any_solute(parameter: str, simulation: unknown)
```
Parameters
____________________________________
parameter: parameter name e.g NO3
simulation, optional
    Simulation name, if `None` use the first simulation.
returns
___________________


### Method: APSIMNG.replace_any_solute

```
# replaces with new solute

Parameters
____________________________________
parameter: parameter name e.g NO3
param_values: new values as a list to replace the old ones
simulation, optional
    Simulation name, if `None` use the first simulation.


## Method: APSIMNG.replace_soil_properties_by_path

```python
replace_soil_properties_by_path(path: str, param_values: list, str_fmt: str)
```
This function processes a path where each component represents different nodes in a hierarchy,
with the ability to replace parameter values at various levels.

:param path:
    A string representing the hierarchical path of nodes in the order:
    'simulations.Soil.soil_child.crop.indices.parameter'. Soil here is a constant

- The components 'simulations', 'crop', and 'indices' can be `None`.
- Example of a `None`-inclusive path: `None.Soil.physical.None.None.BD`
- If `indices` is a list, it is expected to be wrapped in square brackets.
- Example when `indices` are not `None`: 'None.Soil.physical.None.[1].BD'
- if simulations please use square blocks
   Example when `indices` are not `None`: '[maize_simulation].physical.None.[1].BD'

**Note: **
- The `soil_child` node might be replaced in a non-systematic manner, which is why indices
  are used to handle this complexity.
- When a component is `None`, default values are used for that part of the path. See the
  documentation for the `replace_soil_property_values` function for more information on
  default values.

:param param_values:
    A list of parameter values that will replace the existing values in the specified path.
    For example, `[0.1, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]` could be used to replace values for `NH3`.

:param str_fmt:
    A string specifying the formatting character used to separate each component in the path.
    Examples include ".", "_", or "/". This defines how the components are joined together to
    form the full path.

:return:
    Returns the instance of `self` after processing the path and applying the parameter value replacements.

- Example 
```python
from apsimNGpy.core.base_data import load_default_simulations
model = load_default_simulations(crop = 'maize')
model.replace_soil_properties_by_path(path = 'None.Soil.Organic.None.None.Carbon', param_values= [1.23])
# if we want to replace carbon at the bottom of the soil profile, we use a negative index  -1
model.replace_soil_properties_by_path(path = 'None.Soil.Organic.None.[-1].Carbon', param_values= [1.23])
```

### Method: APSIMNG.replace_soil_property_values

```python
replace_soil_property_values(*, parameter: str,
                                     param_values: list,
                                     soil_child: str,
                                     simulations: list = None,
                                     indices: list = None,
                                     crop=None,
                                     **kwargs):
```
Replaces values in any soil property array. The soil property array
:param parameter: str: parameter name e.g., NO3, 'BD'
:param param_values:list or tuple: values of the specified soil property name to replace
:param soil_child: str: sub child of the soil component e.g., organic, physical etc.
:param simulations: list: list of simulations to where the node is found if
not found, all current simulations will receive the new values, thus defaults to None
:param indices: list. Positions in the array which will be replaced. Please note that unlike C#, python satrt counting from 0
:crop (str, optional): string for soil water replacement. Default is None


### Method: APSIMNG.extract_any_soil_organic

```python
extract_any_soil_organic(parameter: str, simulation: tuple)
```
extracts any specified soil parameters in the simulation

Args:
   - parameter (_string_, required): string e.g Carbon, FBiom. open APSIMX file in the GUI and examne the phyicals node for clues on the parameter names
   - simulation (string, optional): Targeted simulation name. Defaults to None.
   - param_values (array, required): arrays or list of values for the specified parameter to replace


### Method: APSIMNG.extract_crop_soil_water

```python
extract_crop_soil_water(parameter: str, crop: str, simulation: Union[list, tuple])
```
_summary_

Args:
    parameter (_str_): crop soil water parameter names e.g. LL, XF etc
    crop (str, optional): crop name. Defaults to "Maize".
    simulation (_str_, optional): _target simulation name . Defaults to None.

Returns:
    _type_: _description_


### Method: APSIMNG.find_simulations

```python
find_simulations(simulations: Union[list, tuple])
```
Find simulations by name

Parameters
----------
simulations, optional
    List of simulation names to find, if `None` return all simulations
Returns
-------
    list of APSIM Models.Core.Simulation objects
```

## Method: APSIMNG.set_swcon

```
set_swcon(swcon: list, simulations: Union[list, tuple], thickness_values: list)

Set soil water conductivity (SWCON) constant for each soil layer.

Parameters
----------
swcon
    Collection of values, has to be the same length as existing values.
simulations, optional
    List of simulation names to update, if `None` update all simulations
    :param thickness_values: the soil profile thickness values
```

## Method: APSIMNG.get_swcon

```
get_swcon(simulation: unknown)

Get soil water conductivity (SWCON) constant for each soil layer.

Parameters
----------
simulation, optional
    Simulation name.
Returns
-------
    Array of SWCON values
```

## Method: APSIMNG.clear_db

```
Clears the attributes of the object and optionally deletes associated files.

If the `copy` attribute is set to True, this method will also attempt to delete
files at `self.path` and `self.datastore`. This is a destructive operation and
should be used with caution.

Returns:
   >>None: This method does not return a value.
   >> Please proceed with caution, we assume that if you want to clear the model objects, then you don't need them,
   but by making copy compulsory, then, we are clearing the edited files
```

## Method: APSIMNG.clear

```
Clears the attributes of the object and optionally deletes associated files.

If the `copy` attribute is set to True, this method will also attempt to delete
files at `self.path` and `self.datastore`. This is a destructive operation and
should be used with caution.

Returns:
   >>None: This method does not return a value.
   >> Please proceed with caution, we assume that if you want to clear the model objects, then you don't need them
   but by making copy compulsory, then, we are clearing the edited files
```

## Method: APSIMNG.replace_soil_organic

```
replace the organic module comprising Carbon , FBIOm, FInert/ C/N

Args:
    organic_name (_str_): _description_
    simulation (_str_, optional): _description_. Defaults to None.
```

## Method: APSIMNG.set_initial_nh4

```
set_initial_nh4(values: unknown, simulations: unknown)

Set soil initial NH4 content

Parameters
----------
values
    Collection of values, has to be the same length as existing values.
simulations, optional
    List of simulation names to update, if `None` update all simulations
```

## Method: APSIMNG.get_initial_urea

```
get_initial_urea(simulation: unknown)

Get soil initial urea content
```

## Method: APSIMNG.set_initial_urea

```
set_initial_urea(values: unknown, simulations: unknown)

Set soil initial urea content

Parameters
----------
values
    Collection of values, has to be the same length as existing values.
simulations, optional
    List of simulation names to update, if `None` update all simulations

### method APSIMNG.update_mgt

```python

update_mgt(self, *, management: Union[dict, tuple],  simulations: [list, tuple] = None, out: [Path, str] = None, **kwargs):
```
- Update management settings in the model. This method handles one management parameter at a time.

Parameters
----------
- management : dict or tuple
A dictionary or tuple of management parameters to update. The dictionary should have 'Name' as the key
for the management script's name and corresponding values to update. Lists are not allowed as they are mutable
and may cause issues with parallel processing. If a tuple is provided, it should be in the form (param_name, param_value).

- simulations : list of str, optional
List of simulation names to update. If `None`, updates all simulations. This is not recommended for large
numbers of simulations as it may result in a high computational load.

- out : str or pathlike, optional
Path to save the edited model. If `None`, uses the default output path specified in `self.out_path` or
`self.model_info.path`. No need to call `save_edited_file` after updating, as this method handles saving.

- returns
Notes ----- - Ensure that the `management` parameter is provided in the correct format to avoid errors. -
This method does not perform validation on the provided `management` dictionary beyond checking for key
existence. - If the specified management script or parameters do not exist, they will be ignored.
using a tuple for a specifying management script, paramters is recommended if you are going to pass the function to  a multi-processing class fucntion

  

# Module: met_functions

## Function: impute_data

```
impute_data(met: unknown, method: unknown, verbose: unknown)

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
```

# Module: model_loader

## Function: load_model_from_dict

```
load_model_from_dict(dict_model: unknown, out: unknown, met_file: unknown)

useful for spawning many simulation files
```

## Function: load_from_path

```
load_from_path(path2file: unknown, method: unknown)



:param path2file: path to apsimx file
:param method: str  with string, we direct the method to first convert the file
into a string using json and then use the APSIM in-built method to load the file with file, we read directly from
the file path. This is slower than the former.
```

## Function: load_apx_model

```
load_apx_model(model: unknown, out: unknown, file_load_method: unknown, met_file: unknown)

>> we are loading apsimx model from file, dict, or in memory.
>> if model is none, we will return a pre - reloaded one from memory.
>> if out parameter is none, the new file will have a suffix _copy at the end
>> if model is none, the name is ngpy_model
returns a named tuple with an out path, datastore path, and IModel in memory
```

## Function: save_model_to_file

```
save_model_to_file(_model: unknown, out: unknown)

Save the model

Parameters
----------
out : str, optional path to save the model to
    reload: bool to load the file using the out path
    :param out: out path
    :param _model:APSIM Models.Core.Simulations object
    returns the filename or the specified out name
```

## Function: recompile

```
recompile(_model: unknown, out: unknown, met_path: unknown)

recompile without saving to disk useful for recombiling the same model on the go after updating management scripts

Parameters
----------
out : str, optional path to save the model to

    :param met_path: path to met file
    :param out: out path name for database reconfiguration
    :param _model:APSIM Models.Core.Simulations object
    returns named tuple with a recompiled model
```

# Module: pythonet_config

## Function: load_pythonnet


A method for loading Python for .NET (pythonnet) and APSIM models.

This class provides a callable method for initializing the Python for .NET (pythonnet) runtime and loading APSIM models.
Initialize the Python for .NET (pythonnet) runtime and load APSIM models.

This method attempts to load the 'coreclr' runtime, and if not found, falls back to an alternate runtime.
It also sets the APSIM binary path, adds necessary references, and returns a reference to the loaded APSIM models.

Returns:
-------
lm: Reference to the loaded APSIM models

Raises:
------
KeyError: If APSIM path is not found in the system environmental variable.
ValueError: If the provided APSIM path is invalid.

Notes:
It raises a KeyError if APSIM path is not found. Please edit the system environmental variable on your computer.
Attributes:
----------
None
```

# Module: runner

## Function: _read_simulation

```
_read_simulation(datastore: unknown, report_name: unknown)

returns all data frame the available report tables
```

## Function: run

```
run(named_tuple_data: unknown, results: unknown, multithread: unknown, simulations: unknown)

Run apsimx model in the simulations. the method first cleans the existing database.

This is the safest way to run apsimx files in parallel
as named tuples are immutable so the chances of race conditioning are very low

   Parameters
   ----------
   simulations (__str_), optional
       List of simulation names to run, if `None` runs all simulations, by default `None`.

   :multithread (bool), optional
       If `True` APSIM uses multiple threads, by default `True`

   results (bool), optional: if True, the results will be returned else the function execute without returning anything
   
```

## Function: run_model

```
run_model(named_tuple_model: unknown, results: unknown, clean_up: unknown)

:param results (bool) for return results
:param named_tuple_model: named tuple from model_loader
:param clean_up (bool), deletes the files associated with the Apsim model. there is no need to worry about this
because everything is compiled in the model_loader
:return: a named tuple objects populated with the results if results is True
```

# Module: simulation

## Function: simulate_single_point

```
simulate_single_point(model: Any, location: Tuple[tuple[float, float]], report: unknown, read_from_string: unknown, start: unknown, end: unknown, soil_series: str)

Run a simulation of a given crop.
 model: Union[str, Simulations],
 location: longitude and latitude to run from, previously lonlat
 soil_series: str
 kwargs:
    copy: bool = False, out_path: str = None, read_from_string=True,

    soil_series: str = 'domtcp', thickness: int = 20, bottomdepth: int = 200,

    thickness_values: list = None, run_all_soils: bool = False

    report_name: str specifies the report or table name in the simulation, for which to read the reasults

    replace_weather: Set this boolean to true to download and replace the weather data based on the specified location.

    replace_soil: Set this boolean to true to download and replace the soil data using the given location details.

    mgt_practices: Provide a list of management decissions
```

# Module: soilmanager

## Function: DownloadsurgoSoiltables

```
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

## Function: set_depth

```
set_depth(depththickness: unknown)

  parameters
  depththickness (array):  an array specifying the thicknness for each layer
  nlayers (int); number of layers just to remind you that you have to consider them
  ------
  return
bottom depth and top depth in a turple
  
```

## Method: OrganizeAPSIMsoil_profile.__init__

```
__init__(sdf: unknown, thickness: unknown, thickness_values: unknown, bottomdepth: unknown)

_summary_

Args:
    sdf (pandas data frame): soil table downloaded from SSURGO_
    thickness double: _the thickness of the soil depth e.g 20cm_
    bottomdepth (int, optional): _description_. Defaults to 200.
    thickness_values (list or None) optional if provided extrapolation will be based on those vlue and should be the same length as the existing profile depth
 
```

## Method: OrganizeAPSIMsoil_profile.set_depth

```
set_depth(depththickness: unknown)

  parameters
  depththickness (array):  an array specifying the thicknness for each layer
  nlayers (int); number of layers just to remind you that you have to consider them
  ------
  return
bottom depth and top depth in a turple
  
```

## Method: OrganizeAPSIMsoil_profile.decreasing_exponential_function

```
decreasing_exponential_function(x: unknown, a: unknown, b: unknown)

Compute the decreasing exponential function y = a * e^(-b * x).

Parameters:
    x (array-like): Input values.
    a (float): Amplitude or scaling factor.
    b (float): Exponential rate.

Returns:
    numpy.ndarray: The computed decreasing exponential values.
```

# Module: weather

## Function: get_iem_bystation

```
get_iem_bystation(dates: unknown, station: unknown, path: unknown, mettag: unknown)

Dates is a tupple/list of strings with date ranges

an example date string should look like this: dates = ["01-01-2012","12-31-2012"]

if station is given data will be downloaded directly from the station the default is false.

mettag: your prefered tag to save on filee
```

## Class: _MetDate

```
This class organises the data for IEM weather download
```

## Method: _MetDate.daterange

```
daterange(start: unknown, end: unknown)

start: the starting year to download the weather data
-----------------
end: the year under which download should stop
```

## Method: _MetDate.daymet_bylocation

```
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

## Method: _MetDate.daymet_bylocation_nocsv

```
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

## Class: EditMet

```
This class edits the weather files
```

## Method: EditMet.merge_columns

```
merge_columns(df1_main: unknown, common_column: unknown, df2: unknown, fill_column: unknown, df2_colummn: unknown)

    Parameters:
    df_main (pd.DataFrame): The first DataFrame to be merged and updated.
    common_column (str): The name of the common column used for merging.
    df2 (pd.DataFrame): The second DataFrame to be merged with 'df_main'.
    fill_column (str): The column in 'edit' to be updated with values from 'df2_column'.
    df2_column (str): The column in 'df2' that provides replacement values for 'fill_column'.
P
    Returns:
    pd.DataFrame: A new DataFrame resulting from the merge and update operations.
    
```

## Method: EditMet._edit_apsim_met

```
converts the weather file into a pandas dataframe by removing specified rows.
It is easier to edit  a pandas data frame than a text file

Returns:
- pandas.DataFrame: A DataFrame containing the modified APSIM weather data.

Example:
```

## Method: EditMet.write_edited_met

```
write_edited_met(old: unknown, daf: unknown, filename: unknown)

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

## Method: EditMet.met_replace_var

```
met_replace_var(parameter: unknown, values: unknown)

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

# Module: weathermanager

## Function: get_iem_bystation

```
get_iem_bystation(dates: Union[tuple, list], station: str, path:  , mettag: str)

Dates is a tupple/list of strings with date ranges

an example date string should look like this: dates = ["01-01-2012","12-31-2012"]

if station is given data will be downloaded directly from the station the default is false.

mettag: your prefered tag to save on filee
```

## Method: metdate.daterange

```
daterange(start: unknown, end: unknown)

start: the starting year to download the weather data
-----------------
end: the year under which download should stop
```

## Method: metdate.daymet_bylocation

```
daymet_bylocation(lonlat: Union[tuple, list], start: int, end: int, cleanup: bool, filename: str)

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

## Method: metdate.daymet_bylocation_nocsv

```
daymet_bylocation_nocsv(lonlat: Union[tuple, list], start: int, end: int, cleanup: bool, filename: str)

collect weather from daymet solar radiation is replaced with that of nasapower
------------
parameters
---------------
start: Starting year

end: Ending year

lonlat: A tuple of xy cordnates

Cleanup:  A bolean True or False default is true: deletes the excel file generated during the file write up

------------
returns a complete path to the new met file but also write the met file to the disk in the working directory
```

# Module: experiment_utils

## Class: MetaInfo

```
Meta info provides meta_infor for each experiment. Here it is initialized with defaults, They can be changed via
the set experiment method
```

## Method: MetaInfo._run_experiment

```
:param meta_info: generated by DesignExperiment class
:param objs: single objects generated by set experiment
:return: None
```

## Class: Factor

```
placeholder for factor variable and names. it is intended to ease the readability of the factor for the user
```

## Method: Factor.define_factor

```
define_factor(parameter: str, param_values: list, factor_type: str, manager_name: str, soil_node: str, simulations: list, out_path_name: str, crop: str, indices: list)

Define a management or soil factor based on the specified type.

Args:
    parameter (str): The parameter name.
    param_values (list): A list of parameter values.
    factor_type (str): Either 'management' or 'soils' to define the type of factor.
    manager_name (str, optional): The manager name (for a management factor).
    soil_node (str, optional): The soil node (for a soil factor).
    simulations (list, optional): The list of simulations.
    out_path_name (str, optional): The output path name (for a management factor).
    crop (str, optional): The crop name (for a soil factor).
    indices (list, optional): The indices (for soil factor).

Returns:
    Factor: A Factor object containing the variable paths and the parameter values.
```

## Method: Factor.define_cultivar

```
define_cultivar(cultivar_name: unknown, commands: unknown, param_values: unknown, parameter: unknown)

Defines the cultivar parameters for a given cultivar_name. these methods are used to abstract arguments for
replacing method
:param cultivar_name: name of the cultivar to edit
:param commands: commands a path for the cutlivar parameter to edit
:param param_values: values to replace with the old ones

 # A cultivar is edited via the replacement module, any simulation file supplied without Replacements for,
 # this method will fail quickly
 Example
 ...
     from apsimNGpy.core.base_data import LoadExampleFiles
     from apsimNGpy.replacements import Replacements
    maize_path = LoadExampleFiles().get_maize_model.path
    model_replacements  = Replacements(maize_path)
    define the cultivar paramters as follows;
     commands = '[Phenology].GrainFilling.Target.FixedValue'
     cultivar_name ='B_110'
     param_values= 540
```

# Module: main

## Class: Experiment

```
Creates and manages a factorial experiment
## example
```python
path = Path.home().joinpath('scratchT')

from apsimNGpy.core.base_data import load_default_simulations

# import the model from APSIM.

# returns a simulation object of apsimNGpy, but we want the path only. so we pass simulations_object=False
model_path = load_default_simulations(crop='maize', simulations_object=False, path=path.parent)
model_path = path.joinpath('m.apsimx')

# define the factors

carbon = define_factor(parameter="Carbon", param_values=[1.4, 2.4, 0.8], factor_type='soils', soil_node='Organic')
Amount = define_factor(parameter="Amount", param_values=[200, 324, 100], factor_type='Management',
                       manager_name='MaizeNitrogenManager')
Crops = define_factor(parameter="Crops", param_values=[200, 324, 100], factor_type='Management',
                      manager_name='Simple Rotation')
# replacement module must be present in the simulation file in order to edit the cultivar
grainFilling = define_cultivar(parameter="grain_filling", param_values=[600, 700, 500],
                               cultivar_name='B_110',
                               commands='[Phenology].GrainFilling.Target.FixedValue')

FactorialExperiment = Experiment(database_name='test.db',
                                 datastorage='test.db',
                                 tag='th', base_file=model_path,
                                 wd=path,
                                 use_thread=True,
                                 by_pass_completed=True,
                                 verbose=False,
                                 test=False,
                                 n_core=6,
                                 reports={'Report'})

FactorialExperiment.add_factor(parameter='Carbon', param_values=[1.4, 2.4, 0.8], factor_type='soils', soil_node='Organic')
FactorialExperiment.add_factor(parameter='Crops', param_values=['Maize', "Wheat"], factor_type='management', manager_name='Simple '
                                                                                                          'Rotation')
# cultivar is edited via the replacement module, any simulation file supplied without Replacements appended
# to Simulations node, this method will fail quickly
FactorialExperiment.add_factor(parameter='grain_filling', param_values=[300, 450, 650, 700, 500], cultivar_name='B_110',
                               commands='[Phenology].GrainFilling.Target.FixedValue', factor_type='cultivar')

FactorialExperiment.clear_data_base()
FactorialExperiment.start_experiment()
sim_data = FactorialExperiment.get_simulated_data()[0]
sim_data.groupby('grain_filling').agg({"Yield": 'mean'})
print(len(FactorialExperiment.factors))
```

## Method: Experiment.add_factor

```python
add_factor(factor_type: unknown)
```
factor_types can be: management, som, cultivar or soils


## Method: Experiment.set_experiment


## example
```python
path = Path.home().joinpath('scratchT')
from apsimNGpy.core.base_data import load_default_simulations

# import the model from APSIM.

# returns a simulation object of apsimNGpy, but we want the path only. so we pass simulations_object=False
# model_path = load_default_simulations(crop='maize', simulations_object=False, path=path.parent)
model_path = path.joinpath('m.apsimx')

# define the factors

carbon = define_factor(parameter="Carbon", param_values=[1.4, 2.4, 0.8], factor_type='soils', soil_node='Organic')
Amount = define_factor(parameter="Amount", param_values=[200, 324, 100], factor_type='Management',
                       manager_name='MaizeNitrogenManager')
Crops = define_factor(parameter="Crops", param_values=[200, 324, 100], factor_type='Management',
                      manager_name='Simple Rotation')
# replacement module must be present in the simulation file in order to edit the cultivar
grainFilling = define_cultivar(parameter="grain_filling", param_values=[600, 700, 500],
                               cultivar_name='B_110',
                               commands='[Phenology].GrainFilling.Target.FixedValue')

FactorialExperiment = Experiment(database_name='test.db',
                                 datastorage='test.db',
                                 tag='th', base_file=model_path,
                                 wd=path,
                                 use_thread=True,
                                 by_pass_completed=True,
                                 verbose=False,
                                 test=False,
                                 n_core=6,
                                 reports={'Report'})

FactorialExperiment.add_factor(parameter='Carbon', param_values=[1.4, 2.4, 0.8], factor_type='soils', soil_node='Organic')
FactorialExperiment.add_factor(parameter='Crops', param_values=['Maize', "Wheat"], factor_type='management', manager_name='Simple '
                                                                                                          'Rotation')
# cultivar is edited via the replacement module, any simulation file supplied without Replacements appended
# to Simulations node, this method will fail quickly
FactorialExperiment.add_factor(parameter='grain_filling', param_values=[300, 450, 650, 700, 500], cultivar_name='B_110',
                               commands='[Phenology].GrainFilling.Target.FixedValue', factor_type='cultivar')

FactorialExperiment.clear_data_base()
FactorialExperiment.start_experiment()
sim_data = FactorialExperiment.get_simulated_data()[0]
sim_data.groupby('grain_filling').agg({"Yield": 'mean'})
print(len(FactorialExperiment.factors))
```

### Method: Experiment.test_experiment

```python
test_experiment(test_size: int)
```
this function will test the experiment set up to be called by the user before running start a few things to
check reports supplied really exist in the simulations, and the data tables are serializable into the sql
database


### Method: Experiment.start_experiment

This will run the experiment
The method may fail miserably if you call it without a guard like if __name__ == '__main__':
It's advisable to use this class below the line


### Method: Experiment.end_experiment

cleans up stuff


## Method: Experiment.clear_data_base

```python
clear_data_base(all_tables: unknown, report_name: unknown)
```
for clearing database before the start of the simulation, is by_pass completed is true, the process won't continue
:param all_tables:(bool) all existing tables will be cleared proceed with caution defaults to true
:param report_name: (str) if specified a specific table will be cleared proceed with caution


# Module: permutations

## Function: create_permutations

```python
create_permutations(factors: list, factor_names: list)
```
_summary_

The create_permutations function is designed to generate a dictionary of permutations from
a list of factors, with each permutation indexed by an enumeration and the factor values labeled
by corresponding names provided in factor_names. This documentation outlines its purpose, parameters, return value, and raises conditions.

The Purpose of
The function aims to create a comprehensive dictionary of all possible combinations (permutations) generated
 from the provided lists of factors. Each permutation is paired with an index, serving as a unique identifier, and
 the factors within each permutation are labeled according to the corresponding names given in factor_names.

Parameters
factors (list of lists): A list where each element is a list representing a factor. Each sublist contains
the possible values that the factor can take.
factor_names (list of str): A list of strings where each string represents the name of a factor. The order
of names should match the order of factor lists in factors.
Returns
A dictionary where each key is an integer index (starting from 0) corresponding to a unique permutation.
The value for each key is another dictionary where each key-value pair corresponds to a factor name (from factor_names)
and its value in the permutation.
Raises
ValueError: If the length of factor_names does not match the length of factors, indicating a mismatch between the number of
 provided factor names and the number of factors. The error message is: "Unacceptable - factor names should have the same length as the factor list.


## Method: GenerateCombinations.mgt_updater

```python
mgt_updater(simId: str, perms: dict, old_list: list)
```
old_list (list) is a list of ALL MANAGEMENT scripts dictionary with key value pairs
perms (dict) is the dictionary returned by the permutation methods,
simId (int) is the target id of the simulation


# Module: set_ups

## Class: DeepChainMap

```
Variant of ChainMap that allows direct updates to inner scopes from collection module
```

# Module: variable

### Class: BoundedVariable

for setting components for continuous variables
manager and parameters can be set after initialization of the class or keywords argument parameter =? manager = /


### Class: DiscreteVariable

for setting components for discrete variables
manager and parameters can be set after initialization of the class or keywords argument parameter =? manager = /




## Method: DiscreteVariable.mean

```
mean(value: unknown)

sets the standard deviation of the distribution
```

## Method: DiscreteVariable.options

```
options(values: unknown)

values: lists
```

## Method: DiscreteVariable.samples

```
Generates a sample of values from the given options.

This method uses numpy's random. Choice to generate a sample of values
from the provided options. It sets the random seed for reproducibility.

If you want to set your own sample size and options, modify the
attributes `sample_size` and `options` of the class instance.

Returns:
--------
numpy.ndarray
    An array of sampled values from the options.
```

# Module: in_pipeline

## Function: DownloadsurgoSoiltables

```
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

## Method: WDir.get_polygon_points

```
get_polygon_points(row: unknown)

Extract points from a polygon geometry.
```

## Method: WDir.path

```
path(name: unknown)

:param name: name of the new file
:return: realpath for the new file name
```

# Module: others

## Function: impute_data

```
impute_data(met: unknown, method: unknown, verbose: unknown)

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
```

# Module: soilmanager

## Function: DownloadsurgoSoiltables

```
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

## Function: set_depth

```
set_depth(depththickness: unknown)

  parameters
  depththickness (array):  an array specifying the thicknness for each layer
  nlayers (int); number of layers just to remind you that you have to consider them
  ------
  return
bottom depth and top depth in a turple
  
```

## Method: OrganizeAPSIMsoil_profile.__init__

```
__init__(sdf: unknown, thickness: unknown, thickness_values: unknown, bottomdepth: unknown, state: unknown)

_summary_

Args:
    sdf (pandas data frame): soil table downloaded from SSURGO_
    thickness double: _the thickness of the soil depth e.g 20cm_
    bottomdepth (int, optional): _description_. Defaults to 200.
    thickness_values (list or None) optional if provided extrapolation will be based on those vlue and should be the same length as the existing profile depth
 
```

## Method: OrganizeAPSIMsoil_profile.set_depth

```
set_depth(depththickness: unknown)

  parameters
  depththickness (array):  an array specifying the thicknness for each layer
  nlayers (int); number of layers just to remind you that you have to consider them
  ------
  return
bottom depth and top depth in a turple
  
```

## Method: OrganizeAPSIMsoil_profile.decreasing_exponential_function

```
decreasing_exponential_function(x: unknown, a: unknown, b: unknown)

Compute the decreasing exponential function y = a * e^(-b * x).

Parameters:
    x (array-like): Input values.
    a (float): Amplitude or scaling factor.
    b (float): Exponential rate.

Returns:
    numpy.ndarray: The computed decreasing exponential values.
```

## Method: OrganizeAPSIMsoil_profile.adjust_SAT_BD_DUL

```
adjust_SAT_BD_DUL(SAT: unknown, BD: unknown, DUL: unknown)

Adjusts saturation and bulk density values in a NumPy array to meet specific criteria.

Parameters:
SAT: 1-D numpy array
BD: 1-D numpy array
- target_saturation_a (float): The maximum acceptable saturation value for Soil water Module.
- target_saturation_b (float): The maximum acceptable saturation value for SWIM
- target_bulk_density (float): The maximum acceptable bulk density value.

Returns:
- np.array: Adjusted 2D NumPy array with saturation and bulk density values.
```

# Module: soil_queries

## Function: get_gssurgo_soil_soil_table_at_lonlat

```
get_gssurgo_soil_soil_table_at_lonlat(lonlat: unknown, select_componentname: unknown, summarytable: unknown)

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

## Function: get_gssurgo_soil_soil_table_at_polygon

```
get_gssurgo_soil_soil_table_at_polygon(_coordinates: unknown)

    Function to get al soil mapunit keys or components intersection a polygon
:param _coordinates: a list returned by get_polygon_bounds function
:return: data frame
```

## Function: get_polygon_points

```
get_polygon_points(row: unknown)

Extract points from a polygon geometry.
```

# Module: weathermanager

## Function: get_iem_by_station

```
get_iem_by_station(dates_tuple: unknown, station: unknown, path: unknown, met_tag: unknown)

Dates is a tupple/list of strings with date ranges

an example date string should look like this: dates = ["01-01-2012","12-31-2012"]

if station is given data will be downloaded directly from the station the default is false.

mettag: your prefered tag to save on filee
```

## Method: MetDate.daterange

```
daterange(start: unknown, end: unknown)

start: the starting year to download the weather data
-----------------
end: the year under which download should stop
```

## Method: MetDate.get_met_from_day_met

```
get_met_from_day_met(lonlat: Union[tuple, list,  ], start: int, end: int, filename: str, fill_method: str, retry_number: Union[int,  ])

collect weather from daymet solar radiation is replaced with that of nasapower API
------------
parameters
---------------:

retry_number (int): retry number of times in case of network errors
:filename. met file name to save on disk
start: Starting year of the met data
end: Ending year of the met data
lonlat (tuple, list, array): A tuple of XY cordnates, longitude first, then latitude second
:fill_method (str, optional): fills the missing data based pandas fillna method arguments may be bfill, ffill defaults to ffill
:keyword timeout specifies the waiting time
:keyword wait: the time in secods to try for every retry in case of network errors
returns a complete path to the new met file but also write the met file to the disk in the working directory

Example:
  # Assuming the function is imported as :
      >>> from apsimNGpy.manager.weathermanager import get_met_from_day_met
      >>> wf = get_met_from_day_met(lonlat=(-93.04, 42.01247),
          >>> start=2000, end=2020,timeout = 30, wait =2, retry_number=3, filename='daymet.met')
```

## Method: MetDate.impute_data

```
impute_data(met: unknown, method: unknown, verbose: unknown)

Imputes missing data in a pandas DataFrame using specified interpolation or mean value.

Parameters:
- met (pd.DataFrame): DataFrame with missing values.
- method (str, optional): Method for imputing missing values ("approx", "spline", "mean"). Default is "mean".
- verbose (bool, optional): If True, prints detailed information about the imputation. Default is False.
- **kwargs (dict, optional): Additional keyword arguments including 'copy' (bool) to deep copy the DataFrame.

Returns:
- pd.DataFrame: DataFrame with imputed missing values.
```

## Method: MetDate.get_weather

```
get_weather(lonlat: unknown, start: unknown, end: unknown, source: unknown, filename: unknown)

collects data from various sources
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
```

## Method: MetDate.write_edited_met

```
write_edited_met(old: Union[str, Path], daf:  , filename: str)

Parameters
----------
old; pathlinke to original met file

old
daf: new data in the form of a pandas dataframe
filename; file name to save defaults to edited_met.met

Returns
-------
new path to the saved file
```

## Method: MetDate.merge_columns

```
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

## Method: MetDate.day_of_year_to_date

```
day_of_year_to_date(year: unknown, day_of_year: unknown)

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
```

## Method: MetDate.vprint

```
Conditional print based on verbose flag.
```

## Method: MetDate.connect

```
just to allow users enter number retries
Returns
-------
```

# Module: rocess

## Function: custom_parallel

```
custom_parallel(func: unknown, iterable: list)

 Run a function in parallel using threads or processes.

 *Args:
     func (callable): The function to run in parallel.

     iterable (iterable): An iterable of items that will be processed by the function.

     *args: Additional arguments to pass to the `func` function.

 Yields:
     Any: The results of the `func` function for each item in the iterable.

**kwargs
 use_thread (bool, optional): If True, use threads for parallel execution; if False, use processes. Default is False.

  ncores (int, optional): The number of threads or processes to use for parallel execution. Default is 50% of cpu
    cores on the machine.

  verbose (bool): if progress should be printed on the screen, default is True
  progress_message (str) sentence to display progress such processing weather please wait

 
```

## Function: run_apsimx_files_in_parallel

```
run_apsimx_files_in_parallel(iterable_files: list)

Run APSIMX simulation from multiple files in parallel.

Args:
- iterable_files (list): A list of APSIMX  files to be run in parallel.
- ncores (int, optional): The number of CPU cores or threads to use for parallel processing. If not provided, it defaults to 50% of available CPU cores.
- use_threads (bool, optional): If set to True, the function uses thread pool execution; otherwise, it uses process pool execution. Default is False.

Returns:
- returns a generator object containing the path to the datastore or sql databases

Example:
```python
# Example usage of read_result_in_parallel function

from apsimNgpy.parallel.process import run_apsimxfiles_in_parallel
simulation_files = ["file1.apsimx", "file2.apsimx", ...]  # Replace with actual database file names

# Using processes for parallel execution
result_generator = run_apsimxfiles_in_parallel(simulation_files, ncores=4, use_threads=False)
```

Notes:
- This function efficiently reads db file results in parallel.
- The choice of thread or process execution can be specified with the `use_threads` parameter.
- By default, the function uses 50% of available CPU cores or threads if `ncores` is not provided.
- Progress information is displayed during execution.
- Handle any exceptions that may occur during execution for robust processing.
```

## Function: read_result_in_parallel

```
read_result_in_parallel(iterable_files: list, ncores: int, use_threads: bool, report_name: str)

Read APSIMX simulation databases results from multiple files in parallel.

Args:
- iterable_files (list): A list of APSIMX db files to be read in parallel.
- ncores (int, optional): The number of CPU cores or threads to use for parallel processing. If not provided, it defaults to 50% of available CPU cores.
- use_threads (bool, optional): If set to True, the function uses thread pool execution; otherwise, it uses process pool execution. Default is False.
-  report_name the name of the report table defaults to "Report" you can use None to return all

Returns:
- generator: A generator yielding the simulation data read from each file.

Example:
```python
# Example usage of read_result_in_parallel function
from  apsimNgpy.parallel.process import read_result_in_parallel

simulation_files = ["file1.db", "file2.db", ...]  # Replace with actual database file names

# Using processes for parallel execution
result_generator = read_result_in_parallel(simulation_files, ncores=4, use_threads=False)

# Iterate through the generator to process results
for data in result_generator:
    print(data)
it depends on the type of data but pd.concat could be a good option on the returned generator
Kwargs
    func custom method for reading data
```

Notes:
- This function efficiently reads db file results in parallel.
- The choice of thread or process execution can be specified with the `use_threads` parameter.
- By default, the function uses 50% of available CPU cores or threads if `ncores` is not provided.
- Progress information is displayed during execution.
- Handle any exceptions that may occur during execution for robust processing.
```

## Function: download_soil_tables

```
download_soil_tables(iterable: list, use_threads: bool, ncores: int)

Downloads soil data from SSURGO (Soil Survey Geographic Database) based on lonlat coordinates.

Args: - iterable (iterable): An iterable containing lonlat coordinates as tuples or lists. Preferred is generator
- use_threads (bool, optional): If True, use thread pool execution. If False, use process pool execution. Default
is False. - Ncores (int, optional): The number of CPU cores or threads to use for parallel processing. If not
provided, it defaults to 40% of available CPU cores. - Soil_series (None, optional): [Insert description if
applicable.]

Returns:
- a generator: with dictionaries containing calculated soil profiles with the corresponding index positions based on lonlat coordinates.

Example:
```python
# Example usage of download_soil_tables function
from your_module import download_soil_tables

Lonlat_coords = [(x1, y1), (x2, y2), ...]  # Replace with actual lonlat coordinates

# Using threads for parallel processing
soil_profiles = download_soil_tables(lonlat_coords, use_threads=True, ncores=4)

# Iterate through the results
for index, profile in soil_profiles.items():
    process_soil_profile(index, profile)

    Kwargs
    func custom method for downloading soils
```

Notes:
- This function efficiently downloads soil data and returns calculated profiles.
- The choice of thread or process execution can be specified with the `use_threads` parameter.
- By default, the function utilizes available CPU cores or threads (40% of total) if `ncores` is not provided.
- Progress information is displayed during execution.
- Handle any exceptions that may occur during execution to avoid aborting the whole download
```

# Module: replacements

## Method: Replacements.update_mgt_by_path

```
Updates management parameters based on a given path and corresponding parameter values.

This method parses the provided `path` string, evaluates its components, and updates
management configurations using the `param_values`. The path is split using the specified
delimiter `fmt` and validated against a predefined guide of parameters. If the path is
invalid, a `ValueError` is raised.

Args: path (str): A formatted string that specifies the hierarchical path of parameters to update. The
default delimiter is a period ('.'). example: path should follow this order
'simulations_name.Manager.manager_name.out_path_name.parameter_name' Manager is constant, simulation_name
can be None the dfault simulations will be used, and the out_path can also be None the default will be
picked param_values: The value(s) to assign to the specified parameter in the management update.
fmt (str, optional): The delimiter used to split the path string. Default is '.'.

Raises:
    ValueError: If the number of elements in the `path` does not match the expected structure.

Returns:
    The result of the `update_mgt` function after applying the updates.

Example:
    from apsimNGpy.core.base_data import load_default_simulations
    model  = Replacements(load_default_simulations(crop ='maize').path)
    path = "['Simulation'].Manager.Sow using a variable rule.None.Population"

    path = "['Simulation'].Manager.Sow using a variable rule.None.Population"
    param_values = 9
    model.update_mgt_by_path(path=path, param_values=param_values, fmt = '.')
    print(model.extract_user_input('Sow using a variable rule'))

     # if we want all simulations in the model to be changed, we keep that part None
    example:
    path = "None.Manager.Sow using a variable rule.None.Population"
    param_values = 9
    model.update_mgt_by_path(path=path, param_values=param_values, fmt = '.')
    print(model.extract_user_input('Sow using a variable rule'))
```

## Method: Replacements.update_children_params

```
update_children_params(children: tuple)

Method to perform various parameters replacements in apSim model.
:param children: (str): name of e.g., weather space is allowed for more descriptive one such a soil organic not case-sensitive
:keyword kwargs: these correspond to each node you are editing see the corresponding methods for each node
the following are available for each child passed to children
'cultivar': ('simulations','CultivarName', 'commands', 'values'),
'manager': ('management', 'simulations', 'out'),
'weather': ('weather_file', 'simulations'),
'soilphysical': ('parameter', 'param_values', 'simulation'),
'soilorganic': ('parameter', 'param_values', 'simulation'),
'soilchemical': ('parameter', 'param_values', 'simulation'),
'soilwater': ('parameter', 'param_values', 'simulation'),
'soilorganicmatter': ('simulations', 'inrm', 'icnr'),
'clock': ('start_date', 'end_date', 'simulations')
```

## Method: Replacements.replace_soil_properties_by_path

```
replace_soil_properties_by_path(path: str, param_values: list, str_fmt: str)

This function processes a path where each component represents different nodes in a hierarchy,
with the ability to replace parameter values at various levels.

:param path:
    A string representing the hierarchical path of nodes in the order:
    'simulations.Soil.soil_child.crop.indices.parameter'. Soil here is a constant

    - The components 'simulations', 'crop', and 'indices' can be `None`.
    - Example of a `None`-inclusive path: 'None.Soil.physical.None.None.BD'
    - If `indices` is a list, it is expected to be wrapped in square brackets.
    - Example when `indices` are not `None`: 'None.Soil.physical.None.[1].BD'
    - if simulations please use square blocks
       Example when `indices` are not `None`: '[maize_simulation].physical.None.[1].BD'

    **Note: **
    - The `soil_child` node might be replaced in a non-systematic manner, which is why indices
      are used to handle this complexity.
    - When a component is `None`, default values are used for that part of the path. See the
      documentation for the `replace_soil_property_values` function for more information on
      default values.

:param param_values:
    A list of parameter values that will replace the existing values in the specified path.
    For example, `[0.1, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]` could be used to replace values for `NH3`.

:param str_fmt:
    A string specifying the formatting character used to separate each component in the path.
    Examples include ".", "_", or "/". This defines how the components are joined together to
    form the full path.

:return:
    Returns the instance of `self` after processing the path and applying the parameter value replacements.

    Example f

    from apsimNGpy.core.base_data import load_default_simulations
    model = load_default_simulations(crop = 'maize')
    model.replace_soil_properties_by_path(path = 'None.Soil.Organic.None.None.Carbon', param_values= [1.23])
    if we want to replace carbon at the bottom of the soil profile, we use a negative index  -1
    model.replace_soil_properties_by_path(path = 'None.Soil.Organic.None.[-1].Carbon', param_values= [1.23])
```

## Method: Replacements.replace_cultivar_params

```
the expected path is 'Cultivar/cultivar_name/commands' Note cultivars are best edited in the replacement folder, so,
make sure it exists in your simulation and the respective crop has been added
```

# Module: joblib

## Function: create_fishnet1

```
create_fishnet1(pt: unknown, lon_step: unknown, lat_step: unknown, ncores: unknown, use_thread: unknown)

Args: pt: shape or point feature class layer lon_step: height of the polygon lat_step: width of the polygon
ncores: number of cores to use use_thread: if True, threads will be used if false processes will be used
**kwargs: use key word Return = gdf to return GeoPandas data frame: this is show polygon coordinates otherwise if
not supplied to will returun an array

Returns: an array or geopandas data frame
```

## Function: generate_random_points

```
generate_random_points(pt: unknown, resolution: unknown, ncores: unknown, num_points: unknown)

Args:
    pt: shape file
    resolution: resolution in meters
    ncores: number of cores to use
    num_points: number of points to sample in each grid

Returns:
```

## Function: random_points_in_polygon

```
random_points_in_polygon(number: unknown, polygon: unknown, seed: unknown)

Generates a specified number of random points within a given polygon.

This function attempts to create a list of points that are guaranteed to be within
the boundaries of the specified polygon. It uses a simple rejection sampling method
where points are randomly generated within the bounding box of the polygon. Points
that fall inside the polygon are kept until the desired number is reached.

Parameters:
- number (int): The number of random points to generate within the polygon.
- polygon (shapely.geometry.polygon.Polygon): The polygon within which the random
  points are to be generated.
- seed (int, optional): A seed for the random number generator to ensure reproducibility
  of the results. Defaults to 1.

Returns:
- list of shapely.geometry.point.Point: A list containing the generated shapely Point
  objects that fall within the specified polygon.

Example:
```
from shapely.geometry import Polygon, Point
import random

# Define a sample polygon (square in this case)
polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])

# Generate 5 random points within the polygon
points = random_points_in_polygon(5, polygon, seed=42)

# Print the generated points
for point in points:
    print(point)
```

Note:
- The function's efficiency decreases as the complexity of the polygon increases,
  due to the nature of the rejection sampling method. For complex polygons or a high
  number of points, consider optimizing or using more sophisticated sampling methods.
```

## Function: sample_by_polygons

```
sample_by_polygons(shp: unknown, k: unknown, filter_by: unknown, filter_value: unknown)

Generates a specified number of sample points within each polygon of a shapefile,
optionally filtering the polygons based on a column value.

This function reads a polygon shapefile and generates a user-defined number of random
points within each polygon. It allows for an optional filtering of polygons based on
a specified column and value. The distribution of points is weighted by the area of
each polygon, ensuring that larger polygons receive a proportionately higher number
of sample points. The function returns the coordinates of the generated points.

Parameters:
- shp (str): Path to the polygon shapefile (.shp).
- k (int, optional): Base number of sample points to generate for each polygon.
  The actual number of points is adjusted based on the polygon's area. Defaults to 1.
- filter_by (str, optional): Column name to filter the polygons. Only polygons
  matching the filter_value will be considered for sampling. Defaults to None.
- filter_value (various, optional): Value in the filter_by column that the polygons
  must match to be included in the sampling. The type depends on the column's content.

Returns:
- numpy.ndarray: An array of tuples containing the (x, y) coordinates of each generated
  sample point within the polygons, adjusted to the WGS84 coordinate reference system.

Note:
- The function assumes the presence of a function `random_points_in_polygon` to generate
  points within a polygon, which is not defined within this docstring.
- The output coordinates are converted to the WGS84 CRS for geospatial compatibility.
```

## Function: match_crop

```
match_crop(abb: unknown, add_wheat: unknown)

Converts agricultural abbreviations to a string of crop names, with an option to insert 'Wheat' at specified
intervals. The function interprets abbreviations where 'B' stands for Soybean, 'C' for Maize, 'P' for Pasture,
'U' for Developed areas, 'T' for Wetlands, 'F' for Forest, and 'R' for Other crops.

This function takes an abbreviation string representing a sequence of crops and optionally inserts 'Wheat' into
the sequence at predetermined positions. It handles special cases where the abbreviation matches certain
patterns, returning None for these cases.

Parameters:
- abb (str): The abbreviation string representing a sequence of crops. Each character stands for a specific crop:
    'C' for Maize,
    'B' for Soybean,
    'W' for Wheat,
    'P' for Tropical Pasture.
  Characters 'U', 'R', 'T', and 'F' are ignored and removed from the abbreviation.
- add_wheat (bool, optional): If True, 'Wheat' is inserted at positions 1, 3, 5, 7, 9, and 11 in the sequence. Defaults to None, which means 'Wheat' is not added.

Returns:
- str or None: A comma-separated string of crop names based on the abbreviation. Returns None if the abbreviation matches special cases 'TTTTTT' or 'UUUUUUU'.

Example:
```
# Convert abbreviation to crop names with additional 'Wheat'
crop_sequence = match_crop("CBWP", add_wheat=True)
print(crop_sequence)
# Output: "Maize,Wheat,Soybean,Wheat,Wheat,Tropical Pasture"

# Convert abbreviation without adding 'Wheat'
crop_sequence = match_crop("CBWP")
print(crop_sequence)
# Output: "Maize,Soybean,Wheat,Tropical Pasture"
```

Note:
- The function returns None for special case abbreviations 'TTTTTT' and 'UUUUUUU' as an indication of non-standard sequences that should not be processed.
- The insertion of 'Wheat' at specified positions assumes the sequence is long enough to accommodate these insertions. If the sequence is shorter, 'Wheat' will only be inserted up to the length of the sequence.
```

## Function: create_apsimx_sim_files

```python
create_apsimx_sim_files(wd: str, model: APSIMNG, iterable: list)
```
Creates copies of a specified APSIM model file for each element in the provided iterable,
renaming the files to have unique identifiers based on their index in the iterable.
The new files are saved in the specified working directory.

Args:
wd (str): The working directory where the new .apsimx files will be stored.
model (str): The path to the .apsimx model file that will be copied.
iterable (iterable): An iterable (e.g., list or range) whose length determines the number of copies made.

Returns:
dict: A dictionary where keys are indices from 0 to len(iterable)-1 and values are paths to the newly created .apsimx files.

The function performs the following steps:
1. Extracts the basename of the model file, removing the '.apsimx' extension to create a model suffix.
2. Iterates over the `iterable`, creating a unique file name for each element by appending an index and '.apsimx' to the model suffix.
3. Copies the original model file to the new file name in the specified working directory.
4. Returns a dictionary mapping each index to the file path of the created .apsimx file.

Example:
>>wd = '/path/to/working/directory'
>> model = '/path/to/original/model.apsimx'
>> file_paths = create_apsimx_files(wd, model, range(5))
>> print(file_paths)
```python
{0: '/path/to/working/directory/model_0.apsimx', 1: '/path/to/working/directory/model_1.apsimx', ...}
```

## Function: download_weather

```
download_weather(df: unknown, start: unknown, end: unknown, use_thread: unknown, ncores: unknown, replace_soils: unknown)

   downloads and replace soil or weather files or both in parallel or threads
Args:
    replace_soils: Set this to true to simulataneoursly downloand and replace soils
    df: data frame generated by 'create_apsimx_sim_files'
    start: start year of the simulation
    end:  end year of the simulation
    use_thread: if true threading will take place otherwise multiprocessing
    ncores: number of cores to use
kwargs:
  verbose: bool, Set to True print current step
  thickness_values: list defining the soil layer thickness
  report : set to true to return results
  report_names; provide the required table names from apsimx model report
Returns:
```

## Function: create_and_run_sim_objects

```
create_and_run_sim_objects(wd: unknown, shp_file: unknown, resolution: unknown, num_points: unknown, model_file: unknown, reports_names: unknown, cores: unknown)

Args:
    wd: working directory
    shp_file: shape file of the target area
    model_file: APSIM model string path
    reports_names:str or list names of the data in the simulation model
    **kwargs:
       Test: bool. set to true to try out 10 sample before simulation
       run_process: set too false to run in parallel
       select_process; set too False to use multiple process
       'replace_weather'

:param shp_file:
:param resolution:int. square qrid resolution
:param num_points:int for random sampling
```

# Module: simulation

## Function: simulate_single_point

```
simulate_single_point(model: Any, location: Tuple[tuple[float, float]], report: unknown, read_from_string: unknown, start: unknown, end: unknown, soil_series: str)

Run a simulation of a given crop.
 model: Union[str, Simulations],
 location: longitude and latitude to run from, previously lonlat
 soil_series: str
 kwargs:
    copy: bool = False, out_path: str = None, read_from_string=True,

    soil_series: str = 'domtcp', thickness: int = 20, bottomdepth: int = 200,

    thickness_values: list = None, run_all_soils: bool = False

    report_name: str specifies the report or table name in the simulation, for which to read the reasults

    replace_weather: Set this boolean to true to download and replace the weather data based on the specified location.

    replace_soil: Set this boolean to true to download and replace the soil data using the given location details.

    mgt_practices: Provide a list of management decissions
```

# Module: glue

## Function: NSE

```
NSE(params: unknown, obs: unknown, simulator_func: unknown)

Nash-Sutcliffe efficiency.
    
```

## Function: weighted_quantiles

```
weighted_quantiles(values: unknown, quantiles: unknown, sample_weight: unknown)

based on : https://nbviewer.org/github/JamesSample/enviro_mod_notes/blob/master/notebooks/07_GLUE.ipynb
    
```

## Method: GlueRunner._check_params

```
_check_params(params: unknown)

Evaluate if all params lists are of equal length
```

## Method: GlueRunner.__init__

```
__init__(simulator_func: unknown, params: unknown, observed: unknown)

:param simulator_func: a customized function that takes in parameters and return the simulation results
:param params:  list of parameter samples use BoundedVariable objects or DiscreteVariable objects classes to specify their distributions
raises:
value errors if param lists are not of equal size
```

## Method: GlueRunner.NSE

```
NSE(params: unknown)

Nash-Sutcliffe efficiency.
        
```

## Method: GlueRunner.loss_function

```
loss_function(_loss_function: unknown)

If you are changing the default loss function from NSE (Nash-Sutcliffe Efficiency) to a
custom loss function, you need to modify your simulator function accordingly. The custom
simulator function should return a tuple containing the loss value and the simulated values.
Notes:
   >> set this before you run gle
   >> the function should take in the prameters as a tuple
   >> should be about calculating the loss value between the simulation and the observed
```

## Method: GlueRunner.run_glue

```
run_glue(threshold: unknown, direction: unknown, parallel: unknown)

Run simulations using the default Nash-Sutcliffe Efficiency (NSE) loss function,
or a user-defined loss function if specified during class instantiation.

This method allows for running the simulator in parallel, where the model running
the data may be defined in another script.

Returns:
    pd.DataFrame: A DataFrame containing all "behavioral" parameter sets and associated model outputs.

Parameters:
    threshold (float): specifies the cut-off points
    direction: str; lt for the behavioral parameter to be less than the specified threshold or gt to be greater than
    ncores (int): Specifies the number of processors to use for parallel processing.
    process (bool): Determines whether to run the processes in threads.

Kwargs:
    ncores: int
        The number of processors to use for parallel processing.
    process: bool
        Whether to run the processes in threads.
```

## Method: GlueRunner.coverage

```
coverage(ci_data: unknown)

Prints coverage from GLUE analysis.
        
```

## Method: GlueRunner.visualize_estimates

```
visualize_estimates(params_data: unknown, simulated_data: unknown, observed: unknown, x: unknown)

Plot median simulation and confidence intervals for GLUE.
        
```

## Method: GlueRunner.nls

```
nls(params: unknown)

Nash-Sutcliffe efficiency.
        
```

# Module: sobol

## Function: replace_samples

```
replace_samples(xdata: unknown, wf: unknown, wd: unknown)

xdata is sobol sample sequence
```

# Module: tools

## Method: CustomComparator.__init__

```
__init__(value: unknown, comparison_direction: unknown)

Initialize the CustomComparator.

Parameters:
-----------
value : int or float
    The value to be compared.
comparison_direction : str
    The direction of comparison. Acceptable values are 'gt' for greater than
    and 'lt' for less than. Default is 'gt'.
```

## Method: CustomComparator.compare

```
compare(other: unknown)

Compare the current value with another value based on the comparison direction.

Parameters:
-----------
other : int or float
    The value to compare against.

Returns:
--------
bool
    The result of the comparison.
```

# Module: database_utils

## Function: read_with_query

```
read_with_query(db: unknown, query: unknown)

Executes an SQL query on a specified database and returns the result as a Pandas DataFrame.

Args:
db (str): The database file path or identifier to connect to.
query (str): The SQL query string to be executed. The query should be a valid SQL SELECT statement.

Returns:
pandas.DataFrame: A DataFrame containing the results of the SQL query.

The function opens a connection to the specified SQLite database, executes the given SQL query,
fetches the results into a DataFrame, then closes the database connection.

Example:
    # Define the database and the query
    database_path = 'your_database.sqlite'
    sql_query = 'SELECT * FROM your_table WHERE condition = values'

    # Get the query result as a DataFrame
    df = read_with_query(database_path, sql_query)

    # Work with the DataFrame
    print(df)

Note: Ensure that the database path and the query are correct and that the query is a proper SQL SELECT statement.
The function uses 'sqlite3' for connecting to the database; make sure it is appropriate for your database.
```

## Function: get_db_table_names

```
get_db_table_names(d_b: unknown)

:param d_b: database name or path
:return: all names sql database table names existing within the database
```

## Function: read_db_table

```
read_db_table(db: unknown, report_name: unknown)

Connects to a specified database, retrieves the entire contents of a specified table,
and returns the results as a Pandas DataFrame.

Args:
    db (str): The database file path or identifier to connect to.
    report_name (str): name of the database table: The name of the table in the database from which to retrieve data.
Returns:
    pandas.DataFrame: A DataFrame containing all the records from the specified table.

The function establishes a connection to the specified SQLite database, constructs and executes a SQL query
to select all records from the specified table, fetches the results into a DataFrame, then closes the database connection.

Examples:
    # Define the database and the table name
    database_path = 'your_database.sqlite'
    table_name = 'your_table'

    # Get the table data as a DataFrame
    #>>>> ddf = read_db_table(database_path, table_name)

    # Work with the DataFrame
   #>>>> print(ddf)

Note:
    - Ensure that the database path and table name are correct.
    - The function uses 'sqlite3' for connecting to the database; make sure it is appropriate for your database.
    - This function retrieves all records from the specified table. Use with caution if the table is very large.
    
```

## Function: clear_table

```
clear_table(db: unknown, table_name: unknown)

:param db: path to db
:param table_name: name of the table to clear
:return: None
```

## Function: clear_all_tables

```
clear_all_tables(db: unknown)

:param db: path to database file
:return: None
```

# Module: data_utils

## Function: _split_df

```
_split_df(daf: unknown)

:param daf: a data frame to be split numerically along the reset index. we are split along axis 0
:return: a list of dataframes with single rows
```

# Module: logger

## Method: DualLogger.__init__

```
__init__(name: unknown, log_file: unknown, console_level: unknown, file_level: unknown)

Initialize the DualLogger.

Parameters:
-----------
name : str
    The name of the logger.
log_file : str
    The filename where logs will be saved.
console_level : int
    The logging level for the console output.
file_level : int
    The logging level for the file output.
```

## Method: DualLogger.__call__

```
__call__(level: unknown, message: unknown)

Log a message at the given level.

Parameters:
-----------
level : str
    The level at which to log the message ('debug', 'info', 'warning', 'error', 'critical').
message : str
    The message to log.
```

# Module: others

## Function: convert_df_to_gdf

```
convert_df_to_gdf(df: unknown, CRS: unknown)

Converts a pandas DataFrame to a GeoPandas GeoDataFrame with specified CRS.

This function assumes that the input DataFrame contains a column named 'geometry'
with WKT (Well-Known Text) representations of geometric objects. It converts these
textual geometry representations into GeoPandas geometry objects and sets the
coordinate reference system (CRS) for the resulting GeoDataFrame.

Parameters:
- df (pandas.DataFrame): The input DataFrame to convert. Must include a 'geometry'
  column with WKT representations of the geometries.
- CRS (str or dict): The coordinate reference system to set for the GeoDataFrame.
  Can be specified as a Proj4 string, a dictionary of Proj parameters, an EPSG
  code, or a WKT string.

Returns:
- gpd.GeoDataFrame: A GeoDataFrame created from the input DataFrame with geometries
  converted from WKT format and the specified CRS.

Example:
```
import pandas as pd
import geopandas as gpd
from shapely import wkt

# Sample DataFrame with WKT geometries
data = {'geometry': ['POINT (12 34)', 'LINESTRING (0 0, 1 1, 2 1, 2 2)'],
        'value': [1, 2]}
df = pd.DataFrame(data)

# Convert DataFrame to GeoDataFrame with an EPSG code for CRS
gdf = convert_df_to_gdf(df, CRS='EPSG:4326')
```

Note:
The 'wkt' module from 'shapely' needs to be imported to convert geometries from WKT.
```

## Function: match_crop

```
match_crop(abb: unknown, add_wheat: unknown)

Converts agricultural abbreviations to a string of crop names, with an option to insert 'Wheat' at specified 
intervals. The function interprets abbreviations where 'B' stands for Soybean, 'C' for Maize, 'P' for Pasture, 
'U' for Developed areas, 'T' for Wetlands, 'F' for Forest, and 'R' for Other crops.

This function takes an abbreviation string representing a sequence of crops and optionally inserts 'Wheat' into 
the sequence at predetermined positions. It handles special cases where the abbreviation matches certain 
patterns, returning None for these cases.

Parameters:
- abb (str): The abbreviation string representing a sequence of crops. Each character stands for a specific crop:
    'C' for Maize,
    'B' for Soybean,
    'W' for Wheat,
    'P' for Tropical Pasture.
  Characters 'U', 'R', 'T', and 'F' are ignored and removed from the abbreviation.
- add_wheat (bool, optional): If True, 'Wheat' is inserted at positions 1, 3, 5, 7, 9, and 11 in the sequence. Defaults to None, which means 'Wheat' is not added.

Returns:
- str or None: A comma-separated string of crop names based on the abbreviation. Returns None if the abbreviation matches special cases 'TTTTTT' or 'UUUUUUU'.

Example:
```
# Convert abbreviation to crop names with additional 'Wheat'
crop_sequence = match_crop("CBWP", add_wheat=True)
print(crop_sequence)
# Output: "Maize,Wheat,Soybean,Wheat,Wheat,Tropical Pasture"

# Convert abbreviation without adding 'Wheat'
crop_sequence = match_crop("CBWP")
print(crop_sequence)
# Output: "Maize,Soybean,Wheat,Tropical Pasture"
```

Note:
- The function returns None for special case abbreviations 'TTTTTT' and 'UUUUUUU' as an indication of non-standard sequences that should not be processed.
- The insertion of 'Wheat' at specified positions assumes the sequence is long enough to accommodate these insertions. If the sequence is shorter, 'Wheat' will only be inserted up to the length of the sequence.
```

# Module: run_utils

## Function: _read_simulation

```
_read_simulation(datastore: unknown, report_name: unknown)

returns all data frame the available report tables
```

## Function: run

```
run(named_tuple_data: unknown, clean: unknown, multithread: unknown, read_db: unknown)

Run apsimx model in the simulations

Parameters
----------
simulations (__str_), optional
    List of simulation names to run, if `None` runs all simulations, by default `None`.
clean (_-boolean_), optional
    If `True` remove existing database for the file before running, deafults to False`
multithread, optional
    If `True` APSIM uses multiple threads, by default `True`
```

## Function: run_model

```
run_model(path: unknown)

:param path: path to apsimx file
:return: none
```

## Function: read_simulation

```
read_simulation(datastore: unknown, report_name: unknown)

returns all data frame from the available report tables
```

# Module: spat

## Function: create_fishnet1

```
create_fishnet1(pt: unknown, lon_step: unknown, lat_step: unknown, ncores: unknown, use_thread: unknown)

Args:
    pt: shape or point feature class layer
    lon_step: height of the polygon
    lat_step: width of the polygon
    ncores: number of cores to use
    use_thread: if True, threads will be used if false processes will be used
    **kwargs: use key word Return = gdf to return geponadas data frame otherwise if not supplied to will retrun an arrya

Returns: an array or geopandas data frame
```

# Module: spatial

## Function: create_fishnet1

```
create_fishnet1(pt: unknown, lon_step: unknown, lat_step: unknown, ncores: unknown, use_thread: unknown)

Args: pt: shape or point feature class layer lon_step: height of the polygon lat_step: width of the polygon
ncores: number of cores to use use_thread: if True, threads will be used if false processes will be used
**kwargs: use key word Return = gdf to return GeoPandas data frame: this is show polygon coordinates otherwise if
not supplied to will returun an array

Returns: an array or geopandas data frame
```

## Function: generate_random_points

```
generate_random_points(pt: unknown, resolution: unknown, ncores: unknown, num_points: unknown)

Args:
    pt: shape file
    resolution: resolution in meters
    ncores: number of cores to use
    num_points: number of points to sample in each grid

Returns:
```

## Function: create_apsimx_sim_files

```
create_apsimx_sim_files(wd: unknown, model: unknown, iterable: unknown)

Creates copies of a specified APSIM model file for each element in the provided iterable,
renaming the files to have unique identifiers based on their index in the iterable.
The new files are saved in the specified working directory.

Args:
wd (str): The working directory where the new .apsimx files will be stored.
model (str): The path to the .apsimx model file that will be copied.
iterable (iterable): An iterable (e.g., list or range) whose length determines the number of copies made.

Returns:
dict: A dictionary where keys are indices from 0 to len(iterable)-1 and values are paths to the newly created .apsimx files.

The function performs the following steps:
1. Extracts the basename of the model file, removing the '.apsimx' extension to create a model suffix.
2. Iterates over the `iterable`, creating a unique file name for each element by appending an index and '.apsimx' to the model suffix.
3. Copies the original model file to the new file name in the specified working directory.
4. Returns a dictionary mapping each index to the file path of the created .apsimx file.

Example:
>>wd = '/path/to/working/directory'
>> model = '/path/to/original/model.apsimx'
>> file_paths = create_apsimx_files(wd, model, range(5))
>> print(file_paths)
{0: '/path/to/working/directory/model_0.apsimx', 1: '/path/to/working/directory/model_1.apsimx', ...}
```

## Function: download_weather

```
download_weather(df: unknown, start: unknown, end: unknown, use_thread: unknown, ncores: unknown, replace_soils: unknown)

   downloads and replace soil or weather files or both in parallel or threads
Args:
    replace_soils: Set this to true to simulataneoursly downloand and replace soils
    df: data frame generated by 'create_apsimx_sim_files'
    start: start year of the simulation
    end:  end year of the simulation
    use_thread: if true threading will take place otherwise multiprocessing
    ncores: number of cores to use
kwargs:
  verbose: bool, Set to True print current step
  thickness_values: list defining the soil layer thickness
  report : set to true to return results
  report_names; provide the required table names from apsimx model report
Returns:
```

## Function: create_and_run_sim_objects

```
create_and_run_sim_objects(wd: unknown, shp_file: unknown, resolution: unknown, num_points: unknown, model_file: unknown, reports_names: unknown, cores: unknown)

Args:
    wd: working directory
    shp_file: shape file of the target area
    model_file: APSIM model string path
    reports_names:str or list names of the data in the simulation model
    **kwargs:
       Test: bool. set to true to try out 10 sample before simulation
       run_process: set too false to run in parallel
       select_process; set too False to use multiple process
       'replace_weather'

:param shp_file:
:param resolution:int. square qrid resolution
:param num_points:int for random sampling
```

# Module: utils

## Method: KeyValuePair.delete_simulation_files

```
delete_simulation_files(path: unknown, patterns: unknown)

:param path: path where the target files are located
:param patterns: a list of different file patterns to delete
:return: none
```

## Method: KeyValuePair.get_data_element

```
get_data_element(data: unknown, column_names: unknown, indexid: unknown)

_summary_

Args:
    data (_array or dataframe_): _description_
    column_names (_type_): _columns name in n dimensional array
    
    indexid (_type_): index of the data to return

Raises:
    ValueError: _erros if the column is not in the data

Returns:
    data corresponding to the index id or position in the array
```

## Method: KeyValuePair.organize_crop_rotations

```
organize_crop_rotations(arrr: unknown)

_summary_

Args:
    arrr (array_): _description_

Returns:
    return concatenated crop rotation names
```

## Method: KeyValuePair.split_and_replace

```
split_and_replace(data: unknown)

Replaces rows in the 'CropRotatn' column of the input structured array ('data')
with calculated values based on a mapping ('crop_mapping').

Parameters:
    data (numpy structured array): A structured array with a 'CropRotatn' column.

Returns:
    numpy array: A new column containing calculated values for rows that do not meet the condition,
                 and 'none' for rows that meet the condition.
```

## Method: KeyValuePair.Cache

```
Cache(func: unknown)

This is a function decorator for class attributes. It just remembers the result of the FIRST function call
and returns this from there on.
```

## Method: KeyValuePair.collect_runfiles

```
collect_runfiles(path2files: unknown, pattern: unknown)

_summary_

Args:
    path2files (_type_): path to the apsimx or database file_
    pattern (str, optional) or lists of strings: file pattern. Defaults to "*.apsimx".

Returns:
    _type_: _description_
```

## Method: KeyValuePair.decreasing_exponential_function

```
decreasing_exponential_function(x: unknown, a: unknown, b: unknown)

Compute the decreasing exponential function y = a * e^(-b * x).

Parameters:
    x (array-like): Input values.
    a (float): Amplitude or scaling factor.
    b (float): Exponential rate.

Returns:
    numpy.ndarray: The computed decreasing exponential values.
```

## Method: KeyValuePair.filter_df

```
filter_df(df: unknown)

Filter a DataFrame based on values in specified columns.

Args:
    df (pd.DataFrame): The DataFrame to be filtered.
    **kwargs: Keyword arguments where the key is the column name and the value is the value to filter on.

Returns:
    pd.DataFrame: The filtered DataFrame.

Example:
    filtered_df = filter_dataframe(df, Age=30, City='Los Angeles')
```

## Method: KeyValuePair.convert_df_to_gdf

```
convert_df_to_gdf(df: unknown, CRS: unknown)

Converts a pandas DataFrame to a GeoPandas GeoDataFrame with specified CRS.

This function assumes that the input DataFrame contains a column named 'geometry'
with WKT (Well-Known Text) representations of geometric objects. It converts these
textual geometry representations into GeoPandas geometry objects and sets the
coordinate reference system (CRS) for the resulting GeoDataFrame.

Parameters:
- df (pandas.DataFrame): The input DataFrame to convert. Must include a 'geometry'
  column with WKT representations of the geometries.
- CRS (str or dict): The coordinate reference system to set for the GeoDataFrame.
  Can be specified as a Proj4 string, a dictionary of Proj parameters, an EPSG
  code, or a WKT string.

Returns:
- gpd.GeoDataFrame: A GeoDataFrame created from the input DataFrame with geometries
  converted from WKT format and the specified CRS.

Example:
```
import pandas as pd
import geopandas as gpd
from shapely import wkt

# Sample DataFrame with WKT geometries
data = {'geometry': ['POINT (12 34)', 'LINESTRING (0 0, 1 1, 2 1, 2 2)'],
        'value': [1, 2]}
df = pd.DataFrame(data)

# Convert DataFrame to GeoDataFrame with an EPSG code for CRS
gdf = convert_df_to_gdf(df, CRS='EPSG:4326')
```

Note:
The 'wkt' module from 'shapely' needs to be imported to convert geometries from WKT.
```

## Method: KeyValuePair.bounding_box_corners

```
bounding_box_corners(center_point: unknown, radius: unknown)

Generates a bounding box around a center point within a specified radius and returns all four corners.

Parameters:
- center_point: tuple of (latitude, longitude)
- radius: radius in meters

Returns:
- A dictionary with the coordinates of the 'north_east', 'south_east', 'south_west', and 'north_west' corners of the bounding box.
```

## Method: WDir.exception_handler

```
exception_handler(re_raise: unknown)

A decorator to handle exceptions with an option to re-raise them.

Args:
re_raise (bool): If True, re-raises the caught exception after logging.
                 If False, logs the exception and suppresses it.
```

## Method: WDir.flatten_nested_list

```
flatten_nested_list(nested_list: unknown, deep: unknown)

this will recursively flatten a nested list
:param nested_list:  to flatten
:return: a list with nested flattened values
```

## Method: WDir.path

```
path(name: unknown)

:param name: name of the new file
:return: realpath for the new file name
```

# Module: evaluator

## Class: Metrics

```
This class is redundant.
These functions can be implemented without the class.
```

## Class: validate

```
supply predicted and observed values for evaluating on the go please see co-current evaluator class
```

## Method: validate.RRMSE

```
RRMSE(actual: unknown, predicted: unknown)

Calculate the root-mean-square error (RRMSE) between actual and predicted values.

Parameters:
- actual: list or numpy array of actual values
- predicted: list or numpy array of predicted values

Returns:
- float: relative root-mean-square error value
```

## Method: validate.WIA

```
WIA(obs: unknown, pred: unknown)

Calculate the Willmott's index of agreement.

Parameters:
- obs: array-like, observed values.
- pred: array-like, predicted values.

Returns:
- d: Willmott's index of agreement.
```

## Method: validate.MSE

```
MSE(actual: unknown, predicted: unknown)

Calculate the Mean Squared Error (MSE) between actual and predicted values.

Args:
actual (array-like): Array of actual values.
predicted (array-like): Array of predicted values.

Returns:
float: The Mean Squared Error (MSE).
```

## Method: validate.mva

```
mva(data: unknown, window: unknown)

Calculate the moving average

Args:
    data: list or array-like
    window: moving window e.g 2

Returns:
```

## Method: validate.ME

```
ME(actual: unknown, predicted: unknown)

Calculate Modeling Efficiency (MEF) between observed and predicted values.

Parameters:
observed (array-like): Array or list of observed values.
predicted (array-like): Array or list of predicted values.

Returns:
float: The Modeling Efficiency (MEF) between observed and predicted values.
```

## Method: validate.__init__

```
__init__(actual: unknown, predicted: unknown)

:param actual (Array): observed values
:param predicted (Array): predicted values
:param metric (str): metric to use default is RMSE
 tip: for metrics use the intellisence on mets class e.g metric = mets.RMSE
```

## Method: validate.evaluate

```
evaluate(metric: str)

:param metric (str): metric to use default is RMSE
:return: returns an index
```

## Method: validate.evaluate_all

```
evaluate_all(verbose: bool)

verbose (bool) will print all the metrics
```

# Module: visual

## Function: plot_data

```
plot_data(x: unknown, y: unknown, plot_type: unknown, xlabel: unknown, ylabel: unknown)

Plot data points.

Parameters:
x (list or array-like): X-axis data.
y (list or array-like): Y-axis data.
plot_type (str): Type of plot ('line', 'scatter', 'bar', 'hist', 'box', 'pie').
```

# Module: visual

## Function: conditional_entropy

```
conditional_entropy(x: List[Union[int, float]], y: List[Union[int, float]])

Calculates conditional entropy 
```

## Function: theil_u

```
theil_u(x: List[Union[int, float]], y: List[Union[int, float]])

Calculate Theil U 
```

## Function: get_theils_u_for_df

```
get_theils_u_for_df(df:  )

Compute Theil's U for every feature combination in the input df 
```

