import gc
import shutil
import tempfile
import unittest
from pathlib import Path

from apsimNGpy.starter.cs_resources import CastHelper as CastHelpers, cast_as
from apsimNGpy.starter.starter import Models, is_file_format_modified
from apsimNGpy.core.model_loader import model_from_string

NEW_APSIM = is_file_format_modified()  # bool


class TestCastHelper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # One temp directory for the whole class
        cls.tmpdir = Path(tempfile.mkdtemp(prefix="apsim_core_cast_"))

    @classmethod
    def tearDownClass(cls):
        # Remove the whole temp tree at the end
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def setUp(self):
        # Unique file per test to avoid cross-test interference
        self.out = self.tmpdir / f"fi_{self._testMethodName}.apsimx"
        m = model_from_string("Maize", out=str(self.out))
        self.model = getattr(m, "Model", m)

    def test_cast(self):
        """tests the cast function compiled as .dll"""
        # ensure that self.model is not the target conversion class
        if NEW_APSIM:
            self.assertNotIsInstance(self.model, Models.Core.Simulations,
                                     f'{self.model} is already a Models.Core.Simulations')
        cast = CastHelpers.CastAs[Models.Core.Simulations](self.model)
        self.assertIsInstance(cast, Models.Core.Simulations,
                              "casting to Models.Core.Simulations failed")

    def test_cast_as(self):
        """tests the cast function compiled as .dll the pythonic way"""
        if NEW_APSIM:
            # ensure that self.model is not the target conversion class
            self.assertNotIsInstance(self.model, Models.Core.Simulations,
                                     f'{self.model} is already a Models.Core.Simulations')
        cast = cast_as(model_class=Models.Core.Simulations, model=self.model)
        self.assertIsInstance(cast, Models.Core.Simulations,
                              "casting to Models.Core.Simulations failed")

    def tearDown(self):
        self.model = None
        gc.collect()

        try:
            if self.out.exists():
                self.out.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    unittest.main()
