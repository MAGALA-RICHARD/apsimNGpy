import os.path
import platform
from pathlib import Path
from subprocess import *
from typing import Dict, Any, Union
import contextlib
import pandas as pd
from functools import lru_cache
from apsimNGpy.core.config import get_apsim_bin_path
from apsimNGpy.settings import logger
from apsimNGpy.core_utils.utils import timer
import contextlib
from apsimNGpy.settings import *
apsim_bin_path = Path(get_apsim_bin_path())

# Determine executable based on OS
if platform.system() == "Windows":
    APSIM_EXEC = apsim_bin_path / "Models.exe"
else:  # Linux or macOS
    APSIM_EXEC = apsim_bin_path / "Models"


def get_apsim_version(verbose:bool=False):
    """ Display version information of the apsim model currently in the apsimNGpy config environment.

    ``verbose``: (bool) Prints the version information ``instantly``

    Example::

            apsim_version = get_apsim_version()

    """
    cmd = [APSIM_EXEC, '--version']
    if verbose:
        cmd.append("--verbose")
    res = Popen(cmd, stdout=PIPE, stderr=PIPE, text=True)
    res.wait()
    return res.stdout.readlines()[0].strip()


def upgrade_apsim_file(file: str, verbose:bool=True):
    """
    Upgrade a file to the latest version of the .apsimx file format without running the file.

    Parameters
    ---------------
    ``file``: file to be upgraded to the newest version

    ``verbose``: Write detailed messages to stdout when a conversion starts/finishes.

    ``return``
       The latest version of the .apsimx file with the same name as the input file

    Example::

        from apsimNGpy.core.base_data import load_default_simulations
        filep =load_default_simulations(simulations_object= False)# this is just an example perhaps you need to pass a lower verion file because this one is extracted from thecurrent model as the excutor
        upgrade_file =upgrade_apsim_file(filep, verbose=False)

    """
    file = str(file)
    assert os.path.isfile(file) and file.endswith(".apsimx"), f"{file} does not exists a supported apsim file"
    cmd = [APSIM_EXEC, file, '--upgrade']
    if verbose:
        cmd.append('--verbose')
    res = Popen(cmd, stdout=PIPE, stderr=PIPE, text=True)
    outp, err = res.communicate()
    if err:
        print(err)
    if verbose:
        print(outp)
    if res.returncode == 0:
        return file


def run_model_externally(model: Union[Path, str], verbose: bool = False, to_csv:bool=False) -> Popen[str]:
    """
    Runs an ``APSIM`` model externally, ensuring cross-platform compatibility.

    Although ``APSIM`` models can be run internally, compatibility issues across different APSIM versions—
    particularly with compiling manager scripts—led to the introduction of this method.

    ``model``: (str) Path to the ``APSIM`` model file or a filename pattern.

    ``verbose``: (bool) If ``True``, prints stdout output during execution.

    ``to_csv``: (bool) If ``True``, write the results to a CSV file in the same directory.

    ``returns``: A subprocess.Popen object.

    Example::

        result =run_model_externally("path/to/model.apsimx", verbose=True, to_csv=True)
        from apsimNGpy.core.base_data import load_default_simulations
        path_to_model = load_default_simulations(crop ='maize', simulations_object =False)
        pop_obj = run_model_externally(path_to_model, verbose=False)
        pop_obj1 = run_model_externally(path_to_model, verbose=True)# when verbose is true, will print the time taken
    """

    apsim_file = model  # Define the APSIMX file path
    cmd = [str(APSIM_EXEC), str(apsim_file), '--verbose']

    if to_csv:
        cmd.append('--csv')

    with contextlib.ExitStack() as stack:
        result = stack.enter_context(Popen(cmd, stdout=PIPE, stderr=PIPE, text=True))

        try:
            out, err = result.communicate()

            if err:
                logger.error(err.strip())
            if verbose:
                logger.info(f"{repr(out.strip())}, output from {apsim_file}")

            return result
        finally:
            if result.poll() is None:  # Ensures the process is properly killed
                result.kill()


from pathlib import Path
from typing import Union, List

@lru_cache(maxsize=20)
def get_matching_files(dir_path: Union[str, Path], pattern: str, recursive: bool = False) -> List[Path]:
    """
    Search for files matching a given pattern in the specified directory.

    Args:
        ``dir_path`` (Union[str, Path]): The directory path to search in.
        ``pattern`` (str): The filename pattern to match (e.g., "*.apsimx").
        ``recursive`` (bool): If True, search recursively; otherwise, search only in the top-level directory.

    Returns:
        List[Path]: A ``list`` of matching Path objects.

    Raises:
        ``ValueError:`` If no matching files are found.
    """
    global_path = Path(dir_path)
    if recursive:
        matching_files = list(global_path.rglob(pattern))
    else:
        matching_files = list(global_path.glob(pattern))

    if not matching_files:
        raise FileNotFoundError(f"No files found that matched pattern: {pattern} in directory: {dir_path}")

    return matching_files


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

def collect_csv_from_dir(dir_path, pattern, recursive=False) -> (pd.DataFrame):
    """Collects the csf=v files in a directory using a pattern, usually the pattern resembling the one of the simulations used to generate those csv files
    ``dir_path``: (str) path where to look for csv files
    ``recursive``: (bool) whether to recursively search through the directory defaults to false:
    ``pattern``:(str) pattern of the apsim files that produced the csv files through simulations

    returns
        a generator object with pandas data frames

    Example::

         mock_data = Path.home() / 'mock_data' # this a mock directory substitute accordingly
         df1= list(collect_csv_from_dir(mock_data, '*.apsimx', recursive=True)) # collects all csf file produced by apsimx recursively
         df2= list(collect_csv_from_dir(mock_data, '*.apsimx',  recursive=False)) # collects all csf file produced by apsimx only in the specified directory directory


    """
    global_path = Path(dir_path)
    if recursive:
        matching_apsimx_patterns = global_path.rglob(pattern)
    else:
        matching_apsimx_patterns = global_path.glob(pattern)
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


def run_from_dir(dir_path, pattern, verbose=False,
                 recursive=False,  # set to false because the data collector is also set to false
                 write_tocsv=True) -> [pd.DataFrame]:
    """
       This function acts as a wrapper around the ``APSIM`` command line recursive tool, automating
       the execution of APSIM simulations on all files matching a given pattern in a specified
       directory. It facilitates running simulations recursively across directories and outputs
       the results for each file are stored to a csv file in the same directory as the file'.

       What this function does is that it makes it easy to retrieve the simulated files, returning a generator that
       yields data frames

       :Parameters:
       __________________
       ``dir_path``: (str or Path, required). The path to the directory where the
           simulation files are located.
       ``pattern``: (str, required): The file pattern to match for simulation files
           (e.g., "*.apsimx").
       ``recursive``: (bool, optional):  Recursively search through subdirectories for files
           matching the file specification.
       ``write_tocsv``: (bool, optional): specify whether to write the
           simulation results to a csv. if true, the exported csv files bear the same name as the input apsimx file name
           with suffix reportname.csv. if it is ``False``,
          - if ``verbose``, the progress is printed as the elapsed time and the successfully saved csv

       ``returns``
        -- a ``generator`` that yields data frames knitted by pandas


       Example::

            mock_data = Path.home() / 'mock_data'  # As an example, let's mock some data; move the APSIM files to this directory before running
            mock_data.mkdir(parents=True, exist_ok=True)

            from apsimNGpy.core.base_data import load_default_simulations
            path_to_model = load_default_simulations(crop='maize', simulations_object=False)  # Get base model

            ap = path_to_model.replicate_file(k=10, path=mock_data) if not list(mock_data.rglob("*.apsimx")) else None

            df = run_from_dir(str(mock_data), pattern="*.apsimx", verbose=True, recursive=True)  # All files that match the pattern


       """
    dir_path = str(dir_path)

    dir_patern = f"{dir_path}/{pattern}"
    base_cmd = [str(APSIM_EXEC), str(dir_patern)]
    if recursive:
        base_cmd.append('--recursive')
    if verbose:
        base_cmd.append('--verbose')
    if write_tocsv:
        base_cmd.append('--csv')
    ran_ok = False
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

@lru_cache(maxsize=None)
def apsim_executable(path, *args):
    base  = [str(APSIM_EXEC), str(path), '--verbose', '--csv']
    return base

def run_p(path):
    run(apsim_executable(path))


if __name__ == "__main__":
    import doctest
# doctest.testmod()
