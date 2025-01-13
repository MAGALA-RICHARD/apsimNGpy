from collections import namedtuple

# Define the named tuple for function arguments
ARGS = namedtuple('Args', ['updater', 'main_param', 'params', 'label', 'var_type'])


def manager(main_param, params: dict, label: str, var_desc, updater=None):
    if updater is None:
        updater = 'update_mgt_by_path'
    return ARGS(updater, main_param, params, label, var_desc)


def soil(main_param, params: dict, label: str, var_desc, updater=None):
    if updater is None:
        updater = 'replace_soil_properties_by_path' #example path 'None.Soil.physical.None.None.BD'
    return ARGS(updater, main_param, params, label, var_desc)


def cultivar(main_param, params: dict, label: str, var_desc, updater=None):
    if updater is None:
        updater = 'edit_cultivar'
    return ARGS(updater, main_param, params, label, var_desc)


def dates(main_param, params: dict, label: str, var_desc, updater=None):
    if updater is None:
        updater = 'change_simulation_dates'
    return ARGS(updater, main_param, params, label, var_desc)
