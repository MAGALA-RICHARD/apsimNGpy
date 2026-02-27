"""
MultiCore Performance Test Module
==================================

This module benchmarks APSIM multi-core execution using the
MultiCoreManager interface in apsimNGpy.

It supports both process-based and thread-based parallel execution
and allows flexible configuration of:

    • APSIM binary path
    • Parallel mode (threads or processes)
    • Number of CPU cores
    • Execution engine
    • Batch size (number of simulation jobs)

The module is intended for:

    • Performance testing
    • Parallel scalability testing
    • Engine comparison (python vs dotnet)
    • CI validation of APSIM runtime stability

---------------------------------------------------------------------
Command Line Usage
---------------------------------------------------------------------

Run as a module:

    python -m apsimNGpy.tests.unittest.mcp [OPTIONS]

Options:

    -bp, --bin PATH
        Path to APSIM binary directory.
        Overrides environment variable TEST_APSIM_BINARY.

    -md, --mode {p,t}
        Parallel mode:
            p = processes (default)
            t = threads

    -c, --cpu_count INT
        Number of worker cores to use.
        Default = max(2, os.cpu_count() - 4)

    -e, --engine {python,dotnet}
        Execution engine backend.
        Default = python

    -s, --size INT
        Number of batch simulation jobs.
        Default = 200

---------------------------------------------------------------------
Binary Path Resolution Precedence
---------------------------------------------------------------------

The APSIM binary path is resolved in the following order:

    1. CLI argument (--bin)
    2. Environment variable TEST_APSIM_BINARY
    3. Automatic detection via get_apsim_bin_path()

If none are valid, execution fails with an error.

---------------------------------------------------------------------
Example
---------------------------------------------------------------------

Using explicit binary path:

    python -m apsimNGpy.tests.unittest.mcp \
        --bin "D:/APSIM/bin" \
        --mode p \
        --cpu_count 8 \
        --engine python \
        --size 500

Using environment variable:

    set TEST_APSIM_BINARY=D:/APSIM/bin
    python -m apsimNGpy.tests.unittest.mcp -md t

---------------------------------------------------------------------
Outputs
---------------------------------------------------------------------

The module:

    • Executes batch simulations
    • Aggregates results into a SQLite database
    • Returns a pandas DataFrame
    • Validates subset extraction
    • Plots Yield vs Amount
    • Prints runtime performance

---------------------------------------------------------------------
Intended Audience
---------------------------------------------------------------------

Developers and researchers evaluating:

    • APSIM multi-core performance
    • Thread vs process scalability

"""
import os
from pathlib import Path

import pandas as pd

from apsimNGpy.config import apsim_bin_context, configuration, get_apsim_bin_path
import time
from apsimNGpy import Apsim
from apsimNGpy.logger import logger
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    '-bp', "--bin",
    required=False,
    help="Path to APSIM binary directory")
parser.add_argument(
    "-md", "--mode",
    required=False,
    default='p',
    help="to use threads or processes")

parser.add_argument(
    "-c", "--cpu_count",
    required=False,
    default=max(2, os.cpu_count() - 4),
    help="to use threads or processes")

parser.add_argument(
    "-e", "--engine",
    required=False,
    default='python',
    help="to use threads or processes")
parser.add_argument(
    "-s", "--size",
    required=False,
    default=200,
    help="Number of batch size to test")
args = parser.parse_args()
threads = {'p': False, 't': True}[args.mode]
cpu = int(args.cpu_count)
arg_bin_path = args.bin
engine = args.engine
batch_size = int(args.size)

bin_path = arg_bin_path or Path(os.environ.get('TEST_APSIM_BINARY')) or get_apsim_bin_path()
bp = bin_path


def edit_weather(model):
    model.get_weather_from_web(lonlat=(-92.034, 42.012), start=1989, end=2020, source='daymet',
                               )
    model.get_soil_from_web(simulations=None, lonlat=(-92.034, 42.012), source='ssurgo', summer_date='15-may',
                            winter_date='01-nov')
    model.edit_model(model_type='Models.Manager', model_name='Sow using a variable rule', Population=8.65,
                     StartDate='28-apr', EndDate='03-may')


if __name__ == '__main__':
    # set the database where data will be stored
    db = (Path.home() / "test_agg_3.db").resolve()
    # get the APSIM binary path

    logger.info(configuration.bin_path, )
    bn = bin_path

    logger.info(configuration.bin_path)
    workspace = Path('D:/')
    os.chdir(workspace)
    # initialize the API
    with Apsim(bp) as apsim:

        logger.info(configuration.bin_path)
        Parallel = apsim.MultiCoreManager(db_path=db, agg_func='mean', table_prefix='di', )
        # define the batch simulation jobs
        jobs = ({'model': 'Maize', 'ID': i, 'payload': [{'path': '.Simulations.Simulation.Field.Fertilise at sowing',
                                                         'Amount': i}]} for i in range(0, batch_size))
        start = time.perf_counter()
        # run all the jobs defined above
        Parallel.run_all_jobs(jobs=jobs, n_cores=cpu, engine=engine, threads=threads, chunk_size=100,
                              subset=['Yield'], callback=edit_weather,
                              progressbar=True)
        # extract the results
        dff = Parallel.results
        if not isinstance(dff, pd.DataFrame):
            raise ValueError('expected results to be a pandas DataFrame')
        if dff.empty:
            raise ValueError('expected results not to be empty')
        if not 'Yield' in dff.columns:
            raise ValueError('subseting not working perhaps')
        print(dff.shape)
        print(time.perf_counter() - start)
        import matplotlib.pyplot as plt

        Parallel.relplot(x='Amount', y='Yield')
        #plt.show()
        logger.info(f"Tested bin path is: {configuration.bin_path}")
        logger.info(f"Tested succeeded")

    # using a context manager to load APSIM
