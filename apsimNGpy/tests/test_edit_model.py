"""
Tests edit_model_method and inspect model_parameters co-currently
"""
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.tests.base_test import BaseTester
import unittest

SIMULATION = 'Simulation'


class TestCoreModel(unittest.TestCase):

    def setUp(self):
        self.model = load_default_simulations('Maize')
        self.out = 'test_edit_model.apsimx'

    def test_edit_soil_organic_matter_module(self):
        toPCarb = 1.233
        self.model.edit_model(
            model_type='Organic',
            simulations=SIMULATION,
            model_name='Organic',
            Carbon=toPCarb)
        out = self.model.inspect_model_parameters(
            model_type='Organic',
            simulations=SIMULATION,
            model_name='Organic',
            parameters='Carbon'

        )
        self.assertEqual(out['Carbon'].iloc[0], toPCarb, msg='Organic carbon not successfully '
                                                             'updated to target top layer')

    def test_edit_soil_multiple_soil_layers(self):
        """
        scenario 2. supplying a list to update soil layers

        """
        toPCarbList = [1.23, 1.0]
        self.model.edit_model(
            model_type='Organic',
            simulations=SIMULATION,
            model_name='Organic',
            Carbon=toPCarbList)

        self.model.edit_model(
            model_type='Organic',
            simulations=SIMULATION,
            model_name='Organic',
            Carbon=toPCarbList)
        out = self.model.inspect_model_parameters(
            model_type='Organic',
            simulations=SIMULATION,
            model_name='Organic',
            parameters='Carbon'

        )
        self.assertEqual(out['Carbon'].iloc[1], toPCarbList[1], msg='carbon  not successfully '
                                                                    'updated by a list')

    def test_edit_solute_nh4(self):
        """

        Edit NH4 soil top layer
        """
        self.model.edit_model(
            model_type='Solute',
            simulations=SIMULATION,
            model_name='NH4',
            InitialValues=0.2)

    def test_editing_lower_layer(self):
        """
            Edit NH4 soil top layer 
            """
        initialValues = 0.34
        self.model.edit_model(
            model_type='Solute',
            simulations=SIMULATION,
            model_name='NH4',
            InitialValues=[initialValues], indices=[-1])
        out = self.model.inspect_model_parameters(
            model_type='Solute',
            model_name='NH4',
            simulations=SIMULATION,

        )
        self.assertEqual(out['InitialValues'].iloc[-1], initialValues, msg='InitialValues for NH4 not successfully '
                                                                           'updated to the target bottom layer')

    def test_edit_solute_urea(self):
        """"edits urea module"""
        urea = 0.03
        self.model.edit_model(
            model_type='Solute',
            simulations=SIMULATION,
            model_name='Urea',
            InitialValues=urea)
        out = self.model.inspect_model_parameters(
            model_type='Solute',
            model_name='Urea',
            simulations=SIMULATION,

        )
        self.assertEqual(out['InitialValues'].iloc[0], urea, msg='InitialValues for Urea not successfully updated')

    def test_edit_manager_script(self):
        """edits manager_script module"""
        population = 8.4
        self.model.edit_model(
            model_type='Manager',
            simulations=SIMULATION,
            model_name='Sow using a variable rule',
            Population=population)
        out = self.model.inspect_model_parameters(
            model_type='Models.Manager',
            model_name='Sow using a variable rule',
            simulations=SIMULATION,
            parameters='Population'
        )
        self.assertEqual(float(out['Population']), population,
                         msg=f'Population; {population} not successfully updated ')

    def test_edit_surface_organic_mass(self):
        InitialResidueMass = 2500
        self.model.edit_model(
            model_type='SurfaceOrganicMatter',
            simulations=SIMULATION,
            model_name='SurfaceOrganicMatter',
            InitialResidueMass=InitialResidueMass)
        out = self.model.inspect_model_parameters(
            model_type='SurfaceOrganicMatter',
            model_name='SurfaceOrganicMatter',
            simulations=SIMULATION,
            parameters='InitialResidueMass'
        )
        self.assertEqual(out['InitialResidueMass'], InitialResidueMass)

    def test_edit_surface_organic_cnr(self):
        InitialCNR = 85
        self.model.edit_model(
            model_type='SurfaceOrganicMatter',
            simulations=SIMULATION,
            model_name='SurfaceOrganicMatter',
            InitialCNR=InitialCNR)
        out = self.model.inspect_model_parameters(
            model_type='SurfaceOrganicMatter',
            model_name='SurfaceOrganicMatter',
            simulations=SIMULATION,
            parameters='InitialCNR'
        )
        self.assertEqual(out['InitialCNR'], InitialCNR)

    def test_edit_clock_dates(self):
        start_year, end_year = 1990, 2000
        import datetime
        self.model.edit_model(
            model_type='Clock',
            simulations=SIMULATION,
            model_name='Clock',
            Start=f'{start_year}-01-01',
            End=f'{end_year}-01-12')

        out = self.model.inspect_model_parameters(
            model_type='Clock',
            model_name='Clock',
            simulations=SIMULATION
        )

        expected_start = datetime.datetime(start_year, 1, 1)
        expected_end = datetime.datetime(end_year, 1, 12)

        self.assertEqual(out['Start'], expected_start, "Clock start date did not match expected value.")
        self.assertEqual(out['End'], expected_end, "Clock end date did not match expected value.")

    def test_edit_report_variable(self):
        self.model.edit_model(
            model_type='Report',
            simulations=SIMULATION,
            model_name='Report',
            variable_spec='[Maize].AboveGround.Wt as abw'
        )
        out = self.model.inspect_model_parameters(
            model_type='Report',
            model_name='Report',
            simulations=SIMULATION,
            parameters='VariableNames'
        )
        self.assertIsInstance(out, dict, 'Inspecting report was not successful, expected dict got {}'.format(type(out)))
        self.assertIn('[Maize].AboveGround.Wt as abw', out['VariableNames'], 'editing report was not successful')

    def test_edit_multiple_report_variables(self):
        self.model.edit_model(
            model_type='Report',
            simulations=SIMULATION,
            model_name='Report',
            variable_spec=[
                '[Maize].AboveGround.Wt as abw',
                '[Maize].Grain.Total.Wt as grain_weight'])

    def test_run_model(self):
        model = ApsimModel(model='Maize')
        model.run()
        self.assertTrue(model.ran_ok)
        model.clean_up(db=True)
        self.model.run()


if __name__ == '__main__':
    unittest.main()
