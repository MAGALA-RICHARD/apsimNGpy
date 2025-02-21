import argparse
import json
import os.path
import logging
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.base_data import load_default_simulations
# from apsimNGpy.settings import logger
from apsimNGpy.manager.weathermanager import get_weather, _is_within_USA_mainland

logger = logging.getLogger(__name__)


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

    # Parse arguments
    args = parser.parse_args()
    logger.info(f"summary of your: {args}")
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

    if args.model.endswith('.apsimx'):
        model = ApsimModel(args.model, args.out)
    else:
        model = load_default_simulations(crop=args.model, simulations_object=True, path=wd)
    met_data = args.met_file or met_form_loc

    if met_data:
        model.replace_met_file(weather_file=met_data, simulations=args.simulation)
        logger.info(f'successfully updated weather file with {met_data}')
    if _loc:
        ...
        # model.replace_soils(_loc, simulation_names=None)
    model.run(report_name=args.table)
    logger.info(model.results)


if __name__ == "__main__":
    ...
    main()
