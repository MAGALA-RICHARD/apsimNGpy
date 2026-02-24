"""
This script validates the functionality of the CoreModel class
as inherited by the ApsimModel. While CoreModel provides the foundational
implementation, ApsimModel remains the primary interface used in practice. So. here ApsimModel is imported for tests
"""
import os
import shutil
import unittest
from functools import lru_cache
from pathlib import Path
import pandas as pd
from apsimNGpy import Apsim
from apsimNGpy.config import stamp_name_with_version
from apsimNGpy.logger import logger

apsim = Apsim()
Models = apsim.CLR.Models
from apsimNGpy.core.model_tools import find_model, validate_model_obj, find_child
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester

IS_NEW_APSIM = apsim.CLR.file_format_modified

wd = Path.cwd() / "test_core"


@lru_cache(maxsize=1)  # run once per process
def prepare():
    if wd.exists():
        try:
            shutil.rmtree(wd)
            logger.info(f"cleaned up directory {wd}")
        except PermissionError:
            for i in wd.iterdir():
                logger.info(f"removing {i}")
                if i.is_file():
                    try:
                        i.unlink(missing_ok=True)
                    except PermissionError:
                        pass


prepare()
wd.mkdir(parents=True, exist_ok=True)
os.chdir(wd)
VERSION = apsim.CLR.apsim_compiled_version


class TestCoreModel(BaseTester):
    def setUp(self):
        self.user_file_name = stamp_name_with_version(
            os.path.realpath(f"{self._testMethodName}.apsimx"))  # do not delete until tearing up
        self.weather_file_nasa = os.path.realpath('test__met_nasa.met')
        self.weather_file_daymet = os.path.realpath('test_met_daymet.met')
        self.test_user_out_path = stamp_name_with_version(os.path.realpath(f'{self._testMethodName}.apsimx'))
        self.model = 'Maize'
        self.test_save_path = Path(f"save_{self._testMethodName}.apsimx")

        self.paths = {self.test_user_out_path,
                      self.weather_file_nasa,
                      self.weather_file_daymet,
                      self.user_file_name}

    def test_save_reload_false(self):

        try:
            self.test_save_path.unlink(missing_ok=True)
        except PermissionError:
            pass
        with apsim.ApsimModel('Maize') as maize_model:
            cp = maize_model.path
            maize_model.save(file_name=self.test_save_path, reload=False)
            self.assertGreater(self.test_save_path.stat().st_size, 0, 'saving the model failed when reload =False')
            self.assertEqual(cp, maize_model.path)
        print(Path(maize_model.datastore).exists())

    def test_save_reload_true(self):

        try:
            self.test_save_path.unlink(missing_ok=True)
        except PermissionError:
            pass
        with apsim.ApsimModel('Maize') as maize_model:
            cp = maize_model.path
            maize_model.save(file_name=self.test_save_path, reload=True)
            self.assertGreater(self.test_save_path.stat().st_size, 0, 'saving the model failed when reload =True')
            self.assertNotEqual(cp, maize_model.path)

    def test_out_path(self):
        """
        Test that we can provide an output path for the file name
        @return:
        """
        user_name = stamp_name_with_version(os.path.realpath(f'use_name_ot_test.apsimx'))
        if os.path.exists(user_name):
            os.remove(user_name)
        with apsim.ApsimModel('Maize') as model:
            in_path = str(model.path)
            # self.assertEqual(in_path, str(user_name))
            self.assertGreater(os.path.getsize(model.path), 0, 'out_path is empty')
            model.clean_up()

    def test_random_out_path(self):
        with apsim.ApsimModel('Maize') as model:
            self.assertTrue(os.path.exists(model.path))
            self.paths.add(model.path)

    def test_run(self):

        """ Test the run method's behavior under normal conditions.
         ==========================================================="""

        """There are several ways to check if the run was successful, here I have tried all of them"""
        with apsim.ApsimModel('Maize') as model:
            model.run(report_name=['Report'])
            self.assertIsInstance(model.results, pd.DataFrame,
                                  msg="an error occurred while passing  alist "
                                      "of report names")
            # one more test
            # check if the use pass  report name as str a strict a pandas.core.frame.DataFrame' is returned
            model.run(report_name='Report', verbose=False)
            df = model.results
            self.assertIsInstance(df, pd.DataFrame)
            # check if it is not empty
            self.assertEqual(df.empty, False, msg='Model was run, but results are empty')
            self.assertTrue(model.ran_ok, f'something happened in {repr(model)}')
            self.paths.add(self.user_file_name)

    #            self.assertTrue(mock_datastore.Close.called)

    def test_update_mgt(self):
        """ Test the update method's behavior under
        ==========================================="""
        Amount = 23.557777
        script_name = 'Fertilise at sowing'
        mgt_script = {'Name': script_name, 'Amount': Amount},
        with apsim.ApsimModel(model='Maize') as model:
            model.update_mgt(management=mgt_script)
            # extract user infor
            value = model.inspect_model_parameters('Manager', simulations='Simulation',
                                                   model_name='Fertilise at sowing', parameters='Amount')
            amountIn = float(value['Amount'])
            self.assertEqual(amountIn, Amount)

    def test_find_simulations(self):
        """ Test find_simulations based on three input None, lists and string
        =====================================================================
        """
        # test None
        sim = 'Simulation'
        MSG = f'test_find_simulations failed to return requested simulation object: {sim}'
        with apsim.ApsimModel("Maize") as model:
            self.assertTrue(model.find_simulations(), msg=MSG)
            # test str
            self.assertTrue(model.find_simulations(simulations=sim), msg=MSG)
            # test tuple

            self.assertTrue(model.find_simulations(simulations=(sim,)), msg=MSG)
            # test list input
            self.assertTrue(model.find_simulations(simulations=[sim]), msg=MSG)

    def test_get_simulated_output(self):
        """ Test load_simulated_results
        requires that the models are run first
        ================================================
        """
        with apsim.ApsimModel('Maize') as model:
            model.run()
            if not model.ran_ok:
                raise unittest.SkipTest(f'skipping test_simulated_results because model did '
                                        f'not run successfully or db was deleted')
            repos = model.get_simulated_output(report_names='Report')
            msg = f"expected pd.dataframe but received {type(repos)}"
            self.assertIsInstance(repos, pd.DataFrame, msg=msg)

    def test_get_reports(self):
        with apsim.ApsimModel('Maize') as maize_model:
            self.assertIsInstance(maize_model.inspect_model('Report'), list)
            self.assertTrue(maize_model.tables_list)

    def test_inspect_clock(self):
        with apsim.ApsimModel('Maize') as maize_model:
            self.assertIsInstance(maize_model.inspect_model('Clock'), list)

    def test_inspect_simulation(self):
        with apsim.ApsimModel('Maize') as maize_model:
            self.assertIsInstance(maize_model.inspect_model('Models.Core.Simulation', fullpath=False), list)

    def test_find__simulations(self):
        with apsim.ApsimModel('Maize') as model:
            # get a list of simulations
            sims = model.find_simulations()
            self.assertIsInstance(sims, tuple)
            self.assertTrue(len(sims) > 0)
            sims = model.find_simulations(simulations=None)
            # ensures simulations are enclosed in a list
            self.assertIsInstance(sims, tuple)
            self.assertTrue(len(sims) > 0)

    def test_find__simulations_when_str(self):
        with apsim.ApsimModel('Maize') as model:
            # get a list of simulations
            sims = model.find_simulations()
            self.assertIsInstance(sims, tuple)
            self.assertTrue(len(sims) > 0)
            sims = model.find_simulations(simulations='Simulation')
            # ensures simulations are enclosed in a list
            self.assertIsInstance(sims, list)
            self.assertTrue(len(sims) > 0)

    def test_rename(self):
        NEW_NAME = 'NEW_SIM_NAME'
        NEW_SIMs_NAME = 'NEW_SIMULATION_NAME'
        with apsim.ApsimModel("Maize") as model:
            model.rename_model(model_type="Simulation", old_name='Simulation', new_name=NEW_NAME)
            # check if it has been successfully renamed
            sims = model.inspect_model(model_type='Simulation', fullpath=False)
            assert NEW_NAME in sims, 'rename not successful'
            # The alternative is to use model.tree to see your changes
            model.rename_model(model_type="Simulations", old_name='Simulations', new_name=NEW_SIMs_NAME)
            assert NEW_SIMs_NAME in model.inspect_model(model_type='Simulations',
                                                        fullpath=False), 'renaming simulations was not successful'
        path = model.datastore
        self.assertFalse(os.path.exists(path))

    def test_replace_soil_property_values(self):
        parameter = 'Carbon'
        param_values = [2.4, 1.4]
        with apsim.ApsimModel("Maize") as model:
            model.replace_soil_property_values(parameter=parameter, param_values=param_values,
                                               soil_child='Organic', )
            lisT = model.inspect_model_parameters(model_type='Organic', simulations='all', model_name='Organic',
                                                  parameters='Carbon')
            lisT = lisT['Carbon'].tolist()
            self.assertIsInstance(lisT, list, msg='expected a list got {}'.format(type(lisT)))
            self.assertTrue(lisT)
            self.assertIsInstance(lisT, list, msg='expected a list got {}'.format(type(lisT)))
            self.assertTrue(lisT)
            # if it was successful
            testP = model.inspect_model_parameters(model_type='Organic', model_name='Organic',
                                                   parameters='Carbon')
            testP = testP['Carbon'].tolist()
            self.assertEqual(lisT[:2], param_values,
                             msg=f'replace_soil_property_values was not successful returned {testP}\n got {param_values}')

    def test_replace_soil_properties_by_path(self):
        param_values = [1.45, 1.95]
        with apsim.ApsimModel("Maize") as model:
            model.edit_model(model_type='Organic', model_name='Organic', Carbon=param_values)

    def test_update_mgt_by_path(self):
        # test when fmt  ='.'
        pathto = '.Simulations.Simulation.Field.Sow using a variable rule'
        with apsim.ApsimModel("Soybean") as model:
            # model.update_mgt_by_path(path=pathto, Population=7.5, fmt='.')
            model.run()
            self.assertTrue(model.ran_ok, msg='simulation was not ran when fmt was .')
            # test when fmt = '/'
            pathto = '/Simulations/Simulation/Field.Sow using a variable rule'
            model.update_mgt_by_path(path=pathto, Population=7.5, fmt='/')
            model.run()
            self.assertTrue(model.ran_ok, msg='simulation was not ran when fmt was /')
        path = model.datastore
        self.assertFalse(os.path.exists(path), msg='datastore path was not deleted')

    def test_create_experiment(self):
        """creates a factorial experiment adds a factor, then test if it runs successfully
        =====================================================================================
        """
        if IS_NEW_APSIM:
            pass
            # being tested else where in another file
        else:
            with apsim.ApsimModel("Maize") as model:
                model.create_experiment()
                # add factor
                model.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20",
                                 factor_name='Nitrogen')
                model.run()
                self.assertTrue(model.ran_ok, msg='after adding the experiment and factor running apsim failed')
            path = model.datastore
            self.assertFalse(os.path.exists(path), msg='datastore path was not deleted or cleaned up')

    def test_add_crop_replacements(self):
        with apsim.ApsimModel("Maize") as model:
            model.add_crop_replacements(_crop='Maize')
            xp = find_child(model.Simulations, child_name='Replacements', child_class='Models.Core.Folder')
            # xp = self.test_ap_sim.Simulations.FindInScope('Replacements')
            if xp:
                rep = True
            else:
                rep = False
            self.assertTrue(rep, msg='replacement was not successful')

    def test_replace_soils_values_by_path(self):
        node = '.Simulations.Simulation.Field.Soil.Organic'
        with apsim.ApsimModel("Maize") as model:
            model.replace_soils_values_by_path(node_path=node,
                                               indices=[0], Carbon=1.3)
            v = model.get_soil_values_by_path(node, 'Carbon')['Carbon'][0]
            self.assertEqual(v, 1.3)

    def test_add_db_table(self):
        with apsim.ApsimModel("Maize") as model:
            model.add_db_table(
                variable_spec=['[Clock].Today', '[Soil].Nutrient.TotalC[1]/1000 as SOC1',
                               '[Maize].Grain.Total.Wt*10 as Yield'],
                rename='report4', set_event_names=['[Maize].Harvesting', '[Clock].EndOfYear'])
            # check if report is created
            _reports = model.inspect_model('Models.Report()', fullpath=False)

            assert 'report4' in _reports, 'report4 was not found in reports'
            # try running
            model.run('report4')

            self.assertTrue(model.ran_ok, msg='simulation was not ran after adding the report table report2.')

    def test_loading_defaults_with(self):
        with apsim.ApsimModel("Maize", out_path=Path('ld.apsimx').absolute()) as model:
            model.run()
            self.assertTrue(model.ran_ok, 'simulation was not ran after using default within apsim.ApsimModel class')
            self.paths.add(model.path)

    def test_edit_with_path_som(self):
        with  apsim.ApsimModel(model='Maize', out_path='path_som.apsimx') as model:
            initial_ratio = 200.0
            model.edit_model_by_path('.Simulations.Simulation.Field.SurfaceOrganicMatter', InitialCNR=initial_ratio,
                                     verbose=False)
            # after inspecting if it was successfully updated
            icnr = model.inspect_model_parameters(model_type='SurfaceOrganicMatter', model_name='SurfaceOrganicMatter',
                                                  parameters='InitialCNR')
            self.assertEqual(icnr['InitialCNR'], initial_ratio, msg='InitialCNR was not successfully updated by '
                                                                    'edit_model_by_path method')
            self.paths.add(model.path)
            model.clean_up()

    def test_find_model_and_eval_models(self):
        """
        Unit test for the `find_model` and `_eval_model` functions.
        Verifies that:
        - Models can be found correctly by name (case-insensitive).
        - Strings representing full module paths are evaluated correctly.
        """

        # Test finding a model by simple string name
        clok_model = find_model('clock')
        validate_model_obj(clok_model)  # Validate model lookup
        self.assertEqual(clok_model, Models.Clock)  # Ensure it matches the Clock model

        simulation_model = find_model('Simulation')
        validate_model_obj(simulation_model)  # Validate model lookup
        self.assertEqual(simulation_model, Models.Core.Simulation)  # Ensure correct match

        # Test direct evaluation of model paths as strings
        clock = validate_model_obj('Models.Clock')
        self.assertEqual(clock, Models.Clock)  # Confirm evaluation matches Clock model

        simulation = validate_model_obj('Models.Core.Simulation')
        self.assertEqual(simulation, Models.Core.Simulation)  # Confirm evaluation matches Core.Simulation model

        # Test direct evaluation of just model name
        experiment = validate_model_obj('Experiment')
        self.assertEqual(experiment,
                         Models.Factorial.Experiment)  # Confirm evaluation matches Models.Factorial.ExperimentManager model

        factors = validate_model_obj('Factors')
        self.assertEqual(factors, Models.Factorial.Factors)  # Confirm evaluation matches Models.Factorial.Factors model

    def test_add_model_simulation(self):
        with apsim.ApsimModel("Maize") as model:
            if not IS_NEW_APSIM:

                try:
                    model.add_model('Simulation', adoptive_parent='Simulations', rename='soybean_replaced',
                                    source='Soybean', override=True)

                    assert 'soybean_replaced' in model.inspect_model('Simulation',
                                                                     fullpath=False), 'testing adding simulations was not successful'
                # clean up
                finally:
                    from apsimNGpy.core.core import get_or_check_model

                    model.remove_model(model_class='Simulation', model_name='soybean_replaced')

    def test_inspect_file(self):
        """Checks if the model simulation tree is working"""
        with apsim.ApsimModel("Maize") as model:
            _inspected = model.tree(console=False)
            self.assertTrue(_inspected)

    def test_get_weather_from_web_nasa(self):
        with apsim.ApsimModel("Maize") as model:
            try:
                model.get_weather_from_web(lonlat=(-93.50456, 42.601247), start=1990, end=2001, source='nasa',
                                           filename=self.weather_file_nasa)
                model.run()
                self.assertTrue(model.ran_ok)
                self.paths.add(model.path)
                model.clean_up()
            except KeyError:
                pass

    def test_add_replacements(self):
        from apsimNGpy.core import ApsimModel
        with ApsimModel('Report', ) as model:
            model.add_replacements('.Simulations.SimpleReportingSim.Field.Soil ')

    def test_add_replacements_with_invalid_args(self):
        from apsimNGpy.exceptions import NodeNotFoundError
        from apsimNGpy.core import ApsimModel
        with self.assertRaises(NodeNotFoundError, msg='Node not found error is not succeeding'):
            # ensure an invalid path leads to a NodeNotFoundError
            with ApsimModel('Report', ) as model:
                model.add_replacements('.Simulations.SimpleReportingSim.Field.Soil-xx ')
        with self.assertRaises(ValueError):
            # ensure empty arguments do not pass
            with ApsimModel('Report', ) as model:
                model.add_replacements()

    def test_get_weather_from_web_daymet(self):
        with apsim.ApsimModel("Maize") as model:
            model.get_weather_from_web(lonlat=(-93.50456, 42.601247), start=1990, end=2001, source='daymet',
                                       filename=self.weather_file_daymet)
            model.run()
            self.assertTrue(model.ran_ok)
            self.paths.add(model.path)

    def test_edit_model(self):
        with apsim.ApsimModel("Maize") as model:
            model.edit_model(model_type='Clock', model_name='Clock', simulations="Simulation",
                             Start='1900-01-01', End='1990-01-12')
            info = model.inspect_model_parameters('Models.Clock', 'Clock')

            self.assertEqual(info['Start'].year, 1900, 'Simulation start date was not successfully changed')
            self.assertEqual(info['End'].year, 1990, 'Simulation end date was not successfully changed')

    def test_edit_water_model_water_balance(self):
        # Context manager loads the APSIM model and ensures cleanup
        with apsim.ApsimModel('Maize') as corep:
            # ------------------------------------------------------------
            # 1. Test layered attribute when provided as a list
            # ------------------------------------------------------------
            replace_with = [3, 3, 5, 50, 60]
            corep.edit_model(
                'Models.WaterModel.WaterBalance',
                'SoilWater',
                SWCON=replace_with
            )

            inp = corep.inspect_model_parameters(
                'Models.WaterModel.WaterBalance',
                'SoilWater'
            )
            out_list = inp["SWCON"][:len(replace_with)]

            self.assertEqual(out_list, replace_with, msg="List-based SWCON update failed")

            # ------------------------------------------------------------
            # 2. Test scalar update for an array attribute
            #    (should broadcast scalar to entire array or update index 0)
            # ------------------------------------------------------------
            corep.edit_model_by_path(
                '.Simulations.Simulation.Field.Soil.SoilWater',
                SWCON=5
            )

            sw1 = corep.inspect_model_parameters_by_path(
                '.Simulations.Simulation.Field.Soil.SoilWater'
            )

            self.assertIsInstance(sw1["SWCON"], list,
                                  msg="SWCON should be converted to a list internally")

            self.assertEqual(sw1["SWCON"][0], 5.0, msg=
            "Scalar-to-array update failed: SWCON not filled with scalar value")

            # ------------------------------------------------------------
            # 3. Test updating typical scalar attributes
            # ------------------------------------------------------------
            corep.edit_model_by_path(
                '.Simulations.Simulation.Field.Soil.SoilWater',
                SWCON=5,
                DiffusConst=35
            )

            sw2 = corep.inspect_model_parameters_by_path(
                '.Simulations.Simulation.Field.Soil.SoilWater'
            )

            self.assertEqual(sw2["DiffusConst"], 35.0,
                             "Scalar update for DiffusConst failed")

            # ------------------------------------------------------------
            # 4. Test updating only the bottom soil layer (index -1)
            # ------------------------------------------------------------
            corep.edit_model_by_path(
                '.Simulations.Simulation.Field.Soil.SoilWater',
                SWCON=5,
                indices=[-1]
            )

            sw3 = corep.inspect_model_parameters_by_path(
                '.Simulations.Simulation.Field.Soil.SoilWater'
            )

            self.assertTrue(sw3["SWCON"][-1] == 5,
                            "Bottom-layer update for SWCON failed")

            # ------------------------------------------------------------
            # 5. Test scalar index update
            #    SWCON=5, indices=-1 → convert to list internally
            # ------------------------------------------------------------
            corep.edit_model_by_path(
                '.Simulations.Simulation.Field.Soil.SoilWater',
                SWCON=5,
                indices=-1
            )

            sw4 = corep.inspect_model_parameters_by_path(
                '.Simulations.Simulation.Field.Soil.SoilWater'
            )

            self.assertTrue(sw4["SWCON"][-1] == 5,
                            "SWCON update with scalar index failed")

            # ------------------------------------------------------------
            # 6. Extra: ensure no unexpected attributes remain
            # ------------------------------------------------------------

            self.assertIsInstance(sw4["SWCON"], list,
                                  msg="SWCON should always be stored as list after edits")

            with self.assertRaises(AssertionError, msg=f'expected to raise AssertionError'):
                corep.edit_model_by_path(
                    '.Simulations.Simulation.Field.Soil.SoilWater',
                    SWCON=5,
                    indices=[-1, 2]
                )
            with self.assertRaises(AttributeError, msg=f'expected to raise AttributeError'):
                corep.edit_model_by_path(
                    '.Simulations.Simulation.Field.Soil.SoilWater',
                    SWCON=5, SYON=30
                )

    def test_edit_soils_physical(self):
        with apsim.ApsimModel("Maize") as model:
            ks = model.inspect_model_parameters('Models.Soils.Physical', 'Physical', parameters='KS')
            length = ks.shape[0]
            #  The top two lines of codes here only modify the KS value for the first layer, but the third line updates all values
            ks_in = [4.752] * length
            model.edit_model(model_type='Models.Soils.Physical', model_name='Physical', simulations='Simulation',
                             KS=ks_in)
            ks1 = model.inspect_model_parameters('Models.Soils.Physical', 'Physical', parameters='KS')
            self.assertEqual(ks_in, ks1.KS.tolist())

            model.edit_model(model_type='Models.Soils.Physical', model_name='Physical', simulations='Simulation',
                             KS=[5, 5, 5, 5, 5, 5, 5, ])
            ref_ks = [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]
            ks2 = model.inspect_model_parameters('Models.Soils.Physical', 'Physical', parameters='KS', )
            self.assertEqual(ks2.KS.tolist(), ref_ks)

            ks_123 = [1, 2, 3, 4, 5, 6, 7]
            model.edit_model(model_type='Models.Soils.Physical', model_name='Physical', simulations='Simulation',
                             KS=[1, 2, 3, 4, 5, 6, 7])
            ks3 = model.inspect_model_parameters('Models.Soils.Physical', 'Physical', parameters='KS')
            self.assertEqual(ks3.KS.tolist(), ks_123, msg=f'KS is not equal to input expected to be {ks_123}')
            with self.assertRaises(AttributeError, msg=f'Expected to raise AttributeError for BDDD'):
                model.edit_model(model_type='Models.Soils.Physical', model_name='Physical',
                                 simulations='Simulation',
                                 KS=[1, 2, 3, 4, 5, 6, 7], BDDD=1.23),

    def test_edit_cultivar_edit_model_method(self):
        """
        Test the edit_cultivar requires that we have replacements in place
        @return:
        """

        # test_ap_sim.add_crop_replacements(_crop='Maize')
        with apsim.ApsimModel("Maize") as test_ap_sim:
            out_cultivar = 'B_110-e'
            new_juvenile = 289.777729777
            com_path = '[Phenology].Juvenile.Target.FixedValue'
            test_ap_sim.edit_model(model_type='Cultivar', model_name='B_110', new_cultivar_name=out_cultivar,
                                   commands=com_path, values=new_juvenile, cultivar_manager='Sow using a variable rule')

            # first we check the current '[Phenology].Juvenile.Target.FixedValue': '211'
            cp = test_ap_sim.inspect_model_parameters(model_type='Cultivar', model_name=out_cultivar)
            self.assertEqual(new_juvenile, float(cp.get(com_path)))
            self.paths.add(test_ap_sim.path)
            test_ap_sim.clean_up()

    def _test_edit_cultivar(self):

        """This is deprecated though"""
        com_path = '[Phenology].Juvenile.Target.FixedValue'

        test_ap_sim = apsim.ApsimModel("Maize", out_path=self.user_file_name)
        with apsim.ApsimModel("Maize") as test_ap_sim:
            cp = test_ap_sim.inspect_model_parameters(model_type='Cultivar', model_name='B_110')

            new_juvenile = 289.888
            test_ap_sim.edit_cultivar(commands=com_path, values=new_juvenile, CultivarName='B_110')
            # read again
            juvenile_replacements = test_ap_sim.inspect_model_parameters(model_type='Cultivar', model_name='B_110')[
                com_path]
            if juvenile_replacements:
                juvenile_replacements = float(juvenile_replacements)
            self.assertEqual(new_juvenile, juvenile_replacements)
            test_ap_sim.run()
            self.paths.add(test_ap_sim.path)

    def test_inspect_model_parameters(self):
        with apsim.ApsimModel("Maize") as model:
            w_file = model.inspect_model_parameters(model_type='Weather', simulations='Simulation',
                                                    model_name='Weather')
            self.assertIsInstance(w_file, str, msg='Inspect weather model parameters failed, when simulation is a str')
            # test a list of simulations
            w_file = model.inspect_model_parameters(model_type='Weather', simulations=['Simulation'],
                                                    model_name='Weather')
            self.assertIsInstance(w_file, dict,
                                  msg='Inspect weather model parameters failed, when simulation is a list')

    def test_model_info_attributes(self):
        with apsim.ApsimModel("Maize") as model:
            self.assertTrue(model.datastore, ' datastore is set to to empty or None')
            self.assertTrue(model._DataStore, '_DataStore model is set to to empty or None')
            self.assertTrue(model.Datastore, '_DataStore is set to empty or null')

    def test_model_info_types(self):
        with apsim.ApsimModel("Maize") as model:
            self.assertIsInstance(model.Datastore, Models.Storage.DataStore,
                                  msg='Inspect DataStore, data store was not casted to Models.Storage.DataStore')
            self.assertIsInstance(model._DataStore, Models.Storage.DataStore,
                                  msg='Inspect DataStore, data store was not casted to Models.Storage.DataStore')

    def test_simulation_container(self):
        with apsim.ApsimModel("Maize") as model:
            import Models
            self.assertIsInstance(model.Simulations, Models.Core.Simulations,
                                  msg=f'{model.Simulations} is expeced to be a Models.Core.Simulations object perhaps casting was not done')

    def test_remove_variable_spec(self):
        variable_spec = '[Clock].Today as Date'
        with apsim.ApsimModel("Maize") as model:
            vs = model.inspect_model_parameters('Models.Report', 'Report')['VariableNames']
            vsIn = variable_spec in vs
            self.assertFalse(vsIn, msg=f'Variable {variable_spec} already in report')
            # safe to add it now
            model.add_report_variable(variable_spec=variable_spec, report_name='Report')
            vs = model.inspect_model_parameters('Models.Report', 'Report')['VariableNames']
            vsIn = variable_spec in vs
            self.assertTrue(vsIn, msg=f'Variable {variable_spec} successfully added')
            # remove it
            model.remove_report_variable(variable_spec='[Clock].Today as Date', report_name='Report')
            vs = model.inspect_model_parameters('Models.Report', 'Report')['VariableNames']
            vsIn = variable_spec in vs
            self.assertFalse(vsIn, msg=f'Variable {variable_spec} was not successfully removed')

    def test_context_manager(self):
        with apsim.ApsimModel("Maize") as model:
            datastore = Path(model.datastore)
            model.run()
            df = model.results
            self.assertFalse(df.empty, msg=f'Empty data frame encountered')
            self.assertTrue(Path(model.path).exists())
        self.assertFalse(Path(model.path).exists(), 'Path exists; context manager not working')
        self.assertFalse(datastore.exists(), msg=f'data store exists context manager not working')

    def tearDown(self):
        if hasattr(self, 'test_ap_sim'):
            self.test_ap_sim.clean_up(db=True)
        for path in self.paths:
            if os.path.exists(path):
                os.remove(path)
        try:
            self.test_save_path.unlink(missing_ok=True)
        except PermissionError:
            pass

    @classmethod
    def tearDownClass(cls):
        scratch = list(wd.glob("*scratch"))

        try:
            if Path(os.getcwd()).resolve() == wd.resolve():
                os.chdir(wd.parent)
            shutil.rmtree(wd, ignore_errors=True)
            for path in scratch:
                if path.exists():
                    shutil.rmtree(path, ignore_errors=True)
        except (PermissionError, FileNotFoundError):
            pass


if __name__ == '__main__':
    try:
        unittest.main()
    finally:
        pass
