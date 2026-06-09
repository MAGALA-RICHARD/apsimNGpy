"""
Tests edit_model_method and inspect model_parameters co-currently.


"""
import unittest
from pathlib import Path
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester
from apsimNGpy.core.apsim import ApsimModel

wd = Path(__file__).parent.joinpath('test_edits')
wd.mkdir(parents=True, exist_ok=True)
from os import chdir

chdir(wd)
SIMULATION = 'Simulation'
import os


class TestCoreModel(BaseTester):

    def setUp(self):
        self.out_path = Path(f"{self._testMethodName}.apsimx")
        self.model = ApsimModel('Maize', out_path=self.out_path)
        self.out = f'test_edit_model{self._testMethodName}.apsimx'
        self.paths = {self.out_path}

    def test_append(self):
        with ApsimModel('Maize') as apsim:
            apsim.append_simulation(apsim[0], rename='clone')
            with self.assertRaises(ValueError):
                # in case same name is accidentally added to the simulation
                apsim.append_simulation(apsim[0], rename='clone')
            self.assertEqual(len(apsim), 2)

    def test_append_run(self):
        with ApsimModel('Maize') as model:
            model.append_simulation(model[0], rename='clone')
            model.run()
            self.assertFalse(model.results.empty)

    def test_append_run_member_wise_clone(self):
        with ApsimModel('Maize') as model:
            mc = model.member_wise_cone(0)
            model.append_simulation(mc, rename='clone')
            model.run()
            self.assertFalse(model.results.empty)

    def test_append_run_member_wise_cone_with_replacements(self):
        with ApsimModel('Maize') as model:
            model.add_crop_replacements()
            mc = model.member_wise_cone(0)
            model.append_simulation(mc, rename='clone')
            model.run()
            self.assertFalse(model.results.empty)

    def test_appended_sim_run_works(self):
        "Ensure that appended simulations can be edited"
        toPCarb = 1.233
        with ApsimModel('Maize') as model:
            sim = model[0]
            model.append_simulation(sim, rename='clone')
            model.edit_model(model_type='Organic', model_name='Organic', simulations='clone', Carbon=toPCarb)
            out = model.inspect_model_parameters(
                model_type='Organic',
                simulations='clone',
                model_name='Organic',
                parameters='Carbon')
            self.assertEqual(out['Carbon'][0], toPCarb, msg='Organic carbon not successfully '
                                                            'updated to target top layer after appending cloned')

    def test_if_we_can_add_simulation_externally(self):
        with ApsimModel('Maize') as model:
            with ApsimModel('Maize') as model2:
                sim = model[0]
                model2.append_simulation(sim, rename='clone2')
                self.assertEqual(len(model2), 2, msg='simulation failed to be added from an external simulations')
                # does it run
                model2.run(verbose=False)
                self.assertFalse(model2.results.empty)

    def test_we_edit_under_factorial_experiments(self):
        with ApsimModel('Factorial') as exp:
            exp.edit_model('Models.Manager', simulations='Base0',
                          model_name= 'FertiliserRule', ApplicationAmount=170)
            print(exp.inspect_model(model_type='Models.Manager'))
            out = exp.inspect_model_parameters('Models.Manager',
                                               'ApplicationAmount')
            print(
                out
            )
            amount = out['Base0']['Parameters']['ApplicationAmount']
            self.assertEqual(str(amount), '170',
                             msg='editing manager module in factorial simulation experiment failed')

    def test_if_we_can_add_simulation_externally2(self):
        with ApsimModel('Soybean') as model:
            # model.edit_model('Models.Report', 'Report', Name='soybean')
            with ApsimModel('Maize') as model2:
                # adding a clock replacement, by the time of this writing, soybean has long simulation period which will raise
                model2.add_replacements('.Simulations.Simulation.Clock')
                sim = model[0]
                model2.append_simulation(sim, rename='clone2')
                self.assertEqual(len(model2), 2, msg='simulation failed to be added from an external simulations')
                # does it run
                model2.run(verbose=False, cpu_count=2)
                self.assertFalse(model2.results.empty)

    def test_payload_in_append(self):
        with ApsimModel('Maize') as fixed_model:
            fixed_model.append_simulation(simulation=fixed_model[0], rename='clone1',
                                          payload=dict(model_type='Models.Manager',
                                                       model_name='Sow using a variable rule',
                                                       Population=12))
            self.assertIn('clone1', fixed_model.inspect_model("Models.Core.Simulation", fullpath=False))
            out = fixed_model.inspect_model_parameters('Models.Manager', model_name='Sow using a variable rule')
            # because they are more than one simulations

            out = out['clone1']['Parameters']

            pop = out['Population']
            pop = int(float(pop))
            self.assertEqual(pop, 12, msg='population was not successfully edited')
            fixed_model.run()
            df = fixed_model.results.groupby('SimulationID')['Yield'].mean()
            ans = list(df)
            self.assertNotEqual(*ans, msg='population was not successfully updated for the append simulation')

    def test_edit_report(self):
        with ApsimModel('Maize') as model:
            vs = model.inspect_model_parameters("Report", 'Report')['VariableNames']
            len_before = len(vs)
            model.edit_model(
                model_type="Report",
                model_name="Report",
                variable_spec=
                "[Maize].AboveGround.Wt as abw"
            )
            # inspect again
            vs = model.inspect_model_parameters("Report", 'Report')['VariableNames']
            len_after = len(vs)
            self.assertNotEqual(len_after, len_before, 'editing report failed')
            # test clear_old flag
            model.edit_model(
                model_type="Report",
                model_name="Report",
                clear_old=True,
                variable_spec=
                "[Maize].AboveGround.Wt as abw"
            )
            # inspect again
            vs = model.inspect_model_parameters("Report", 'Report')['VariableNames']
            len_after_clear_old = len(vs)
            self.assertEqual(1, len_after_clear_old, "clear_old flag did not work")

    def test_payload_with_external_simulation(self):
        with ApsimModel('Maize') as fixed_model:
            with ApsimModel('Maize') as model:
                sim = model[0]
            fixed_model.append_simulation(simulation=sim, rename='clone1',
                                          payload=dict(model_type='Models.Manager',
                                                       model_name='Sow using a variable rule',
                                                       Population=12))
            self.assertIn('clone1', fixed_model.inspect_model("Models.Core.Simulation", fullpath=False))
            out = fixed_model.inspect_model_parameters('Models.Manager', model_name='Sow using a variable rule')
            # because they are more than one simulations
            out = out['clone1']['Parameters']

            pop = out['Population']
            pop = int(pop)
            self.assertEqual(pop, 12, msg='population was not successfully edited')
            fixed_model.run()
            df = fixed_model.results.groupby('SimulationID')['Yield'].mean()
            ans = list(df)
            self.assertNotEqual(*ans, msg='population was not successfully')

    def test_independent_clone(self):
        with ApsimModel('Maize') as fixed_model:
            sim = fixed_model.independent_clone(0)
            fixed_model.append_simulation(simulation=sim, rename='pop12',
                                          payload=dict(model_type='Models.Manager',
                                                       model_name='Sow using a variable rule',
                                                       Population=12))
            fixed_model.run()
            df = fixed_model.results.groupby('SimulationID')['Yield'].mean()
            ans = list(df)
            self.assertEqual(len(fixed_model), 2)
            self.assertEqual(len(ans), 2)
            self.assertNotEqual(*ans, msg='population was not successfully')

    def test_edit_soil_organic_matter_module(self):
        toPCarb = 1.233
        self.model.edit_model(model_type='Organic', model_name='Organic', simulations=SIMULATION, Carbon=toPCarb)
        out = self.model.inspect_model_parameters(
            model_type='Organic',
            simulations=SIMULATION,
            model_name='Organic',
            parameters='Carbon'

        )
        self.assertEqual(out['Carbon'][0], toPCarb, msg='Organic carbon not successfully '
                                                        'updated to target top layer')

    def test_edit_sensitivity_models(self):
        "Test editing a soil related variable"
        with ApsimModel('sobol') as sobol:
            SIM = sobol[0].Name
            toPCarb = 1.233
            sobol.edit_model(model_type='Organic', model_name='Organic', simulations=SIM, Carbon=toPCarb)
            out = sobol.inspect_model_parameters(
                model_type='Organic',
                simulations=SIM,
                model_name='Organic',
                parameters='Carbon'

            )
            self.assertEqual(out['Carbon'][0], toPCarb, msg='Organic carbon not successfully '
                                                            'updated to target top layer for a sobol model')

    @staticmethod
    def check_param(parameters, name, lower, upper):
        """Check parameters for morris and sobol model types"""
        flag = False
        for pa in parameters:
            if pa.Name == name and pa.LowerBound == lower and pa.UpperBound == upper:
                flag = True
        return flag

    def test_editing_sobol_or_morris_model_clear_old_true(self):
        # For Morris
        with ApsimModel('Morris') as mmm:
            mmm.edit_model(model_type='Models.Morris', model_name='FallowSensitivity', Parameters=[
                dict(Name='my', Path='Field.SurfaceOrganicMatter.InitialResidueMass', LowerBound=10, UpperBound=400)
            ], clear_old=True, NumPaths=200)
            param = mmm.inspect_model_parameters('Models.Morris', model_name='FallowSensitivity')
            params = param['Parameters']
            num_path = param['NumPaths']
            self.assertEqual(float(num_path), 200.0)

            my = self.check_param(params, name='my', lower=10, upper=400)
            self.assertTrue(my, "Morris model was not updated successfully")
            # ensure that we can access the sobol model

            self.assertEqual(len(mmm.inspect_model('Models.Morris')), 1)
            # what about single string without a dot or full path?
            self.assertEqual(len(mmm.inspect_model('Morris')), 1)
            self.assertEqual(len(params), 1)
            # ensure missing keys are flagged off
            with self.assertRaises(ValueError):
                # skips the Name keys in the parameter description
                mmm.edit_model(model_type='Models.Morris', model_name='FallowSensitivity', Parameters=[
                    dict(Path='Field.SurfaceOrganicMatter.InitialResidueMass', LowerBound=10, UpperBound=400)
                ], clear_old=True)

    def test_editing_sobol_or_morris_model_clear_old_false(self):
        # For Morris
        with ApsimModel('Morris') as mmm:
            mmm.edit_model(model_type='Models.Morris', model_name='FallowSensitivity', Parameters=[
                dict(Name='my', Path='Field.SurfaceOrganicMatter.InitialResidueMass', LowerBound=10, UpperBound=400)
            ])
            params = mmm.inspect_model_parameters('Models.Morris', model_name='FallowSensitivity')
            params = params['Parameters']

            my = self.check_param(params, name='my', lower=10, upper=400)
            self.assertTrue(my, "Morris model was not updated successfully")
            # ensure that we can access the sobol model

            self.assertEqual(len(mmm.inspect_model('Models.Morris')), 1)
            # what about single string without a dot or full path?
            self.assertEqual(len(mmm.inspect_model('Morris')), 1)
        # for Sobol
        with ApsimModel('Sobol') as mmm:
            mmm.edit_model(model_type='Models.Sobol', model_name='Sobol', Parameters=[
                dict(Name='my', Path='Field.SurfaceOrganicMatter.InitialResidueMass', LowerBound=17, UpperBound=400)
            ], clear_old=False)
            params = mmm.inspect_model_parameters('Models.Sobol', model_name='Sobol')
            params = params['Parameters']
            my = self.check_param(params, name='my', lower=17, upper=400)
            self.assertTrue(my, "Sobol model was not updated successfully")
            # ensure that we can access the sobol model
            self.assertEqual(len(mmm.inspect_model('Models.Sobol')), 1)
            # what about single string without a dot or full path?
            self.assertEqual(len(mmm.inspect_model('Sobol')), 1)

    def test_edit_soil_multiple_soil_layers(self):
        """
        Scenario 2. Supplying a list to update soil layers

        """
        toPCarbList = [1.23, 1.0]
        self.model.edit_model(model_type='Organic', model_name='Organic', simulations=SIMULATION, Carbon=toPCarbList)

        self.model.edit_model(model_type='Organic', model_name='Organic', simulations=SIMULATION, Carbon=toPCarbList)
        out = self.model.inspect_model_parameters(
            model_type='Organic',
            simulations=SIMULATION,
            model_name='Organic',
            parameters='Carbon'

        )
        self.assertEqual(out['Carbon'][1], toPCarbList[1], msg='carbon  not successfully '
                                                               'updated by a list')

    def test_edit_solute_nh4(self):
        """

        Edit NH4 soil top layer
        """
        self.model.edit_model(model_type='Solute', model_name='NH4', simulations=SIMULATION, InitialValues=0.2)

    def test_editing_lower_layer(self):
        """
            Edit NH4 soil top layer
            """
        initialValues = 0.34
        self.model.edit_model(model_type='Solute', model_name='NH4', simulations=SIMULATION,
                              InitialValues=[initialValues], indices=[-1])
        out = self.model.inspect_model_parameters(
            model_type='Solute',
            model_name='NH4',
            simulations=SIMULATION,

        )
        self.assertEqual(out['InitialValues'][-1], initialValues, msg='InitialValues for NH4 not successfully '
                                                                      'updated to the target bottom layer')

    def test_edit_solute_urea(self):
        """"edits urea module"""
        urea = 0.03
        self.model.edit_model(model_type='Solute', model_name='Urea', simulations=SIMULATION, InitialValues=urea)
        out = self.model.inspect_model_parameters(
            model_type='Solute',
            model_name='Urea',
            simulations=SIMULATION,

        )
        self.assertEqual(out['InitialValues'][0], urea, msg='InitialValues for Urea not successfully updated')

    def test_edit_manager_script(self):
        """edits manager_script module"""
        population = 8.4
        self.model.edit_model(model_type='Manager', model_name='Sow using a variable rule', simulations=SIMULATION,
                              Population=population)
        out = self.model.inspect_model_parameters(
            model_type='Models.Manager',
            model_name='Sow using a variable rule',
            simulations=SIMULATION,

        )
        out = out['Parameters']
        self.assertEqual(float(out['Population']), population,
                         msg=f'Population; {population} not successfully updated ')

    def test_edit_surface_organic_mass(self):
        InitialResidueMass = 2500
        self.model.edit_model(model_type='SurfaceOrganicMatter', model_name='SurfaceOrganicMatter',
                              simulations=SIMULATION, InitialResidueMass=InitialResidueMass)
        out = self.model.inspect_model_parameters(
            model_type='SurfaceOrganicMatter',
            model_name='SurfaceOrganicMatter',
            simulations=SIMULATION,
            parameters='InitialResidueMass'
        )
        self.assertEqual(out['InitialResidueMass'], InitialResidueMass)

    def test_edit_surface_organic_cnr(self):
        InitialCNR = 85
        self.model.edit_model(model_type='SurfaceOrganicMatter', model_name='SurfaceOrganicMatter',
                              simulations=SIMULATION, InitialCNR=InitialCNR)
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
        self.model.edit_model(model_type='Clock', model_name='Clock', simulations=SIMULATION,
                              Start=f'{start_year}-01-01', End=f'{end_year}-01-12')

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
        self.model.edit_model(model_type='Report', model_name='Report', simulations=SIMULATION,
                              variable_spec='[Maize].AboveGround.Wt as abw')
        out = self.model.inspect_model_parameters(
            model_type='Report',
            model_name='Report',
            simulations=SIMULATION,
            parameters='VariableNames'
        )
        self.assertIsInstance(out, dict, 'Inspecting report was not successful, expected dict got {}'.format(type(out)))
        self.assertIn('[Maize].AboveGround.Wt as abw', out['VariableNames'], 'editing report was not successful')

    def test_edit_multiple_report_variables(self):
        self.model.edit_model(model_type='Report', model_name='Report', simulations=SIMULATION, variable_spec=[
            '[Maize].AboveGround.Wt as abw',
            '[Maize].Grain.Total.Wt as grain_weight'])
        out = self.model.inspect_model_parameters('Models.Report', 'Report')

        self.assertIn('[Maize].AboveGround.Wt as abw', out['VariableNames'])
        self.assertIn('[Maize].Grain.Total.Wt as grain_weight', out['VariableNames'])
        # avoid duplicates
        self.model.edit_model(model_type='Report', model_name='Report', simulations=SIMULATION, variable_spec=[
            '[Maize].AboveGround.Wt as abw',
            '[Maize].Grain.Total.Wt as grain_weight'])
        out = self.model.inspect_model_parameters('Models.Report', 'Report')
        vs = out['VariableNames']
        iv = '[Maize].AboveGround.Wt as abw', '[Maize].Grain.Total.Wt as grain_weight'
        data = []
        for i in vs:
            if i in iv:
                data.append(i)
        length = len(data)
        self.assertEqual(length, 2, "duplicates are appearing in the report ")

    def test_edit_model_sim_is_models_core_simulations(self):
        """Testing if editing models, with real simulation object specified works"""
        with ApsimModel("Maize") as model:
            model.edit_model(model_type='Report', model_name='Report', simulations=model[0], variable_spec=[
                '[Maize].AboveGround.Wt as abw',
                '[Maize].Grain.Total.Wt as grain_weight'])
            out = model.inspect_model_parameters('Models.Report', 'Report')
            self.assertIn('[Maize].AboveGround.Wt as abw', out['VariableNames'])
            self.assertIn('[Maize].Grain.Total.Wt as grain_weight', out['VariableNames'])

    def test_edit_model_sim_is_models_core_simulations2(self):
        """Testing if editing models, with real simulation object specified works"""
        with ApsimModel("Maize") as model:
            model.edit_model(model_type='Report', model_name='Report', simulations=model['Simulation'], variable_spec=[
                '[Maize].AboveGround.Wt as ABW',
                '[Maize].Grain.Total.Wt as grain_weight'])
            out = model.inspect_model_parameters('Models.Report', 'Report')
            self.assertIn('[Maize].AboveGround.Wt as ABW', out['VariableNames'])
            self.assertIn('[Maize].Grain.Total.Wt as grain_weight', out['VariableNames'])
            pass

    def test_run_model(self):
        """finally run model"""
        self.model.run()
        self.assertTrue(self.model.ran_ok)

    def tearDown(self):
        """finally teardown"""
        self.model.clean_up(db=True)
        for path in self.paths:
            if os.path.exists(path):
                os.remove(path)

    @classmethod
    def tearDownClass(cls):
        cls._clean_up(where=wd)


if __name__ == '__main__':
    unittest.main()
