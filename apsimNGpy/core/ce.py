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


@cache
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


cacher = {}


def hash_or_get(cmds):
    if isinstance(cmds, dict):
        key = hashlib.sha256(
            json.dumps(cmds, sort_keys=True).encode()
        ).hexdigest()

        if key in cacher:
            return cacher[key]

        cacher[key] = cmds.copy()
        return cacher[key]


@dataclass(slots=True)
class CreatNewCultivar:
    model: Any
    template: str
    plant: str

    def __hash__(self):
        return hash((self.plant, self.template, self.model))

    @lru_cache(maxsize=200)  # templates are the same
    def inspect_commands(self):
        try:
            commands = self.model.inspect_model_parameters('Cultivar', self.template)
        except NotImplementedError:
            raise NodeNotFoundError(f'Template Cultivar name `{self.template}` not found')
        return commands

    @lru_cache(maxsize=200)
    def attach_cultivar(self, name: str, manager: str, param_name: str):
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
        # Manager provided as full path
        if manager in self.model.inspect_model('Models.Manager', fullpath=True):
            self.model.edit_model_by_path(
                path=manager,
                **{param_name: name}
            )

        # Manager provided as name
        elif manager in self.model.inspect_model('Models.Manager', fullpath=False):
            self.model.edit_model(
                model_type='Models.Manager',
                model_name=manager,
                **{param_name: name}
            )

        else:
            raise NodeNotFoundError(
                f"Manager script '{manager}' not found in the model."
            )

    # @lru_cache(maxsize=200)  # crucial during optimization
    def add_plant_replacements(self):
        self.model.add_crop_replacements()
        pr = self.model.get_crop_replacement(self.plant)
        plant_path = pr.FullPath
        return plant_path

    def get_plant_rep(self):
        pn = self.model.get_crop_replacement(self.plant)

        return pn

    def _load_plant_context(self):
        """
           Resolve the plant node and validate the template cultivar.

           Returns
           -------
           tuple
               (pp, pn, template_cultivars) where:
               - pp : str
                   Path to the plant replacement node.
               - pn : Models.PMF.Plant
                   The resolved plant node cast to a PMF Plant.
               - template_cultivars : list
                   Available cultivar names for the plant.
           """
        pp = self.add_plant_replacements()  # full path of the plant node in the replacements folder
        plant_node = get_node_by_path(self.model.Simulations, pp)
        pn = CLR.CastHelper.CastAs[CLR.Models.PMF.Plant](plant_node.Model)
        template_cultivars = self.model.inspect_model('Models.PMF.Cultivar', scope=pn, fullpath=False)
        if self.template not in template_cultivars:
            raise ValueError(f'Cultivar `{self.template} not in template cultivars')
        return pp, pn, template_cultivars

    def _init_edits(self, name):
        metas = self._load_plant_context()
        path, node, tpc = metas
        exp_new_cultivar_path = f"{node.FullPath}.{name}"
        if not self.model.has_node(exp_new_cultivar_path, node_type='Models.PMF.Cultivar', scope=node)['ok']:
            clt = CLR.Models.PMF.Cultivar()
            clt.Name = name
            # after attaching it is mutable in place
            ModelTools.ADD(clt, node)
        else:
            clt = get_node_by_path(node, exp_new_cultivar_path, cast_as=CLR.Models.PMF.Cultivar)
        return clt, node  # node is the plant node in the replacements folder

    def _format_cmds(self, new_commands):
        """Return merged commands formatted as key=value strings."""
        if not isinstance(new_commands, dict):
            raise TypeError(f'new_commands must be a dict got {type(new_commands)}')
        base_cmd = self.inspect_commands()
        merge_cmds = base_cmd.copy()
        merge_cmds.update(new_commands)  # new_commands take priority
        fmt_cmds = [f"{k}={v}" for k, v in merge_cmds.items()]
        return fmt_cmds

    def _update_cmds(self, cmds, name):
        """Format and apply command updates to the cultivar, then save the model."""
        if not isinstance(cmds, dict):
            raise TypeError(f'expected a dict but got {type(cmds)}')
        clt, clt_node = self._init_edits(name)
        cmds = self._format_cmds(cmds)
        clt.Command = cmds
        self.model.save()


    def edit_by_cmd_pairs(self, commands: dict, name: str = None, ):
        """
        Update cultivar commands using a dictionary of parameter–value pairs.

        Parameters
        ----------
        name : str
            New cultivar name to create or update.
        commands : dict
            Dictionary mapping command parameter paths to their new values.

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

            commands = {
                "[Phenology].Juvenile.Target.FixedValue": 180
            }

            ec.edit_by_cmd_pairs(name="eB_100", commands=commands)

            # Attach the new cultivar to a manager script
            ec.attach_cultivar(
                name="eB_100",
                manager="Sow using a variable rule",
                param_name="CultivarName"
            )
        """
        if not isinstance(commands, dict):
            raise TypeError(f'expected a dict but got {type(commands)}')

        name = name or f"ed_{self.plant}_{self.template}"
        self._update_cmds(cmds=commands, name=name)

    @timer
    def edit_by_cmd_values(self, commands: Iterable, values: Iterable, name: str = None, ):
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
        name = name or f"ed_{self.plant}_{self.template}"
        self._update_cmds(cmds=commands, name=name)

    def edit_by_cmd_iterable(self, name: str, commands: Iterable):
        """
           Update cultivar commands using an iterable of command strings.

           Parameters
           ----------
           name : str
               New cultivar name to create or update.
           commands : Iterable
               Iterable of command strings specifying parameter updates.
               Each command should follow the format:
               "[Node].path = value" see example below;

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
                   "[Phenology].Juvenile.Target.FixedValue = 180"
               ]

               ec.edit_by_cmd_iterable(name="eB_100", commands=commands)
               # the next part is to attach our new cultivar to whatever manager is sowing the cultivar
               ec.attach_cultivar('eB_100', manager='Sow using a variable rule, param_name='CultivarName')
           """
        cmds = _check_cmds(commands)
        self._update_cmds(cmds=cmds, name=name)


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


    def edit_cultivar_with_new_name(name, cmd_mtd, jtf=200, ):
        a_model = ApsimModel('Maize', f'_model2.apsimx')
        cc = CreatNewCultivar(model=a_model, template='Dekalb_XL82', plant='Maize')
        # cc.inspect_commands()
        # cc._load_plant_context()
        # p = cc.add_plant_replacements()
        if cmd_mtd == list or cmd_mtd == set:
            cc.edit_by_cmd_iterable(name, commands=(f'[Phenology].Juvenile.Target.FixedValue={jtf}',))
        else:
            cc.edit_by_cmd_pairs(commands={f'[Phenology].Juvenile.Target.FixedValue': jtf}, name=name, )
        # print(a_model.inspect_model_parameters('Cultivar', name))
        cc.attach_cultivar(name=name, manager='Sow using a variable rule', param_name='CultivarName')
        a_model.run()
        print(a_model.results.Yield.mean())
        return float(a_model.results.Yield.mean())


    apsim = ApsimModel('Maize', 'llmodel.apsimx')
    obj = CreatNewCultivar(model=apsim, template='Laila', plant='Maize')

    ed = apsim.inspect_model_parameters('Cultivar', 'Laila')
    # apsim.open_in_gui()
    # test dict like command
    test1 = edit_cultivar_with_new_name('Dekalb_XL82', jtf=100, cmd_mtd=dict)
    test2 = edit_cultivar_with_new_name('Dekalb_XL82-x', jtf=150, cmd_mtd=dict)
    assert test1 != test2, 'cultivar changes perhaps not successful'
    # test interavle
    test1 = edit_cultivar_with_new_name('Dekalb_XL82-x', jtf=100, cmd_mtd=list)
    test2 = edit_cultivar_with_new_name('Dekalb_XL82-x', jtf=150, cmd_mtd=list)
    assert test1 != test2, 'cultivar changes perhaps not successful'
    create_new_cultivar(apsim_model=apsim, template='B_100', parent_plant='Maize', commands=cm)
    create_new_cultivar(apsim_model=apsim, template='B_100', parent_plant='Maize',
                        commands={'[Phenology].GrainFilling.Target.FixedValue': '811'}, )
    model = apsim
    apsim.add_crop_replacements()
    apsim.add_crop_replacements()
    apsim.open_in_gui()
