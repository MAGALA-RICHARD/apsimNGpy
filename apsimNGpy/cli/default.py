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
def my_model():
    """"
    default crop is maize"""
    # Create argument parser

    # Add arguments
    parser.add_argument('-m', '--model', type=str, required=False, help='Path to the APSIM model file', default=None)
    parser.add_argument('-o', '--out', type=str, required=False,
                        help='out path for the new model')
    parser.add_argument('-t', '--table', type=str, required=False, default='Report', help= 'table or report name in '
                                                                                           'the apsim simulations')

    # Parse arguments
    args = parser.parse_args()

    # Run the simulation using the provided model and location
    model_file = args.model
    if model_file is None:
        model_file = load_default_simulations(crop = 'Maize',simulations_object=False)
    model = ApsimModel(model_file)
    print(f'RUNNING: {model}')
    table_name = args.table
    model.run(report_name=table_name)
    res = model.results
    logger.info(res.describe())


if __name__ == "__main__":
    my_model()
