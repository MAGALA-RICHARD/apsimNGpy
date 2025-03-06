import os
from pathlib import Path
import logging
from pathlib import Path
from subprocess import run, CalledProcessError, CompletedProcess, PIPE
import platform

import pandas as pd
from apsimNGpy.settings import logger
from apsimNGpy.core.config import get_apsim_bin_path
from typing import NamedTuple
from apsimNGpy.core.model_loader import load_model_from_dict
from apsimNGpy.utililies.utils import timer
from subprocess import *

logger = logging.getLogger(__name__)
apsim_bin_path = Path(get_apsim_bin_path())

# Determine executable based on OS
if platform.system() == "Windows":
    apsim_exe = apsim_bin_path / "Models.exe"
else:  # Linux or macOS
    apsim_exe = apsim_bin_path / "Models"


def run_model_externally(model, verbose: bool = False) -> Popen[str]:
    """Runs an APSIM model externally, ensuring cross-platform compatibility."""

    # Get the APSIM binary path

    # Define the APSIMX file path
    apsim_file = model
    result = Popen([str(apsim_exe), str(apsim_file), '--verbose'], stdout=PIPE, stderr=PIPE, text=True)
    try:
        if verbose:
            logger.info("APSIM Run Successful!")
            logger.info(result.stdout)  # Print APSIM output
        # logger.info("Errors:", result.stderr)
        result.communicate()
        res, err = result.communicate()

        if err:
            logger.error(err.strip)
        logger.info(res.strip())
        return result
    finally:
        if not result.poll():
            result.kill()


def collect_csv_from_dir(dir_path, pattern):
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
                    else: # notify potential issue
                        logger.warning(f"{base_name} is not a csv file or itis empty")


@timer
def run_from_dir(dir_path, pattern, verbose=False) -> [pd.DataFrame]:
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

       Example:
           _____________________________________________
       ```python
       run_from_dir(dir_path = r"/path/to/apsim/files",  pattern ="*.apsimx")

       @returns
        --a generator that yields data frames knitted by pandas
       ```



       """
    dir_path = str(dir_path)
    dir_patern = f"{dir_path}/{pattern}"

    verbose_flag = {True: '--verbose', False: 'None'}.get(verbose, 'None')

    process = Popen([str(apsim_exe), dir_patern, '--recursive', verbose_flag, '--csv'])

    try:
        logger.info('waiting for APSIM simulations to complete')
        process.wait()
    finally:
        if process.poll() is None:
            process.terminate()
    logger.info(f"Loading data into memory.")
    out = collect_csv_from_dir(dir_path, pattern)
    return out



