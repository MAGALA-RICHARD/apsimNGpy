"""
The role of this module is to provide explicit support for editing cultivars
"""
from functools import lru_cache

from apsimNGpy.exceptions import NodeNotFoundError
from apsimNGpy.core.apsim import ApsimModel, CLR
from dataclasses import dataclass
from apsimNGpy.core.model_loader import get_node_by_path
from apsimNGpy.core.model_tools import ModelTools


def _check_cmds(commands):
    if isinstance(commands, dict):
        raise ValueError(f'expected a list like but got {type(commands)}')
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
        return hash((self.plant, self.template_cultivar,  self.commands, self.model))

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
            # manager does not exisit
            raise NodeNotFoundError(f'manager script `{manager}` is not available i')

    def add_plant_replacements(self):
        plants = self.model.inspect_model('Models.PMF.Plant')
        for plant in plants:
            if self.plant == plant.split('.')[-1]:
                plant_path = plant
                self.model.add_replacements(plant_path)
                break
        else:
            raise ValueError(f'No plants name `{self.plant}` found')
        pr = self.model.get_crop_replacement(self.plant)
        plant_path = pr.FullPath
        return plant_path

    def get_plant_rep(self):
        return self.model.get_crop_replacement(self.plant)

    def get_plant_node(self):
        pp = self.add_plant_replacements()
        plant_node = get_node_by_path(self.model.Simulations, pp)
        pn = CLR.CastHelper.CastAs[CLR.Models.PMF.Plant](plant_node.Model)
        template_cultivars = self.model.inspect_model('Models.PMF.Cultivar', scope=pn, fullpath=False)
        if self.template_cultivar not in template_cultivars:
            raise ValueError(f'Cultivar `{self.template_cultivar} not in template cultivars')
        return pp, pn, template_cultivars

    def _is_cultivar_added(self, cultivar_name, plant_node):
        inspect_c = self.model.inspect_model('Models.PMF.Cultivar', scope=plant_node, fullpath=False)
        if cultivar_name in inspect_c:
            return True
        return False

    def base(self, name):
        metas = self.get_plant_node()
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
        base_cmd = self.inspect_commands()
        merge_cmds = base_cmd.copy()
        merge_cmds.update(new_commands)  # new_commands take priority
        fmt_cmds = [f"{k}={v}" for k, v in merge_cmds.items()]
        return fmt_cmds

    def _update_cmds(self, cmds, name):
        if not isinstance(cmds, dict):
            raise ValueError(f'expected a dict but got {type(cmds)}')
        clt, clt_node = self.base(name)
        cmds = self._format_cmds(cmds)
        clt.Command = cmds
        self.model.save()

    def edit_cmds_by_dicts(self, name, commands):
        if not isinstance(commands, dict):
            raise ValueError(f'expected a dict but got {type(commands)}')
        self._update_cmds(cmds=commands, name=name)

    def edit_cmds_by_list_like(self, name, commands):
        cmds = _check_cmds(commands)
        self._update_cmds(cmds=cmds, name=name)


if __name__ == "__main__":
    model = ApsimModel('Maize', 'model.apsimx')
    cc = CultivarEditor(model=model, template_cultivar='B_100', plant='Maize')
    cc.inspect_commands()
    cc.get_plant_node()
    p = cc.add_plant_replacements()
    cc.edit_cmds_by_dicts('B_1002', commands={'[Phenology].Juvenile.Target.FixedValue': 270})
    cc.edit_cmds_by_list_like('B_1002', commands={'[Phenology].Juvenile.Target.FixedValue=8'})
    print(model.inspect_model_parameters('Cultivar', 'B_1002'))
    cc.get_plant_rep()
    cc.attach_cultivar(name='B_1002', manager='Sow using a variable rule', param_name='CultivarName')

    # model.open_in_gui()
