from typing import Iterable, TYPE_CHECKING

from apsimNGpy.starter.starter import CLR

from apsimNGpy.core.model_loader import get_node_by_path

from apsimNGpy import logger
from apsimNGpy.core_utils.utils import is_scalar
from apsimNGpy import timer

if TYPE_CHECKING:
    from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.model_tools import validate_model_obj, Models, ModelTools
from functools import cache

__all__ = ['switch_sensitivity_method', 'edit_model_by_name']

HIGH_LEVEL_MODELS = ['Models.Sobol', 'Models.Core.Simulations',
                     'Models.Factorial.Experiment',
                     'Models.Storage.DataStore',
                     'Models.Factorial.Factors',
                     'Models.Factorial.CompositeFactor',
                     'Models.Morris']



def get_models_of_type(model: "ApsimModel", model_type) -> dict:
    model_cls = validate_model_obj(model_type)
    model_type_name = model_cls().ToString()

    full_paths = model.inspect_model(model_type=model_cls, fullpath=True)

    if not full_paths:
        return {}

    models = {
        path: path.split(".")[-1]
        for path in full_paths
    }

    return {model_type_name: models}


def get_models_to_edit(model, model_type):
    models = get_models_of_type(model, model_type)
    if not models:
        raise ValueError(f'Models of type {model_type} not found.')
    return models


def get_model_paths_to_edit(model: 'ApsimModel', model_type, model_name: str,
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
        sims = {i.Name for i in model.simulations}
        specified_simulations = {}

    else:
        # user has specified some simulations
        sims = {simulations} if is_scalar(simulations) else set(simulations)
        specified_simulations = sims
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

    if unmatched_sims and specified_simulations:
        msg2 = "Model named '%s' of type '%s' was not found in the following simulation(s):"
        raise ValueError(f"{msg2} {unmatched_sims}")
    if len(unmatched_sims) == len(sims) and model_type not in HIGH_LEVEL_MODELS:
        # simulations aren't specified and no match was found
        msg = f"Model named {model_name} of type {model_type} was not found in any of the following simulation {sims}"
        raise ValueError(msg)

    return models_to_edit


@timer
def edit_model_by_name(model, model_type, model_name, simulations=None, clear_old=False, **kwargs):
    """
    Filter model paths to the requested simulations and validate that the
    target model exists within those simulations.

    Validation rules
    ----------------
    1. If one or more simulations are explicitly specified and the requested
       model (identified by both ``model_type`` and ``model_name``) is not
       found in any of those simulations, a ``ValueError`` is raised.

    2. When multiple simulations are supplied, the method requires the model
       to exist in every specified simulation. If the model is missing from
       one or more of the requested simulations, a ``ValueError`` is raised
       listing the unmatched simulations.

    3. When no simulations are specified, the search is performed across all
       simulations in the model. If no matching model is found anywhere in
       the simulation tree, a ``ValueError`` is raised.

    These checks are intended to prevent silent failures where edits appear
    to succeed but are not applied because the requested model does not exist
    in the target simulation(s).
    """
    if not kwargs:
        logger.warning('Parameters not set for editing')
    models_to_edit = get_model_paths_to_edit(model, model_type, model_name, simulations)
    for path in models_to_edit:
        model_instance = get_node_by_path(model.Simulations, path, cast_as='auto')
        model.edit_model_by_path(path=path, clear_old=clear_old, **kwargs)
        print(model_instance)
    model.save()


def switch_sensitivity_method(model, switch_to, aggregation_var_name=None, table_name=None,
                              num_path=None, jumps=10, num_intervals=20, verbose=True):
    kwargs = {}
    model_map = {
        "sobol": "Models.Sobol",
        "morris": "Models.Morris",
        "models.sobol": "Models.Sobol",
        "models.morris": "Models.Morris",
    }

    key = switch_to.lower()
    if key not in model_map:
        raise ValueError(
            f"Invalid sensitivity method '{switch_to}'. "
            f"Expected one of: {list(model_map)}"
        )

    switch_to_model = validate_model_obj(model_map[key])

    opposite_model = Models.Morris if switch_to_model == Models.Sobol else Models.Sobol

    mods = model.inspect_model(opposite_model, fullpath=True)
    if not mods:
        # is the one to switch to in
        if model.inspect_model(switch_to_model):
            logger.warning(
                f"Sensitivity model is already a {switch_to_model.__name__} model"
            )
            return model
        else:
            raise ValueError(f"No Sobol or Morris sensitivity model found under Simulations.Children")
    # get existing sensitivity model class instances
    sens_model = get_node_by_path(model.Simulations, node_path=mods[0], cast_as='auto')
    if sens_model:

        # create a new simulation tree as empty
        root = CLR.Node.Create(Models.Core.Simulations())
        sm = CLR.CastHelper.CastAs[Models.Core.Simulations](root.Model)
        base_sim = model[0].Node.Clone()

        if switch_to_model == Models.Morris:
            kwargs = {}
            kwargs.setdefault("NumIntervals", num_intervals)
            kwargs.setdefault("Jump", jumps)
        add = switch_to_model()
        add.AggregationVariableName = aggregation_var_name or sens_model.AggregationVariableName
        add.TableName = table_name or sens_model.TableName
        add.NumPaths = num_path or sens_model.NumPaths
        exchange_params = sens_model.Parameters
        sm.Children.Add(add)
        add.Children.Add(base_sim.Model)
        sm.Children.Add(Models.Storage.DataStore())
        add.Parameters = exchange_params
        for k, v in kwargs.items():
            if hasattr(add, k):
                setattr(add, k, v)
        model.Simulations = sm
        model.save()
        if verbose:
            logger.info(
                f"Switched sensitivity model from "
                f"{opposite_model.__name__} to {switch_to_model.__name__}"
            )
        return model


if __name__ == "__main__":
    from apsimNGpy import ApsimModel

    maize = ApsimModel('Factorial', 'out.apsimx')
    m = get_models_of_type(maize, 'Models.Manager')
    no_sim = get_model_paths_to_edit(maize, 'Models.Manager', 'Sow on a fixed date')
    w_sims = get_model_paths_to_edit(maize, 'Models.Manager', 'Sow on a fixed date',
                                     ['Base4'])
    edit_model_by_name(maize, 'Models.Manager', 'FertiliserRule', ApplicationAmount=177, simulations=['Base0'])
    maize.inspect_model_parameters('Models.Manager', 'Sow on a fixed date', parameters='Parameters')


    def _evaluate(model, model_type, model_name, **kwargs):
        edit_model_by_name(model, model_type, model_name, **kwargs)
        p = model.inspect_model_parameters(model_type, model_name, parameters=kwargs.values())


    with ApsimModel('Maize') as m1:
        edit_model_by_name(m1, 'Models.Summary', 'Summary', Name='sum')
        m1.save()
        print(m1.inspect_model('Models.Summary'))
        _evaluate(m1, 'Models.Clock', 'Clock', Name='sum2')
        m1.tree()
        edit_model_by_name(m1, 'Models.Surface.SurfaceOrganicMatter', 'SurfaceOrganicMatter', InitialCNR=85)
    with ApsimModel('Morris') as sob:
        switch_sensitivity_method(sob, 'sobol', num_path=104)
       # sob.open_in_gui(watch=True)
        sob.run()
        print(sob.results)
