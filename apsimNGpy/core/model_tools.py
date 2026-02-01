import warnings
from array import array
from dataclasses import dataclass
from functools import lru_cache, cache
from gc import collect
from typing import Union, Dict, Any
import pandas as pd
from apsimNGpy.core.pythonet_config import CLR
# These should be below CLR imports
from System import String, Double, Array
from System.Collections import IEnumerable
from System.Collections.Generic import List, KeyValuePair

from apsimNGpy.core.cs_resources import simple_rotation_code, update_manager_code
from apsimNGpy.core.model_loader import load_apsim_model
from apsimNGpy.core.version_inspector import is_higher_apsim_version
from apsimNGpy.core_utils.utils import is_scalar
from apsimNGpy.settings import *

Models = CLR.Models
Physical, SoilCrop, Organic, Solute, Chemical = Models.Soils.Physical, Models.Soils.SoilCrop, Models.Soils.Organic, Models.Soils.Solute, Models.Soils.Chemical
IS_NEW_APSIM = CLR.file_format_modified

from apsimNGpy.core.cs_resources import CastHelper, sow_using_variable_rule, sow_on_fixed_date, harvest, \
    fertilizer_at_sow, cast_as

APSIM_VERSION = CLR.apsim_compiled_version


def _add_model(model, parent) -> None:
    """
    Adds a model node from the model tree based on the file structure.
    @param model: model to add to the parent.
    @param parent: parent model where to add the model.
    @return: None
    """
    if hasattr(Models.Core, 'ApsimFile'):
        Models.Core.ApsimFile.Structure.Add(model, parent)
    else:
        parent.Children.Add(model)


def _delete_node(node) -> None:
    """
    deletes a node from the model tree based on the file structure
    @param node:
    @return: None
    """
    if hasattr(Models.Core, 'ApsimFile'):
        Models.Core.ApsimFile.Structure.Delete(node)
    else:
        Node  = CLR.Node
        node = getattr(node, 'Node', node)
        Node.Clear(node)


@cache
def select_thread(multithread):
    if multithread:
        runtype = Models.Core.Run.Runner.RunTypeEnum.MultiThreaded
    else:
        runtype = Models.Core.Run.Runner.RunTypeEnum.SingleThreaded
    return runtype


select_thread(multithread=True)


@cache
def _tools(method):
    if hasattr(Models.Core, 'ApsimFile'):
        FileTools = {
            "MOVE": Models.Core.ApsimFile.Structure.Move,
            "REPLACE": Models.Core.ApsimFile.Structure.Replace,
            "RENAME": getattr(Models.Core.ApsimFile.Structure, 'Rename', None)
        }
    else:
        FileTools = {}
    config = {
        "ADD": _add_model,
        "DELETE": _delete_node,
        "CLONER": Models.Core.Apsim.Clone,
        "MultiThreaded": Models.Core.Run.Runner.RunTypeEnum.MultiThreaded,
        "SingleThreaded": Models.Core.Run.Runner.RunTypeEnum.SingleThreaded,
        "ModelRUNNER": Models.Core.Run.Runner,
        "CLASS_MODEL": type(Models.Clock),
        "ACTIONS": ('get', 'delete', 'check'),
        "COLLECT": collect,
        **FileTools}
    method = config.get(method)
    del config
    return method


CLASS_MODEL = _tools('CLASS_MODEL')


def find_child(parent, child_class, child_name):
    parent = getattr(parent, 'Model', parent)
    if isinstance(child_class, str):
        child_class = validate_model_obj(child_class)
    _children = getattr(parent, "Children", None)
    if _children is None:
        _children = parent.GetChildren()
    for child in _children:
        cast_child = CastHelper.CastAs[child_class](child)
        if child.Name == child_name and cast_child:
            # child = CastHelper.CastAs[child_class](child)
            return child
        #  Recursively search in child's children
        result = find_child(child, child_class, child_name)
        if result is not None:
            return result

    return None  # Not found


def find_all_in_scope(parent, child_class):
    """

    @param parent: base model scope to search
    @param child_class: Model class from the Models namespace to search for
    @return: list[Models.Core.IModel] objects
    """

    all_in_scope = []
    if isinstance(child_class, str):
        child_class = validate_model_obj(child_class)

    for child in parent.Children:
        cast_child = CastHelper.CastAs[child_class](child)

        if cast_child:
            all_in_scope.append(cast_child)

        # 🔁 Recursively search in this child's children
        child_results = find_all_in_scope(child, child_class)
        if child_results:
            all_in_scope.extend(child_results)
    return tuple(all_in_scope)


def find_descendant(parent, child_class):
    parent = getattr(parent, 'Model', parent)
    if isinstance(child_class, str):
        child_class = validate_model_obj(child_class)
    for child in parent.Children:
        cast_child = CastHelper.CastAs[child_class](child)
        if cast_child:
            # child = CastHelper.CastAs[child_class](child)
            return child
        # 🔁 Recursively search in child's children
        result = find_descendant(child, child_class)
        if result is not None:
            return result


def find_child_of_class(parent, child_class):
    """
    Finds a child with a break. Equivalent to old method of FindDescendant. can return None if no child

    """
    return find_descendant(parent, child_class)


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

    def _execute(search_scope, model_type, model_name, action):
        if action not in ModelTools.ACTIONS:
            raise ValueError(f'sorry action should be any of {ModelTools.ACTIONS} ')
        # get bound methods based on model type
        try:
            finder = search_scope.FindIDescendant[model_type]
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

    return _execute(search_scope, model_type, model_name, action)


def _find_model(model_name: str, model_namespace=Models, target_type=CLASS_MODEL) -> CLASS_MODEL:
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

    ITEMS = model_namespace.__dict__.copy()
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
    Models = CLR.Models
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
def validate_model_obj(model__type, evaluate_bound=False) -> CLASS_MODEL:
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
        case Models.WaterModel.WaterBalance:
            to_descr = {}
            desc = dict(Salib='Fraction of incoming solar radiation',
                        WinterU='Cumulative soil water evaporation to reach end of stage 1 soil water evaporation in winter',
                        SummerU='Cumulative soil water evaporation to reach end of stage 1 soil water evaporation in winter',
                        PSIDul='Matric Potential at DUL (cm)',
                        CNCov='Cover for maximum curve number reduction',
                        DiffusSlope='effect of soil water storage above the lower limit on on soil water diffusivity (mm)',
                        DischargeWidth='Basal width of the down slope boundary of the catchment for lateral flow calculations',
                        SummerCona='Drying coefficient for stage 2 soil water evaporation in summer',
                        DiffusConst='Constant in soil water diffusivity calculations',
                        CN2Bare='Run off curve number ofr bare soil with average moisture',
                        CatchmentArea='Catchment area flow calculations (m2)',
                        WinterDate='Start date to switch to winter parameters',
                        WinterCona='Drying coefficient for stage 2 soil water evaporation in winter',
                        SummerDate='Start date to switch to summer parameters',
                        )
            collections = {}
            list_params = {'KLAT', 'Depth', 'SWCON'}
            non_list = {'Salb', 'Water', 'WinterU', 'WinterDate', 'WinterCona', 'SummerCona', 'SummerDate',
                        'PrecipitationInterception',
                        'PoreInteractionIndex',
                        'SummerU', 'DiffusSlope',
                        'DischargeWidth',
                        'DiffusConst',
                        'CN2Bare',
                        'CatchmentArea',
                        'CNCov',
                        'PSIDul',
                        'SummerCona',
                        'SWmm',
                        'Runoff',
                        'PotentialInfiltration'}

            if not parameters:
                parameters = list_params.union(non_list)
            if parameters:
                for p in parameters:
                    hasattr(model_instance, p)
                    if p in list_params:
                        attrib_val = getattr(model_instance, p)
                        collections[p] = list(attrib_val) if attrib_val is not None else None
                    else:
                        collections[p] = getattr(model_instance, p)
                        to_descr[p] = desc.get(p)
            collections['dictionary'] = desc
            value = collections

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
    if isinstance(parameters, str):
        parameters = {parameters}
    reps = scope.get_replacements_node()
    if reps:
        model_ins = find_child(reps, model_type_class, model_name)
        if model_ins:
            modelIN = CastHelper.CastAs[model_type_class](model_ins)
            return extract_value(modelIN, parameters)

    is_single_sim = True if isinstance(simulations, str) else False
    sim_list = scope.find_simulations(simulations)

    result = {} if not is_single_sim else None

    for sim in sim_list:
        model_instance = find_child(sim, child_class=model_type_class, child_name=model_name)
        model_class = validate_model_obj(model_type_class)
        model_instance = CastHelper.CastAs[model_class](model_instance)
        value = extract_value(model_instance, parameters)
        if is_single_sim:
            return value
        else:
            result[sim.Name] = value

    return result


def replace_variable_by_index(
        old_list: List,
        new_value: Union[List, str, array, int, float],
        indices: Union[List[int], None]
) -> List:
    """
    Replace one or more values in a list-like structure at the specified indices.

    This utility is designed for editing APSIM array-style attributes (e.g.,
    ``double[]`` arrays exposed through pythonnet). It supports replacing
    individual elements or slices of the array when calibrating or manipulating
    parameters programmatically.

    Parameters
    ----------
    old_list : list
        The original Python list to be modified. In typical APSIM workflows,
        this is produced by converting a ``System.Double[]`` into a native list.
    new_value : list, str, array, int, or float
        The new value(s) to insert into ``old_list``. If a scalar (str, int,
        float), it is automatically wrapped into a list. ``set`` objects are not
        allowed because sets are unordered.
    indices : list of int or None
        The list of indices at which to apply the new values. If ``None``,
        replacement proceeds from the beginning of the list in order.

    Returns
    -------
    list
        The modified list with updated values.

    Raises
    ------
    TypeError
        If ``new_value`` is a set (unordered and therefore invalid).
    AssertionError
        If ``indices`` is provided and the number of indices does not match
        the number of replacement values.

    Notes
    -----
    - When editing APSIM arrays (``System.Double[]``), they must first be
      converted to Python lists before assignment.
    - The caller is responsible for reassigning the edited list back to
      the APSIM model attribute.
    """

    if isinstance(new_value, set):
        raise TypeError("`set` data type is not allowed because it is not ordered.")

    # normalize scalar values into a list
    if is_scalar(new_value):
        new_value = [new_value]
    if indices is not None and is_scalar(indices) and len(new_value) == 1:
        indices = [indices]
    # indexed replacement
    if len(new_value) > len(old_list):
        raise ValueError(
            f' length of new_values{new_value} are more than the current values {old_list} expected not more than {len(old_list)}\n got {len(new_value)} values')
    if indices is not None:
        assert len(indices) == len(new_value), (
            "If indices are provided, the number of indices must match "
            "the number of replacement values."
        )
        for idx, new_val in zip(indices, new_value):
            old_list[idx] = new_val
    else:
        # sequential replacement
        for idx, v in enumerate(new_value):
            old_list[idx] = v
    return old_list


def edit_instance_attributes(model_instance: "Models", **kwargs):
    """
    Edit attributes on an APSIM model instance, including APSIM array attributes.

    This function provides a unified interface for modifying both scalar and
    array-type attributes on APSIM model objects accessed via pythonnet. It
    automatically handles conversion of ``System.Double[]`` attributes into
    Python lists, performs indexed replacements when required, and reassigns
    modified values back to the model instance.

    Parameters
    ----------
    model_instance : Models
        The APSIM model instance whose attributes should be modified.
    **kwargs :
        Arbitrary keyword arguments representing attribute names and their new
        values. An optional ``indices`` argument may be supplied to specify
        which positions in an array attribute should be edited.

        Examples
        --------
        ``edit_instance_attributes(model, KLAT=[0.1, 0.2, 0.3])``

        ``edit_instance_attributes(model, SWCON=[0.3], indices=[2])``

    Special Keyword Arguments
    -------------------------
    indices : list of int, optional
        If provided, applies the new value(s) only at the specified positions
        within the attribute (used for APSIM arrays).

    Returns
    -------
    None

    Raises
    ------
    AttributeError
        If an attribute specified in ``kwargs`` does not exist on the APSIM
        model instance.
    TypeError
        If a provided value is invalid (e.g., a set where ordering matters).

    Notes
    -----
    - APSIM ``double[]`` arrays exposed through pythonnet appear as
      ``System.Double[]``. These arrays must be converted into Python lists
      before editing and reassigned back after modification.
    - Scalar attributes are assigned directly.
    """
    indices = kwargs.get("indices", None)
    kwargs.pop("indices", None)  # prevent interference with actual attribute names

    for attr_name, new_value in kwargs.items():

        if not hasattr(model_instance, attr_name):
            raise AttributeError(
                f"Attribute '{attr_name}' not found on model instance at path "
                f"{model_instance.FullPath} (type: {type(model_instance).__name__})"
            )

        current_value = getattr(model_instance, attr_name)

        # APSIM array attribute → System.Double[]
        if isinstance(current_value, Array[Double]):
            # convert APSIM array → Python list
            py_list = list(current_value)

            # edit the list
            edited = replace_variable_by_index(py_list, new_value, indices=indices)

            # assign back as a list; APSIM model will accept it and convert internally
            setattr(model_instance, attr_name, edited)

        else:
            # scalar attribute → assign directly
            setattr(model_instance, attr_name, new_value)


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


def _edit_in_cultivar(_model, model_name, param_values, simulations=None, verbose=False, by_path=False):
    # if there is a need to target a specific simulation in case of changing the current cultvar in simulation

    _cultivar_names = _model.inspect_model('Cultivar', fullpath=False)

    # Extract input parameters
    commands = param_values.get("commands")
    if isinstance(commands, dict):
        commands, values = commands.items()
    if not isinstance(commands, dict):
        values = param_values.get("values")
        if values is None:
            raise ValueError(f"expected values to be a str or a sequence of values provided {values}")
    values = param_values.get("values")

    cultivar_manager = param_values.get("cultivar_manager")
    new_cultivar_name = param_values.get("new_cultivar_name", None)
    cultivar_manager_param = param_values.get("parameter_name", 'CultivarName')
    plant_name = param_values.get('plant')
    # Input validation
    required_keys = ["commands", "values", "cultivar_manager", "parameter_name", "new_cultivar_name"]
    if by_path:
        required_keys = ["commands", "values"]
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
        cultivar_params[commands] = values.strip()  # direct update
    elif is_scalar(values):
        cultivar_params[commands] = values  # direct update
    else:
        for cmd, val in zip(commands, values):  # esle iterate
            cultivar_params[cmd.strip()] = val.strip() if isinstance(val, str) else val

    # Apply updated commands
    updated_cmds = [f"{k.strip()}={v}" for k, v in cultivar_params.items()]
    if hasattr(cultivar, 'set_Command'):
        cultivar.set_Command(updated_cmds)
    else:
        cultivar.Command = updated_cmds

    # Attach cultivar under a plant model
    plant_model = get_or_check_model(replacements, Models.PMF.Plant, plant_name,
                                     action='get')

    # Remove existing cultivar with same name
    get_or_check_model(replacements, Models.PMF.Cultivar, new_cultivar_name, action='delete')

    # Rename and reattach cultivar
    cultivar.Name = new_cultivar_name
    if not by_path:
        ModelTools.ADD(cultivar, plant_model)
    if not by_path:
        for sim in _model.find_simulations(simulations):
            # Update cultivar manager script
            _model.edit_model(model_type=Models.Manager, model_name=cultivar_manager, simulations=sim.Name,
                              **{cultivar_manager_param: new_cultivar_name})

    if verbose:
        logger.info(f"\nEdited Cultivar '{model_name}' and saved it as '{new_cultivar_name}'")
    _model.save()


def load_parameters(**kwargs):
    params = List[KeyValuePair[String, String]]()
    for k, v in kwargs.items():
        kv = KeyValuePair[String, String](String(k), String(str(v)))
        params.Add(kv)
    return params


def add_model(_model, parent, model):
    parent = validate_model_obj(parent)
    if callable(model):
        model = model()
    find_parent = _model.Simulations


def add_as_simulation(_model, resource, sim_name):
    """
    Get a simulation from another file or model and it to the current apsimNGpy model simulation
    _model: apsimNgpy.core.apsim.ApsimModel,
    resource: source of the simulation file,
    sim_name, new name to name the added simulation
    """
    model = load_apsim_model(resource)

    try:
        sim = model.IModel.FindDescendant[Models.Core.Simulation]()
    except AttributeError:
        sim = find_child_of_class(model.IModel, Models.Core.Simulation)
    if sim is None:
        raise RuntimeError(f'simulation not found {model.IModel}')
    new_sim = sim
    names = _model.inspect_model(Models.Core.Simulation, fullpath=False)
    if sim_name in names:
        raise ValueError(f"new '{sim_name}' can not be any of '{",".join(names)}'")
    try:
        if IS_NEW_APSIM:
            try:
                new_sim.Rename(sim_name)
            except AttributeError:
                new_sim.Name = sim_name

        else:
            new_sim.Name = sim_name
        model.Simulations.sim_name = sim_name
        _model.Simulations.Children.Add(new_sim)

        ModelTools.DELETE(sim)
        return model
    finally:
        os.remove(model.path)


def detect_sowing_managers(_model):
    if is_higher_apsim_version(_model.Simulations):
        managers = find_all_in_scope(_model.Simulations, Models.Manager)
    else:
        managers = _model.Simulations.FindAllDescendants[Models.Manager]()
    if managers is not None:
        for manager in managers:
            code = manager.Code
            if code is not None:
                if 'Crop.Sow' in code and 'using Models.PMF' in code and 'IPlant' in code:
                    return manager


def compile_manager(code):
    manager = Models.Manager()
    manager.set_Code(code)
    return manager


planting_info = {'seq': 'Maize, Soybean', 'in_crop': ('Maize',)}


def configure(app, seq: Union[str, tuple, list], in_crop: Union[tuple, list], strategy: str,
              sowing_depth: str, row_spacing: str, population: int,
              cultivar_name: str, start_date: str, end_date=None, min_esw=100,
              min_rain=10, rain_duration=4, simulations=None, fertilize_crop=None):
    """

    @param fertilize_crop:
    @param simulations: simulation to configure rotation
    @param min_esw:
    @param min_rain:
    @param sowing_depth:
    @param row_spacing: spacing between rows
    @param population: int, planting density
    @param rain_duration:
    @param cultivar_name: name of the cultivar
    @param app: apsimNGpy model
    @param seq: str e.g (Maize, Soybean) or as a string 'Maize, Soybean'. The first crop will be planted first in the first yea, then followed by another crop after the comma
    @param in_crop: is the crop currently in the simulation
    @param strategy: either fixed or variable, variable required start and end date, while foxed only start date is required
    @param start_date: sowing date or start date if sowing is through a variable time window
    @param end_date: date to end the sowing
    @return:
    """

    def _add_child_model(parent, child_model, name):
        """
        if child is found remove and add, or add, proceed with caution
        @param parent: parent model
        @param child_model:  child imodel
        @param name: name of the child
        @return:
        """

        # enforce
        child_model.Name = name
        ch = parent.Children
        for child in ch:
            if child.Name == name:
                parent.Children.Remove(child)
                parent.Children.Add(child_model)
                break
        else:
            parent.Children.Add(child_model)

    if not fertilize_crop:
        fertilize_crop = {}
    fixed_parameters = dict(SowDate=start_date,
                            SowingDepth=sowing_depth,
                            CultivarName=cultivar_name,
                            RowSpacing=row_spacing,
                            Population=population,
                            Crop="")
    if strategy == 'fixed':
        sow_params = fixed_parameters
    else:
        if end_date is None:
            raise ValueError(f"end_date must be specified if sowing strategy is variable not  fixed")
        fixed_parameters.pop('SowDate', None)
        sow_params = dict(**fixed_parameters, EndDate=end_date, StartDate=start_date, MinESW=min_esw,
                          MinRain=min_rain, RainDays=rain_duration, )
    rotation = '.'.join(seq) if not isinstance(seq, str) else seq
    if isinstance(seq, str):
        seq = seq.split(",")
    in_crop = [in_crop] if isinstance(in_crop, str) else in_crop
    for crop in in_crop:
        if crop not in seq:
            raise ValueError(f"in_crop must be in {seq}")
    sims = app.find_simulations(None)
    # get crop that needs new sowing_manager
    need_sower = set(seq) - set(seq).difference(in_crop)
    print(need_sower)
    print(need_sower)
    # add rotation manager
    rot_manager = compile_manager(simple_rotation_code)
    # set the rotation
    rot_manager.set_Parameters(load_parameters(Crops=rotation))

    for crops in need_sower:
        # add new plant
        m_crop = Models.PMF.Plant()
        m_crop.Name = crops
        m_crop.ResourceName = crops

        for sim in sims:
            zone = sim.FindDescendant[Models.Core.Zone]()
            _add_child_model(zone, rot_manager, 'Simple Rotation Manager')
            _add_child_model(zone, m_crop, crops)
            # add sowing manager
            code = sow_on_fixed_date if strategy == 'fixed' else sow_using_variable_rule
            sow_manager = compile_manager(code)
            sow_manager.Name = f"{crops}_sow_on_fixed_date" if strategy == 'fixed' else f"{crops}_sow_using_variable_rule"
            sow_params['Crop'] = crops
            sow_params['RotationManager'] = rot_manager.Name
            sow_manager.set_Parameters(load_parameters(**sow_params))
            zone.Children.Add(sow_manager)

            # add harvest manager
            manager_harvest = compile_manager(harvest)
            manager_harvest.set_Parameters(load_parameters(Crop=crops))
            manager_harvest.Name = f"harvest{crops}"
            _add_child_model(zone, manager_harvest, manager_harvest.Name)

            # add soil crop
            soil_crop = zone.FindDescendant[Models.Soils.SoilCrop]()
            clonedSoilCrop = ModelTools.CLONER(soil_crop)
            # change its name
            clonedSoilCrop.Name = f"{crops}Soil"
            soilPhysical = zone.FindDescendant[Models.Soils.Physical]()
            for child in soilPhysical.Children:
                if child.Name == f"{crops}Soil":
                    soilPhysical.Children.Remove(child)
            soilPhysical.Children.Add(clonedSoilCrop)
            n_amount = fertilize_crop.get(crops)
            if n_amount:
                # add fertilizer manager or operations
                f_manager = compile_manager(fertilizer_at_sow)
                params = {"Crop": crops, 'Amount': n_amount, 'FertiliseDepth': '10', 'FertiliserType': "UreaN"}
                f_manager.set_Parameters(load_parameters(**params))
                f_manager.Name = f"{crops}-fertilize-at-sowing"
                zone.Children.Add(f_manager)

                app.save()
                # app.edit_model(model_type='Models.Manager',
                #                model_name=f_manager.Name, simulations=sim.Name, **params)

                return find_child(app.Simulations, child_class=Models.Manager, child_name=f_manager.Name)
            ...


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
        model_class = validate_model_obj(model_class)
    add_replacement_folder(simulations)
    # ensure that model being added as replacement exists
    try:
        model_to_replace = simulations.FindDescendant[model_class](model_name)
    except AttributeError:
        model_to_replace = find_child(simulations, child_class=model_class, child_name=model_name)
    fin_all = find_all_in_scope(simulations, model_class)
    names = ','.join([i.Name for i in fin_all])
    if not model_to_replace:
        raise ValueError(f"model class {model_class} with {model_name} not found in the current simulations. "
                         f"suggested available model names: {names}")
    rep_old = find_child(simulations, child_class=Models.Core.Folder, child_name='Replacements')
    if rep_old:
        # find if the requested model exists in the replacement folder, remove or do nothing
        model_exists = find_child(rep_old, child_class=model_class, child_name=model_name)
        if model_exists:
            rep_old.Children.Remove(model_exists)
        # now we add the found model at the top as replacement
        rep_old.Children.Add(model_to_replace)
    else:
        raise RuntimeError("failed to add replacement folder")
    # check again before exiting caller
    model_exists = find_child(rep_old, child_class=model_class, child_name=model_name)
    if not model_exists:
        raise RuntimeError(f"failed to add model of class{model_class} with identification name: {model_name}")


@dataclass(slots=True)
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
    CAST = cast_as
    find_child = find_child
    add_replacement_folder = add_replacement_folder
    find_all_in_scope = find_all_in_scope
    find_child_of_class = find_child_of_class
    edit_instance = edit_instance_attributes


def find_all_model_type(parent, model_type, ignore_errors=False):
    if not callable(model_type):
        model_type = getattr(Models, model_type)

    # node_base = getattr(parent, "Node", parent)

    error_MSG = f"Failed to find models of type {model_type} under parent node {parent}"

    ALL_MODELS = find_all_in_scope(parent=parent, child_class=model_type)

    if ALL_MODELS is None and not ignore_errors:
        raise ValueError(error_MSG)
    return ALL_MODELS


collect()
# add_method_to_model_tools(find_child)
# add_method_to_model_tools(find_all_in_scope)
# add_method_to_model_tools(add_replacement_folder)

if __name__ == "__main__":
    ...
    import time
    from apsimNGpy.core.pythonet_config import get_apsim_file_reader
    from apsimNGpy.core.config import load_crop_from_disk

    maize = load_crop_from_disk(crop='Maize', out='apism_run.apsimx')
    wf = load_crop_from_disk('AU_Dalby.met', out='AU_Dalby.met')
    string_name = maize.read_text()
    reader = get_apsim_file_reader('string')
    node = reader[Models.Core.Simulations](string_name, None, initInBackground=True, fileName='apsim_rune.apsimx')
    climate = node.FindChild[Models.Climate.Weather](recurse=True)
    climate.FileName = str(wf.resolve())
    print(Path(climate.FileName).resolve().exists())
    sim = node.FindChild[Models.Core.Simulation](recurse=True)
    datastore = node.FindChild[Models.Storage.DataStore](recurse=True)
    db = str(Path(node.FileName).with_suffix('.db'))
    datastore.FileName = db
    datastore.UseInMemoryDB = False
    a = time.perf_counter()
    sim.Prepare()

    b = time.perf_counter()
    print(b - a, 'seconds')


    def edit_cultivar(cultivar_name, commands):
        def validate_commands(cmds):
            valid = []
            invalid = []
            for command in cmds:
                spc = command.split('=')
                if '=' in command and len(spc) > 1 and spc[-1]:
                    valid.append(command.strip())
                else:
                    invalid.append(command)
            if invalid:
                raise ValueError(f'{invalid} are not valid cultivar commands')
            return valid

        cultivar = node.FindChild[Models.PMF.Cultivar](cultivar_name, recurse=True)
        if isinstance(commands, str):
            commands = {commands}
        existing = list(cultivar.Command)
        valid_commands = validate_commands(commands)
        update = existing + list(valid_commands)
        unique_updated = list(dict.fromkeys(update))
        return unique_updated


    try:
        pp = edit_cultivar('B_110', "1")
    except ValueError:
        print('working as expected')

    try:
        ppd = edit_cultivar('B_110', "1=")
    except ValueError:
        print('working as expected')
    pp1 = edit_cultivar('B_110', commands='[Leaf].Photosynthesis.RUE.FixedValue=2')
    ppl = edit_cultivar('B_110', commands=['[Phenology].Juvenile.Target.FixedValue = 210',
                                           '[Phenology].Photosensitive.Target.XYPairs.X = 0, 12.5, 24',
                                           '[Phenology].Photosensitive.Target.XYPairs.Y = 0, 0, 0', ])
