from __future__ import annotations

import contextlib
import gc
import os.path
import platform
import sqlite3
import subprocess
import warnings
from functools import lru_cache, cache
from pathlib import Path
from subprocess import *
from subprocess import Popen, PIPE
from typing import Any, Dict, Iterable, List, Optional, Tuple, Hashable
from typing import Mapping
from typing import Union

import pandas as pd
from sqlalchemy.engine import Connection as SAConnection
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from apsimNGpy.core.df_grp import group_and_concat_by_schema
from apsimNGpy.core.pythonet_config import configuration
from apsimNGpy.core_utils.database_utils import read_db_table, get_db_table_names
from apsimNGpy.core_utils.database_utils import write_schema_grouped_tables
from apsimNGpy.exceptions import ApsimRuntimeError
from apsimNGpy.settings import *
from apsimNGpy.core_utils.utils import timer

AUTO = object()
SchemaKey = Tuple[Tuple[Hashable, str], ...]  # ((column_name, dtype_str), ...)


def is_connection(obj):
    """Return True if obj looks like a DB connection."""
    return isinstance(obj, (sqlite3.Connection, SAConnection, Engine, Session))


apsim_bin_path = Path(configuration.bin_path)
print(apsim_bin_path)
# Determine executable based on OS
if platform.system() == "Windows":
    APSIM_EXEC = apsim_bin_path / "Models.exe"
else:  # Linux or macOS
    APSIM_EXEC = apsim_bin_path / "Models"


@cache
def get_apsim_executable(bin_path) -> str:
    bin_path = Path(bin_path)
    # Determine executable based on OS
    if platform.system() == "Windows":
        execU = bin_path / "Models.exe"
    else:  # Linux or macOS
        execU = bin_path / "Models"
    return os.path.realpath(execU)


from System import GC

import subprocess
from pathlib import Path
from typing import Union

from apsimNGpy.settings import logger



AUTO = object()

def run_apsim_by_path(
    model: Union[str, Path],
    *,
    bin_path: Union[str, Path, object] = AUTO,
    timeout: int = 800,
    ncores: int = -1,
    verbose: bool = False,
    to_csv: bool = False,
) -> None:
    """
    Execute an APSIM model safely and reproducibly.

    Parameters
    ----------
    model : str | Path
        Path to the APSIM .apsimx model file.
    bin_path : str | Path | AUTO
        APSIM bin directory. Defaults to configured APSIM path.
    timeout : int
        Maximum execution time in seconds.
    ncores : int
        Number of CPU cores (-1 uses all available).
    verbose : bool
        Enable APSIM verbose output.
    to_csv : bool
        Export APSIM outputs to CSV.

    Raises
    ------
    ApsimRuntimeError
        If APSIM execution fails or times out.
    """

    # Resolve APSIM binary
    if bin_path is AUTO:
        bin_path = configuration.bin_path

    apsim_exec = _ensure_exec(get_apsim_executable(bin_path))
    model_path = _ensure_model(model)

    cmd: list[str] = [
        str(apsim_exec),
        str(model_path),
        "--cpu-count",
        str(ncores),
    ]

    if verbose:
        cmd.append("--verbose")
    if to_csv:
        cmd.append("--csv")

    logger.debug("Executing APSIM command: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,   # we handle errors explicitly
            text=True,
        )

    except subprocess.TimeoutExpired as exc:
        logger.error("APSIM execution timed out after %s seconds", timeout)
        raise ApsimRuntimeError(
            f"APSIM execution exceeded timeout ({timeout}s)"
        ) from exc

    # Log outputs
    if verbose and result.stdout:
        logger.info(result.stdout.strip())

    if result.stderr:
        logger.error(result.stderr.strip())

    # Non-zero return code → failure
    if result.returncode != 0:
        raise ApsimRuntimeError(
            f"APSIM failed (exit code: {result.returncode})\n"
            f"STDERR:\n{result.stderr}\n"
            f"STDOUT:\n{result.stdout}"
        )
    return result


def invoke_csharp_gc():
    GC.Collect()
    GC.WaitForPendingFinalizers()


def get_apsim_version(verbose: bool = False):
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


def upgrade_apsim_file(file: str, verbose: bool = True):
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


class RunError(RuntimeError):
    """Raised when the APSIM external run fails."""


def _ensure_exec(path: Union[str, Path]) -> str:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"APSIM executable not found: {p}")
    if os.name != "nt" and not os.access(p, os.X_OK):
        raise PermissionError(f"APSIM executable not executable: {p}")
    return str(p)


def _ensure_model(path: Union[str, Path]) -> str:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"APSIM model file not found: {p}")
    # Optional: enforce extension
    # if p.suffix.lower() != ".apsimx": raise ValueError(f"Expected .apsimx: {p}")
    return str(p)


@lru_cache(maxsize=None)
def _get_arguments(model: Union[Path, str],
                   *,
                   apsim_exec: Optional[Union[Path, str]] = APSIM_EXEC,
                   verbose: bool = False,
                   to_csv: bool = False,
                   timeout: int = 600,
                   cpu_count=-1,
                   cwd: Optional[Union[Path, str]] = None,
                   env: Optional[Mapping[str, str]] = None):
    exec_path = _ensure_exec(apsim_exec)
    model_path = _ensure_model(model)

    cmd = [exec_path, model_path, '--cpu-count', str(cpu_count)]
    if verbose:
        cmd.append("--verbose")
    if to_csv:
        cmd.append("--csv")

    # capture stderr; capture stdout only if verbose
    stdout_choice = subprocess.PIPE  # if verbose else subprocess.DEVNULL
    return cmd, {'stdout': stdout_choice,
                 'text': True,
                 'shell': False,
                 'timeout': timeout,
                 'encoding': "utf-8",
                 'stderr': subprocess.PIPE,
                 'errors': 'replace'
                 }



def run_model_externally(
        model: Union[Path, str],
        *,
        apsim_bin_path: Optional[Union[Path, str]] = AUTO,
        verbose: bool = False,
        to_csv: bool = False,
        timeout: int = 20,
        cpu_count=-1,
        cwd: Optional[Union[Path, str]] = None,
) -> subprocess.CompletedProcess[str]:
    """
    Run APSIM externally (cross-platform) with safe defaults.

    - Validates an executable and model path.
    - Captures stderr always; stdout only if verbose.
    - Uses UTF-8 decoding with error replacement.
    - Enforces a timeout and returns a CompletedProcess-like object.
    - Does NOT use shell, eliminating injection risk.

    .. seealso::

          Related API: :func:`~apsimNGpy.core.runner.run_from_dir`
    """
    if apsim_bin_path is AUTO:
        apsim_bin_path = configuration.bin_path
    apsim_exec = get_apsim_executable(apsim_bin_path)
    try:
        ar = _get_arguments(model,
                            apsim_exec=apsim_exec,
                            verbose=verbose,
                            to_csv=to_csv,
                            timeout=timeout,
                            cpu_count=cpu_count,
                            cwd=cwd,
                            )
        cmd, others = ar
        proc = subprocess.run(
            cmd, **others
        )
    finally:
        pass
        # clear any external file database locks by using Garbage collector; as a matter of fact, python's gc failed to do the job
        invoke_csharp_gc()

    if verbose and proc.stdout:
        logger.info("APSIM stdout for %s:\n%s", proc.args, proc.stdout.strip())

    # Non-zero exit is treated as failure; caller can relax this if needed
    if proc.returncode != 0:
        logger.error(f"APSIM exited with zero return code: {proc.stdout}\n{proc.stderr}{proc.args}", )
        raise ApsimRuntimeError(
            f"APSIM exited with code {proc.returncode}.\n {proc.stdout} "
        )
    return proc


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
        ``ValueError: `` If no matching files are found.
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


def collect_db_from_dir(dir_path, pattern, recursive=False, tables=None, con=None) -> (pd.DataFrame):
    """Collects the data in a directory using a pattern, usually the pattern resembling the one of the simulations
      used to generate those csv files
    Parameters
    ----------
    dir_path : (str)
       path where to look for csv files
    recursive : (bool)
       whether to recursively search through the directory defaults to false:
    pattern :(str)
        pattern of the apsim files that produced the csv files through simulations
    con: database connection
       database connection object to aggregate the date to from all the simulation

    returns
        a dict generator object with pandas data frames as the values as the schemas as the keys, note the schemas are grouped according to their similarities on
        of data types

    Example::

         mock_data = Path.home() / 'mock_data' # this a mock directory substitute accordingly
         df1= list(collect_csv_from_dir(mock_data, '*.apsimx', recursive=True)) # collects all csf file produced by apsimx recursively
         df2= list(collect_csv_from_dir(mock_data, '*.apsimx',  recursive=False)) # collects all csf file produced by apsimx only in the specified directory directory


    """
    schemas = []
    global_path = Path(dir_path)
    if recursive:
        matching_apsimx_patterns = global_path.rglob(pattern)
    else:
        matching_apsimx_patterns = global_path.glob(pattern)
    if matching_apsimx_patterns:
        # each file has the same collectionID
        for collectionID, file_path in enumerate(matching_apsimx_patterns):

            # Strip the '.apsimx' extension and prepare to match .db files
            base_name = str(file_path.stem)
            db = Path(file_path).with_suffix('.db')
            if tables:
                tables = (tables,) if isinstance(tables, str) else tables

            else:
                tables = set(get_db_table_names(db))
            tabs = [tb for tb in tables if tb in get_db_table_names(db) and not tb.startswith("__")]
            if db.is_file():
                reports = set(get_db_table_names(db))
                if tabs:
                    df = tuple(
                        read_db_table(db, report).assign(source_file=base_name).assign(CollectionID=collectionID) for
                        report in tabs if report in reports)
                    df = pd.concat(df, ignore_index=True)
                    yield df
                else:
                    logging.warning(f"Skipping {file_path} it is empty")


def aggregate_data(dir_path, pattern, recursive=False):
    dfs = collect_db_from_dir(dir_path, pattern, recursive)
    # Example: three schemas among 20 DataFrames

    # A) Group by schema and stack rows within each group
    groups_rows = group_and_concat_by_schema(dfs, axis=0, order_sensitive=False)
    for schema, df_cat in groups_rows.items():
        print("Schema:", schema)  # ((col, dtype), ...)
        print(df_cat.shape)  # concatenated along rows
        # df_cat is a single DataFrame per schema

    # B) Group by schema and concatenate side-by-side (columns) within each group
    groups_cols = group_and_concat_by_schema(dfs, axis=1, order_sensitive=False)
    for schema, df_cat in groups_cols.items():
        print("Schema:", schema)
        print(df_cat.shape)  # concatenated along columns


def _run_from_dir(dir_path, pattern, verbose=False,
                  recursive=False,  # set to false because the data collector is also set to false
                  write_tocsv=False,
                  run_only=False,
                  cpu_count=-1,
                  tables=None, axis=0,
                  order_sensitive=False,
                  add_keys=False,
                  keys_prefix: str = "g",
                  connection: Engine = None
                  ) -> [pd.DataFrame]:
    """
       This function acts as a wrapper around the ``APSIM`` command line recursive tool, automating
       the execution of APSIM simulations on all files matching a given pattern in a specified
       directory. It facilitates running simulations recursively across directories and outputs
       the results for each file are stored to a csv file in the same directory as the file'.

       What this function does is that it makes it easy to retrieve the simulated files, returning a generator that
       yields data frames

       .. warning::

         This function doesn’t clone the input files (unlike: class:`~apsimNGpy.core.apsim.ApsimModel`), so runs started with it cannot be reopened in older APSIM versions


       Parameters
       ____________
       dir_path: (str or Path, required).
          The path to the directory where the simulation files are located.
       pattern: (str, required)
          The file pattern to match for simulation files (e.g., "*.apsimx").
       recursive: (bool, optional)
         Recursively search through subdirectories for files matching the file specification.
       write_tocsv: (bool, optional)
         specify whether to write the simulation results to a csv. if true, the exported csv files bear the same name as the input apsimx file name
           with suffix reportname.csv. if it is ``False``. If ``verbose``, the progress is printed as the elapsed time and the successfully saved csv
       run_only: (bool, optional)
           If True no results are loaded in memory.
       cpu_count: (int, optional)
           No of threads to use for parallel processing of simulations


       :returns:
           generator that yields data frames knitted by pandas if ran_only is False else None


       Example::

            mock_data = Path.home() / 'mock_data'  # As an example, let's mock some data; move the APSIM files to this directory before running
            mock_data.mkdir(parents=True, exist_ok=True)

            from apsimNGpy.core.base_data import load_default_simulations
            path_to_model = load_default_simulations(crop='maize', simulations_object=False)  # Get base model

            ap = path_to_model.replicate_file(k=10, path=mock_data) if not list(mock_data.rglob("*.apsimx")) else None

            df = run_from_dir(str(mock_data), pattern="*.apsimx", verbose=True, recursive=True)  # All files that match the pattern

       .. seealso::

          Related API: :func:`~apsimNGpy.core.runner.run_model_externally`
       """
    dir_path = str(dir_path)

    dir_patern = f"{dir_path}/{pattern}"
    base_cmd = [str(APSIM_EXEC), str(dir_patern), '--cpu-count', str(cpu_count)]
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
            #logger.info('waiting for APSIM simulations to complete')
            process.wait()
            out, st_err = process.communicate()
            if verbose:
                logger.info(f'{out.strip()}')
            if process.returncode != 0:
                logger.info(f"{out}, {st_err}")
            ran_ok = True
        finally:
            if process.poll() is None:
                process.kill()
            invoke_csharp_gc()

    if write_tocsv and ran_ok and not run_only:
        logger.info(f"Loading data into memory.")
        out = collect_csv_from_dir(dir_path, pattern, recursive=recursive)
        return out
    elif not write_tocsv and ran_ok and not run_only:
        out = collect_db_from_dir(dir_path, pattern, recursive=recursive, tables=tables)
        groups = group_and_concat_by_schema(out, axis=axis, order_sensitive=order_sensitive, add_keys=add_keys,
                                            keys_prefix=keys_prefix)
        if connection:
            write_schema_grouped_tables(
                schema_to_df=groups,  # A dict
                engine=connection,
                base_table_prefix="T",
                schema_table_name="_schemas",
            )
        else:
            return groups
    else:
        return process


@lru_cache(maxsize=None)
def apsim_executable(path, *args):
    base = [str(APSIM_EXEC), str(path), '--verbose', '--csv']
    return base


@timer
def run_p(path):
    run(apsim_executable(path))

@timer
def trial_run(self, report_name=None,
              simulations=None,
              clean=False,
              multithread=True,
              verbose=False,
              get_dict=False, **kwargs):
    """
    Run APSIM model simulations.

    Parameters
    ----------
    report_name : str or list of str, optional
        Name(s) of report table(s) to retrieve. If not specified or missing in the database,
        the model still runs and results can be accessed later.

    simulations : list of str, optional
        Names of simulations to run. If None, all simulations are executed.

    clean : bool, default False
        If True, deletes the existing database file before running.

    multithread : bool, default True
        If True, runs simulations using multiple threads.

    verbose : bool, default False
        If True, prints diagnostic messages (e.g., missing report names).

    get_dict : bool, default False
        If True, returns results as a dictionary {table_name: DataFrame}.

    Returns
    -------
    results : DataFrame or list or dict of DataFrames
        Simulation output(s) from the specified report table(s).

    .. seealso::

          Related API: :func:`~apsimNGpy.core.runner.run_model_externally`
    """
    import Models
    invoke_csharp_gc()
    try:
        # Set run type
        runtype = Models.Core.Run.Runner.RunTypeEnum.MultiThreaded if multithread \
            else Models.Core.Run.Runner.RunTypeEnum.SingleThreaded

        # Open and optionally clean the datastore

        if clean:
            self._DataStore.Dispose(True)
            self._DataStore.set_FileName(str(self.datastore))

        # Get simulations to run
        self._DataStore.Open()
        sims = self.find_simulations(simulations) if simulations else self.Simulations
        if simulations:
            cs_sims = List[Models.Core.Simulation]()
            for s in sims:
                cs_sims.Add(s)
            sim = cs_sims
        else:
            sim = sims
        from apsimNGpy.core.pythonet_config import get_apsim_file_reader
        # file = get_apsim_file_reader('file')[Models.Core.Simulations](self.path).Model

        Runner = Models.Core.Run.Runner(self.Simulations.Node.Model)
        Runner.Run()
        # Run the model
        _run_model = Models.Core.Run.Runner(self.path, wait=True)
        # errors = _run_model.Run()
        invoke_csharp_gc()

        # Determine report names
        if report_name is None:
            report_name = get_db_table_names(self.datastore)
            if 'Report' in report_name:
                print('success')
            else:
                print('fail')
            if '_Units' in report_name:
                report_name.remove('_Units')
            if verbose:
                warnings.warn(f"No report name specified. Using detected tables: {report_name}")

        # Read results
        if isinstance(report_name, (list, tuple)):
            if get_dict:
                results = {rep: read_db_table(self.datastore, rep) for rep in report_name}
            else:
                results = [read_db_table(self.datastore, rep) for rep in report_name]
        else:
            if get_dict:
                results = {report_name: read_db_table(self.datastore, report_name)}
            else:
                results = read_db_table(self.datastore, report_name)
    finally:
        self._DataStore.Close()
        invoke_csharp_gc()

    return results


def build_apsim_command(
        dir_path: str,
        pattern: str,
        *,
        cpu_count: int = -1,
        recursive: bool = False,
        verbose: bool = False,
        write_tocsv: bool = False,
) -> List[str]:
    """
    Build the APSIM command-line invocation for all files in a directory
    matching a given pattern.
    """
    dir_pattern = f"{dir_path}/{pattern}"
    cmd = [str(APSIM_EXEC), str(dir_pattern), "--cpu-count", str(cpu_count)]

    if recursive:
        cmd.append("--recursive")
    if verbose:
        cmd.append("--verbose")
    if write_tocsv:
        cmd.append("--csv")

    return cmd


def run_dir_simulations(
        dir_path: str,
        pattern: str,
        *,
        cpu_count: int = -1,
        recursive: bool = False,
        verbose: bool = False,
        write_tocsv: bool = False,
) -> Popen[str]:
    """
    Execute APSIM simulations for all matching files in a directory and wait
    for completion.

    This helper is responsible only for building the command, running it,
    logging output, and ensuring resources are cleaned up. It either completes
    successfully or raises an exception.

    used by: :func:`dir_simulations_to_dfs`, :func:`dir_simulations_to_sql`, :func:`dir_simulations_to_csv`

    Returns
    -------
    process : subprocess.Popen
        The completed APSIM process object.

    Raises
    ------
    RuntimeError
        If APSIM returns a non-zero exit code.
    """
    cmd = build_apsim_command(
        dir_path=dir_path,
        pattern=pattern,
        cpu_count=cpu_count,
        recursive=recursive,
        verbose=verbose,
        write_tocsv=write_tocsv,
    )

    with contextlib.ExitStack() as stack:
        process: Popen[str] = stack.enter_context(
            Popen(cmd, stdout=PIPE, stderr=PIPE, text=True)
        )

        try:
            logger.info("Waiting for APSIM simulations to complete")
            stdout, stderr = process.communicate()
            if verbose and stdout:
                logger.info(stdout.strip())

            if process.returncode != 0:
                logger.error(f"APSIM process failed: {stdout}\n{stderr}")
                raise RuntimeError(
                    f"APSIM exited with code {process.returncode}. "
                    f"Stdout:\n{stdout}\nStderr:\n{stderr}"
                )
        finally:
            # Ensure the process is not left running
            if process.poll() is None:
                process.kill()
            invoke_csharp_gc()

    return process


# -----------------------------------------------------------------------------
# 1) Run and load from CSV
# -----------------------------------------------------------------------------


def dir_simulations_to_csv(
        dir_path: str | Path,
        pattern: str,
        *,
        verbose: bool = False,
        recursive: bool = False,
        cpu_count: int = -1,
) -> Iterable[pd.DataFrame]:
    """
    Run APSIM for all files matching a pattern in a directory and load
    outputs from CSV files into memory.

    APSIM is invoked with the ``--csv`` flag, so reports are written to CSV
    files in the same directories as the input *.apsimx files. This function
    then calls :func:`collect_csv_from_dir` to return the results.

    Parameters
    ----------
    dir_path : str or Path
        Path to the directory containing the simulation files.
    pattern : str
        File pattern to match simulation files (e.g., ``"*.apsimx"``).
    verbose : bool, optional
        If True, log APSIM console output.
    recursive : bool, optional
        If True, search recursively through subdirectories.
    cpu_count : int, optional
        Number of threads to use for APSIM's internal parallel processing.
     What this function does is that it makes it easy to retrieve the simulated files, returning a generator that
       yields data frames

    Returns
    -------
    Iterable[pd.DataFrame]
        (commonly a generator or list of DataFrames, one per report file).

    Raises
    ------
    RuntimeError
        If the APSIM process fails.

    .. seealso::

       :func:`~apsimNGpy.core.runner.dir_simulations_to_dfs`
       :func:`~apsimNGpy.core.runner.dir_simulations_to_sql`
    """
    dir_path = str(dir_path)

    # 1) Run simulations, writing results to CSV
    run_dir_simulations(
        dir_path=dir_path,
        pattern=pattern,
        cpu_count=cpu_count,
        recursive=recursive,
        verbose=verbose,
        write_tocsv=True,
    )

    # 2) Collect results from CSV
    logger.info("Loading CSV results into memory.")
    return collect_csv_from_dir(dir_path, pattern, recursive=recursive)


# -----------------------------------------------------------------------------
# 2) Run and return grouped DataFrames (by schema)
# -----------------------------------------------------------------------------


def dir_simulations_to_dfs(
        dir_path: str | Path,
        pattern: str,
        *,
        verbose: bool = False,
        recursive: bool = False,
        cpu_count: int = -1,
        tables: Optional[List[str], str] = None,
        axis: int = 0,
        order_sensitive: bool = False,
        add_keys: bool = False,
        keys_prefix: str = "g",
) -> Dict[SchemaKey, pd.DataFrame]:
    """
    Run APSIM for all files matching a pattern in a directory, collect results
    from APSIM databases, and return grouped DataFrames based on schema.

    Parameters
    ----------
    dir_path : str or Path
        Path to the directory containing the simulation files.
    pattern : str
        File pattern to match simulation files (e.g., ``"*.apsimx"``).
    verbose : bool, optional
        If True, log APSIM console output.
    recursive : bool, optional
        If True, search recursively through subdirectories.
    cpu_count : int, optional
        Number of threads to use for APSIM's internal parallel processing.
    tables : list of str, optional
        Subset of table names to collect from each APSIM database. If None,
        all tables are collected.
    axis : {0, 1}, optional
        Axis along which to concatenate grouped DataFrames.
    order_sensitive : bool, optional
        If True, column order is part of the schema definition when grouping.
    add_keys : bool, optional
        If True, add keys when concatenating grouped DataFrames.
    keys_prefix : str, optional
        Prefix for keys used when concatenating grouped DataFrames.

     What this function does is that it makes it easy to retrieve the simulated files, returning a dict that
       yields data frames

    Returns
    -------
    dict
        Mapping from schema signatures to concatenated DataFrames. Each key is
        a tuple of (column_name, dtype_str) pairs describing the schema. if all simulations are the same, the key
         is going to be one, as keys and values are filtered according to data types similarities among data frames

    Raises
    ------
    RuntimeError
        If the APSIM process fails.

    .. seealso::

       :func:`~apsimNGpy.core.runner.dir_simulations_to_sql`
       :func:`~apsimNGpy.core.runner.dir_simulations_to_csv`

    """
    dir_path = str(dir_path)

    # 1) Run simulations without --csv (so APSIM writes to its DBs)
    run_dir_simulations(
        dir_path=dir_path,
        pattern=pattern,
        cpu_count=cpu_count,
        recursive=recursive,
        verbose=verbose,
        write_tocsv=False,
    )

    # 2) Collect DB results and group by schema
    logger.info("Loading database results into memory.")
    raw = collect_db_from_dir(dir_path, pattern, recursive=recursive, tables=tables)

    groups: Dict[SchemaKey, pd.DataFrame] = group_and_concat_by_schema(
        raw,
        axis=axis,
        order_sensitive=order_sensitive,
        add_keys=add_keys,
        keys_prefix=keys_prefix,
    )
    return groups


# -----------------------------------------------------------------------------
# 3) Run and write grouped tables + schema to a SQL database
# -----------------------------------------------------------------------------


def dir_simulations_to_sql(
        dir_path: str | Path,
        pattern: str,
        connection: Engine,
        *,
        verbose: bool = False,
        recursive: bool = False,
        cpu_count: int = -1,
        tables: Optional[List[str], str] = None,
        axis: int = 0,
        order_sensitive: bool = False,
        add_keys: bool = False,
        keys_prefix: str = "g",
        base_table_prefix: str = "group",
        schema_table_name: str = "_schemas",
) -> None:
    """
    Run APSIM, collect grouped results from databases, and write the grouped
    tables plus a schema metadata table into a SQL database via the provided database connection.

    Parameters
    ----------
    dir_path : str or Path
        Path to the directory containing the simulation files.
    pattern : str
        File pattern to match simulation files (e.g., ``"*.apsimx"``).
    connection : sqlalchemy.engine.Engine
        SQLAlchemy engine (or compatible) to write tables into.
    verbose : bool, optional
        If True, log APSIM console output.
    recursive : bool, optional
        If True, search recursively through subdirectories.
    cpu_count : int, optional
        Number of threads to use for APSIM's internal parallel processing.
    tables : list of str, optional
        Subset of table names to collect from each APSIM database. If None,
        all tables are collected.
    axis : {0, 1}, optional
        Axis along which to concatenate grouped DataFrames.
    order_sensitive : bool, optional
        If True, column order is part of the schema definition when grouping.
    add_keys : bool, optional
        If True, add keys when concatenating grouped DataFrames.
    keys_prefix : str, optional
        Prefix for keys used when concatenating grouped DataFrames.
    base_table_prefix : str, optional
        Prefix for the generated data table names in SQL.
    schema_table_name : str, optional
        Name of the schema metadata table in SQL.
     What this function does is that it makes it easy to aggregate the simulated files to an SQL database

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        If the APSIM process fails.

    .. seealso::

       :func:`~apsimNGpy.core.runner.dir_simulations_to_dfs`
       :func:`~apsimNGpy.core.runner.dir_simulations_to_csv`
    """
    dir_path = str(dir_path)

    # Reuse the in-memory grouping logic
    groups = dir_simulations_to_dfs(
        dir_path=dir_path,
        pattern=pattern,
        verbose=verbose,
        recursive=recursive,
        cpu_count=cpu_count,
        tables=tables,
        axis=axis,
        order_sensitive=order_sensitive,
        add_keys=add_keys,
        keys_prefix=keys_prefix,
    )

    # Persist grouped tables + schema to SQL
    write_schema_grouped_tables(
        schema_to_df=groups,
        engine=connection,
        base_table_prefix=base_table_prefix,
        schema_table_name=schema_table_name,
    )
    del groups
    gc.collect()


if __name__ == '__main__':
    import time
    from apsimNGpy.core.config import load_crop_from_disk

    maize = load_crop_from_disk('Maize', out='maizee.apsimx')
    try:
        a1 = time.perf_counter()
        run_apsim_by_path(maize)
        b = time.perf_counter()
        print(b - a1, 'seconds in dir mode')
    finally:
        os.remove(maize)

    from apsimNGpy.core.apsim import ApsimModel
    with ApsimModel('Mungbean') as model:
        trial_run(model)
