

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

## Description
The `download_soil_tables` function is used to download soil data from SSURGO and convert it into the required APSIM soil profiles. It takes an iterable of lonlat coordinates and returns a dictionary containing calculated soil profiles with corresponding index positions.

## Parameters
- `iterable` (Iterable): An iterable containing lonlat coordinates as tuples or lists.
- `use_threads` (bool, optional): If `True`, the function uses threads for parallel processing; otherwise, it uses processes. Default is `False`.
- `ncores` (int, optional): The number of CPU cores to use for parallel processing. If not provided, it uses 40% of available CPU cores. Default is `None`.
- `soil_series` (None, optional): [Insert description if applicable.]

## Returns
- A dictionary where the keys are index positions from the lonlat coordinates and the values are the corresponding calculated soil profiles.

## Example Usage
```python
# Example usage of download_soil_tables function
from your_module import download_soil_tables

lonlat_coords = [(x1, y1), (x2, y2), ...]  # Replace with actual lonlat coordinates

# Using threads for parallel processing
soil_profiles = download_soil_tables(lonlat_coords, use_threads=True, ncores=4)

# Iterate through the results
for index, profile in soil_profiles.items():
    print(f"Lonlat Index: {index}, Soil Profile: {profile}")


