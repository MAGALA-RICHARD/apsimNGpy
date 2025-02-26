import argparse
import json
import os.path
import logging

import numpy as np
import pandas as pd
from apsimNGpy.utililies.utils import timer
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.settings import logger
from apsimNGpy.manager.weathermanager import get_weather, _is_within_USA_mainland



@timer
def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Run a simulation of a given crop.')

    # Add arguments
    parser.add_argument('-m', '--model', type=str, required=False, help='Path to the APSIM model file', default='Maize')
    parser.add_argument('-o', '--out', type=str, required=False,
                        help='out path')
    parser.add_argument('-t', '--table', type=str, required=False, default='Report')
    parser.add_argument('-w', '--met_file', type=str, required=False)
    parser.add_argument('-sim', '--simulation', type=str, required=False)
    parser.add_argument('-ws', '--wd', type=str, required=False)
    parser.add_argument('-l', '--lonlat', type=str, required=False)
    parser.add_argument('-sf', '--save', type=str, required=False)
    parser.add_argument('-s', '--aggfunc', type=str, required=False, default='mean',
                        help='statistical summary to summarize the data')

    # Parse arguments
    args = parser.parse_args()

    logger.info(f"commands summary: '{args}'")
    wd = args.wd or os.getcwd()
    if wd != os.getcwd():
        os.makedirs(wd, exist_ok=True)
    met_form_loc = False
    _loc = False
    _source = False
    if args.lonlat:
        _loc = tuple(map(float, args.lonlat.split(',')))
        if _is_within_USA_mainland(_loc):
            _source = 'daymet'
        else:
            _source = 'nasa'
        met_form_loc = get_weather(lonlat=_loc, source=_source)
    file_name = args.save or 'out_' + args.model.strip('a.apsimx') + ".csv"
    if args.model.endswith('.apsimx'):
        model = ApsimModel(args.model, args.out)
    else:
        model = load_default_simulations(crop=args.model, simulations_object=True, path=wd)
    met_data = args.met_file or met_form_loc

    if met_data:
        model.replace_met_file(weather_file=met_data, simulations=args.simulation)
        sms = f'successfully updated weather file with {met_data}'
        if args.lonlat:
            sms = f'successfully updated weather file with {met_data} from location: {args.lonlat}'
        logger.info(sms)
    if _loc:
        ...
        # model.replace_soils(_loc, simulation_names=None)
    model.run(report_name=args.table)
    df = model.results
    if isinstance(df, pd.DataFrame):
        model.results.to_csv(file_name)
        numeric_df = df.select_dtypes(include=np.number)
        stati = getattr(numeric_df, args.aggfunc)()

        logger.info(stati)


if __name__ == "__main__":
    ...
    main()
    import subprocess
    from apsimNGpy.core.config import get_apsim_bin_path
    import sys


