"""
This module contains methods for generating variables used in optimization, particular those related to APSIM replacement
"""
from dataclasses import dataclass
from typing import Union

import numpy as np

from apsimNGpy.core.apsim import ApsimModel

Var_types = ['int', 'float', 'choice_var', 'grid_var']


def _auto_data(data_type, bounds: tuple, step=None):
    if data_type not in ['int', 'float', int, float, np.int8, np.int32, np.int16, np.float32, np.float64]:
        raise ValueError('data-child not supported')
    if isinstance(data_type, str):
        data_type = eval(data_type)
    data = np.arange(bounds[0], bounds[1], step=step).astype(data_type)
    return data


class ContinuousVar:
    __slots__ = ['bounds', 'data_type', 'steps', ]

    def __init__(self, bounds: tuple, data_type: Union[int, float], steps: Union[int, float] = None):
        self.bounds = bounds
        self.data_type = data_type
        self.steps = steps

    @property
    def values(self):
        return _auto_data(self.data_type, self.bounds, self.steps)


class ChoiceVar:
    __slots__ = ['values']

    def __init__(self, categories: [int, str, float] = None):
        self.values = categories


@dataclass(slots=True, frozen=True)
class CropVar:
    updater: str
    main_param: str
    params: dict
    label: str
    var_desc: Union[ContinuousVar, ChoiceVar]


def _doc(section_desc):
    return f"""
    Any parameters that is in the `{section_desc}` of apsim model can be optimized by calling this function
    @param params:is a dictionary that could hold extra argument for each function.
    @param label: name tag for the control variable being optimized
    @param var_desc: instance of `{ContinuousVar}` or `{ChoiceVar}` for categorical variables. Big up to the authors of this 
    package we wrap around their variable description to facilitate mixed variable optimization. @param main_param: 
    is main_param arguments @param updater: method of ApsimModel class to update the parameters during the 
    optimization @return:  instance of `{CropVar}`
    """


def _evaluate_args(updater, main_param, params, label, var_desc):
    assertion_msg = 'params  must be a dict '
    if not isinstance(params, dict):
        raise ValueError(assertion_msg)
    if not isinstance(label, str):
        raise ValueError('label must be a string')
    if not isinstance(main_param, str):
        raise ValueError('main param must be defined as a string')
    if not isinstance(var_desc, (ContinuousVar, ChoiceVar)):
        raise ValueError(f"Var_desc must be any of: '{[ContinuousVar, ChoiceVar]}")
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


soil.__doc__ = _doc('soil child')
manager.__doc__ = _doc('manager script')
cultivar.__doc__ = _doc('cultivar child')
dates.__doc__ = _doc('dates or clock child')
