

apsimNGpy: parallel simulation module
====================================================================

This library is used to run or read apsim simulation in parallelel including downloading and organizing soil tables


.. _Requirements

Requirements
*****************************************
apsimNGpy installed on your system

Main methods
*****************************************************

- run_apsimxfiles_in_parallel

  runs the .apsim files. the files can be supplied as a list or use the utils module method called collect_runfiles, 
  which returns an iterator of file apths supplied to the paraleld simulation methods.

- read_result_in_parallel.

 This reads the simulated output data 

- download_soil_tables

  Evidently, this method downloads soil data from SSURGO and transforms it into the necessary APSIM soil profiles. It necessitates passing an iterable of lonlat coordinates and returns an iterator indexed by their lonlat positions.

************************

.. _Usage:


Usage
**********************************************************************************************************************************************

.. code:: python


    from apsimNGpy.parallel.process import run_apsimxfiles_in_parallel, read_result_in_parallel
    from apsimNGpy.utililies.utils import collect_runfiles
    from pathlib import Path
    hd = Path.home()
    os.chdir(hd)
    from apsimNGpy.base.base_data import load_example_files
    # let's copy two files here
    data = load_example_files(hd)
    maize = data.get_maize
    nt_maize = data.get_maize_no_till
    # that is it all these files are now in the directory
    files = collect_runfiles(path2files=hd, pattern=["*.apsimx"])
    if __name__ == "__main__": # It's important to protect the script with this statement, especially given that we are working with file operations, as spawning processes can potentially result in file permission errors.
        # run all simulation files collected
        run_apsimxfiles_in_parallel(files, ncores=10,use_threads=False)
        # files is an iterable or a generator
        # ncores is the number of processes or threads to use and use_threads will determine whether we use threads or not
        # returns nothing
        rpath = os.path.realpath(hd)
        # we can now read the results using the .db path as follow
        files_db = collect_runfiles(path2files=rpath, pattern=["*.db"])
        dat = read_result_in_parallel(files_db, ncores=10)
        # return a generator object
        df = pd.concat(dat)
        print(df)


download_soil_tables Function Documentation
***************************************************************************************************

Description
***********

The `download_soil_tables` function is used to download soil data from SSURGO and convert it into the required APSIM soil profiles. It takes an iterable of lonlat coordinates and returns a dictionary containing calculated soil profiles with corresponding index positions.

Parameters
**********************

- `iterable` (Iterable): An iterable containing lonlat coordinates as tuples or lists.
- `use_threads` (bool, optional): If `True`, the function uses threads for parallel processing; otherwise, it uses processes. Default is `False`.
- `ncores` (int, optional): The number of CPU cores to use for parallel processing. If not provided, it uses 40% of available CPU cores. Default is `None`.
- `soil_series` (None, optional): [Insert description if applicable.]

## Returns
- A genratr object with dictionary where the keys are index positions from the lonlat coordinates and the values are the corresponding calculated soil profiles.



# Example usage of download_soil_tables function
***********************************************************

.. code:: python


    from apsimNGpy.parallel.process import download_soil_tables

    lonlat_coords = [(x1, y1), (x2, y2), ...]  # Replace with actual lonlat coordinates
    if __name__ == "__main__":
        # Using threads for parallel processing
        soil_profiles = download_soil_tables(lonlat_coords, use_threads=True, ncores=4)

        # Iterate through the results
        for sp in soil_profiles:
            for index, profile in sp.items():
                print(f"Lonlat Index: {index}, Soil Profile: {profile}")

Notes
*****************
- When using threads (use_threads=True), the function utilizes ThreadPoolExecutor for parallel processing.
- When not specifying the number of cores (ncores=None), the function uses 40% of available CPU cores.
- The function provides progress information while downloading soil tables.
- It's recommended to handle any exceptions that may occur during execution.

run_apsimxfiles_in_parallel Function
************************************

Description
****************************************
The `run_apsimxfiles_in_parallel` function is designed for executing APSIMX simulation files in parallel. It accepts a list of APSIMX simulation files, the number of cores or threads to use for parallel processing, and an optional flag to specify whether to use threads or processes for parallel execution. It efficiently handles the execution of APSIMX files in parallel, making it suitable for running multiple simulations simultaneously.

Function Signature
**********************


.. code:: python


    run_apsimxfiles_in_parallel(iterable_files, ncores, use_threads=False)

Parameters
**************************************

- iterable_files (list): A list of APSIMX simulation files to be executed in parallel.
- ncores (int): The number of CPU cores or threads to use for parallel processing.
- use_threads (bool, optional): If set to True, the function uses thread pool execution. If set to False, it utilizes process poo 

Removing Duplicates
*********************************
The function automatically removes duplicate files from the input list to prevent race conditions in parallel computing.

Usage Examples
*********************************************
Usage Examples
*********************************************

.. code:: python


    # Example usage of run_apsimxfiles_in_parallel function
    from apsimNGpy.parallel.process import run_apsimxfiles_in_parallel

    simulation_files = ["file1.apsimx", "file2.apsimx", ...]  # Replace with actual file names
    # alternatively use colect_runfile function from util modules

    # Using processes for parallel execution
    run_apsimxfiles_in_parallel(simulation_files, ncores=4, use_threads=False)

    # Using threads for parallel execution
    run_apsimxfiles_in_parallel(simulation_files, ncores=4, use_threads=True)


Notes
************************
- When using threads (use_threads=True), the function employs ThreadPoolExecutor for parallel processing.
- When not specifying the number of cores (ncores), the function will run simulations using the available CPU cores or threads.
- The function provides progress information while running APSIMX files, including the percentage completion.
- Execution time and the number of files processed are displayed at the end.
- Feel free to integrate this function into your APSIM simulation workflow to execute multiple simulation files concurrently and save valuable time.
- read_result_in_parallel takes the same argument and returns an iterators of the results from each sitmulation database see quick implimentation above. It also takes in file with .db extension as the iterable

