"""
The role of this module is to provide explicit support for editing cultivars
"""
from functools import lru_cache

from apsimNGpy import timer
from apsimNGpy.exceptions import NodeNotFoundError
from apsimNGpy.core.apsim import ApsimModel, CLR
from dataclasses import dataclass
from apsimNGpy.core.model_loader import get_node_by_path
from apsimNGpy.core.model_tools import ModelTools


def _check_cmds(commands):
    if isinstance(commands, dict):
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


@dataclass
class CultivarEditor:
    model: ApsimModel
    template_cultivar: str
    plant: str
    commands: dict = None

    def __hash__(self):
        return hash((self.plant, self.template_cultivar, self.commands, self.model))

    @lru_cache(maxsize=200)# templates are the same
    def inspect_commands(self):
        try:
            commands = self.model.inspect_model_parameters('Cultivar', self.template_cultivar)
        except NotImplementedError:
            raise NodeNotFoundError(f'Template Cultivar `{self.template_cultivar}` not found')
        return commands

    @lru_cache(maxsize=200)
    def attach_cultivar(self, name, manager, param_name):
        if name not in self.model.inspect_model('Models.PMF.Cultivar', fullpath=False):
            raise NodeNotFoundError(f"Attachment failed because Cultivar '{name}' not found in any Simulation")
        # manager is a full path
        if manager in self.model.inspect_model('Models.Manager', fullpath=True):
            manager_path = manager
            self.model.edit_model_by_path(path=manager_path, **{param_name: name})
        # manager is not full path
        elif manager in self.model.inspect_model('Models.Manager', fullpath=False):
            self.model.edit_model(model_type='Models.Manager', model_name=manager, **{param_name: name})
        else:
            # manager does not exist
            raise NodeNotFoundError(f'manager script `{manager}` is not available i')

    @lru_cache(maxsize=200)  # crucial during optimization
    def add_plant_replacements(self):
        self.model.add_crop_replacements()
        pr = self.model.get_crop_replacement(self.plant)
        plant_path = pr.FullPath
        return plant_path

    def get_plant_rep(self):
        pn = self.model.get_crop_replacement(self.plant)
        print(pn.Name, pn)
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
        pp = self.add_plant_replacements()
        plant_node = get_node_by_path(self.model.Simulations, pp)
        pn = CLR.CastHelper.CastAs[CLR.Models.PMF.Plant](plant_node.Model)
        template_cultivars = self.model.inspect_model('Models.PMF.Cultivar', scope=pn, fullpath=False)
        if self.template_cultivar not in template_cultivars:
            raise ValueError(f'Cultivar `{self.template_cultivar} not in template cultivars')
        return pp, pn, template_cultivars

    def _init_edits(self, name):
        metas = self._load_plant_context()
        path, node, tpc = metas

        temps = self.model.inspect_model('Models.PMF.Cultivar', scope=node)
        exp_new_cultivar_path = f"{node.FullPath}.{name}"
        if exp_new_cultivar_path not in temps:
            clt = CLR.Models.PMF.Cultivar()
            clt.Name = name
            # after attaching it is mutable in place
            ModelTools.ADD(clt, node)
        else:
            clt = get_node_by_path(node, exp_new_cultivar_path, cast_as=CLR.Models.PMF.Cultivar)
        return clt, node

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

    def edit_by_cmd_pairs(self, name, commands):
        """
            Update cultivar commands using a dictionary of parameter-value pairs.

            Parameters
            ----------
            name : str
                nw cultivar name to update.
            commands : dict
                Mapping of command parameters to their new values.
            """
        if not isinstance(commands, dict):
            raise TypeError(f'expected a dict but got {type(commands)}')
        self._update_cmds(cmds=commands, name=name)

    def edit_by_cmd_iterable(self, name, commands):
        """
        Update cultivar commands using a dictionary of parameter-value pairs.

        Parameters
        ----------
        name : str
            nw cultivar name to update.
        commands : Iterable
            Iterable of command parameters to their new values.
        """
        cmds = _check_cmds(commands)
        self._update_cmds(cmds=cmds, name=name)


if __name__ == "__main__":
    model = ApsimModel('Maize', 'model.apsimx')
    cc = CultivarEditor(model=model, template_cultivar='B_100', plant='Maize')
    cc.inspect_commands()
    cc._load_plant_context()
    p = cc.add_plant_replacements()
    cc.edit_by_cmd_pairs('B_1002', commands={'[Phenology].Juvenile.Target.FixedValue': 270})
    cc.edit_by_cmd_iterable('B_1002', commands={'[Phenology].Juvenile.Target.FixedValue=250'})
    print(model.inspect_model_parameters('Cultivar', 'B_1002'))

    cc.attach_cultivar(name='B_1002', manager='Sow using a variable rule', param_name='CultivarName')

    # model.open_in_gui()
