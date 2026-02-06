import os.path
import sys
import time
import unittest
from pathlib import Path
import pandas as pd
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.model_tools import validate_model_obj, add_as_simulation, find_model, \
    detect_sowing_managers, find_child, find_all_in_scope, add_replacement_folder, \
    add_model_as_a_replacement, get_or_check_model, clone_simulation
from apsimNGpy.starter.starter import is_file_format_modified

IS_NEW_APSIM = is_file_format_modified()


class TestModelTools(unittest.TestCase):
    def setUp(self) -> None:
        self.apsim_path = Path(f"{self._testMethodName}.apsimx")

    def test_add_a_simulation(self):
        with ApsimModel('Maize') as model:
            ans = [add_as_simulation(model, i, i) for i in ['Soybean']]
            sims = len(ans)
            t_add = sims >= 1
            self.assertTrue(t_add)

    def test_validate_model_obj(self):
        model = 'Report'
        obj = validate_model_obj(model)
        self.assertTrue(hasattr(obj, '__class__'))

    def test_find_model(self):
        result = find_model('Clock')
        self.assertIsNotNone(result)

    def test_get_or_check_model_get(self):
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            model_class = find_model("Clock")
            result = get_or_check_model(model.Simulations, model_class, 'Clock', 'get')
            self.assertTrue(result)

    def test_get_or_check_model_delete(self):
        with ApsimModel('Maize') as model:
            results = get_or_check_model(model.Simulations, 'Models.Core.Simulation', 'Simulation', action='delete')
            self.assertIsNone(results)
            # ensure model is deleted
            child = find_child(model.Simulations, 'Models.Core.Simulations', child_name='Simulation')
            self.assertIsNone(child, 'child found implies was not deleted successfully')

    def test_get_or_check_model_check(self):
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            results = get_or_check_model(model.Simulations, 'Models.Core.Simulation', 'Simulation', action='check')
            res = results == True
            self.assertTrue(res, msg='checking is not doing the desired thing')

    def test_detect_sow_manager(self):
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            sowing_manager = detect_sowing_managers(model)
            self.assertIsNotNone(sowing_manager)

    def _test_detect_sow_manager_when_none(self):
        from apsimNGpy.core.model_tools import ModelTools
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            sowing_manager = detect_sowing_managers(model)
            ModelTools.DELETE(sowing_manager)
            model.save(reload=True)
            model.inspect_file()
            sowing_manager = detect_sowing_managers(model)
            self.assertIsNone(sowing_manager)

    def test_get_or_check_model_delete1(self):
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            model_class = find_model("Clock")
            result = get_or_check_model(model.Simulations, model_class, 'Clock', 'delete')
            self.assertIsNone(result)

    def test_get_or_check_model_check2(self):
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            model_class = find_model("Clock")
            result = get_or_check_model(model.Simulations, model_class, 'Clock', 'check')
            self.assertTrue(result)

    def test_find_child(self):
        """test for find_child for a clock"""
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            clock = find_child(model.Simulations, 'Models.Clock', 'Clock')
            self.assertIsNotNone(clock, msg='failed to find clock child from simulations')

    def test_find_child_cultivar(self):
        """test find_child of Cultivar"""
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            cultivar = find_child(parent=model.Simulations, child_class='Models.PMF.Cultivar', child_name='B_110')
            self.assertIsNotNone(cultivar, msg='failed to find cultivar child from simulations')

    def test_find_child_simulations(self):
        """test finding child simulations"""
        with  ApsimModel('Maize', out_path=self.apsim_path) as model:
            simulation = find_child(parent=model.Simulations, child_class='Models.Core.Simulation',
                                    child_name='Simulation')
            self.assertIsNotNone(simulation, msg='failed to find simulation child from simulations')

    def test_find_child_weather(self):
        """test finding child simulations"""

        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            weather = find_child(parent=model.Simulations, child_class='Models.Climate.Weather', child_name='Weather')
            self.assertIsNotNone(weather, msg='failed to find weather  child from simulations')

    def test_find_all_in_scope_managers(self):
        """test finding all managers"""
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            manager = find_all_in_scope(parent=model.Simulations, child_class='Models.Manager')
            # ensure something is found
            self.assertIsNotNone(manager, msg='failed to find weather  child from simulations')

    def test_find_all_in_scope_clock(self):
        """test finding all managers"""
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            clock = find_all_in_scope(parent=model.Simulations, child_class='Models.Clock')
            # ensure something is found
            self.assertIsNotNone(clock, msg='failed to find all clock children from simulations')

    def test_find_all_in_scope_physical(self):
        """test finding all managers"""
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            physical = find_all_in_scope(parent=model.Simulations, child_class='Models.Soils.Physical')
            # ensure something is found
            self.assertIsNotNone(physical, msg='failed to find all clock children from simulations')

    def test_find_all_in_scope_simulations(self):
        """test finding all managers"""
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            simulations = find_all_in_scope(parent=model.Simulations, child_class='Models.Core.Simulations')
            # ensure something is found
            self.assertIsNotNone(simulations, msg='failed to find all manager children from simulations')

    def test_find_all_in_scope_return_emptyforNone(self):
        """test finding all managers"""
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            experiments = find_all_in_scope(parent=model.Simulations, child_class='Models.Factorial.Experiment')
            test = True if experiments else False
            # ensure that it is empty because experiment does not exist at this node
            self.assertFalse(test, msg='failed to return empty for no existing experiments class models')

    def test_add_folder(self):
        'Ensure that replacement folder is added'
        with ApsimModel('Maize', out_path=os.path.realpath('replacement2.apsimx')) as model:
            add_replacement_folder(model.Simulations)
            folder = find_child(model.Simulations, 'Models.Core.Folder', "Replacements")
            self.assertTrue(folder, 'replacement folder not found')

    def test_add_crop_replacement(self):
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            add_model_as_a_replacement(model.Simulations, 'Models.PMF.Plant', 'Maize')
            folder = find_child(model.Simulations, 'Models.Core.Folder', "Replacements")
            self.assertTrue(folder, 'replacement folder not found')

    def test_add_crop_replacement_and_run(self):
        """ensures that model runs after replacement"""
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            add_model_as_a_replacement(model.Simulations, 'Models.PMF.Plant', 'Maize')
            folder = find_child(model.Simulations, 'Models.Core.Folder', "Replacements")
            model.run()
            self.assertTrue(model.ran_ok, 'after replacement, model did not run properly')

    def test_add_clock_replacement(self):
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            add_model_as_a_replacement(model.Simulations, 'Models.PMF.Plant', 'Maize')
            folder = find_child(model.Simulations, 'Models.Core.Folder', "Replacements")
            self.assertTrue(folder, 'replacement folder not found')

    def test_clone_simulation(self):
        """test the clone_simulation method both when inplace and not inplace"""
        rename = 'cloned'
        with ApsimModel('Maize') as m:
            clone_simulation(m, 'Simulation', rename=rename, inplace=True)
            self.assertTrue(rename in {i.Name for i in m.simulations}, msg=f'cloning Simulation failed')
        with ApsimModel('Maize') as mm:
            clone_simulation(mm, 'Simulation', rename=rename, inplace=False)
            self.assertFalse(rename in {i.Name for i in mm.simulations},
                             msg='Cloning Simulation was added even though it was not the intention')

        with ApsimModel('Maize') as ap:
            with self.assertRaisesRegex(
                    NameError,
                    "already exists",
                    msg=f"Model not raising {NameError.__name__} when duplicated simulation name is expected"
            ):
                clone_simulation(ap, 'Simulation', rename='Simulation')

        with ApsimModel('Maize') as pp:
            with self.assertRaisesRegex(
                    ValueError,
                    "does not exist",
                    msg=f"Model not raising {ValueError.__name__} when simulation name provided is invalid or does not exist"
            ):
                clone_simulation(pp, 'does not exists', rename=rename)

    from apsimNGpy.core_utils.utils import timer

    def test_all_simulation_runs_well_on_cloning(self):
        """
        Assert that simulation runs on the cloning and when inplace=True
        @return:
        """
        with ApsimModel('Maize') as m:
            a= time.perf_counter()
            for i in range(0, 200):
                clone_simulation(m, 'Simulation', rename=f"sim_{i}")
            b = time.perf_counter()
            print(b-a, 'seconds elapsed to add the simulations')
            a = time.perf_counter()
            m.run(verbose=True)
            print(time.perf_counter() - a, 'seconds to run simulations')
            self.assertFalse(m.results.empty, msg=f'cloning Simulation led to malformed results')
            # also check that simulations ID are more than 1
            self.assertGreater(len(m.results.SimulationID.unique()), 1,
                               msg=f'simulation are not greater than 1 despite adding another simulation')
            print(sys.getsizeof(m.simulations) / (1024 ** 2))
            print(m.results.shape)
            print(len(m.simulations))

    def test_simulation_extractor_returns_correct_no_of_sims(self):
        """
        # Test that if we add three simulations, then expected number of simulations are four
        @return:
        """
        with ApsimModel('Maize') as m:
            clone_simulation(m, 'Simulation', rename='cloned_simulation', inplace=True)
            clone_simulation(m, 'Simulation', rename='cloned_simulation1', inplace=True)
            clone_simulation(m, 'Simulation', rename='cloned_simulation2', inplace=True)
            # if we add three simulations, then expected number of simulations are four
            self.assertEqual(len(m.simulations), 4,
                             msg=f'cloning simulation is changing the number of simulations in self.simulations')

    def test_add_what_happens_to_repeat_reps(self):
        with ApsimModel('Maize', out_path=os.path.realpath('replacement4.apsimx')) as model:
            add_model_as_a_replacement(model.Simulations, 'Models.Clock', 'Clock')
            add_model_as_a_replacement(model.Simulations, 'Models.Clock', 'Clock')
            folder = find_child(model.Simulations, 'Models.Core.Folder', "Replacements")
            self.assertTrue(folder, 'replacement folder not found')

    def test_add_what_happens_to_repeat_reps_with_run(self):
        with ApsimModel('Maize', out_path=self.apsim_path) as model:
            add_model_as_a_replacement(model.Simulations, 'Models.Clock', 'Clock')
            add_model_as_a_replacement(model.Simulations, 'Models.Clock', 'Clock')
            folder = find_child(model.Simulations, 'Models.Core.Folder', "Replacements")
            self.assertTrue(folder, 'replacement folder not found')
            model.run()
            self.assertTrue(model.ran_ok)

    def tearDown(self):
        self.apsim_path.unlink(missing_ok=True)


# Optional utility function
@timer
def datatable_to_dataframe(dt) -> pd.DataFrame:
    columns = [col.ColumnName for col in dt.Columns]
    data = []
    for row in dt.Rows:
        data.append([row[col] for col in columns])
    return pd.DataFrame(data, columns=columns)


if __name__ == '__main__':
    unittest.main()
