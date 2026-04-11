from apsimNGpy.core.ce import create_new_cultivar, CreatNewCultivar
from apsimNGpy.core.apsim import ApsimModel
import unittest
from apsimNGpy.exceptions import NodeNotFoundError

cm = {
    '[Phenology].Juvenile.Target.FixedValue': '201',
    '[Phenology].Photosensitive.Target.XYPairs.X': '0, 12.5, 24',
    '[Phenology].Photosensitive.Target.XYPairs.Y': '0, 0, 0',
    '[Phenology].FlagLeafToFlowering.Target.FixedValue': '1',
    '[Phenology].FloweringToGrainFilling.Target.FixedValue': '200',
    '[Phenology].GrainFilling.Target.FixedValue': '812',
    '[Phenology].Maturing.Target.FixedValue': '1',
    '[Phenology].MaturityToHarvestRipe.Target.FixedValue': '1',
    '[Rachis].DMDemands.Structural.DMDemandFunction.MaximumOrganWt.FixedValue': '360',
    '[Grain].MaximumGrainsPerCob.FixedValue': '500'
}


class TestEditCultivar(unittest.TestCase):

    def setUp(self):
        self.commands_dict = dict(cm)
        self.commands_list = [f"{k}={v}" for k, v in cm.items()]
        self.commands_set = set(self.commands_list)
        self.commands_str = '[Grain].MaximumGrainsPerCob.FixedValue=550'
        self.template = 'B_100'
        self.parent = 'Maize'

    # --------------------------------------------------
    # ✅ STRING INPUT
    # --------------------------------------------------
    def test_edit_cultivar_str(self):
        cultivar_name = 'ed_str'
        with ApsimModel('Maize') as model:
            create_new_cultivar(
                apsim_model=model,
                template=self.template,
                commands=self.commands_str,
                parent_plant=self.parent,
                rename=cultivar_name
            )

            params = model.inspect_model_parameters(
                'Models.PMF.Cultivar', model_name=cultivar_name
            )

            self.assertEqual(
                str(params.get('[Grain].MaximumGrainsPerCob.FixedValue')),
                '550'
            )

    # --------------------------------------------------
    # ✅ LIST INPUT
    # --------------------------------------------------
    def test_edit_cultivar_list(self):
        cultivar_name = 'ed_list'
        with ApsimModel('Maize') as model:
            create_new_cultivar(
                apsim_model=model,
                template=self.template,
                commands=self.commands_list,
                parent_plant=self.parent,
                rename=cultivar_name
            )

            params = model.inspect_model_parameters(
                'Models.PMF.Cultivar', model_name=cultivar_name
            )

            self.assertEqual(
                str(params.get('[Grain].MaximumGrainsPerCob.FixedValue')),
                '500'
            )

    # --------------------------------------------------
    # ✅ DICT INPUT
    # --------------------------------------------------
    def test_edit_cultivar_dict(self):
        cultivar_name = 'ed_dict'
        with ApsimModel('Maize') as model:
            create_new_cultivar(
                apsim_model=model,
                template=self.template,
                commands=self.commands_dict,
                parent_plant=self.parent,
                rename=cultivar_name
            )

            params = model.inspect_model_parameters(
                'Models.PMF.Cultivar', model_name=cultivar_name
            )
            self.assertEqual(
                str(params.get('[Grain].MaximumGrainsPerCob.FixedValue')),
                '500'
            )

    # --------------------------------------------------
    # ✅ SET INPUT
    # --------------------------------------------------
    def test_edit_cultivar_set(self):
        cultivar_name = 'ed_set'
        with ApsimModel('Maize') as model:
            create_new_cultivar(
                apsim_model=model,
                template=self.template,
                commands=self.commands_set,
                parent_plant=self.parent,
                rename=cultivar_name
            )

            params = model.inspect_model_parameters(
                'Models.PMF.Cultivar', model_name=cultivar_name
            )

            self.assertEqual(
                str(params.get('[Grain].MaximumGrainsPerCob.FixedValue')),
                '500'
            )

    # --------------------------------------------------
    # ✅ MULTIPLE PARAM UPDATE
    # --------------------------------------------------
    def test_multiple_parameter_update(self):
        cultivar_name = 'ed_multi'
        cmds = dict(self.commands_dict)
        key = '[Phenology].Juvenile.Target.FixedValue'
        cmds[key] = '201'
        with ApsimModel('Maize') as model:
            model.add_crop_replacements()
            create_new_cultivar(
                apsim_model=model,
                template=self.template,
                commands=cmds,
                parent_plant=self.parent,
                rename=cultivar_name
            )

            params = model.inspect_model_parameters(
                'Models.PMF.Cultivar', model_name=cultivar_name
            )

            self.assertEqual(
                str(params.get(key)),
                '201'
            )
            self.assertEqual(
                str(params.get('[Grain].MaximumGrainsPerCob.FixedValue')),
                '500'
            )

    def _cultivar_value_test(self, *, model, key, value, cultivar_name):
        params = model.inspect_model_parameters(
            'Models.PMF.Cultivar', model_name=cultivar_name
        )

        self.assertEqual(
            str(params.get(key)),
            value
        )

    def test_creat_new_cultivar_class_dict_input(self):
        cultivar_name = 'ed_lised'
        cmds = dict(self.commands_dict)
        key = '[Phenology].Juvenile.Target.FixedValue'
        key2 = '[Phenology].GrainFilling.Target.FixedValue'
        value2 = '816'
        cmds[key] = '201'
        cmds[key2] = value2
        with ApsimModel('Maize') as model:
            cc = CreatNewCultivar(model=model, template='Dekalb_XL82', plant='Maize')
            cc.edit_by_cmd_pairs(name=cultivar_name, commands=cmds)
            self._cultivar_value_test(model=model, key=key, value='201', cultivar_name=cultivar_name)
            self._cultivar_value_test(model=model, key=key2, value=value2, cultivar_name=cultivar_name)
            for k, v in cmds.items():
                self._cultivar_value_test(model=model, key=k, value=v, cultivar_name=cultivar_name)
            # Ensure it runs
            model.run()
            self.assertFalse(model.results.empty)

    def test_creat_new_cultivar_class_sequence_input(self):
        cultivar_name = 'ed_seq'
        cmds = tuple(self.commands_list)

        with ApsimModel('Maize') as model:
            cc = CreatNewCultivar(model=model, template='Hycorn_53', plant='Maize')
            cc.edit_by_cmd_iterable(name=cultivar_name, commands=cmds)
            cmds ={kv.split('=')[0]:kv.split('=')[1] for kv in cmds}
            for k, v in cmds.items():
                self._cultivar_value_test(model=model, key=k, value=v, cultivar_name=cultivar_name)
            # Ensure it runs
            model.run()
            self.assertFalse(model.results.empty)

    # --------------------------------------------------
    # ✅ RENAME DEFAULT (None)
    # --------------------------------------------------
    def test_default_rename(self):
        with ApsimModel('Maize') as model:
            create_new_cultivar(
                apsim_model=model,
                template=self.template,
                commands=self.commands_str,
                parent_plant=self.parent,
                rename=None
            )

            cultivars = model.inspect_model('Models.PMF.Cultivar', fullpath=False)

            # should contain something like edB_100
            self.assertTrue(any('ed' in c for c in cultivars))

    # --------------------------------------------------
    # ✅ Ensure model runs and returns results after editing
    # --------------------------------------------------

    def test_run(self):
        with ApsimModel('Maize') as model:
            model.add_crop_replacements()
            create_new_cultivar(
                apsim_model=model,
                template=self.template,
                commands=self.commands_str,
                parent_plant=self.parent,
                rename=None
            )
            model.run()
            self.assertFalse(model.results.empty, msg='Model did not run successfully')

    # --------------------------------------------------
    # ❌ INVALID COMMAND TYPE
    # --------------------------------------------------
    def test_invalid_command_type(self):
        with ApsimModel('Maize') as model:
            with self.assertRaises(ValueError):
                create_new_cultivar(
                    apsim_model=model,
                    template=self.template,
                    commands=123,  # invalid
                    parent_plant=self.parent,
                    rename='bad_case'
                )

    def test_plant_not_found(self):
        with ApsimModel('Maize') as model:
            with self.assertRaises(NodeNotFoundError):
                create_new_cultivar(
                    apsim_model=model,
                    template=self.template,
                    commands=self.commands_set,
                    parent_plant='Wheat',  # invalid because only maize is available
                    rename='bad_case'
                )


if __name__ == '__main__':
    unittest.main()
