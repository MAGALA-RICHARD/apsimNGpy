import json
import os
import unittest
from pathlib import Path

from apsimNGpy.starter.cs_resources import CastHelper as CastHelpers
from apsimNGpy.core.model_loader import (load_apsim_model, get_model, save_model_to_file, load_from_path, load_crop_from_disk, load_from_dict)
from apsimNGpy.starter.starter import Models
from apsimNGpy.exceptions import CastCompilationError
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester


def cast(out_model, target=Models.Core.Simulations):
    casted = CastHelpers.CastAs[target](out_model)
    if casted:
        return casted
    raise CastCompilationError(" cast was not successful because the provided object is invalid")


class TestCoreModel(BaseTester):
    """Unit tests for APSIM model loading functions from various sources."""

    def setUp(self):
        self.MODEL_PATH = f"m_{self._testMethodName}.apsimx"
        out = "m_out_model" + self._testMethodName + '.apsimx'
        self.fp = Path.home() / f"__{self._testMethodName}file_path-test.apsimx"
        self.file_on_disk = load_crop_from_disk("Soybean", out=out)
        self.save_to = Path(f"save_{self._testMethodName}.apsimx")

    def mock_model_from_dict(self):
        model_to_dict = self.file_on_disk
        with open(model_to_dict) as f:
            dic = json.load(f)
            return dic

    def test_load_model_from_path_str_mtd(self):
        """Test loading APSIM model from a file path using 'string' method."""
        model_from_path = load_from_path(self.file_on_disk, method='string')
        g_model = get_model(model_from_path)
        if not isinstance(g_model, Models.Core.Simulation):
            model_class = CastHelpers.CastAs[Models.Core.Simulations](g_model)
            self.assertIsInstance(model_class, Models.Core.Simulations,
                                  'Casting failed failed loading model from file path, while using string method')
        else:
            self.skipTest(f'{g_model} is already a model loaded as {Models.Core.Simulation}')

    def test_load_model_from_path_file_mtd(self):
        """Test loading APSIM model from a file path using 'file' method."""
        model_from_path = load_from_path(self.file_on_disk, method='file')
        g_model = get_model(model_from_path)
        path = getattr(g_model, "FileName", "filepath.com")

        # no need for false confidence first test whether it is not the target class
        if not isinstance(g_model, Models.Core.Simulations):
            model_class = CastHelpers.CastAs[Models.Core.Simulations](g_model)
            path = getattr(model_class, "FileName", "/filepath.com")
            path = path or "/filepath.com"
            self.assertIsInstance(model_class, Models.Core.Simulations,
                                  'casting failed failed while loading model from file path using file method')
        else:
            self.skipTest(f'{g_model} is already a model loaded as {Models.Core.Simulation}')

    def test_load_model_from_dict(self):
        """Test loading APSIM model from a dictionary representation."""
        mocked_dict = self.mock_model_from_dict()
        node_or_model = load_from_dict(mocked_dict, out=self.MODEL_PATH)
        out_model = get_model(node_or_model)

        model_class = CastHelpers.CastAs[Models.Core.Simulations](out_model)
        self.assertIsInstance(model_class, Models.Core.Simulations, 'casting failed failed loading data from dict')

    def test_load_load_apsim_model_dict(self):
        """Test unified APSIM model loader with dictionary input."""
        dict_data = self.mock_model_from_dict()
        out = load_apsim_model(dict_data, out_path=self.MODEL_PATH)
        sims = cast(out.IModel)

        self.assertIsInstance(sims, Models.Core.Simulations, 'loading model fro dict using load_apsim_model '
                                                             'failed')
        self.delete_random(out.path, out.datastore)

    def test_load_load_apsim_model_path(self):
        """Test unified APSIM model loader with file path string input."""
        out = load_apsim_model(self.file_on_disk, out_path=self.MODEL_PATH)
        sims = cast(out.IModel)

        self.assertIsInstance(sims, Models.Core.Simulations, 'loading model from model file path using '
                                                             'load_apsim_model'
                                                             'failed')
        self.delete_random(out.path)

    @staticmethod
    def delete_random(*args):
        for file in args:
            if os.path.exists(file):
                os.remove(file)

    def test_load_load_apsim_model_path_out_is_none(self):
        """Test unified APSIM model loader with file path string input."""
        out = load_apsim_model(self.file_on_disk)
        sims = cast(out.IModel)

        self.assertIsInstance(sims, Models.Core.Simulations, 'loading model from model file path using '
                                                             'load_apsim_model and out is None'
                                                             'failed')
        # clean up from here since we don't know the random file assigned to the out path
        self.delete_random(out.path, out.datastore)

    def test_load_load_apsim_model_pathlib_path(self):
        """Test unified APSIM model loader with pathlib.Path input."""
        fp = Path(self.file_on_disk)
        out = load_apsim_model(fp, out_path=self.MODEL_PATH)
        sims = cast(out.IModel)

        self.assertIsInstance(sims, Models.Core.Simulations, 'loading model from model file pathlib path using '
                                                             'load_apsim_model'
                                                             'failed')
        self.delete_random(out.path, out.datastore)

    def test_load_load_apsim_model_path_from_disk(self):
        """Test unified APSIM model loader with pathlib.Path input."""
        fp = self.file_on_disk

        out = load_apsim_model(fp, out_path=self.MODEL_PATH)
        sims = cast(out.IModel)

        self.assertIsInstance(sims, Models.Core.Simulations, 'loading model from model file from disk using '
                                                             'load_apsim_model'
                                                             'failed')
        self.delete_random(out.path)

    def test_load_load_apsim_model_mock_none(self):
        """Test unified APSIM model loader raises ValueError when model is None."""
        fp = None
        failed = False
        try:
            load_apsim_model(fp, out_path=self.MODEL_PATH)
        except ValueError:
            failed = True

        self.assertTrue(failed, 'loading model from model while mocking None did not succeed error was not raised')

    def _test_save_method(self, mod_p):
        if os.path.exists(self.MODEL_PATH):
            try:
                os.remove(self.MODEL_PATH)
            except PermissionError:
                self.skipTest('skipping due to permission error')
        model_to_save = load_apsim_model(mod_p, out_path=self.MODEL_PATH)
        self.MODEL_PATH = Path(self.MODEL_PATH)

        self.save_to.unlink(missing_ok=True)
        self.assertFalse(self.save_to.exists(), 'target file exists')

        save_model_to_file(model_to_save.IModel, out=self.save_to)
        exi_fp = all([self.save_to.is_file()])
        self.assertGreater(self.save_to.stat().st_size, 0, msg=f'save file failed size is zero')
        self.assertTrue(exi_fp)
        self.assertTrue(self.MODEL_PATH)
        self.delete_random(model_to_save.path)
        self.delete_random(self.MODEL_PATH)
        self.delete_random(self.save_to)

    def _test_save_model_to_disk_from_default(self):

        # Test loading model from models shipped with APSIM. These reside in example dir
        # test from default
        self._test_save_method('Soybean')

    def test_save_model_to_disk_from_file(self):
        out_path = f"{self._testMethodName}.apsimx"
        # test from disk
        file_on_disk = load_crop_from_disk("Soybean", out=out_path)
        self._test_save_method(file_on_disk)
        self.delete_random(file_on_disk)

    def tearDown(self):
        if os.path.exists(self.MODEL_PATH):
            os.remove(self.MODEL_PATH)
        if os.path.exists(self.file_on_disk):
            os.remove(self.file_on_disk)


# initialize the model
if __name__ == '__main__':

    try:
        unittest.main()
    finally:
        pass
