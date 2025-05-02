import pandas as pd
from apsimNGpy.core import pythonet_config
from dataclasses import dataclass
from gc import collect
import Models
from typing import Union, Tuple
from System.Collections import IEnumerable
from System import String

from typing import Union, Dict, Any


@dataclass
class ModelTools:
    ADD = Models.Core.ApsimFile.Structure.Add
    DELETE = Models.Core.ApsimFile.Structure.Delete
    MOVE = Models.Core.ApsimFile.Structure.Move
    RENAME = Models.Core.ApsimFile.Structure.Rename
    CLONER = Models.Core.Apsim.Clone
    REPLACE = Models.Core.ApsimFile.Structure.Replace
    MultiThreaded = Models.Core.Run.Runner.RunTypeEnum.MultiThreaded
    SingleThreaded = Models.Core.Run.Runner.RunTypeEnum.SingleThreaded
    ModelRUNNER = Models.Core.Run.Runner
    CLASS_MODEL = type(Models.Clock)
    ACTIONS = ('get', 'delete', 'check')
    COLLECT = collect


def get_or_check_model(search_scope, model_type, model_name, action='get'):
    """
            Helper function to check if a model instance is found in the simulation
            and perform a specified action.

            Actions supported:
            - 'get': returns the found model.
            - 'delete': deletes the model.
            - 'check': returns True/False depending on whether the model exists.

            Parameters:
            -----------
            sim : ApsimSimulation
                The APSIM simulation object.
            model_type : str
                The type of model to search for (e.g., 'Soil', 'Manager').
            model_name : str, optional
                The name of the model to find. If omitted, returns the first model of that type.
            action : str
                One of 'get', 'delete', or 'check'.

            Returns:
            --------
            object or bool or None
                - The found model if action is 'get'.
                - True/False if action is 'check'.
                - None if action is 'delete'.

            Raises:
            -------
            ValueError
                If the model is not found (when action is 'get' or 'delete'),
                or if an invalid action is specified.
            """

    if action not in ModelTools.ACTIONS:
        raise ValueError(f'sorry action should be any of {ModelTools.ACTIONS} ')
    # get bound methods based on model type
    finder = search_scope.FindInScope[model_type]
    get_model = finder(model_name) if model_name else finder()
    if action == 'check':
        return True if get_model is not None else False
    if not get_model and action == 'get':
        raise ValueError(f"{model_name} of type {model_type} not found")

    if action == 'delete' and get_model:
        ModelTools.DELETE(get_model)
    if get_model and action == 'get':
        return get_model

def _find_model(model_name: str, model_namespace=Models, target_type=ModelTools.CLASS_MODEL) -> ModelTools.CLASS_MODEL:
    """
    Recursively find a model by name within a namespace.

    Args:
        model_name (str): The name of the model to find.
        model_namespace (object, optional): The root namespace (defaults to Models).
        target_type (type, optional): Expected type of the model.

    Returns:
        object: The found model object, or None if not found.
    """

    if not hasattr(model_namespace, "__dict__"):
        return None

    ITEMS =  model_namespace.__dict__
    if isinstance(model_name, str):
        model_name = model_name.capitalize()
    for attr, value in ITEMS.items():
        if attr == model_name and isinstance(value, target_type):
            return value

        _get_attr = getattr(value, model_name, None)

        if isinstance(_get_attr, target_type):
                return _get_attr

        if hasattr(value, "__dict__"):

            result = _find_model(model_name, value, target_type=target_type)
            if result:
                return result
    # recursion is complete but model is none

    return None


def find_model(model_name: str):
    model_type = _find_model(model_name)
    if model_type:
        return model_type
    # for some unknown reasons Models.Factorial namespace is not featuring so let's do it mannually here
    import Models
    if model_type is None:
        model_type = getattr(Models.Factorial, model_name, None)
    collect()
    return model_type

def _eval_model(model__type, evaluate_bound=False) -> ModelTools.CLASS_MODEL:
    """
    Evaluates the model type from either string or Models namespace
    @param model__type (str,Models, required)
    it can also accept either string or Models namespace as single letter specifying the final model or as a whole path e.g 'Models.Clock' and 'Clock' are all valid
         'Clock', 'Simulation', 'Manager', 'Report','Simulations', 'Weather', 'Soil
    @return:
       model type from Models namespace

    :Raises
       raises a ValueError if model__type is not valid or found from the Models namespace
    """
    import Models
    model_types = None
    bound_model = None
    try:
        if isinstance(model__type, str):
            _model_name_space = 'Models.'
            ln = len(_model_name_space)
            # find _find_model could be sufficent, where we only allow the user to supply a single name but we dont know whether some names repeated on some models
            if find_model(model__type):
                from_single = find_model(model__type)
                if from_single is not None:
                    return from_single
            if model__type[:ln] == _model_name_space:
                _model_type = eval(model__type)
                bound_model = _model_type.__class__
                if isinstance(_model_type, ModelTools.CLASS_MODEL):
                    model_types = _model_type

        if isinstance(model__type, ModelTools.CLASS_MODEL):
            model_types = model__type

        if evaluate_bound and not isinstance(model__type, str):
            bound_model = model__type.__class__
        if isinstance(bound_model,ModelTools.CLASS_MODEL):

            model_types = bound_model

        if model_types:
            return model_types
        else:
            raise ValueError(f"invalid model_type: '{model__type}' from type: {type(model__type)}")
    finally:
        # future implimentation

        pass



def inspect_model_inputs(scope, model_type: str, simulations: Union[str, list], model_name: str, **kwargs) -> Union[Dict[str, Any], pd.DataFrame, list, Any]:
    """
    Inspect the current input values of a specific APSIM model type instance within given simulations.

    Parameters:
    -----------
    scope : ApsimNG model context
        Root scope or project object containing simulations.
    model_type : str
        Name of the model class (e.g., 'Clock', 'Manager', 'Soils.Physical', etc.)
    simulations : Union[str, list]
        Name or list of names of simulation(s) to inspect.
    model_name : str
        Name of the model instance within each simulation.
    **kwargs : dict
        Optional keyword arguments — not used here but accepted for interface compatibility.

    Returns:
    --------
    Union[Dict[str, Any], pd.DataFrame, list, Any]
        - For Weather: file path(s)
        - For Clock: (start, end) tuple(s)
        - For Manager: dictionary of parameters
        - For Soil models: pandas DataFrame(s) of layer-based properties
        - For Report: dictionary with 'VariableNames' and 'EventNames'
        - For Cultivar: dictionary of parsed parameter=value pairs

    Raises:
    -------
    ValueError:
        If model is not found or invalid arguments are passed.
    NotImplementedError:
        If the model type is unsupported.

    Requirements:
    -------------
    - APSIM Next Gen Python bindings (apsimNGpy)
    - Python 3.10+
    """
    model_type_class = _eval_model(model_type)

    is_single_sim = isinstance(simulations, str)
    sim_list = scope.find_simulations(simulations)
    result = {} if not is_single_sim else None

    for sim in sim_list:
        model_instance = get_or_check_model(sim, model_type_class, model_name, action='get')

        match type(model_instance):
            case Models.Climate.Weather:
                value = model_instance.FileName
            case Models.Clock:
                value = (model_instance.Start, model_instance.End)
            case Models.Manager:
                value = {param.Key: param.Value for param in model_instance.Parameters}
            case Models.Soils.Physical | Models.Soils.Chemical | Models.Soils.Organic | Models.Soils.Water:
                thick = getattr(model_instance, 'Thickness', None)
                df = pd.DataFrame()
                if thick:
                    for attr in dir(model_instance):
                        if attr.startswith('__'):
                            continue
                        val = getattr(model_instance, attr)
                        if isinstance(val, IEnumerable) and not isinstance(val, String):
                            val_list = list(val)
                            if len(val_list) == len(thick):
                                df[attr] = val_list
                value = df
            case Models.Report:
                value = {
                    'VariableNames': list(model_instance.VariableNames),
                    'EventNames': list(model_instance.get_EventNames())
                }
            case Models.PMF.Cultivar:
                params = {}
                for cmd in model_instance.Command:
                    if cmd:
                        if '=' in cmd:
                            key, val = cmd.split('=', 1)
                            params[key.strip()] = val.strip()
                value = params
            case _:
                raise NotImplementedError(f"No inspect input method implemented for model type: {type(model_instance)}")

        if is_single_sim:
            return value
        else:
            result[sim.Name] = value

    return result

collect()