import os
import unittest
from pathlib import Path
from os.path import realpath
import shutil
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.config import load_crop_from_disk
from apsimNGpy.exceptions import NodeNotFoundError

# -----------------------------
# Constants and APSIM node paths
# -----------------------------
Fertilise_at_sowing = '.Simulations.Simulation.Field.Fertilise at sowing'
SurfaceOrganicMatter = '.Simulations.Simulation.Field.SurfaceOrganicMatter'
Clock = ".Simulations.Simulation.Clock"
Weather = '.Simulations.Simulation.Weather'
Organic = '.Simulations.Simulation.Field.Soil.Organic'
cultivar_path = '.Simulations.Simulation.Field.Maize.CultivarFolder.Generic.B_100'
cultivar_path_soybean = '.Simulations.Simulation.Field.Soybean.Cultivars.Generic.Generic_MG2'
cultivar_path_for_sowed_soybean = '.Simulations.Simulation.Field.Soybean.Cultivars.Australia.Davis'
cultivar_path_for_sowed_maize = ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82"
# Create weather file on disk
met_file = realpath(Path('wf.met'))
met_file = load_crop_from_disk('AU_Goondiwindi', out=met_file, suffix='.met')
mf = load_crop_from_disk('AU_Goondiwindi', out=met_file, suffix='.met')


class TestEditModelByPath(unittest.TestCase):
    def setUp(self) -> None:
        put = Path(f'met-file{self._testMethodName}.met').resolve()
        src = load_crop_from_disk('AU_Goondiwindi', out=put, suffix='.met')
        self.met_file_copy = src

    # ---------------------------------------------------
    # Test editing a cultivar and verifying rename + update
    # ---------------------------------------------------
    def test_edit_cultivar_path_sowed_true(self):
        with ApsimModel('Maize') as model:
            with self.assertRaises(ValueError):
                model.edit_model_by_path(
                    path=cultivar_path_for_sowed_maize,
                    commands='[Grain].MaximumGrainsPerCob.FixedValue',
                    values=20,
                    sowed=True,
                    rename='edm'
                )

    # ---------------------------------------------------
    # Test multiple parameter edits on the main model
    # ---------------------------------------------------
    def test_edit_model_by_path(self):
        with ApsimModel('Maize') as apsim:
            # Apply edits
            apsim.edit_model_by_path(Fertilise_at_sowing, Amount=12)
            apsim.edit_model_by_path(Clock, start_date='01/01/2020')
            apsim.edit_model_by_path(SurfaceOrganicMatter, InitialCNR=100)
            apsim.edit_model_by_path(Weather, weather_file=realpath(self.met_file_copy))
            apsim.edit_model_by_path(Organic, Carbon=1.23)

            # Inspect updated values
            organic_params = apsim.inspect_model_parameters_by_path(Organic)
            self.assertIn('Carbon', organic_params)
            self.assertAlmostEqual(organic_params['Carbon'][0], 1.23, places=2)

            # Verify replacements node exists
            node = apsim.get_replacements_node()
            self.assertIsNone(node)

            # Test dict unpacking
            apsim.edit_model_by_path(**dict(path=Organic, Carbon=1.20))
            cc = apsim.inspect_model_parameters_by_path(Organic)
            self.assertAlmostEqual(cc['Carbon'][0], 1.20, places=2)

            # Test set_params interface
            apsim.set_params(dict(path=Organic, Carbon=1.58))
            updated = apsim.inspect_model_parameters_by_path(Organic)
            self.assertAlmostEqual(updated['Carbon'][0], 1.58, places=2)

    # ---------------------------------------------------
    # Test editing multiple params at once but with mixed unfounded attributes
    # assert raises
    # ---------------------------------------------------
    def test_edit_model_multiple_fields(self):
        with self.assertRaises(AttributeError):
            with ApsimModel('Maize') as model:
                model.edit_model_by_path(
                    SurfaceOrganicMatter,
                    InitialCNR=90,
                    InitialFractionFlat=0.3,
                    InitialFractionStanding=0.7
                )
                params = model.inspect_model_parameters_by_path(SurfaceOrganicMatter)

                self.assertEqual(params['InitialCNR'], 90)
                self.assertAlmostEqual(params['InitialFractionFlat'], 0.3, places=3)
                self.assertAlmostEqual(params['InitialFractionStanding'], 0.7, places=3)

    # ---------------------------------------------------
    # Test invalid path raises appropriate errors
    # ---------------------------------------------------
    def test_invalid_path(self):
        with ApsimModel('Maize') as model:
            with self.assertRaises(NodeNotFoundError):
                model.edit_model_by_path(".Simulations.Simulation.DoesNotExist", X=10)

    # ---------------------------------------------------
    # Test manager update requirement
    # ---------------------------------------------------
    def test_update_manager_requires_path(self):
        with ApsimModel('Maize') as model:
            with self.assertRaises(ValueError):
                # update_manager=True but no manager_path passed
                model.edit_model_by_path(
                    path=cultivar_path,
                    commands='[Grain].MaximumGrainsPerCob.FixedValue',
                    values=50,
                    update_manager=True
                )

    # ---------------------------------------------------
    # Ensure edited cultivar is in the node added
    # ---------------------------------------------------

    def test_edited_cultivar_added_to_replacements(self):
        with ApsimModel('Maize') as model:
            model.tree(cultivar=True)
            model.edit_model_by_path(
                path='.Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82',
                commands=[f'[Grain].MaximumGrainsPerCob.FixedValue={50}'],
                plant='Maize',
                managers={'.Simulations.Simulation.Field.Sow using a variable rule': 'CultivarName'},
                rename='edit-added')
            self.assertIn('edit-added', model.inspect_model('Models.PMF.Cultivar', fullpath=False),
                          msg='edited cultivar edit-added was not added to the replacement')

    # ---------------------------------------------------
    # Ensure edited cultivar is updated in the manager script; soybean model
    # ---------------------------------------------------
    def test_edited_cultivar_is_updated_to_manager(self):
        with ApsimModel('Maize') as model:
            model.edit_model_by_path(
                path=cultivar_path,
                commands={'[Grain].MaximumGrainsPerCob.FixedValue': 50},
                plant='Maize',
                sowed=False,
                managers={'.Simulations.Simulation.Field.Sow using a variable rule': 'CultivarName'},
                rename='edit-added')
            self.assertIn('edit-added', model.inspect_model_parameters_by_path(
                '.Simulations.Simulation.Field.Sow using a variable rule')['Parameters'].values())
        # ---------------------------------------------------
        # Ensure edited cultivar is updated in the manager script
        # ---------------------------------------------------

    def test_edited_cultivar_is_updated_to_manager_soy(self):
        with ApsimModel('Soybean') as model:
            model.edit_model_by_path(
                path=cultivar_path_soybean,
                commands={f'[Grain].MaximumGrainsPerCob.FixedValue': 50},
                plant='Soybean',
                sowedr=False,
                managers={'.Simulations.Simulation.Field.Sow using a variable rule': 'CultivarName'},
                rename='edit-added')
            self.assertIn('edit-added', model.inspect_model_parameters_by_path(
                '.Simulations.Simulation.Field.Sow using a variable rule')['Parameters'].values())

    # ---------------------------------------------------
    # Ensure if updating a cultivar path to manger is given but not the parameter holder, raise values error
    # ---------------------------------------------------
    def test_edited_updated_to_manager_cultivar_None(self):
        with ApsimModel('Maize') as model:
            with self.assertRaises(ValueError):
                model.edit_model_by_path(
                    path=cultivar_path,
                    commands='[Grain].MaximumGrainsPerCob.FixedValue',
                    values=50,
                    sowed=False,
                    manager_path='.Simulations.Simulation.Field.Sow using a variable rule',
                    manager_param=None,
                    rename='edit-added')

    # ---------------------------------------------------
    # Ensure if updating a cultivar path to manger is given but not the parameter holder, raise values error
    # ---------------------------------------------------

    def test_edited_updated_to_manager_cultivar_None_soy(self):
        with ApsimModel('Soybean') as model:
            with self.assertRaises(ValueError):
                model.edit_model_by_path(
                    path=cultivar_path_soybean,
                    commands='[Grain].MaximumGrainsPerCob.FixedValue',
                    values=50,
                    sowed=True,
                    manager_path='.Simulations.Simulation.Field.Sow using a variable rule',
                    manager_param=None,
                    rename='edit-added')

    # ensure editing morris/sobol works by path
    def test_edit_morris_clear_old_true(self):
        self.sens_model_test('Models.Morris', clear=True)
        self.sens_model_test('Models.Sobol', clear=True)

    def sens_model_test(self, sens_model, clear):
        if sens_model == 'Models.Morris':
            m_name = 'Morris'
        elif sens_model == 'Models.Sobol':
            m_name = 'Sobol'
        else:
            raise NotImplementedError(f"{sens_model} is not implemented")
        with ApsimModel(m_name) as model:
            path = model.inspect_model(sens_model)[0]
            model.edit_model_by_path(path=path, clear_old=clear,
                                     Parameters=[dict(Name='my', Path='Field.SurfaceOrganicMatter.InitialResidueMass',
                                                      LowerBound=10, UpperBound=400)])
            params = model.inspect_model_parameters_by_path(path)
            params = params['Parameters']
            if not clear:
                self.assertGreater(len(params), 1)
            else:
                self.assertEqual(len(params), 1)

    def test_edit_morris_clear_old_false(self):
        self.sens_model_test('Models.Morris', clear=False)
        self.sens_model_test('Models.Sobol', clear=False)

    # ---------------------------------------------------
    # Ensure edited cultivar values are reflected in the added node
    # ---------------------------------------------------
    def test_edited_updated_to_manager_values_are_updated(self):
        with ApsimModel('Maize') as model:
            model.edit_model_by_path(
                path=cultivar_path,
                plant='Maize',
                commands=[f'[Grain].MaximumGrainsPerCob.FixedValue={505}'],
                update_manager=False,
                managers={'.Simulations.Simulation.Field.Sow using a variable rule': 'CultivarName'},
                rename='edit-added')
            model.save()
            params = model.inspect_model_parameters('Models.PMF.Cultivar', 'edit-added')
            params = params['Command']

            self.assertIn(
                "[Grain].MaximumGrainsPerCob.FixedValue", params.keys(), 'Edited model not reflect reflecting'
            )
            value = params['[Grain].MaximumGrainsPerCob.FixedValue']
            self.assertEqual(value, '505', 'editing cultivar failed')
        # ---------------------------------------------------
        # Ensure edited cultivar values are reflected in the added node. Soybean
        # ---------------------------------------------------

    def test_edited_updated_to_manager_values_are_updated_soybean(self):
        with ApsimModel('Soybean') as model:
            model.edit_model_by_path(
                path=cultivar_path_soybean,
                plant='Soybean',
                commands=[f'[Grain].MaximumGrainsPerCob.FixedValue={50}'],

                sowed=False,
                managers={'.Simulations.Simulation.Field.Sow using a variable rule': 'CultivarName'},
                rename='edit-added')
            model.save()
            params = model.inspect_model_parameters('Models.PMF.Cultivar', 'edit-added')
            params = params['Command']

            self.assertIn(
                "[Grain].MaximumGrainsPerCob.FixedValue", params.keys(), 'Edited model not reflect reflecting'
            )
            value = params['[Grain].MaximumGrainsPerCob.FixedValue']
            self.assertEqual(value, '50', 'editing cultivar failed')

    def tearDown(self):
        try:
            Path(self.met_file_copy).unlink(missing_ok=True)
        except PermissionError:
            pass


if __name__ == '__main__':
    unittest.main()
