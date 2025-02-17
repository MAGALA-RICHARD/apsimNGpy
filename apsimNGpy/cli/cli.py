import argparse
import json
import os.path

from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.settings import logger


def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Run a simulation of a given crop.')

    # Add arguments
    parser.add_argument('-m', '--model', type=str, required=False, help='Path to the APSIM model file', default ='Maize')
    parser.add_argument('-o', '--out', type=str, required=False,
                        help='out path')
    parser.add_argument('-t', '--table', type=str, required=False, default='Report')
    parser.add_argument('-w', '--met_file', type=str, required=False)
    parser.add_argument('-sim', '--simulation', type=str, required=False)
    parser.add_argument('-ws', '--wd', type=str, required=False)


    # Parse arguments
    args = parser.parse_args()

    wd = args.wd or os.getcwd()
    if wd != os.getcwd():
        os.makedirs(wd, exist_ok=True)
    if args.model.endswith('.apsimx'):
        model = ApsimModel(args.model)
    else:
        model = load_default_simulations(crop=args.model, simulations_object=True, path = wd)
    if args.met_file is not None:
        model.replace_met_file(weather_file=args.met_file, simulations=args.simulation)
        print(f'successfully updated weather file with {args.met_file}')
    model.run(report_name=args.table)
    print(model.results)


def defaults_model():
    """"
    default crop is maize"""
    # Create argument parser
    parser = argparse.ArgumentParser(description='Run a simulation of a given crop.')
    # Add arguments
    parser.add_argument('-c', '--model', type=str, required=False, help='name of the model')
    parser.add_argument('-o', '--out', type=str, required=False,
                        help='out path for the new model')
    parser.add_argument('-t', '--table', type=str, required=False, default='Report', help='table or report name in '
                                                                                          'the apsim simulations')
    parser.add_argument('-st', '--saveto', type=str, required=False, default=None,
                        help='name to save the results')

    parser.add_argument('-w', '--met_file', type=str, required=False)
    parser.add_argument('-sim', '--simulation', type=str, required=False)

    # Parse arguments
    args = parser.parse_args()

    model_file = load_default_simulations(crop=args.model, simulations_object=False, path = os.getcwd())
    model = ApsimModel(model_file)
    logger.info(f'RUNNING: {model}')
    table_name = args.table
    model.run(report_name=table_name)
    res = model.results
    if args.saveto is not None:
        res.to_csv(args.saveto)
        logger.info(f"results saved to {args.saveto}")
    if args.met_file is not None:
        model.replace_met_file(weather_file=args.met_file, simulations=args.simulation)
    logger.info(res.describe())


if __name__ == "__main__":
    ...
    main()


