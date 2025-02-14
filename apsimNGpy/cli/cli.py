import argparse
import json
from apsimNGpy.core.apsim import ApsimModel


def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Run a simulation of a given crop.')

    # Add arguments
    parser.add_argument('-m', '--model', type=str, required=True, help='Path to the APSIM model file')
    parser.add_argument('-l', '--location', type=str, required=True,
                        help='Longitude and latitude as a comma-separated string')

    # Parse arguments
    args = parser.parse_args()

    # Split the location into longitude and latitude
    lon, lat = map(float, args.location.split(','))

    # Run the simulation using the provided model and location
    model = ApsimModel(args.model, lonlat=(lon, lat))

    # Assuming the ApsimModel class has a method to run, which you will need to call
    model.run()  # Make sure the ApsimModel has this method or adapt accordingly
    print(model.results)


if __name__ == "__main__":
    main()
