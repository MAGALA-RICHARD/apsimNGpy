"""
The role of this module is to provide explicit support for editing cultivars
"""

from typing import Iterable

from apsimNGpy.core_utils.utils import is_scalar
from apsimNGpy.exceptions import NodeNotFoundError
from apsimNGpy.starter.starter import CLR

Models = CLR.Models

REPLACEMENTS = 'Replacements'


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


def attach_cultivar(model, name: str, manager: str, param_name: str, simulations=None):
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
            simulations =simulations,
            **{param_name: name}
        )

    else:
        raise NodeNotFoundError(
            f"Manager script '{manager}' not found in the model."
        )


def harmonize(command):
    match command:
        case list() | tuple():
            return _check_cmds(commands=command)
        case dict():
            # dicts dont need to be validated
            return command
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


def derive_cultivar(model, *, commands, plant, template=None, rename=None, managers=None, simulations=None):
    # template can be None
    command_inspection = model.inspect_model_parameters("Models.PMF.Cultivar", model_name=template)[
        'Command'] if template else {}

    cmds = _format_cmds(command_inspection, commands, clear_old=False)
    model.add_crop_replacements()
    plant_path = f"{model.Simulations.FullPath}.{REPLACEMENTS}.{plant.capitalize()}"
    # check if a plant path is valid
    if not plant_path in model.inspect_model("Models.PMF.Plant"):
        raise ValueError(f"{plant} not found in the simulation root")
    default = f"modified_{template}_{plant}_cultivar" if template else f"modified_{plant}_cultivar"
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
            attach_cultivar(model, rename, manager=k, param_name=v, simulations=simulations)


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
        cms_tup = tuple(cms)
        derive_cultivar(mod, template=None, commands=cms, rename=None, plant='maize',
                        managers={'Sow using a variable rule': "CultivarName"})
        out = mod.inspect_model_parameters("Models.Manager", model_name="Sow using a variable rule",
                                           parameters='Parameters')
        if 'modified_maize_cultivar' in set(mod.inspect_model('Models.PMF.Cultivar', fullpath=False)):
            # check if edits were successful
             p = mod.inspect_model_parameters('Models.PMF.Cultivar', 'modified_maize_cultivar')
             juv = p.get('Command', p)['[Phenology].Juvenile.Target.FixedValue']
             assert juv =='490'
        else:
            raise ValueError('edits were not successful')

        assert out.get('Parameters', out)['CultivarName']=='modified_maize_cultivar'
        #mod.open_in_gui(watch=True)
        derive_cultivar(mod, template=None, commands=cms_tup, rename='th', plant='maize',
                        managers={'Sow using a variable rule': "CultivarName"})
        if 'th' in set(mod.inspect_model('Models.PMF.Cultivar', fullpath=False)):
            # check if edits were successful
             p = mod.inspect_model_parameters('Models.PMF.Cultivar', 'modified_maize_cultivar')
             juv = p.get('Command', p)['[Phenology].Juvenile.Target.FixedValue']
             assert juv =='490'
        else:
            raise ValueError('edits were not successful')
        mod.open_in_gui()
