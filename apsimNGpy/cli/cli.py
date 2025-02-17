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
    parser.add_argument('-m', '--model', type=str, required=False, help='Path to the APSIM model file', default='Maize')
    parser.add_argument('-o', '--out', type=str, required=False,
                        help='out path')
    parser.add_argument('-t', '--table', type=str, required=False, default='Report')
    parser.add_argument('-w', '--met_file', type=str, required=False)
    parser.add_argument('-sim', '--simulation', type=str, required=False)
    parser.add_argument('-ws', '--wd', type=str, required=False)
    parser.add_argument('-l', '--loc', type=tuple, required=False)

    # Parse arguments
    args = parser.parse_args()
    print(args.loc)
    wd = args.wd or os.getcwd()
    if wd != os.getcwd():
        os.makedirs(wd, exist_ok=True)
    if args.model.endswith('.apsimx'):
        model = ApsimModel(args.model, args.out)
    else:
        model = load_default_simulations(crop=args.model, simulations_object=True, path=wd)
    if args.met_file is not None:
        model.replace_met_file(weather_file=args.met_file, simulations=args.simulation)
        print(f'successfully updated weather file with {args.met_file}')
    model.run(report_name=args.table)
    print(model.results)


if __name__ == "__main__":
    ...
    main()
