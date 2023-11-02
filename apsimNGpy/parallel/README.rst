

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
  Apparently, this methods downloads soil table from SSURGO and convert them to apsim soil provide. it requires apsing an iterbale of lonlat

************************

.. _Usage:


Usage
*********************************************************************************


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
    if __name__ == "__main__": # need to guard the script with this statement, especially since we are dealing with 
           #reading and writing files spawning processes can lead file permission errors
        # run all simulation files collected
        run_apsimxfiles_in_parallel(files, ncores=10,use_threads=False)
        # files is an iterable or a generator
        # ncores is the numbe rof process or threads to use and use_threads will determine wthere we use threads or not
        # returns nothing
        rpath = os.path.realpath(hd)
        # we can now read the results using the .db path as follow
        files_db = collect_runfiles(path2files=rpath, pattern=["*.db"])
        dat = read_result_in_parallel(files_db, ncores=10)
        # return a generator object
        df = pd.concat(dat)
        print(df)

