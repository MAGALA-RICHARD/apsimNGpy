# runs any crop from the defaults simulations
import argparse
import json
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.base_data import load_default_simulations
import logging
from apsimNGpy.utililies import utils
parser = argparse.ArgumentParser(description='Run a simulation of a given crop.')
from apsimNGpy.settings import logger

@utils.timer
def main():
    """"
    default crop is maize"""
    # Create argument parser


    # Add arguments
    parser.add_argument('-m', '--crop', type=str, required=False, help='Path to the APSIM model file', default='Maize')
    parser.add_argument('-o', '--out', type=str, required=False,
                        help='out path')
    parser.add_argument('-t', '--table', type=str, required=False, default='Report')

    # Parse arguments
    args = parser.parse_args()

    # Run the simulation using the provided model and location
    model = load_default_simulations(crop=args.crop, simulations_object=True)
    print(f'RUNNING {model}')
    model.run(report_name=args.table)
    res = model.results
    logger.info(res.describe())


if __name__ == "__main__":
    main()
