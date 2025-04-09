import argparse
import json
import os.path
import logging
import pprint

import time
import numpy as np
import pandas as pd
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core.apsim import ApsimModel, Models
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.settings import logger
from apsimNGpy.manager.weathermanager import get_weather, _is_within_USA_mainland
from apsimNGpy.cli.model_desc import extract_models
import os
import asyncio


async def fetch_weather_data(lonlat):
    """Fetch weather data asynchronously."""
    if _is_within_USA_mainland(lonlat):
        source = 'daymet'
    else:
        source = 'nasa'
    return await asyncio.to_thread(get_weather, lonlat=lonlat, source=source, start=1985, end=2020)


def fetch_soil_data(lonlat):
    """
    Fetch soil data asynchronously
    @param lonlat:
    @return:
    """
    pass


async def run_apsim_model(model, report_name):
    """Run APSIM model asynchronously."""
    # model.run(report_name)
    return await asyncio.to_thread(model.run, report_name=report_name)
    # return await asyncio.to_thread(model,)


async def save_results(df, file_name):
    """Save results asynchronously."""
    await asyncio.to_thread(df.to_csv, file_name)


def clean(path):
    """Remove the apsim related files such as the .db files
    """


def replace_soil_data(model: ApsimModel, args):
    """Replace soil data"""
    s_nodes = ['chemical', 'physical', 'organic']
    for node in s_nodes:
        if getattr(args, node, None):
            valS = getattr(args, node)
            soil = valS.split(',')
            soil_eq = [soi.split('=') for soi in soil]
            _args_params = {k[0].strip(): k[1].strip() for k in
                            soil_eq}  # assumes that the second index 1 will be the value if we hand
            # "node_path='.Simulations.Simulation.Field.Soil.Physical, BD=1.23"

            for k, v in _args_params.items():
                if k != 'node_path':
                    _args_params[k] = eval(v)  # expect all other values not to be a string
                else:
                    nl = len(node)
                    if v[-nl:] != node.capitalize():
                        _args_params[k] = f"{v}.{node.capitalize()}"

            model.replace_soils_values_by_path(**_args_params)


async def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Run a simulation of a given crop.')

    # Add arguments
    parser.add_argument('-m', '--model', type=str, required=False,
                        help='Path  or name of the APSIM model file if path it should ends with .apsimx'
                             'defaults to maize from the default '
                             'simulations ', default='Maize')
    parser.add_argument('-o', '--out', type=str, required=False, help='Out path for apsim file')
    parser.add_argument('-t', '--table', type=str, required=False, default='Report', help='Report table name. '
                                                                                          'Defaults to "Report"')
    parser.add_argument('-w', '--met_file', type=str, required=False, help="Path to the weather data file.")
    parser.add_argument('-i', '--inspect',choices=['file', *extract_models()], type=str, required=False, help=f"inspect your model to get the model paths.")
    parser.add_argument('-sim', '--simulation', type=str, required=False, help='Name of the APSIM simulation to run')
    parser.add_argument('-ws', '--wd', type=str, required=False, help='Working directory')
    parser.add_argument('-l', '--lonlat', type=str, required=False, help='longitude and Latitude (comma-separated) '
                                                                         'for fetching weather data.')
    parser.add_argument('-sf', '--save', type=str, required=False, help='File name for saving output data.')
    parser.add_argument('-s', '--aggfunc', type=str, required=False, default='mean',
                        help='Statistical summary function (e.g., mean, median). Defaults to "mean".')
    parser.add_argument('-og', '--organic', type=str,
                        required=False,
                        help="Replace any soil data through a soil organic parameters and path specification"
                             " e.g, 'node_path=.Simulations.Simulation.Field.Soil, Carbon=[2.2]'")
    parser.add_argument('-ph', '--physical', type=str,
                        required=False,
                        help="Replace any soil data through a soil physical parameters and path specification"
                             " e.g, 'node_path=.Simulations.Simulation.Field.Soil, BD=[1.2]'")
    parser.add_argument('-ch', '--chemical', type=str,
                        required=False,
                        help="Replace any soil data through a soil chemical parameters and path specification"
                             " e.g, 'node_path=.Simulations.Simulation.Field.Soil, NH4=[2.2]'")

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

    if args.inspect:
        print()
        # inspect returns after excecutions
        if args.inspect != 'file':
            model_type = eval(args.inspect)
            print(model.inspect_model(model_type=model_type))

        else:
            model.inspect_file()
        print()
        return

    await asyncio.to_thread(replace_soil_data, model, args)
    met_data = args.met_file or met_form_loc
    if met_data:
        await asyncio.to_thread(model.replace_met_file, weather_file=met_data, simulations=args.simulation)
        msg = f'Successfully updated weather file with {met_data}'
        if args.lonlat:
            msg += f' from location: {args.lonlat}'
        logger.info(msg)

    # Run APSIM asynchronously
    model = await run_apsim_model(model, report_name=args.table)

    df = model.results

    if isinstance(df, pd.DataFrame):
        await save_results(df, file_name)
        numeric_df = df.select_dtypes(include=np.number)
        stati = getattr(numeric_df, args.aggfunc)()

        logger.info(stati)


@timer
def main_entry_point() -> None:
    asyncio.run(main())


# Run asyncio event loop
if __name__ == "__main__":
    main_entry_point()
    #-m maize -sf 'm.csv' --organic "node_path=.Simulations.Simulation.Field.Soil, Carbon=[1.2]"
