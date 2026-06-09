from typing import Iterable

from apsimNGpy.core.model_loader import get_node_by_path

from apsimNGpy import logger
from apsimNGpy.core_utils.utils import is_scalar
from apsimNGpy.core.apsim import ApsimModel, timer
from apsimNGpy.core.model_tools import validate_model_obj
from functools import cache

HIGH_LEVEL_MODELS = ['Models.Sobol', 'Models.Core.Simulations',
                     'Models.Factorial.Experiment',
                     'Models.Storage.DataStore',
                     'Models.Morris']


@timer
@cache
def get_models_of_type(model: ApsimModel, model_type) -> dict:
    model_types = validate_model_obj(model_type)
    # full path first because duplicates names will be overwritten
    models = dict(zip(model.inspect_model(model_type=model_types, fullpath=True),
                      model.inspect_model(model_type=model_types, fullpath=False)))
    if models:
        return {model_types().ToString(): models}
    return {}


def get_models_to_edit(model, model_type):
    models = get_models_of_type(model, model_type)
    if not models:
        raise ValueError(f'Models of type {model_type} not found.')
    return models


def get_model_paths_to_edit(model: ApsimModel, model_type, model_name: str,
                            simulations: str | None | Iterable = None) -> dict:
    # Either string or class of NameSpace: Models
    model_type = model_type().ToString() if not isinstance(model_type, str) else model_type
    models = get_models_to_edit(model, model_type)[model_type]
    available_names = set(models.values())
    if model_name not in available_names:
        raise ValueError(
            f'model_name {model_name}  of type {model_type} not found. Available models: {available_names}')
    models_to_edit = {}
    if simulations is None or model_type in HIGH_LEVEL_MODELS:
        models_to_edit = {}
        for k, v in models.items():
            if v == model_name:
                models_to_edit[k] = v

    else:
        sims = {simulations} if is_scalar(simulations) else set(simulations)
        sims_available = {i.Name for i in model.simulations}
        missing_sims = sims - sims_available
        if missing_sims:
            raise ValueError(
                f"The following specified simulation(s): {sorted(missing_sims)} were not found."
            )

        for path, name_of_model in models.items():
            path_parts = path.split(".")

            if any(sim in path_parts for sim in sims):
                if name_of_model == model_name:
                    models_to_edit[path] = name_of_model
        matched_sims = {
            sim
            for sim in sims
            if any(sim in path.split(".") for path in models_to_edit)
        }
        unmatched_sims = sims - matched_sims

        if unmatched_sims and not model_type in HIGH_LEVEL_MODELS:
            logger.warning(
                "Model named '%s' of type '%s' was not found in the following simulation(s): %s. "
                "Edits will be applied only to matching simulations.",
                model_name,
                model_type,
                sorted(unmatched_sims),
            )
            # big debate whether we should raise this warning
            # raise ValueError("Model named '%s' of type '%s' was not found in the following simulation(s): %s. "
            #     "Edits will be applied only to matching simulations.",)

    return models_to_edit

@timer
def edit_model_by_name(model, model_type, model_name, simulations=None, clear_old=False, **kwargs):
    if not kwargs:
        logger.warning('Parameters not set for editing')
    models_to_edit = get_model_paths_to_edit(model, model_type, model_name, simulations)
    for path in models_to_edit:
        model_instance = get_node_by_path(model.Simulations, path, cast_as='auto')
        model.edit_model_by_path(path=path, clear_old=clear_old, **kwargs)
        print(model_instance)
    model.save()


maize = ApsimModel('Factorial', 'out.apsimx')
m = get_models_of_type(maize, 'Models.Manager')
no_sim = get_model_paths_to_edit(maize, 'Models.Manager', 'Sow on a fixed date')
w_sims = get_model_paths_to_edit(maize, 'Models.Manager', 'Sow on a fixed date',
                                 simulations=[ 'Base4', 'Base1'])
edit_model_by_name(maize, 'Models.Manager', 'FertiliserRule', ApplicationAmount=177, simulations=['Base0'])
maize.inspect_model_parameters('Models.Manager', 'Sow on a fixed date', parameters='Parameters')

with ApsimModel('Maize') as m1:
    edit_model_by_name(m1, 'Models.Summary', 'Summary', Name='sum')
    edit_model_by_name(m1, 'Models.Surface.SurfaceOrganicMatter', 'SurfaceOrganicMatter', InitialCNR=85)


