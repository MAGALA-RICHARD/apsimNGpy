import argparse
import json
from apsimNGpy.core.apsim import ApsimModel


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


if __name__ == "__main__":
    main()
