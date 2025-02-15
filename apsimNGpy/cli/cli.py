import argparse
import json
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.settings import logger


def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Run a simulation of a given crop.')

    # Add arguments
    parser.add_argument('-m', '--model', type=str, required=True, help='Path to the APSIM model file')
    parser.add_argument('-o', '--out', type=str, required=False,
                        help='out path')
    parser.add_argument('-t', '--table', type=str, required=False)

    # Parse arguments
    args = parser.parse_args()

    # Run the simulation using the provided model and location
    model = ApsimModel(args.model, out=args.out)

    model.run(report_name=args.table)
    print(model.results)


def defaults_model():
    """"
    default crop is maize"""
    # Create argument parser
    parser = argparse.ArgumentParser(description='Run a simulation of a given crop.')
    # Add arguments
    parser.add_argument('-m', '--crop', type=str, required=False, help='name of the crop', default='Maize')
    parser.add_argument('-o', '--out', type=str, required=False,
                        help='out path for the new model')
    parser.add_argument('-t', '--table', type=str, required=False, default='Report', help='table or report name in '
                                                                                          'the apsim simulations')
    parser.add_argument('-st', '--saveto', type=str, required=False, default=None,
                        help='name to save the results')

    # Parse arguments
    args = parser.parse_args()

    # Run the simulation using the provided model and location
    model_file = args.crop

    model_file = load_default_simulations(crop=args.crop, simulations_object=False)
    model = ApsimModel(model_file)
    logger.info(f'RUNNING: {model}')
    table_name = args.table
    model.run(report_name=table_name)
    res = model.results
    if args.saveto is not None:
        res.to_csv(args.saveto)
        logger.info(f"results saved to {args.saveto}")
    logger.info(res.describe())


if __name__ == "__main__":
    defaults_model()
