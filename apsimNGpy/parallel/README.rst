

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

