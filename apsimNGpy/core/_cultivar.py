from pathlib import Path
from typing import Dict, Optional
from apsimNGpy.core.model_tools import find_all_model_type, get_or_check_model
import Models
from apsimNGpy.settings import logger
from apsimNGpy.core.model_loader import get_node_by_path
from apsimNGpy.core.cs_resources import CastHelper
from apsimNGpy.core.model_tools import ModelTools
from apsimNGpy.core_utils.utils import is_scalar, evaluate_commands_and_values_types


def trace_cultivar(
        location,
        cultivar_name: str,
        verbose: bool = False,
        strict: bool = True
) -> Dict[str, str]:
    """
    Trace the crop (Plant node) associated with a specific cultivar within an APSIM simulation tree.

    Parameters
    ----------
    location : object
        The APSIM simulation or sub-model node to search within (e.g., a Simulation, Zone, or Field node).
        This typically represents the parent model scope under which plant models are defined.
    cultivar_name : str
        The name of the cultivar to locate within the simulation hierarchy.
        The search is case-insensitive and recursive across all plant models.
    verbose : bool, optional, default=False
        If True, log detailed search progress and results to the active logger.
        Useful for debugging or validating the model structure.
    strict : bool, optional, default=True
        If True, raises a `ValueError` when the cultivar cannot be found.
        If False, returns None instead of raising an exception.

    Returns
    -------
    dict
        A dictionary mapping the found cultivar name to its parent crop name, e.g.,
        ``{"Pioneer_1185": "Maize"}``.

    Raises
    ------
    ValueError
        If `strict=True` and the cultivar cannot be found within the specified location.

    Notes
    -----
    This function searches for all `Models.PMF.Plant` nodes within the provided APSIM model hierarchy.
    For each plant, it checks whether the given cultivar exists as a child node (`Models.PMF.Cultivar`).
    If found, the crop (plant) name associated with that cultivar is returned.

    The search can be made more verbose by setting `verbose=True`, which logs intermediate steps
    and results to the APSIMNGpy logger.

    Examples
    --------
    .. code-block:: python

        from apsimNGpy.core.apsim import ApsimModel
        from apsimNGpy.utils.cultivar_tools import trace_cultivar

        model = ApsimModel("Maize.apsimx")
        crop = trace_cultivar(model.Simulations, "Pioneer_1185", verbose=True)
        print(crop)
        # {'Pioneer_1185': 'Maize'}

    """
    if not cultivar_name:
        raise ValueError("Cultivar name must be provided.")

    if verbose:
        logger.debug(f"Searching for cultivar '{cultivar_name}' within APSIM location: {location}")

    plants = find_all_model_type(parent=location, model_type=Models.PMF.Plant)

    for plant in plants:
        node = getattr(plant, "Node", plant)
        cultivar = node.FindChild[Models.PMF.Cultivar](cultivar_name, recurse=True)
        if cultivar is not None:
            if verbose:
                logger.info(f"Cultivar '{cultivar_name}' found under plant '{plant.Name}'.")
            return {cultivar_name: plant.Name}

    if strict:
        raise ValueError(
            f" Cultivar '{cultivar_name}' not found in {location}. "
            "Ensure the cultivar name matches one defined in the APSIM simulation."
        )
    return None


def search_cultivar_manager(
        model,
        cultivar_name: str,
        verbose: bool = False,
        simulations=None,
        strict: bool = True
) -> Optional[Dict[str, Dict[str, str]]]:
    """
    Identify the APSIM Manager script responsible for sowing or managing a given cultivar.

    Parameters
    ----------
    model : ApsimModel, required
        An active APSIM model instance. Must expose the `inspect_model` and
        `inspect_model_parameters_by_path` methods for model introspection.
    cultivar_name : str, required
        The name of the cultivar to locate within APSIM Manager scripts.
        The search matches parameter values case-insensitively.
    verbose : bool, optional, default=False
        If True, enables detailed logging of the manager inspection process.
    simulations : list[str] or None, optional
        A subset of simulation names to limit the search scope.
        If None, all simulations are searched.
    strict : bool, optional, default=True
        If True, raises a `ValueError` when no matching manager script is found.
        If False, returns None.

    Returns
    -------
    dict or None
        A dictionary mapping each simulation name to the Manager script and parameter referencing
        the given cultivar, e.g.:
        ``{"Sim1": {"manager": "Sow using a variable rule", "param": "CultivarName"}}``.
        Returns None if not found and `strict=False`.

    Raises
    ------
    TypeError
        If the `model` is not an instance of `ApsimModel` or lacks required methods.
    ValueError
        If `strict=True` and no Manager script containing the cultivar reference is found.

    Notes
    -----
    This function traverses Manager nodes in each APSIM simulation to find parameters matching
    the given cultivar name. It performs case-insensitive comparisons and stops searching once
    a match is found per simulation, minimizing overhead for large simulation trees.

    Examples
    --------
    .. code-block:: python

        from apsimNGpy.core.apsim import ApsimModel
        from apsimNGpy.utils.cultivar_tools import search_cultivar_manager

        model = ApsimModel("MaizeExample.apsimx")
        manager_info = search_cultivar_manager(model, "Pioneer_1185", verbose=True)
        print(manager_info)
        # {'Sim1': {'manager': 'Sow using a variable rule', 'param': 'CultivarName'}}

    """
    # ---- validation ----
    if not hasattr(model, "inspect_model") or not hasattr(model, "inspect_model_parameters_by_path"):
        raise TypeError("Expected 'model' to be an instance of ApsimModel or compatible class.")
    if not cultivar_name:
        raise ValueError("Cultivar name must be provided.")

    cultivar_key = cultivar_name.strip().lower()
    sims = model.simulations if simulations is None else model.find_simulations(simulations)
    results: Dict[str, Dict[str, str]] = {}
    reps = model.get_replacements_node()
    if reps:
        sims.append(reps)

    if verbose:
        logger.debug(f"Searching for cultivar '{cultivar_name}' across {len(sims)} simulation(s)...")

    for sim in sims:
        # Pre-fetch all manager nodes in this simulation
        manager_objs = find_all_model_type(sim, Models.Manager)
        if not manager_objs:
            if verbose:
                logger.warning(f"No manager scripts found in simulation '{sim.Name}'.")
            continue

        # Loop through managers efficiently
        for manager in manager_objs:
            # Inspect parameters once per manager node
            params = model.inspect_model_parameters_by_path(manager.FullPath)
            if not params:
                continue

            # Perform direct lowercased string match
            match = next(
                ((k, v) for k, v in params.items() if str(v).strip().lower() == cultivar_key),
                None
            )

            if match:
                param_name, _ = match
                results[sim.Name] = {"manager": manager.Name, "param": param_name, 'manager_path': manager.FullPath}
                if verbose:
                    logger.info(
                        f"[{sim.Name}] Cultivar '{cultivar_name}' found in manager '{manager.Name}', param '{param_name}'."
                    )
                break  # stop searching this simulation once found

    if not results:
        msg = f"No manager script found for cultivar '{cultivar_name}'."
        if strict:
            raise ValueError(msg)
        if verbose:
            logger.warning(msg)
        return None

    return results


def resolve_selected_simulations(simulations, exclude):
    if simulations is None:
        simulations = set()
    if exclude is None:
        exclude = set()
    if exclude.intersection(simulations):
        raise ValueError(f"one of the excluded simulations: `{exclude}` found in specified simulations {simulations}")


def inspect_cultivars(simulation: Models.Core.Simulation, full_path: bool = True) -> list:
    objs = find_all_model_type(simulation, Models.PMF.Cultivar)
    if objs:
        if full_path is True:
            return [o.FullPath for o in objs]
        else:
            return [o.Name for o in objs]
    return []


def _set_commands(_model, selected_cultivar, commands, values):
    evaluate_commands_and_values_types(commands, values)
    cultivar_params = _model._cultivar_params(selected_cultivar)
    print(values)
    if is_scalar(commands):
        cultivar_params[commands] = values
    else:
        for cmd, val in zip(commands, values):
            cultivar_params[cmd.strip()] = val.strip() if isinstance(val, str) else val

    updated_cmds = [f"{k.strip()}={v}" for k, v in cultivar_params.items()]
    # Assign commands efficiently
    if hasattr(selected_cultivar, "set_Command"):
        selected_cultivar.set_Command(updated_cmds)
    else:
        selected_cultivar.Command = updated_cmds
    return selected_cultivar


def _insert_updated_cultivar(replacements, plant_name: str, rename: str, selected_cultivar, at_parent=False):
    """
    Insert or replace an updated cultivar within a plant node under the replacements structure.

    Parameters
    ----------
    replacements : object
        The APSIM 'Replacements' node (from `_model.get_replacements_node()`).
    plant_name : str
        The name of the plant to which the cultivar belongs.
    rename : str
        The target name for the updated cultivar (new or existing).
    selected_cultivar : object
        The updated cultivar node (e.g., a `Models.PMF.Cultivar` instance) to insert.

    Notes
    -----
    - If a cultivar with the same name already exists, it is replaced in place.
    - If it does not exist, the new cultivar is appended as a child.
    - This function is idempotent—running it multiple times produces the same result.

    Returns
    -------
    object
        The modified plant node after insertion.
    """
    # Retrieve the target plant node

    plant = get_or_check_model(replacements, Models.PMF.Plant, plant_name, action="get")
    node = getattr(plant, "Node", plant)
    if at_parent:
        parent = selected_cultivar.get_Parent()
    else:
        parent = plant

    # Remove any existing cultivar with the same name
    existing = get_or_check_model(parent, Models.PMF.Cultivar, rename, action='check')
    if existing:
        get_or_check_model(replacements, Models.PMF.Cultivar, rename, action="delete")

    ModelTools.ADD(selected_cultivar, parent)

    return plant


def _edit_in_cultivar(
        _model,
        model_name: str,
        param_values: dict,
        simulation: Models.Core.Simulation,
        verbose: bool = False,
        by_path: bool = False
):
    """
    Edit or duplicate a specific cultivar within a given APSIM simulation.

    This operation targets a single simulation to safely modify cultivar parameters,
    optionally creating a new cultivar node or updating an existing one.
    The changes are propagated to the corresponding Manager script for simulation consistency.

    Parameters
    ----------
    _model : ApsimModel
        Active APSIM model instance.
    model_name : str
        Name of the existing cultivar to modify (e.g., "B_110").
    param_values : dict
        A dictionary defining the edits.
        Expected structure:
            {
              "new_cultivar_name": "B_110-edited",  # optional
              "commands": ["[Phenology].CAMP.FLNparams.VxPLN"],
              "values": [0.0]
            }
    simulation : Models.Core.Simulation
        Simulation node to target the cultivar edit.
    verbose : bool, optional
        If True, logs progress and success messages to console and file.
    by_path : bool, optional
        If True, forces command/value updates by explicit path.

    Returns
    -------
    None
        The APSIM model is modified in memory and persisted to disk.

    Raises
    ------
    ValueError
        If required inputs are missing or inconsistent, or if cultivar references cannot be located.

    Notes
    -----
    - All modifications are performed within a single simulation scope to prevent
      cross-simulation interference.
    - Command/value pairs must be aligned in length when provided as iterables.
    - Uses in-memory mutation and deferred saving for performance.
    """

    sim_name = simulation.Name

    # ---- Validation ----
    if not isinstance(param_values, dict):
        raise TypeError("param_values must be a dictionary.")
    if not model_name:
        raise ValueError("model_name must be provided.")
    if "commands" not in param_values or "values" not in param_values:
        raise ValueError("param_values must include both 'commands' and 'values'.")

    commands = param_values["commands"]
    values = param_values["values"]
    new_cultivar_name = param_values.get("new_cultivar_name", f"{sim_name}_{model_name}")

    # ---- Locate plant and manager once ----
    plant_name = trace_cultivar(_model.Simulations, model_name)[model_name]
    manager_info = search_cultivar_manager(_model, model_name, verbose=verbose, strict=True)
    manager_entry = manager_info.get(sim_name)
    if not manager_entry:
        raise ValueError(f"No Manager script found for cultivar '{model_name}' in simulation '{sim_name}'.")

    cultivar_manager, cultivar_param = manager_entry["manager"], manager_entry["param"]

    # ---- Locate replacement node ----
    replacements = _model.get_replacements_node()
    if not replacements:
        raise ValueError("Editing cultivar requires a replacement node in the APSIM file.")

    # ---- Locate and clone target cultivar ----
    selected_cultivar = replacements.Node.FindChild[Models.PMF.Cultivar](model_name, recurse=True)
    if not selected_cultivar:
        raise ValueError(f"Specified cultivar '{model_name}' not found under replacements node.")

    selected_cultivar.Name = new_cultivar_name

    # ---- Apply parameter updates ----

    selected_cultivar = _set_commands(_model, selected_cultivar, commands, values)
    # ---- Attach cultivar to target plant ----

    _insert_updated_cultivar(replacements, selected_cultivar=selected_cultivar, rename=new_cultivar_name,
                             plant_name=plant_name)
    # Delete existing cultivar if present

    # ---- Update manager script ----
    _model.edit_model(
        model_type=Models.Manager,
        model_name=cultivar_manager,
        simulations=sim_name,
        **{cultivar_param: new_cultivar_name}
    )

    # ---- Save model once ----
    _model.save()

    if verbose:
        logger.info(f"✅ Cultivar '{model_name}' updated to '{new_cultivar_name}' in simulation '{sim_name}'.")


def edit_cultivar_by_path(
        model_obj, *,
        path: str,
        commands,
        values=None,
        rename: str | None = None,
        manager_path: str | None = None,
        manager_param: str | None = None,
        sowed: bool = True,
        verbose: bool = False,
        **kwargs
):
    """
    Edit or create a new cultivar in APSIM given its path, updating associated manager if required.

    Parameters
    ----------
    model_obj : ApsimModel
        The active APSIM model instance.
    path : str
        Full APSIM node path to the cultivar (e.g., ".Simulations.Replacements.Maize.B_110").
    commands : str | list[str]
        APSIM command(s) or property path(s) to modify (e.g., "[Phenology].CAMP.FLNparams.VxPLN").
    values : str | float | list
        Corresponding value(s) to apply for each command.
    rename : str, optional
        New cultivar name. If not provided, appends "___edited" to the original name.
    manager_path : str, optional
        Full path to the sowing manager script. Required if `update_manager=True`.
    sowed : bool, default=True
        implies that the cultivar being proposed to be edited is already sowed in the manager. If so, the caller will try to detect the corresponding
        parameter holder in the manager script to update it.

    Raises
    ------
    ValueError
        If the cultivar or replacement node cannot be found, or inputs are mismatched.

    Notes
    -----
    - The function edits a cultivar node defined by `path`, updates its internal parameterization,
      and optionally adds it to the corresponding plant’s cultivar list under the Replacements node.
    - If `update_manager=True`, the associated manager script must be provided via `manager_path`.

    Returns
    -------
    updated_cultivar : Models.PMF.Cultivar
        The updated cultivar node.
        @param manager_param:
    """

    # ---- Retrieve target cultivar node ----
    cultivar_node = get_node_by_path(model_obj.Simulations.Node, node_path=path)
    if not cultivar_node:
        raise ValueError(f"Specified cultivar path '{path}' not found in model '{model_obj}'.")
    cut = getattr(cultivar_node, 'Model', cultivar_node)
    cultivar = CastHelper.CastAs[Models.PMF.Cultivar](cut)
    if cultivar is None:
        raise ValueError(f"Node at path '{path}' is not a Cultivar model.")

    original_name = cultivar.Name
    cultivar_name = rename or f"{original_name}___edited"
    if isinstance(commands, dict):
        commands, values = commands.items()

    # ---- Apply parameter updates ----
    updated_cultivar = _set_commands(model_obj, cultivar, commands, values)
    updated_cultivar.Name = cultivar_name

    # ---- Get replacement node ----
    replacements = model_obj.get_replacements_node()
    if not replacements:
        raise ValueError("Editing cultivar requires a Replacements node in the APSIM file.")

    # ---- Trace parent plant efficiently ----
    plant_name = trace_cultivar(replacements, cultivar_name=original_name, strict=True)[original_name]

    # ---- Insert updated cultivar ----
    _insert_updated_cultivar(
        replacements,
        plant_name=plant_name,
        rename=cultivar_name,
        selected_cultivar=updated_cultivar
    )

    # ---- Optionally update manager ----
    if not sowed:
        # user has to help and supply these parameters
        if not manager_path or not manager_param:
            raise ValueError(
                "Manager path and corresponding `cultivar_param' holder must be provided if sowed=False.")
        else:
            model_obj.edit_model_by_path(path=manager_path, **{manager_param: cultivar_name})

    else:
        if not manager_path or not manager_param:
            mns = search_cultivar_manager(model_obj, cultivar_name=original_name, simulations=kwargs.get('simulations'),
                                          verbose=verbose)
            for k, v in mns.items():
                model_obj.edit_model_by_path(v['manager_path'], **{v['param']: cultivar_name})
        else:
            # if a user has provided them well and good, some overhead in searching is mitigated.
            model_obj.edit_model_by_path(manager_path, **{manager_param: cultivar_name})

    # ---- Save once ----
    model_obj.save()

    if hasattr(updated_cultivar, "Name") and verbose:
        print(f"✅ Cultivar '{original_name}' updated as '{updated_cultivar.Name}'")

    return updated_cultivar


if __name__ == "__main__":
    from apsimNGpy.core.apsim import ApsimModel

    pa_v = {'commands': '[Grain].MaximumGrainsPerCob.FixedValue', 'values': 34}
    with ApsimModel('Soybean') as model:
        model.add_base_replacements()

        sim = model.simulations[0]

        model.save()
        for _ in [2, 3]:
            cv = model.inspect_model('Models.PMF.Cultivar', 'Simulation_Davis')

            edit_cultivar_by_path(model, path='.Simulations.Simulation.Field.Soybean.Cultivars.Generic.Generic_MG3',
                                  commands='[Grain].MaximumGrainsPerCob.FixedValue', values=20,
                                  manager_path='.Simulations.Simulation.Field.Sow using a variable rule',
                                  manager_param='CultivarName',
                                  sowed=False, rename='re00000000000000000000000000000000000')

            model.inspect_file(cultivar=True)
            print('success')

        model.save()
        # edit_new_cultivar_by_path(model, '.Simulations.Replacements.Soybean.Simulation_Davis',
        #                           '[Grain].MaximumGrainsPerCob.FixedValue', 20,
        #                           update_manager=False, rename='edavis')
        if 're00000000000000000000000000000000000' in model.inspect_model('Models.PMF.Cultivar', fullpath=False):
            print('re00000000000000000000000000000000000')
        else:
            for i in model.inspect_model('Models.PMF.Cultivar', fullpath=False):
                print(i)
