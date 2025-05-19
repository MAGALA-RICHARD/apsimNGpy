import pandas as pd
from pandas import to_datetime

from apsimNGpy.core import pythonet_config
from dataclasses import dataclass
from gc import collect
import Models
from typing import Union, Tuple
from System.Collections import IEnumerable
from System import String

from typing import Union, Dict, Any
from Models.Soils import Soil, Physical, SoilCrop, Organic, Solute, Chemical
import warnings
@dataclass
class ModelTools:
    """
       A utility class providing convenient access to core APSIM model operations and constants.

       Attributes:
           ADD (callable): Function or class for adding components to an APSIM model.
           DELETE (callable): Function or class for deleting components from an APSIM model.
           MOVE (callable): Function or class for moving components within the model structure.
           RENAME (callable): Function or class for renaming components.
           CLONER (callable): Utility to clone APSIM models or components.
           REPLACE (callable): Function to replace components in the model.
           MultiThreaded (Enum): Enumeration value to specify multi-threaded APSIM runs.
           SingleThreaded (Enum): Enumeration value to specify single-threaded APSIM runs.
           ModelRUNNER (class): APSIM run manager that handles simulation execution.
           CLASS_MODEL (type): The type of the APSIM Clock model, often used for type checks or instantiation.
           ACTIONS (tuple): Set of supported string actions ('get', 'delete', 'check').
           COLLECT (callable): Function for collecting or extracting model data (e.g., results, nodes).
       """
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



def inspect_model_inputs(scope, model_type: str, simulations: Union[str, list], model_name: str, parameters:Union[list, str] =None,
                         **kwargs) -> Union[Dict[str, Any], pd.DataFrame, list, Any]:
    """
    Inspect the current input values of a specific APSIM model type instance within given simulations.

    Parameters:
    -----------
    scope : ApsimNG model context with Models.Core.Simulations  and its associated Simulation
        Root scope or project object containing Simulations.
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
        - For Clock: (start, end) tuple(s). To narrow down the inspection, accepted parameters are, Start and End supplied as a list or a str if any of them is needed,
        - For Manager: dictionary of parameters
        - For Soil models: pandas DataFrame(s) of layer-based properties
        - For Report: dictionary with 'VariableNames' and 'EventNames'. To narrow down the inspection, 'VariableNames' and 'EventNames' supplied as a list or a str if any of them is needed,
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
    if isinstance(parameters, str):
        parameters = {parameters}
    for sim in sim_list:
        model_instance = get_or_check_model(sim, model_type_class, model_name, action='get')

        match type(model_instance):
            case Models.Climate.Weather:
                value = model_instance.FileName
            case Models.Clock:
                import datetime
                def __convert_to_datetime(dotnet_dt):
                   return datetime.datetime(
                        dotnet_dt.Year,
                        dotnet_dt.Month,
                        dotnet_dt.Day,
                        dotnet_dt.Hour,
                        dotnet_dt.Minute,
                        dotnet_dt.Second,
                        dotnet_dt.Millisecond * 1000  # Python uses microseconds
                    )

                accepted_attributes = {'Start', 'End'}
                selected_parameters = {k.capitalize() for k in parameters if hasattr(model_instance, k)} if parameters else set()
                dif = accepted_attributes - selected_parameters
                if dif==accepted_attributes and parameters:
                    raise ValueError(f"Parameters must be none or any of '{accepted_attributes}'")
                attributes = selected_parameters or accepted_attributes

                if len(attributes) == 1:
                   value = __convert_to_datetime(getattr(model_instance, *attributes))
                else:
                   value = tuple(__convert_to_datetime(getattr(model_instance, atr)) for atr in attributes)

            case Models.Manager:
                selected_parameters = parameters if parameters else set()

                if selected_parameters:
                    value  = {param.Key: param.Value for param in model_instance.Parameters if param.Key in selected_parameters}
                else:
                    value = {param.Key: param.Value for param in model_instance.Parameters}
            case Models.Soils.Physical | Models.Soils.Chemical | Models.Soils.Organic | Models.Soils.Water:
                # get selected parameters
                selected_parameters = {k for k in parameters if hasattr(model_instance, k)} if parameters else set()

                thick = getattr(model_instance, 'Thickness', None)

                df = pd.DataFrame() # empty data frame
                attributes = selected_parameters or dir(model_instance)
                if thick:
                    for attr in attributes:
                        if attr.startswith('__'):
                            continue
                        val = getattr(model_instance, attr)
                        if isinstance(val, IEnumerable) and not isinstance(val, String):
                            val_list = list(val)
                            if len(val_list) == len(thick):
                                df[attr] = val_list
                value = df
            case Models.Report:
                accepted_attributes= {'VariableNames',  'EventNames'}
                selected_parameters = {k for k in parameters if hasattr(model_instance, k)} if parameters else set()
                dif =  accepted_attributes - selected_parameters
                if dif==accepted_attributes and parameters:
                    raise ValueError(f"Parameters must be none or any of '{accepted_attributes}'")

                attributes = selected_parameters or accepted_attributes
                value = {}
                for attr in attributes:
                    value[attr] = list(getattr(model_instance, attr))

            case Models.PMF.Cultivar:
                selected_parameters = parameters if parameters else set()
                params = {}
                for cmd in model_instance.Command:
                    if cmd:
                        if '=' in cmd:
                            key, val = cmd.split('=', 1)
                            params[key.strip()] = val.strip()
                if selected_parameters:
                    value = {k:v for k, v in params.items() if k in selected_parameters}
                    if not value:
                        raise ValueError(f"None of '{selected_parameters}' was found. Available parameters are: '{', '.join(params.keys())}'")
                else:
                    value = params
            case _:
                raise NotImplementedError(f"No inspect input method implemented for model type: {type(model_instance)}")

        if is_single_sim:
            return value
        else:
            result[sim.Name] = value

    return result



def replace_variable_by_index(old_list: list, new_value: list, indices: list):
    for idx, new_val in zip(indices, new_value):
        old_list[idx] = new_val
    return old_list


def soil_components(component):
    _comp = component.lower()
    comps = {'organic': Organic,
             'physical': Physical,
             'soilcrop': SoilCrop,
             'solute': Solute,
             'chemical': Chemical,
             }
    return comps[_comp]

def old_method(old_method, new_method):
    warnings.warn(
        f"{old_method} is deprecated and will be removed in a future release/version. Please use {new_method}() instead.",
        category=DeprecationWarning,
        stacklevel=2
    )
    # method logic here


collect()