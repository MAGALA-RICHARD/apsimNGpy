import os.path
import platform
from pathlib import Path
from subprocess import *
from typing import Dict, Any

import pandas as pd

from apsimNGpy.core.config import get_apsim_bin_path
from apsimNGpy.settings import logger
from apsimNGpy.core_utils.utils import timer
import contextlib
apsim_bin_path = Path(get_apsim_bin_path())

# Determine executable based on OS
if platform.system() == "Windows":
    apsim_exe = apsim_bin_path / "Models.exe"
else:  # Linux or macOS
    apsim_exe = apsim_bin_path / "Models"

import subprocess
import contextlib
from subprocess import Popen, PIPE


def run_model_externally(model, verbose: bool = False, to_csv=False) -> Popen[str]:
    """Runs an APSIM model externally, ensuring cross-platform compatibility.
    returns a Popen object
    Example:

        >>> from apsimNGpy.core.base_data import load_default_simulations
        >>> path_to_model = load_default_simulations(crop ='maize', simulations_object =False)
        >>> pop = run_model_externally(path_to_model, verbose=False)
        >>> pop = run_model_externally(path_to_model, verbose=True)# when verbose is true, will print the time taken
    """

    apsim_file = model  # Define the APSIMX file path
    cmd = [str(apsim_exe), str(apsim_file), '--verbose']

    if to_csv:
        cmd.append('--csv')

    with contextlib.ExitStack() as stack:
        result = stack.enter_context(Popen(cmd, stdout=PIPE, stderr=PIPE, text=True))

        try:
            out, err = result.communicate()

            if err:
                logger.error(err.strip())
            if verbose:
                logger.info(f"{out.strip()}, output from {apsim_file}")

            return result
        finally:
            if result.poll() is None:  # Ensures the process is properly killed
                result.kill()


@timer
def collect_csv_by_model_path(model_path) -> dict[Any, Any]:
    """Collects the data from the simulated model after run
    """
    ab_path = Path(os.path.abspath(model_path))

    dirname = ab_path.parent
    name = ab_path.stem

    csv_files = list(dirname.glob(f"*{name}*.csv"))
    if csv_files:
        stems = [s.stem.split('.')[-1] for s in csv_files]
        report_paths = {k: v for k, v in zip(stems, csv_files)}

    else:
        report_paths = {}
    return report_paths


def collect_csv_from_dir(dir_path, pattern)-> (pd.DataFrame):
    """Collects the the csf files in a directory
    @param dir_path: path where to look for csv files
    @param pattern: pattern of the apsim files that produced the csv files through simulations
    @ returnsa generator object with pandas data frames
    Example:
     >>> mock_data = Path.home() / 'mock_data' # this a mock directory substitute accordingly
     >>> df= list(collect_csv_from_dir(mock_data, '*.apsimx')) # collects all csf file produced by apsimx


    """
    global_path = Path(dir_path)
    matching_apsimx_patterns = global_path.rglob(pattern)
    if matching_apsimx_patterns:
        for file_path in matching_apsimx_patterns:

            # Strip the '.apsimx' extension and prepare to match CSV files
            base_name = str(file_path.stem)

            # Search for CSV files in the same directory as the original file
            for csv_file in global_path.rglob(f"*{base_name}*.csv"):
                file = csv_file.with_suffix('.csv')
                if file.is_file():
                    df = pd.read_csv(file)
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        yield df
                    else:  # notify potential issue
                        logger.warning(f"{base_name} is not a csv file or itis empty")



def run_from_dir(dir_path, pattern, verbose=False, write_tocsv=True) -> [pd.DataFrame]:
    """
       This function acts as a wrapper around the APSIM command line recursive tool, automating
       the execution of APSIM simulations on all files matching a given pattern in a specified
       directory. It facilitates running simulations recursively across directories and outputs
       the results for each file are stored to a csv file in the same directory as the file'.

       What this situation does is that it makes it easy to retrieve the simulated files, returning a generator that
       yields data frames

       @Parameters:
       __________________________________________________________________
       - dir_path (str or Path): The path to the directory where the simulation files are located.
       - pattern (str): The file pattern to match for simulation files (e.g., "*.apsimx").

       The function constructs a command to execute APSIM simulations using the provided directory
       path and file pattern. It adds flags for recursive search, verbosity, and output formatting.
       The results of the simulations are directed to csf files in the directory
       where the command is executed.

       It then waits for the process to complete and checks the process status. If the process
       is still running due to any interruptions or errors, it terminates the process to avoid
       hanging or resource leakage.


       @returns
        --a generator that yields data frames knitted by pandas


       Example:
          >>> mock_data = Path.home() / 'mock_data'# As an example let's mock some data move the apsim files to this directory before runnning
          >>> mock_data.mkdir(parents=True, exist_ok=True)
          >>> from apsimNGpy.core.base_data import load_default_simulations
          >>> path_to_model = load_default_simulations(crop ='maize', simulations_object =False) # get base model
          >>> ap =path_to_model.replicate_file(k=10, path= mock_data)  if not list(mock_data.rglob("*.apsimx")) else None

          >>> df = run_from_dir(str(mock_data), pattern="*.apsimx", verbose=True)# all files that matches that pattern


       """
    dir_path = str(dir_path)

    dir_patern = f"{dir_path}/{pattern}"
    base_cmd = [str(apsim_exe), str(dir_patern),  '--recursive']
    if verbose:
        base_cmd.append('--verbose')
    if write_tocsv:
        base_cmd.append('--csv')
    ran_ok =False
    with  contextlib.ExitStack() as stack:
        process = stack.enter_context(Popen(base_cmd, stdout=PIPE, stderr=PIPE,
                        text=True))

        try:
            logger.info('waiting for APSIM simulations to complete')
            out, st_err = process.communicate()
            if verbose:
                logger.info(f'{out.strip()}')
            ran_ok = True
        finally:
            if process.poll() is None:
                process.kill()

    if write_tocsv and ran_ok:
        logger.info(f"Loading data into memory.")
        out = collect_csv_from_dir(dir_path, pattern)
        return out

if __name__ == "__main__":
    import doctest
    doctest.testmod()
