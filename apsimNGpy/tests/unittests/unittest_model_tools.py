import unittest
from pathlib import Path
import pandas as pd
import warnings
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.model_tools import validate_model_obj, ModelTools, add_as_simulation, find_model, \
    get_or_check_model, detect_sowing_managers
from apsimNGpy.core.pythonet_config import is_file_format_modified

IS_NEW_APSIM = is_file_format_modified()


class TestModelTools(unittest.TestCase):

    @timer
    def test_add_a_simulation(self):
        # if IS_NEW_APSIM:
            model = ApsimModel('Maize')
            ans = [add_as_simulation(model, i, i) for i in ['Soybean']]
            sims = len(ans)

            t_add = sims >= 1
            self.assertTrue(t_add)

    @timer
    def test_validate_model_obj(self):
        model = 'Report'
        obj = validate_model_obj(model)
        self.assertTrue(hasattr(obj, '__class__'))

    @timer
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
