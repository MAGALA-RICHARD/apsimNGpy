import os.path
import unittest
from pathlib import Path
import pandas as pd
import warnings
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.model_tools import validate_model_obj, ModelTools, add_as_simulation, find_model, \
    get_or_check_model, detect_sowing_managers, find_child, find_all_in_scope
from apsimNGpy.core.pythonet_config import is_file_format_modified

IS_NEW_APSIM = is_file_format_modified()


class TestModelTools(unittest.TestCase):

    def test_add_a_simulation(self):
        # if IS_NEW_APSIM:
        model = ApsimModel('Maize')
        ans = [add_as_simulation(model, i, i) for i in ['Soybean']]
        sims = len(ans)

        t_add = sims >= 1
        self.assertTrue(t_add)

    def test_validate_model_obj(self):
        model = 'Report'
        obj = validate_model_obj(model)
        self.assertTrue(hasattr(obj, '__class__'))

    def test_find_model(self):
        model = ApsimModel('Maize')
        result = find_model('Clock')
        self.assertIsNotNone(result)

    def test_get_or_check_model_get(self):
        model = ApsimModel('Maize')
        model_class = find_model("Clock")
        result = get_or_check_model(model.Simulations, model_class, 'Clock', 'get')
        self.assertTrue(result)

    def test_detect_sow_manager(self):
        model = ApsimModel('Maize')
        sowing_manager = detect_sowing_managers(model)
        self.assertIsNotNone(sowing_manager)

    def test_detect_sow_manager_when_none(self):
        model = ApsimModel('Maize')
        sowing_manager = detect_sowing_managers(model)
        ModelTools.DELETE(sowing_manager)
        model.save()
        sowing_manager = detect_sowing_managers(model)
        self.assertIsNone(sowing_manager)

    def test_get_or_check_model_delete(self):
        model = ApsimModel('Maize')
        model_class = find_model("Clock")
        result = get_or_check_model(model.Simulations, model_class, 'Clock', 'delete')
        self.assertIsNone(result)

    def test_get_or_check_model_check(self):
        model = ApsimModel('Maize')
        model_class = find_model("Clock")
        result = get_or_check_model(model.Simulations, model_class, 'Clock', 'check')
        self.assertTrue(result)

    def test_find_child(self):
        """test for find_child for a clock"""
        model = ApsimModel('Maize', out_path=os.path.realpath('./find_child_clok1.apsimx'))
        clock = find_child(model.Simulations, 'Models.Clock', 'Clock')
        self.assertIsNotNone(clock, msg='failed to find clock child from simulations')

    def test_find_child_cultivar(self):
        """test find_child of Cultivar"""
        model = ApsimModel('Maize', out_path=os.path.realpath('./find_child_clok2.apsimx'))
        cultivar = find_child(parent=model.Simulations, child_class='Models.PMF.Cultivar', child_name='B_110')
        self.assertIsNotNone(cultivar, msg='failed to find cultivar child from simulations')

    def test_find_child_simulations(self):
        """test finding child simulations"""
        model = ApsimModel('Maize', out_path=os.path.realpath('./find_child_clok3.apsimx'))
        simulation = find_child(parent=model.Simulations, child_class='Models.Core.Simulation', child_name='Simulation')
        self.assertIsNotNone(simulation, msg='failed to find simulation child from simulations')

    def test_find_child_weather(self):
        """test finding child simulations"""
        model = ApsimModel('Maize', out_path=os.path.realpath('./find_child_clok4.apsimx'))
        weather = find_child(parent=model.Simulations, child_class='Models.Climate.Weather', child_name='Weather')
        self.assertIsNotNone(weather, msg='failed to find weather  child from simulations')

    def test_find_all_in_scope_managers(self):
        """test finding all managers"""
        model = ApsimModel('Maize', out_path=os.path.realpath('./find_all_in_scope_manager.apsimx'))
        manager = find_all_in_scope(scope=model.Simulations, child_class='Models.Manager')
        # ensure something is found
        self.assertIsNotNone(manager, msg='failed to find weather  child from simulations')

    def test_find_all_in_scope_clock(self):
        """test finding all managers"""
        model = ApsimModel('Maize', out_path=os.path.realpath('./find_all_in_scope_clock.apsimx'))
        clock = find_all_in_scope(scope=model.Simulations, child_class='Models.Clock')
        # ensure something is found
        self.assertIsNotNone(clock, msg='failed to find all clock children from simulations')

    def test_find_all_in_scope_physical(self):
        """test finding all managers"""
        model = ApsimModel('Maize', out_path=os.path.realpath('./find_all_in_scope_physical.apsimx'))
        physical = find_all_in_scope(scope=model.Simulations, child_class='Models.Soils.Physical')
        # ensure something is found
        self.assertIsNotNone(physical, msg='failed to find all clock children from simulations')

    def test_find_all_in_scope_simulations(self):
        """test finding all managers"""
        model = ApsimModel('Maize', out_path=os.path.realpath('./find_all_in_scope_simulations.apsimx'))
        simulations = find_all_in_scope(scope=model.Simulations, child_class='Models.Core.Simulations')
        # ensure something is found
        self.assertIsNotNone(simulations, msg='failed to find all manager children from simulations')

    def test_find_all_in_scope_return_emptyforNone(self):
        """test finding all managers"""
        model = ApsimModel('Maize', out_path=os.path.realpath('./find_all_in_scope_simulations.apsimx'))
        experiments = find_all_in_scope(scope=model.Simulations, child_class='Models.Factorial.Experiment')
        # ensure that it is empty because experiment does not exist at this node
        test = experiments == []
        self.assertTrue(test, msg='failed to return empty for no existing experiments class models')


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
