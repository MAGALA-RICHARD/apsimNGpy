"""
This module contains methods for generating variables used in optimization, particular those related to APSIM replacement
"""

import logging
from collections import namedtuple

import numpy as np

from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core.apsim import ApsimModel
import wrapdisc
from wrapdisc.var import ChoiceVar, GridVar, QrandintVar, QuniformVar, RandintVar, UniformVar
from dataclasses import dataclass, field


def _doc(section_desc):
    return f"""
    Any parameters that is in the {section_desc} of apsim model can be optimized by calling this function
    @param params:is a dictionary that could hold extra argument for each function.
    @param label: name tag for the control variable being optimized
    @param var_desc: instance of wrapdisc.var big up to the authors of this package we wrap around their
     variable description to facilitate mixed variable optimization.
    @param main_param: is main_param arguments
    @param updater: method of ApsimModel class to update the parameters during the optimization
    @return:  instance of CropVar
    """


def auto_guess(data):
    if isinstance(data, ChoiceVar):
        sample_set = np.random.choice(data.categories, size=1)[0]
    elif isinstance(data, GridVar):
        sample_set = np.random.choice(data.values, size=1)[0]
    elif isinstance(data, (QrandintVar, RandintVar, QuniformVar)):
        sample_set = data.lower
    elif isinstance(data, UniformVar):
        if len(data.bounds) == 1:
            bounds = data.bounds[0]
        else:
            bounds = data.bounds
        sample_set = np.random.uniform(bounds[0], bounds[1], size=1)[0]
    else:
        raise ValueError(f'data: {type(data)} not supported')
    return sample_set


@dataclass(slots=True, frozen=True)
class CropVar:
    updater: str
    main_param: str
    params: dict
    label: str
    var_type: wrapdisc.var


def _evaluate_args(updater, main_param, params, label, var_desc):
    assertion_msg = 'params  must be a dict '
    if not isinstance(params, dict):
        raise ValueError(assertion_msg)
    if not isinstance(label, str):
        raise ValueError('label must be a string')
    if not isinstance(main_param, str):
        raise ValueError('main param must be defined as a string')
    try:
        # CHECK IF UPDATOR IS A valid attribute from ApsimModel
        getattr(ApsimModel, updater)
    except AttributeError as e:
        raise AttributeError(f'{updater} is not a valid method for updating parameters')


def manager(params: dict, label: str, var_desc, main_param=None, updater=None) -> CropVar:
    """
    Any parameters that is in the manager script of apsim model can be optimized by calling this function
    @param params:is a dictionary that could hold extra argument for each function.
    @param label: name tag for the control variable being optimized
    @param var_desc: instance of wrapdisc.var big up to the authors of this package we wrap around their
     variable description to facilitate mixed variable optimization.
    @param main_param: is function updator  arguments which will hold the trial values during optimization
    @param updater: method of ApsimModel class to update the parameters during the optimization
    @return:  instance of CropVar
    """
    if updater is None:
        updater = 'update_mgt_by_path'
        main_param = 'param_values'

    _evaluate_args(updater, main_param, params, label, var_desc)

    return CropVar(updater, main_param, params, label, var_desc)


def soil(params: dict, label: str, var_desc, main_param=None, updater=None):
    if updater is None:
        updater = 'replace_soil_properties_by_path'  # example path 'Simulation.Soil.physical.None.None.BD'
        main_param = "param_values"
    _evaluate_args(updater, main_param, params, label, var_desc)
    return CropVar(updater, main_param, params, label, var_desc)


def cultivar(params: dict, label: str, var_desc, main_param=None, updater=None):
    if updater is None:
        updater = 'edit_cultivar'
        main_param = 'values'
    _evaluate_args(updater, main_param, params, label, var_desc)
    return CropVar(updater, main_param, params, label, var_desc)


def dates(params: dict, label: str, var_desc, main_param=None, updater=None):
    if updater is None:
        updater = 'change_simulation_dates'
        main_param = 'start_date'
    _evaluate_args(updater, main_param, params, label, var_desc)
    return CropVar(updater, main_param, params, label, var_desc)


soil.__doc__ = _doc('soil node')
manager.__doc__ = _doc('manager script')
cultivar.__doc__ = _doc('cultivar node')
dates.__doc__ = _doc('dates or clock node')
