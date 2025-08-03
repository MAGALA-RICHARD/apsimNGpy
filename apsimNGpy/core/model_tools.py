import pandas as pd
from pandas import to_datetime

from apsimNGpy.core import pythonet_config
from dataclasses import dataclass
from gc import collect
import Models
from typing import Union, Tuple
from System.Collections import IEnumerable
from System import String, Double, Array
from functools import lru_cache, cache
from typing import Union, Dict, Any
from Models.Soils import Soil, Physical, SoilCrop, Organic, Solute, Chemical
import warnings
from System.Collections.Generic import List
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.settings import *
from pathlib import Path
from apsimNGpy.core.config import load_crop_from_disk
from apsimNGpy.core.model_loader import load_apsim_model, get_node_by_path
from apsimNGpy.core_utils.cs_utils import simple_rotation_code, update_manager_code
from core_utils.database_utils import read_db_table
from apsimNGpy.core.pythonet_config import is_file_format_modified

IS_NEW_APSIM = is_file_format_modified()

from apsimNGpy.core_utils.cs_utils import CastHelper


@cache
def select_thread(multithread):
    if multithread:
        runtype = Models.Core.Run.Runner.RunTypeEnum.MultiThreaded
    else:
        runtype = Models.Core.Run.Runner.RunTypeEnum.SingleThreaded
    return runtype


select_thread(multithread=True)


def _tools(method):
    if hasattr(Models.Core.ApsimFile.Structure, 'Rename'):
        rename = Models.Core.ApsimFile.Structure.Rename
    else:
        rename = None
    config = {
        "ADD": Models.Core.ApsimFile.Structure.Add,
        "DELETE": Models.Core.ApsimFile.Structure.Delete,
        "MOVE": Models.Core.ApsimFile.Structure.Move,
        "RENAME": rename,
        "CLONER": Models.Core.Apsim.Clone,
        "REPLACE": Models.Core.ApsimFile.Structure.Replace,
        "MultiThreaded": Models.Core.Run.Runner.RunTypeEnum.MultiThreaded,
        "SingleThreaded": Models.Core.Run.Runner.RunTypeEnum.SingleThreaded,
        "ModelRUNNER": Models.Core.Run.Runner,
        "CLASS_MODEL": type(Models.Clock),
        "ACTIONS": ('get', 'delete', 'check'),
        "COLLECT": collect,
    }
    method = config[method]
    del config
    return method


@dataclass
class ModelTools:
    """
       A utility class providing convenient access to core APSIM model operations and constants.

       Attributes:
           ``ADD`` (callable): Function or class for adding components to an APSIM model.

           ``DELETE`` (callable): Function or class for deleting components from an APSIM model.

           ``MOVE`` (callable): Function or class for moving components within the model structure.

           ``RENAME`` (callable): Function or class for renaming components.

           ``CLONER`` (callable): Utility to clone APSIM models or components.

           ``REPLACE`` (callable): Function to replace components in the model.

           ``MultiThreaded`` (Enum): Enumeration value to specify multi-threaded APSIM runs.

           ``SingleThreaded`` (Enum): Enumeration value to specify single-threaded APSIM runs.

           ``ModelRUNNER`` (class): APSIM run manager that handles simulation execution.

           ``CLASS_MODEL`` (type): The type of the APSIM Clock model, often used for type checks or instantiation.

           ``ACTIONS`` (tuple): Set of supported string actions ('get', 'delete', 'check').

           ``COLLECT`` (callable): Function for forcing memory checks
       """
    ADD = _tools('ADD')
    DELETE = _tools('DELETE')
    MOVE = _tools('MOVE')
    RENAME = _tools('RENAME')
    CLONER = _tools('CLONER')
    REPLACE = _tools('REPLACE')
    MultiThreaded = _tools('MultiThreaded')
    SingleThreaded = _tools('SingleThreaded')
    ModelRUNNER = _tools('ModelRUNNER')
    CLASS_MODEL = _tools('CLASS_MODEL')
    ACTIONS = _tools('ACTIONS')
    COLLECT = _tools('COLLECT')
    String = String
    Double = Double
    Array = Array


ModelTools.ACTIONS
ModelTools.DELETE


def find_child(parent, child_class, child_name):
    parent = getattr(parent, 'Model', parent)
    if isinstance(child_class, str):
        child_class = validate_model_obj(child_class)

    for child in parent.Children:
        cast_child = CastHelper.CastAs[child_class](child)
        if child.Name == child_name and cast_child:
            return child
        # 🔁 Recursively search in child's children
        result = find_child(child, child_class, child_name)
        if result is not None:
            return result

    return None  # Not found


def find_all_in_scope(scope, child_class):
    all_in_scope = []

    if isinstance(child_class, str):
        child_class = validate_model_obj(child_class)

    for child in scope.Children:
        cast_child = CastHelper.CastAs[child_class](child)
        if cast_child:
            all_in_scope.append(child)

        # 🔁 Recursively search in this child's children
        child_results = find_all_in_scope(child, child_class)
        if child_results:
            all_in_scope.extend(child_results)

    return all_in_scope


def get_or_check_model(search_scope, model_type, model_name, action='get', cache_size=300):
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
            model_class : str
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

    def __excute(search_scope, model_type, model_name, action):
        if action not in ModelTools.ACTIONS:
            raise ValueError(f'sorry action should be any of {ModelTools.ACTIONS} ')
        # get bound methods based on model type
        try:
            finder = search_scope.FindInScope[model_type]
            get_model = finder(model_name) if model_name else finder()
        except AttributeError:
            get_model = find_child(search_scope, child_class=model_type, child_name=model_name)
        if action == 'check':
            return True if get_model is not None else False
        if not get_model and action == 'get':
            if model_type == 'Models.Core.Simulations' or model_type == Models.Core.Simulations:
                return search_scope
            raise ValueError(f"{model_name} of type {model_type} not found")

        if action == 'delete' and get_model:
            ModelTools.DELETE(get_model)
        if get_model and action == 'get':
            return get_model

    # if cacheit:
    #     __excute = lru_cache(maxsize=cache_size)(__excute)
    return __excute(search_scope, model_type, model_name, action)


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

    ITEMS = model_namespace.__dict__
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
    if model_type is None:
        model_type = getattr(Models.Surface, model_name, None)
    if model_type is None:
        model_type = getattr(Models.Core, model_name, None)
    if model_type is None:
        model_type = getattr(Models.Storage, model_name, None)
    collect()
    return model_type


@lru_cache(maxsize=300)
def validate_model_obj(model__type, evaluate_bound=False) -> ModelTools.CLASS_MODEL:
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
        if isinstance(bound_model, ModelTools.CLASS_MODEL):
            model_types = bound_model

        if model_types:
            return model_types
        else:
            raise ValueError(f"invalid model_class: '{model__type}' from type: {type(model__type)}")
    finally:
        # future implementation

        pass


def extract_value(model_instance, parameters=None):

    if isinstance(parameters, str):
        parameters = {parameters}


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

            validated = dict(End='End', Start='Start', end='End', start='Start', end_date='End', start_date='Start')
            accepted_attributes = {'Start', 'End'}
            selected_parameters = {validated.get(k) for k in parameters if
                                   validated.get(k) in accepted_attributes} if parameters else set()
            dif = accepted_attributes - selected_parameters
            if dif == accepted_attributes and parameters:
                raise ValueError(
                    f"To inspect the 'Clock Model Parameters:\n, Parameters must be None or any of '{', '.join(validated.keys())}'")
            attributes = selected_parameters or accepted_attributes

            if len(attributes) == 1:
                value = __convert_to_datetime(getattr(model_instance, *attributes))
            else:
                value = {atr: __convert_to_datetime(getattr(model_instance, atr)) for atr in attributes}

        case Models.Manager:
            selected_parameters = parameters if parameters else set()

            if selected_parameters:
                value = {param.Key: param.Value for param in model_instance.Parameters if
                         param.Key in selected_parameters}
            else:
                value = {param.Key: param.Value for param in model_instance.Parameters}
        case Models.Soils.Physical | Models.Soils.Chemical | Models.Soils.Organic | Models.Soils.Water | Models.Soils.Solute:
            # get selected parameters
            selected_parameters = {k for k in parameters if hasattr(model_instance, k)} if parameters else set()

            thick = getattr(model_instance, 'Thickness', None)

            df = pd.DataFrame()  # empty data frame
            attributes = selected_parameters or dir(model_instance)
            evp = [at for at in attributes if not at.startswith('__')]
            if not selected_parameters and parameters:
                raise ValueError(f"Parameters must be none or any of '{", \n".join(evp)}'")
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
            accepted_attributes = {'VariableNames', 'EventNames'}
            selected_parameters = {k for k in parameters if hasattr(model_instance, k)} if parameters else set()
            dif = accepted_attributes - selected_parameters
            if dif == accepted_attributes and parameters:
                raise ValueError(f"Parameters must be none or any of '{accepted_attributes}'")

            attributes = selected_parameters or accepted_attributes
            value = {}
            for attr in attributes:
                value[attr] = list(getattr(model_instance, attr))

        case Models.PMF.Cultivar:
            selected_parameters = set(parameters) if parameters else set()
            params = {}
            for cmd in model_instance.Command:
                if cmd:
                    if '=' in cmd:
                        key, val = cmd.split('=', 1)
                        params[key.strip()] = val.strip()
            if selected_parameters:
                value = {k: v for k, v in params.items() if k in selected_parameters}
                if not value:
                    raise ValueError(
                        f"None of '{selected_parameters}' was found. Available parameters are: '{', '.join(params.keys())}'")
            else:
                value = params
        case Models.Surface.SurfaceOrganicMatter:
            selected_parameters = set(parameters) if parameters else set()
            accepted_attributes = {'LyingWt', 'N', 'NH4', 'NO3', 'LabileP', 'SurfOM', 'P', "C", 'Cover',
                                   'InitialCPR', 'InitialResidueMass', 'StandingWt',
                                   'InitialCNR', 'InitialCPR'}
            dif = accepted_attributes - selected_parameters
            if len(dif) == len(accepted_attributes) and parameters:
                raise ValueError(f"Parameters must be none or any of '{', '.join(accepted_attributes)}'")
            params = {}
            attributes = selected_parameters or accepted_attributes
            for attrib in attributes:
                x_attrib = getattr(model_instance, attrib)
                params[attrib] = x_attrib

            value = params
        case _:
            raise NotImplementedError(f"No inspect input method implemented for model type: {type(model_instance)}")
    return value


def inspect_model_inputs(scope, model_type: str, model_name: str,
                         simulations: Union[str, list] = MissingOption,
                         parameters: Union[list, str] = None,
                         **kwargs) -> Union[Dict[str, Any], pd.DataFrame, list, Any]:
    """
    Inspect the current input values of a specific APSIM model type instance within given simulations.

    Parameters:
    -----------
    scope : ApsimNG model context with Models.Core.Simulations  and its associated Simulation
        Root scope or project object containing Simulations.
    model_class : str
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
        - For Clock: (start, end) dict(s) or datetime if any of parameters is one. To narrow down the inspection, accepted parameters are, Start and End supplied as a list or a str if any of them is needed,
        - For Manager: dictionary of parameters
        - For Soil models: pandas DataFrame(s) of layer-based properties
        - For Report: dictionary with 'VariableNames' and 'EventNames'. To narrow down the inspection, use 'VariableNames' and 'EventNames' supplied as a list or a str if any of them is needed,
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

    model_type_class = validate_model_obj(model_type)

    is_single_sim = True if isinstance(simulations, str) else False
    sim_list = scope.find_simulations(simulations)

    result = {} if not is_single_sim else None
    if isinstance(parameters, str):
        parameters = {parameters}
    for sim in sim_list:
        model_instance = find_child(sim, child_class= model_type_class, child_name=model_name)
        model_class = validate_model_obj(model_type_class)
        model_instance = CastHelper.CastAs[model_class](model_instance)
        value = extract_value(model_instance, parameters)
        if is_single_sim:
            return value
        else:
            result[sim.Name] = value

    return result


def replace_variable_by_index(old_list: list, new_value: list, indices: list):
    for idx, new_val in zip(indices, new_value):
        old_list[idx] = new_val
    return old_list


@lru_cache(maxsize=None)
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


def run_p(_model, simulations='all', clean=False, multithread=True):
    """Run apsim model in the simulations

    Parameters
    ----------
    ``_model`` : ApsimNGpy model object

    ``simulations`` (__str_), optional
        List of simulation names to run, if `None` runs all simulations, by default `None`.

    ``clean`` (_-boolean_), optional
        If `True` remove existing database for the file before running, deafults to False`.

    ``multithread``, optional
        If `True` APSIM uses multiple threads, by default `True`.

    """

    if clean:
        _model._DataStore.Dispose()
        Path(_model._DataStore.FileName).unlink(missing_ok=True)
        _model._DataStore.Open()

    if simulations == 'all':
        simulations = None
    sims = _model.find_simulations(simulations)  # returns a list
    print(sims)
    # Runner needs C# list
    cs_sims = List[Models.Core.Simulation]()
    for sim in sims:
        cs_sims.Add(sim)
    runmodel = Models.Core.Run.Runner(cs_sims, True, False, False, None, select_thread(multithread))
    e = runmodel.Run()
    if (len(e) > 0):
        logger.info(e[0].ToString())


def _edit_in_cultivar(_model, model_name, param_values, simulations=None, verbose=False):
    # if there is a need to target a specific simulation in case of changing the current culvar in simulation

    _cultivar_names = _model.inspect_model('Cultivar', fullpath=False)

    # Extract input parameters
    commands = param_values.get("commands")
    values = param_values.get("values")

    cultivar_manager = param_values.get("cultivar_manager")
    new_cultivar_name = param_values.get("new_cultivar_name", None)
    cultivar_manager_param = param_values.get("parameter_name", 'CultivarName')
    plant_name = param_values.get('plant')
    # Input validation
    required_keys = ["commands", "values", "cultivar_manager", "parameter_name", "new_cultivar_name"]
    # Extract input parameters
    missing = [key for key in required_keys if not param_values.get(key)]

    if missing:
        raise ValueError(f"Missing required parameter(s): {', '.join(missing)}")

    if isinstance(commands, (list, tuple)) or isinstance(values, (list, tuple)):
        assert isinstance(commands, (list, tuple)) and isinstance(values, (list, tuple)), \
            ("Both `commands` and `values` must be iterables (list or tuple), not sets or mismatched "
             "types")
        assert len(commands) == len(values), "`commands` and `values` must have the same length"

    # Get replacement folder and source cultivar model
    replacements = get_or_check_model(_model.Simulations, Models.Core.Folder, 'Replacements',
                                      action='get')

    get_or_check_model(replacements, Models.Core.Folder, 'Replacements',
                       action='delete')
    cultivar_fallback = get_or_check_model(_model.Simulations, Models.PMF.Cultivar, model_name,
                                           action='get', )
    cultivar = ModelTools.CLONER(cultivar_fallback)

    # Update cultivar parameters
    cultivar_params = _model._cultivar_params(cultivar)

    if isinstance(values, str):
        cultivar_params[commands] = values.strip()
    elif isinstance(values, (int, float)):
        cultivar_params[commands] = values
    else:
        for cmd, val in zip(commands, values):
            cultivar_params[cmd.strip()] = val.strip() if isinstance(val, str) else val

    # Apply updated commands
    updated_cmds = [f"{k.strip()}={v}" for k, v in cultivar_params.items()]
    cultivar.set_Command(updated_cmds)

    # Attach cultivar under a plant model
    plant_model = get_or_check_model(replacements, Models.PMF.Plant, plant_name,
                                     action='get')

    # Remove existing cultivar with same name
    get_or_check_model(replacements, Models.PMF.Cultivar, new_cultivar_name, action='delete')

    # Rename and reattach cultivar
    cultivar.Name = new_cultivar_name
    ModelTools.ADD(cultivar, plant_model)

    for sim in _model.find_simulations(simulations):
        # Update cultivar manager script
        _model.edit_model(model_type=Models.Manager, simulations=sim.Name,
                          model_name=cultivar_manager, **{cultivar_manager_param: new_cultivar_name})

    if verbose:
        logger.info(f"\nEdited Cultivar '{model_name}' and saved it as '{new_cultivar_name}'")
    _model.save()


def add_model(_model, parent, model):
    parent = validate_model_obj(parent)
    if callable(model):
        model = model()
    find_parent = _model.Simulations


def add_as_simulation(_model, resource, sim_name):
    model = load_apsim_model(resource)
    sim = model.IModel.FindDescendant[Models.Core.Simulation]()
    if sim is None:
        raise RuntimeError(f'simulation not found {model.IModel}')
    new_sim = sim
    names = _model.inspect_model(Models.Core.Simulation, fullpath=False)
    if sim_name in names:
        raise ValueError(f"new '{sim_name}' can not be any of '{",".join(names)}'")
    try:
        if IS_NEW_APSIM:
            new_sim.Rename(sim_name)
        else:
            new_sim.Name = sim_name
        model.Simulations.sim_name = sim_name
        _model.Simulations.Children.Add(new_sim)

        ModelTools.DELETE(sim)
        return model
    finally:
        os.remove(model.path)


def detect_sowing_managers(_model):
    managers = _model.Simulations.FindAllDescendants[Models.Manager]()
    if managers is not None:
        for manager in managers:
            code = manager.Code
            if code is not None:
                if 'Crop.Sow' in code and 'using Models.PMF' in code and 'IPlant' in code:
                    return manager


def configure_rotation(_model, simulations=None):
    manager = Models.Manager()
    manager.set_Code(simple_rotation_code)
    model_sims = _model.simulations
    if simulations is None:
        new_sim = _model.simulations
    else:
        if isinstance(simulations, str):
            sims = [simulations]
        else:
            sims = simulations
        new_sim = [si for si in model_sims if si.Name in sims]
    for sim in new_sim:
        zone = sim.FindDescendant[Models.Core.Zone]()
        zone.Children.Add(manager)
    man = detect_sowing_managers(_model)
    update = update_manager_code(man.Code, description="Simple Rotation Manager", typeof='Manager', var_name='rotation')
    new_manager = Models.Manager()
    new_manager.Rename('rots')
    new_manager.set_Code(update)
    for sim in new_sim:
        zone = sim.FindDescendant[Models.Core.Zone]()
        zone.Children.Add(new_manager)

    _model.save()
    return _model
def add_method_to_model_tools(method):
    setattr(ModelTools, method.__name__, method)

def add_replacement_folder(simulations):

    rep_old = find_child(simulations, child_class=Models.Core.Folder, child_name='Replacements')
    if not rep_old:
        folder = Models.Core.Folder()
        try:
            folder.Rename('Replacements')
        except AttributeError:
            folder.Name = "Replacements"
        simulations.Children.Add(folder)
def add_model_as_a_replacement(simulations, model_class, model_name):
    if isinstance(model_class, str):
        model_class =validate_model_obj(model_class)
    model = model_class()
    model.Name = model_name
    if model_class == Models.PMF.Plant:
        model.ResourceName = model_name
    add_replacement_folder(simulations)
    rep_old = find_child(simulations, child_class=Models.Core.Folder, child_name='Replacements')
    if rep_old:
        # find weather requested model exists, remove or do nothing
        model_exists = find_child(rep_old, child_class=model_class, child_name=model_name)
        if not model_exists:
           rep_old.Children.Add(model)
    # check again before exiting caller
    model_exists = find_child(rep_old, child_class=model_class, child_name=model_name)
    if not model_exists:
        raise RuntimeError(f"failed to add model of class{model_class} with identification name: {model_name}")

collect()
add_method_to_model_tools(find_child)
add_method_to_model_tools(find_all_in_scope)
add_method_to_model_tools(add_replacement_folder)

if __name__ == "__main__":
    ...
