# cli.py

import argparse
import json
import click


@click.command()
@click.option('--location', type=str, prompt='The location for which the simulation is being run')
@click.option('--model', type=str, prompt='The crop/model for which the simulation is run')
def run_simulation(location, model):
    from apsimNGpy.core.simulation import simulate
    simulate(model, location, **kwargs)


if __name__ == "__main__":
    main()
