# cli.py

import argparse
import json
import click


@click.command()
@click.option('--location', type=str)
@click.option('--model', type=str)
def run_simulation():
    from apsimNGpy.core.simulation import simulate
    parser = argparse.ArgumentParser(description='Run a simulation of a given crop.')

    args = parser.parse_args()

    # Convert args to dictionary and unpack for the simulate function
    kwargs = vars(args)
    location = kwargs.pop('location')
    model = kwargs.pop('model')
    simulate(model, location, **kwargs)


if __name__ == "__main__":
    main()
