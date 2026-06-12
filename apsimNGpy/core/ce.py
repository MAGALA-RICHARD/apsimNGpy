"""
The role of this module is to provide explicit support for editing cultivars
"""
from functools import lru_cache, cache

import json
import hashlib

from apsimNGpy import timer, is_scalar
from apsimNGpy.exceptions import NodeNotFoundError
from apsimNGpy.starter.starter import CLR
from dataclasses import dataclass
from apsimNGpy.core.model_loader import get_node_by_path
from apsimNGpy.core.model_tools import ModelTools
from typing import Iterable, Any

Models = CLR.Models

REPLACEMENTS = 'Replacements'


@timer
def create_new_cultivar(apsim_model, *, commands, template, parent_plant, rename=None):
    """
    Functionsl approach for creating or updating a cultivar by applying parameter commands and attaching it
    under the Replacements folder for a given plant.

    This method constructs a new `Models.PMF.Cultivar` node by merging user-provided
    commands with existing cultivar parameters, then inserts it under:

        .Simulations.Replacements.<parent_plant> implying that the new cultivar needs to be sown in the appropriate manager script or operations module

    If the `Replacements` folder or the specified plant does not exist, they will
    be created automatically.

    Parameters
    ----------
    apsim_model : apsimNGpy.core.apsim.ApsimModel | apsimNGpy.core.Experiment.ExperimentManager
         any instance of the `apsimNGpy.core.apsim.ApsimModel or apsimNGpy.core.Experiment.ExperimentManager`
    commands : dict | list | tuple | set | str
        Parameter modification commands to apply to the cultivar.

        Supported formats:
        - dict:
            {"[Phenology].Juvenile.Target.FixedValue": 300}
        - iterable (list/tuple/set):
            ["[Phenology].Juvenile.Target.FixedValue=300"]
        - str:
            "[Phenology].Juvenile.Target.FixedValue=300"

        All inputs are normalized internally to a set of APSIM command strings
        of the form:
            "parameter_path=value"

    template : str
        Name of the base cultivar used as a template for extracting existing parameters.
        It Should be exactly as it is named in APSIM e.g., maize is incorrect, and Maize is correct


    parent_plant : str
        Name of the plant (e.g., "Maize", "Wheat", "Soybean") under which the cultivar
        will be attached in the Replacements folder.

    rename : str, optional
        Name of the new cultivar. If not provided, defaults to:
            f"ed{template}"

    Behavior
    --------
    - Converts all input commands into APSIM-compatible command strings.
    - Retrieves existing parameters from a reference cultivar.
    - Merges existing parameters with user-provided commands (user commands override).
    - Ensures the following structure exists:
        .Simulations
            └── Replacements
                └── <parent_plant>
    - Creates or replaces a cultivar under the specified plant using `add_new_model`.

    Notes
    -----
    - The cultivar is created with:
        ReadOnly = False
    - Existing cultivars with the same name may be replaced depending on `replace=True`.
    - This method assumes APSIM model is already loaded and valid in memory.

    Returns
    -------
    None
        The method modifies the APSIM model in-place.

    Raises
    ------
    ValueError
        If `commands` is not one of the supported types:
        (dict, list, tuple, set, or str)

    Examples
    --------
    >>> from apsimNGpy import ApsimModel
    >>> model = ApsimModel('Maize')
    >>> create_new_cultivar(apsim_model=model,
    ...     commands={"[Phenology].Juvenile.Target.FixedValue": 350},
    ...     template="B_100",
    ...     parent_plant="Maize",
    ...     rename="Maize_fast"
    ... )

    >>> create_new_cultivar(apsim_model=model,
    ...     commands=[
    ...         "[Grain].MaximumGrainsPerCob.FixedValue=800",
    ...         "[Phenology].ThermalTime.Target=1200"
    ...     ],
    ...     template="B_100",
    ...     parent_plant="Maize"
    ... )

    >>> create_new_cultivar(apsim_model=model,
    ...     commands="[Phenology].Juvenile.Target.FixedValue=280",
    ...     template="B_100",
    ...     parent_plant="Maize"
    ... )

    Developer Notes
    ---------------
    - Consider parameterizing the base cultivar instead of hardcoding 'B_100'.
    - Ensure `add_new_model` correctly resolves CLR types and handles replacement logic.
    @param apsim_model:
    """
    apsim_model.add_crop_replacements()
    # avoids mixing pup different plants
    plant_node = apsim_model.has_node(parent_plant, node_type="Models.PMF.Plant")
    if not plant_node['ok']:
        raise NodeNotFoundError(f"model node:{parent_plant} not found")
    match commands:
        case dict():
            keys = commands.keys()
            commands = {f"{k}={v}" for k, v in commands.items()}
        case list() | tuple() | set():
            commands = set(commands)
            keys = [k.split("=")[0].strip() for k in commands]
        case str():
            keys = commands.split('=')[0].strip()
            commands = {commands}
        case _:
            raise ValueError(f"Unknown command type: {type(commands)} expected list, str, tuple, dicts or set")
    existing_params = apsim_model.inspect_model_parameters(model_type='Models.PMF.Cultivar', model_name='B_100')
    all_EX = {f"{k}={v}" for k, v in existing_params.items() if k not in keys}
    # NOW WE CAN MERGE COMFORTABLY below
    rename = rename or f"ed_{parent_plant}_{template}"

    cult_load = {
        "$type": "Models.PMF.Cultivar, Models",
        "Command": [
            *all_EX,
            *commands,
        ],
        "Name": f"{rename}",
        # "Enabled": True,
        "ReadOnly": False,

    }

    apsim_model.save()
    # get this again to get it full path
    rep_path = f".{apsim_model.Simulations.Name}.{REPLACEMENTS}.{parent_plant}"
    apsim_model.add_new_model(parent_type='Models.PMF.Plant',
                              parent_identifier=rep_path,
                              replace=True,
                              source=cult_load)


def _check_cmds(commands):
    if isinstance(commands, (dict, set)):
        raise TypeError(f'expected a list like but got {type(commands)}')
    elif isinstance(commands, str):
        commands = [commands]
    invalid = set()
    valid = {}
    for cmd in commands:
        if '=' not in cmd or '.' not in cmd:
            invalid.add(cmd)
        elif '==' in cmd:
            invalid.add(cmd)
        elif '/' in cmd:
            invalid.add(cmd)
        else:
            k, v = cmd.split('=')
            valid[k.strip()] = v.strip()
    if invalid:
        raise ValueError(f'following commands are invalid: {invalid} expected an = in between path and values')
    return valid


def format_cmd_values(commands: Iterable, values: Iterable):
    """
    Update cultivar commands using a separate commands and values iterables.

    Parameters
    ----------
    name : str
        New cultivar name to create or update.
    commands : Iterable
        iterable of command parameter paths without values.
    values: Iterable
        iterable of values with index position corresponding to the appropriate paths in the commands .

    Examples
    --------
    .. code-block:: python

        from apsimNGpy import Apsim

        apsim = Apsim()
        app_model = apsim.ApsimModel("Maize")

        ec = CultivarEditor(
            model=app_model,
            template_cultivar="B_100",
            plant="Maize"
        )

        commands = [
            "[Phenology].Juvenile.Target.FixedValue"
        ]
        values =[180]

        ec.edit_by_cmd_values(name="eB_100", commands=commands, values=values)

        # Attach the new cultivar to a manager script
        ec.attach_cultivar(
            name="eB_100",
            manager="Sow using a variable rule",
            param_name="CultivarName"
        )
    """

    if isinstance(commands, set) or isinstance(values, set):
        raise TypeError(
            "Invalid input type: 'set' is not supported. "
            "Use an ordered iterable (e.g., list or tuple) or a dict instead."
        )
    if is_scalar(commands):
        if not is_scalar(values):
            raise TypeError(f"un matching data type for commands: {type(commands)} to {type(values)}")
        commands = [commands]
        values = [values]
    if len(commands) != len(values):
        raise ValueError(
            f"Length mismatch: {len(commands)} command(s) vs {len(values)} value(s)."
        )
    commands = dict(zip(commands, values))
    return commands


def attach_cultivar(model, name: str, manager: str, param_name: str):
    """
    Attach a cultivar to a manager script by updating the specified parameter.

    This is typically used after editing or creating a cultivar to ensure it is
    referenced correctly within a management script (e.g., sowing rules).

    Parameters
    ----------
    name : str
        Name of the cultivar to attach.
    manager : str
        Manager script name or full path where the cultivar is referenced.
    param_name : str
        Name of the parameter in the manager script that defines the cultivar.

    Raises
    ------
    NodeNotFoundError
        If the specified cultivar or manager script cannot be found.
    """

    # Manager provided as a full path
    if manager in model.inspect_model('Models.Manager', fullpath=True):
        model.edit_model_by_path(
            path=manager,
            **{param_name: name},

        )

    # Manager provided as name
    elif manager in model.inspect_model('Models.Manager', fullpath=False):
        model.edit_model(
            model_type='Models.Manager',
            model_name=manager,
            **{param_name: name}
        )

    else:
        raise NodeNotFoundError(
            f"Manager script '{manager}' not found in the model."
        )


def harmonize(command):
    match command:
        case list():
            return _check_cmds(commands=command)
        case _:
            raise NotImplementedError(f"{type(command)} is not supported")


def _format_cmds(old_commands, new_commands: dict | list, clear_old=False):
    """Return merged commands formatted as key=value strings."""
    if isinstance(new_commands, (list, tuple)):
        new_commands = harmonize(new_commands)
    if not isinstance(new_commands, dict):
        raise TypeError(f'new_commands must be a dict got {type(new_commands)}')
    base_cmd = old_commands
    merge_cmds = base_cmd.copy()
    if not clear_old:
        merge_cmds.update(new_commands)  # new_commands take priority
    else:
        merge_cmds = dict(new_commands)
    fmt_cmds = [f"{k.strip()}={v}" for k, v in merge_cmds.items()]

    return fmt_cmds


def new_cultivar(model, *, commands, plant, template=None, rename=None, managers=None):
    # template can be None
    command_inspection = model.inspect_model_parameters("Models.PMF.Cultivar", model_name=template)[
        'Command'] if template else {}

    cmds = _format_cmds(command_inspection, commands, clear_old=False)
    model.add_crop_replacements()
    plant_path = f"{model.Simulations.FullPath}.Replacements.{plant.capitalize()}"
    # check if a plant path is valid
    if not plant_path in model.inspect_model("Models.PMF.Plant"):
        raise ValueError(f"{plant} not found in the simulation root")
    default = f"new{template}_{plant}_cultivar" if template else f"new_{plant}_cultivar"
    rename = rename or default
    model.add_new_model(parent_identifier=plant_path, parent_type='Models.PMF.Plant',
                        replace=True,
                        source={
                            "$type": "Models.PMF.Cultivar, Models",
                            "Command": [
                                *cmds
                            ],
                            "Name": rename,
                            "ResourceName": None,
                            "Children": [],
                            "Enabled": True,
                            "ReadOnly": False
                        })
    if managers:
        for k, v in managers.items():
            attach_cultivar(model, rename, manager=k, param_name=v, )


if __name__ == "__main__":
    from apsimNGpy.core.apsim import ApsimModel

    cm = {'[Phenology].Juvenile.Target.FixedValue': '201',
          '[Phenology].Photosensitive.Target.XYPairs.X': '0, 12.5, 24',
          '[Phenology].Photosensitive.Target.XYPairs.Y': '0, 0, 0',
          '[Phenology].FlagLeafToFlowering.Target.FixedValue': '1',
          '[Phenology].FloweringToGrainFilling.Target.FixedValue': '200',
          '[Phenology].GrainFilling.Target.FixedValue': '812',
          '[Phenology].Maturing.Target.FixedValue': '1',
          '[Phenology].MaturityToHarvestRipe.Target.FixedValue': '1',
          '[Rachis].DMDemands.Structural.DMDemandFunction.MaximumOrganWt.FixedValue': '360',
          '[Grain].MaximumGrainsPerCob.FixedValue': '500'}

    model = ApsimModel('Maize', f'_model.apsimx')
    cm_list = [f"{k}={v}" for k, v in cm.items()]

    from apsimNGpy import ApsimModel

    with ApsimModel('Maize') as mod:
        cms = [f'[Phenology].Juvenile.Target.FixedValue=490']
        new_cultivar(mod, template=None, commands=cms, rename=None, plant='maize', clear_old=True,
                      managers={'Sow using a variable rule': "CultivarName"})
        out = mod.inspect_model_parameters("Models.Manager", model_name="Sow using a variable rule",
                                           parameters='Parameters')
        mod.open_in_gui(watch=True)
