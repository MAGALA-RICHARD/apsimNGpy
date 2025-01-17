import logging
from collections import namedtuple
from utils import fun_inspector, create_data
from apsimNGpy.utililies.utils import timer
from apsimNGpy.core.apsim import ApsimModel
import wrapdisc
from wrapdisc.var import ChoiceVar, GridVar, QrandintVar, QuniformVar, RandintVar, UniformVar
from dataclasses import dataclass


@dataclass
class CropVar:
    updater: str
    main_param: str
    params: dict
    label: str
    var_type: wrapdisc.var


def _evaluate_args(updater, main_param, params, label, var_desc):
    assertion_msg = 'params  must be a dict '
    assert isinstance(params, dict), assertion_msg
    assert isinstance(label, str), 'label must be a string'
    assert isinstance(main_param, str), 'main param must be defined as a string'
    try:
        method = getattr(ApsimModel, updater)
    except AttributeError as e:
        logging.error(e)
        raise AttributeError(f'{updater} is not a valid method for updating parameters')


@timer
def manager(params: dict, label: str, var_desc, main_param=None, updater=None):
    if updater is None:
        updater = 'update_mgt_by_path'
        main_param = 'param_values'

    _evaluate_args(updater, main_param, params, label, var_desc)

    return CropVar(updater, main_param, params, label, var_desc)


@timer
def soil(params: dict, label: str, var_desc, main_param=None, updater=None):

    if updater is None:
        updater = 'replace_soil_properties_by_path'  # example path 'None.Soil.physical.None.None.BD'
        main_param = "param_values"
    _evaluate_args(updater, main_param, params, label, var_desc)
    return CropVar(updater, main_param, params, label, var_desc)


def cultivar(params: dict, label: str, var_desc, main_param=None, updater=None):

    if updater is None:
        updater = 'edit_cultivar'
        main_param = 'values'
    _evaluate_args(updater, main_param, params, label, var_desc)
    return CropVar(updater, main_param, params, label, var_desc)


def dates(main_param, params: dict, label: str, var_desc, updater=None):
    if updater is None:
        updater = 'change_simulation_dates'
    _evaluate_args(updater, main_param, params, label, var_desc)
    return CropVar(updater, main_param, params, label, var_desc)


if __name__ == '__main__':
    xp = manager(params={'nitrogen': 239}, label='ni', var_desc='desc')
    ap = soil({'nitrogen': 199}, 'param_values', 'choice', 'ba')
