# cli.py

import argparse
import json
import click


@click.command()
@click.option('--location', type=str, prompt='The location for which the simulation is being run')
@click.option('--model', type=str, prompt='The crop/model for which the simulation is run')
def run_simulation(location, model):
    from ..core.core import run_simulation_from_string
    run_simulation_from_string(model)


if __name__ == "__main__":
    run_simulation()
