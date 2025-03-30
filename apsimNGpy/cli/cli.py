import argparse
import json
import os.path
import logging

import numpy as np
import pandas as pd
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.settings import logger
from apsimNGpy.manager.weathermanager import get_weather, _is_within_USA_mainland
import os
import asyncio

import logging

logger = logging.getLogger(__name__)


async def fetch_weather_data(lonlat):
    """Fetch weather data asynchronously."""
    if _is_within_USA_mainland(lonlat):
        source = 'daymet'
    else:
        source = 'nasa'
    return await asyncio.to_thread(get_weather, lonlat=lonlat, source=source)


async def run_apsim_model(model, report_name):
    """Run APSIM model asynchronously."""
    await asyncio.to_thread(model.run, report_name=report_name)


async def save_results(df, file_name):
    """Save results asynchronously."""
    await asyncio.to_thread(df.to_csv, file_name)

@timer
async def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Run a simulation of a given crop.')

    # Add arguments
    parser.add_argument('-m', '--model', type=str, required=False, help='Path to the APSIM model file', default='Maize')
    parser.add_argument('-o', '--out', type=str, required=False, help='Out path')
    parser.add_argument('-t', '--table', type=str, required=False, default='Report')
    parser.add_argument('-w', '--met_file', type=str, required=False)
    parser.add_argument('-sim', '--simulation', type=str, required=False)
    parser.add_argument('-ws', '--wd', type=str, required=False)
    parser.add_argument('-l', '--lonlat', type=str, required=False)
    parser.add_argument('-sf', '--save', type=str, required=False)
    parser.add_argument('-s', '--aggfunc', type=str, required=False, default='mean',
                        help='Statistical summary to summarize the data')

    # Parse arguments
    args = parser.parse_args()
    logger.info(f"Commands summary: '{args}'")

    wd = args.wd or os.getcwd()
    os.makedirs(wd, exist_ok=True)

    met_form_loc = None
    if args.lonlat:
        lonlat_tuple = tuple(map(float, args.lonlat.split(',')))
        met_form_loc = await fetch_weather_data(lonlat_tuple)

    file_name = args.save or f"out_{args.model.strip('.apsimx')}.csv"

    if args.model.endswith('.apsimx'):
        model = ApsimModel(args.model, args.out)
    else:
        model = load_default_simulations(crop=args.model, simulations_object=True, set_wd=wd)

    met_data = args.met_file or met_form_loc
    if met_data:
        await asyncio.to_thread(model.replace_met_file, weather_file=met_data, simulations=args.simulation)
        msg = f'Successfully updated weather file with {met_data}'
        if args.lonlat:
            msg += f' from location: {args.lonlat}'
        logger.info(msg)

    # Run APSIM asynchronously
    await run_apsim_model(model, report_name=args.table)

    df = model.results

    if isinstance(df, pd.DataFrame):

        await save_results(df, file_name)
        numeric_df = df.select_dtypes(include=np.number)
        stati = getattr(numeric_df, args.aggfunc)()
        print(stati)
        logger.info(stati)


# Run asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())

#
# if __name__ == "__main__":
#     ...
#     main()
#     import subprocess
#     from apsimNGpy.core.config import get_apsim_bin_path
#     import sys
#
