upgrade_apsim_file Class: API Reference
---------------------------------

Upgrade a file to the latest version of the .apsimx file format without running the file.

Parameters
---------------
:param file: file to be upgraded to the newest version
:param verbose: Write detailed messages to stdout when a conversion starts/finishes.
:return:
   The latest version of the .apsimx file with the same name as the input file
Example:
    >>> from apsimNGpy.core.base_data import load_default_simulations
    >>> filep =load_default_simulations(simulations_object= False)# this is just an example perhaps you need to pass a lower verion file because this one is extracted from thecurrent model as the excutor
    >>> upgrade_file =upgrade_apsim_file(filep, verbose=False)
collect_csv_by_model_path Class: API Reference
----------------------------------------

Collects the data from the simulated model after run
    
run_model_externally Class: API Reference
-----------------------------------

Runs an APSIM model externally, ensuring cross-platform compatibility.

Although APSIM models can be run internally, compatibility issues across different APSIM versions—
particularly with compiling manager scripts—led to the introduction of this method.

:param model: (str) Path to the APSIM model file or a filename pattern.
:param verbose: (bool) If True, prints stdout output during execution.
:param to_csv: (bool) If True, write the results to a CSV file in the same directory.
:returns: A subprocess.Popen object.

Example:
    >>> result =run_model_externally("path/to/model.apsimx", verbose=True, to_csv=True)
    >>> from apsimNGpy.core.base_data import load_default_simulations
    >>> path_to_model = load_default_simulations(crop ='maize', simulations_object =False)
    >>> pop_obj = run_model_externally(path_to_model, verbose=False)
    >>> pop_obj1 = run_model_externally(path_to_model, verbose=True)# when verbose is true, will print the time taken
run_from_dir Class: API Reference
---------------------------

This function acts as a wrapper around the APSIM command line recursive tool, automating
the execution of APSIM simulations on all files matching a given pattern in a specified
directory. It facilitates running simulations recursively across directories and outputs
the results for each file are stored to a csv file in the same directory as the file'.

What this situation does is that it makes it easy to retrieve the simulated files, returning a generator that
yields data frames

:Parameters:
__________________
:param dir_path: (str or Path, required). The path to the directory where the
    simulation files are located.
:param pattern: (str, required): The file pattern to match for simulation files
    (e.g., "*.apsimx").
:param recursive: (bool, optional):  Recursively search through subdirectories for files
    matching the file specification.
:param write_tocsv: (bool, optional): specify whether to write the
    simulation results to a csv. if true, the exported csv files bear the same name as the input apsimx file name
    with suffix reportname.csv. if it is false,
   - if verbose, the progress is printed as the elapsed time and the successfully saved csv

:returns
 -- a generator that yields data frames knitted by pandas


Example:
   >>> mock_data = Path.home() / 'mock_data'# As an example let's mock some data move the apsim files to this directory before runnning
   >>> mock_data.mkdir(parents=True, exist_ok=True)
   >>> from apsimNGpy.core.base_data import load_default_simulations
   >>> path_to_model = load_default_simulations(crop ='maize', simulations_object =False) # get base model
   >>> ap =path_to_model.replicate_file(k=10, path= mock_data)  if not list(mock_data.rglob("*.apsimx")) else None

   >>> df = run_from_dir(str(mock_data), pattern="*.apsimx", verbose=True, recursive=True)# all files that matches that pattern
