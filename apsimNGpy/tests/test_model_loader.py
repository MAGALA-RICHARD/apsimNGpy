import os

from apsimNGpy.core_utils.cs_utils import CastHelper as CastHelpers
from apsimNGpy.core.pythonet_config import Models
from apsimNGpy.core.model_loader import (load_apsim_model, get_model, version,
                                         save_model_to_file, model_from_string,
                                         load_from_path, load_crop_from_disk, load_from_dict)
import unittest
import shutil
import uuid
from unittest.mock import patch
from apsimNGpy.tests.base_test import BaseTester
import json
from pathlib import Path
from apsimNGpy.exceptions import CastCompilationError

model = model_from_string("Maize")
if hasattr(model, 'Model'):  # incase it is an APSIM.Core.Node object
    model = model.Model

# variables
MODEL_PATH = load_crop_from_disk("Maize")


def mock_model_from_dict():
    with open(MODEL_PATH) as f:
        dic = json.load(f)
        return dic


def mock_file_from_disk():
    target = Path.home() / 'mock_on_disk.apsimx'
    return shutil.copyfile(MODEL_PATH, target)


def cast(out_model, target=Models.Core.Simulations):
    casted = CastHelpers.CastAs[target](out_model)
    if casted: return casted
    raise CastCompilationError(" cast was not successful because the provided object is invalid")


class TestCoreModel(BaseTester):
    """Unit tests for APSIM model loading functions from various sources."""

    def test_load_model_from_path_str_mtd(self):
        """Test loading APSIM model from file path using 'string' method."""
        model_from_path = load_from_path(MODEL_PATH, method='string')
        g_model = get_model(model_from_path)
        model_class = CastHelpers.CastAs[Models.Core.Simulations](g_model)
        self.assertIsInstance(model_class, Models.Core.Simulations,
                              'casting failed failed loading model from file path, while using string emthod')

    def test_load_model_from_path_file_mtd(self):
        """Test loading APSIM model from file path using 'file' method."""
        model_from_path = load_from_path(MODEL_PATH, method='file')
        g_model = get_model(model_from_path)
        model_class = CastHelpers.CastAs[Models.Core.Simulations](g_model)
        self.assertIsInstance(model_class, Models.Core.Simulations,
                              'casting failed failed while loading model from file path using file method')

    def test_load_model_from_dict(self):
        """Test loading APSIM model from a dictionary representation."""
        mocked_dict = mock_model_from_dict()
        node_or_model = load_from_dict(mocked_dict, out='mock_model_from_dict.apsimx')
        out_model = get_model(node_or_model)
        model_class = CastHelpers.CastAs[Models.Core.Simulations](out_model)
        self.assertIsInstance(model_class, Models.Core.Simulations, 'casting failed failed loading data from dict')

    def test_load_load_apsim_model_dict(self):
        """Test unified APSIM model loader with dictionary input."""
        dict_data = mock_model_from_dict()
        out = load_apsim_model(dict_data, out='maize.apsimx')
        sims = cast(out.IModel)

        self.assertIsInstance(sims, Models.Core.Simulations, 'loading model fro dict using load_apsim_model '
                                                             'failed')

    def test_load_load_apsim_model_path(self):
        """Test unified APSIM model loader with file path string input."""
        out = load_apsim_model(MODEL_PATH, out='maize_from_fp.apsimx')
        sims = cast(out.IModel)

        self.assertIsInstance(sims, Models.Core.Simulations, 'loading model from model file path using '
                                                             'load_apsim_model'
                                                             'failed')

    def test_load_load_apsim_model_path_out_is_none(self):
        """Test unified APSIM model loader with file path string input."""
        out = load_apsim_model(MODEL_PATH, out=None)
        sims = cast(out.IModel)

        self.assertIsInstance(sims, Models.Core.Simulations, 'loading model from model file path using '
                                                             'load_apsim_model and out is None'
                                                             'failed')

    def test_load_load_apsim_model_pathlib_path(self):
        """Test unified APSIM model loader with pathlib.Path input."""
        fp = Path(MODEL_PATH)
        out = load_apsim_model(fp, out='maize_from_fp.apsimx')
        sims = cast(out.IModel)

        self.assertIsInstance(sims, Models.Core.Simulations, 'loading model from model file pathlib path using '
                                                             'load_apsim_model'
                                                             'failed')

    def test_load_load_apsim_model_path_from_disk(self):
        """Test unified APSIM model loader with pathlib.Path input."""
        fp = mock_file_from_disk()
        out = load_apsim_model(fp, out='maize_from_fp.apsimx')
        sims = cast(out.IModel)

        self.assertIsInstance(sims, Models.Core.Simulations, 'loading model from model file from disk using '
                                                             'load_apsim_model'
                                                             'failed')

    def test_load_load_apsim_model_mock_none(self):
        """Test unified APSIM model loader raises ValueError when model is None."""
        fp = None
        failed = False
        try:
            load_apsim_model(fp, out='maize_from_fp.apsimx')
        except ValueError:
            failed = True

        self.assertTrue(failed, 'loading model from model while mocking None did not succeed error was not raised')

    def test_save_model_to_disk(self):
        import pathlib
        def test(mod_p):
            mod = load_apsim_model(mod_p, out='maize_from_fp.apsimx')
            fp = pathlib.Path.home() / f"{uuid.uuid1()}_{version}.apsimx"
            try:
                fp.unlink(missing_ok=True)
                self.assertFalse(fp.exists(), 'target file exists')

                save_model_to_file(mod, out=fp)
                exi_fp = all([fp.exists(), fp.is_file()])
                self.assertTrue(exi_fp)

            finally:
                fp.unlink(missing_ok=True)
                Path('maize_from_fp.apsimx').unlink(missing_ok=True)

        # test from default
        mod = load_apsim_model("Maize", out='maize_from_fp.apsimx')
        test('Maize')
        # test from disk
        test(mock_file_from_disk())


# initialize the model
if __name__ == '__main__':
    ...
    mo = load_apsim_model('Maize')
    unittest.main()
