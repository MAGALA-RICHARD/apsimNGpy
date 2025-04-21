import asyncio
import argparse
import json
import os.path
import logging
import pprint
from apsimNGpy import settings
import time
import numpy as np
import pandas as pd
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core.apsim import ApsimModel, Models
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.settings import logger
from apsimNGpy.manager.weathermanager import get_weather, _is_within_USA_mainland
from apsimNGpy.cli.model_desc import extract_models
import os, sys
import asyncio
from apsimNGpy.cli.set_ups import print_msg, ColoredHelpFormatter
from apsimNGpy.manager.soilmanager import DownloadsurgoSoiltables, OrganiseSoilProfile


def print_msg(msg, normal = True):
    if normal:
       print(f'  \033[96m{msg}\033[0m')
    else:
        print(f'  \033[91m{msg}\033[0m')
def change_mgt(model, args):

    """
    Update management parameters in the model using a string specification of various parameters.

    The `args.management` string should contain one or more manager specifications in the form:
        'path=path_to_manager, param1=value, param2=value'

    To update multiple managers, separate them using a colon (`:`):
        'path=manager1, rate=20 : path=manager2, rate=30, start_day="2023-01-01"'

    Notes:
        - The 'path' key is required for each manager block.

    """

    if not args.management:
        return model

    def parse_management_args(management_str):
        parsed = []

        specs = management_str.split(':')
        for spec in specs:
            if ',' not in spec:
                raise argparse.ArgumentTypeError(f'invalide management specification {spec} detected')
            parts = [s.strip() for s in spec.split(',') if s.strip()]
            param_dict = {}
            for part in parts:
                if '__' in part:
                    raise argparse.ArgumentTypeError(f'invalid specification path `{part}` detected')
                if '=' not in part:
                    continue
                key, value = map(str.strip, part.split('=', 1))

                    # Evaluate non-path values (assumes they’re Python literals)
                param_dict[key] = value if key == 'path' else eval(value)
            if 'path' in param_dict:
                parsed.append(param_dict)
        return parsed

    for mgt_params in parse_management_args(args.management):
        print(mgt_params)
        model.update_mgt_by_path(**mgt_params)

    return model


async def fetch_weather_data(lonlat):
    """Fetch weather data asynchronously."""
    if _is_within_USA_mainland(lonlat):
        source = 'daymet'
    else:
        source = 'nasa'
    return await asyncio.to_thread(get_weather, lonlat=lonlat, source=source, start=1985, end=2020)


def replace_soil_from_web(lonlat):
    """
    Fetch soil data asynchronously
    @param lonlat:
    @return:
    """

    sp = DownloadsurgoSoiltables(lonlat)
    sop = OrganiseSoilProfile(sp, thickness=20, thickness_values=settings.SOIL_THICKNESS).cal_missingFromSurgo()
    return sop


async def run_apsim_model(model, report_name):
    print("running apsim")
    """Run APSIM model asynchronously."""
    # model.run(report_name)
    if report_name is None:
        report_name = model.inspect_model(Models.Report, fullpath=False)
    return await asyncio.to_thread(model.run, report_name=report_name, verbose=True)
    # return await asyncio.to_thread(model,)

async def create_experiment(model, factors, permutation =True, basename=None):
    print('creating experiment')
    if ";" in factors:
       factors = factors.split(';')
    else:
        factors = factors
    def _add(_model, _factors):
        for factor in _factors:
            _model.add_factor(factor) if factor else None
        return _model
    model.create_experiment(permutation=permutation, basename=basename)
    return _add(model, factors)

async def save_results(df, file_name):
    """Save results asynchronously."""
    await asyncio.to_thread(df.to_csv, file_name)


def clean(path):
    """Remove the apsim related files such as the .db files
    """


def replace_soil_data(model: ApsimModel, args):
    """Replace soil data"""
    s_nodes = ['chemical', 'physical', 'organic']
    for node in s_nodes:
        if getattr(args, node, None):
            valS = getattr(args, node)
            soil = valS.split(',')
            soil_eq = [soi.split('=') for soi in soil]
            _args_params = {k[0].strip(): k[1].strip() for k in
                            soil_eq}  # assumes that the second index 1 will be the value if we hand
            # "node_path='.Simulations.Simulation.Field.Soil.Physical, BD=1.23"

            for k, v in _args_params.items():
                if k != 'node_path':
                    _args_params[k] = eval(v)  # expect all other values not to be a string
                else:
                    nl = len(node)
                    if v[-nl:] != node.capitalize():
                        _args_params[k] = f"{v}.{node.capitalize()}"

            model.replace_soils_values_by_path(**_args_params)


