import unittest
from pathlib import Path
from os.path import realpath

from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.config import load_crop_from_disk
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
cultivar_path_soybean ='.Simulations.Simulation.Field.Soybean.Cultivars.Generic.Generic_MG2'
cultivar_path_for_sowed_soybean = '.Simulations.Simulation.Field.Soybean.Cultivars.Australia.Davis'
cultivar_path_for_sowed_maize = ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82"
# Create weather file on disk
met_file = realpath(Path('wf.met'))
met_file = load_crop_from_disk('AU_Goondiwindi', out=met_file, suffix='.met')


class TestEditModelByPath(unittest.TestCase):

    # ---------------------------------------------------
    # Test editing a cultivar and verifying rename + update
    # ---------------------------------------------------
    def test_edit_cultivar_path_sowed_true(self):
        with ApsimModel('Maize') as model:

            model.edit_model_by_path(
                path=cultivar_path_for_sowed_maize,
                commands='[Grain].MaximumGrainsPerCob.FixedValue',
                values=20,
                sowed=True,
                rename='edm'
            )

            # Verify rename
            edited = model.inspect_model_parameters_by_path(cultivar_path)
            self.assertIsNotNone(edited)

    # ---------------------------------------------------
    # Test multiple parameter edits on the main model
    # ---------------------------------------------------
    def test_edit_model_by_path(self):
        with ApsimModel('Maize') as apsim:

            # Apply edits
            apsim.edit_model_by_path(Fertilise_at_sowing, Amount=12)
            apsim.edit_model_by_path(Clock, start_date='01/01/2020')
            apsim.edit_model_by_path(SurfaceOrganicMatter, InitialCNR=100)
            apsim.edit_model_by_path(Weather, weather_file=realpath(met_file))
            apsim.edit_model_by_path(Organic, Carbon=1.23)

            # Inspect updated values
            organic_params = apsim.inspect_model_parameters_by_path(Organic)
            self.assertIn('Carbon', organic_params)
            self.assertAlmostEqual(organic_params['Carbon'].iloc[0], 1.23, places=2)

            # Verify replacements node exists
            node = apsim.get_replacements_node()
            self.assertIsNone(node)

            # Test dict unpacking
            apsim.edit_model_by_path(**dict(path=Organic, Carbon=1.20))
            cc = apsim.inspect_model_parameters_by_path(Organic)
            self.assertAlmostEqual(cc['Carbon'].iloc[0], 1.20, places=2)

            # Test set_params interface
            apsim.set_params(dict(path=Organic, Carbon=1.58))
            updated = apsim.inspect_model_parameters_by_path(Organic)
            self.assertAlmostEqual(updated['Carbon'].iloc[0], 1.58, places=2)

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
            model.inspect_file(cultivar=True)
            model.edit_model_by_path(
                path='.Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82',
                commands='[Grain].MaximumGrainsPerCob.FixedValue',
                values=50,
                sowed=True,
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
                commands='[Grain].MaximumGrainsPerCob.FixedValue',
                values=50,
                sowed=False,
                manager_path='.Simulations.Simulation.Field.Sow using a variable rule',
                manager_param='CultivarName',
                rename='edit-added')
            self.assertIn('edit-added', model.inspect_model_parameters_by_path(
                '.Simulations.Simulation.Field.Sow using a variable rule').values())
        # ---------------------------------------------------
        # Ensure edited cultivar is updated in the manager script
        # ---------------------------------------------------

    def test_edited_cultivar_is_updated_to_manager_soy(self):
        with ApsimModel('Soybean') as model:

            model.edit_model_by_path(
                path=cultivar_path_soybean,
                commands='[Grain].MaximumGrainsPerCob.FixedValue',
                values=50,
                sowedr=False,
                manager_path='.Simulations.Simulation.Field.Sow using a variable rule',
                manager_param='CultivarName',
                rename='edit-added')
            self.assertIn('edit-added', model.inspect_model_parameters_by_path(
                '.Simulations.Simulation.Field.Sow using a variable rule').values())

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

    # ---------------------------------------------------
    # Ensure edited cultivar values are reflected in the added node
    # ---------------------------------------------------
    def test_edited_updated_to_manager_values_are_updated(self):
        with ApsimModel('Maize') as model:
            model.edit_model_by_path(
                path=cultivar_path,
                commands='[Grain].MaximumGrainsPerCob.FixedValue',
                values=505,
                update_manager=False,
                manager_path='.Simulations.Simulation.Field.Sow using a variable rule',
                manager_param='CultivarName',
                rename='edit-added')
            model.save()
            params = model.inspect_model_parameters('Models.PMF.Cultivar', 'edit-added')

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
                commands='[Grain].MaximumGrainsPerCob.FixedValue',
                values=50,
                sowed=False,
                manager_path='.Simulations.Simulation.Field.Sow using a variable rule',
                manager_param='CultivarName',
                rename='edit-added')
            model.save()
            params = model.inspect_model_parameters('Models.PMF.Cultivar', 'edit-added')

            self.assertIn(
                "[Grain].MaximumGrainsPerCob.FixedValue", params.keys(), 'Edited model not reflect reflecting'
            )
            value = params['[Grain].MaximumGrainsPerCob.FixedValue']
            self.assertEqual(value, '50', 'editing cultivar failed')


if __name__ == '__main__':
    unittest.main()

