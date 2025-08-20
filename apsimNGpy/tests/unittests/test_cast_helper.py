import gc
import shutil
import tempfile
import unittest
from pathlib import Path

from apsimNGpy.core.cs_resources import CastHelper as CastHelpers, cast_as
from apsimNGpy.core.pythonet_config import Models
from apsimNGpy.core.model_loader import model_from_string


class TestCoreModel(unittest.TestCase):
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
        cast = CastHelpers.CastAs[Models.Core.Simulations](self.model)
        self.assertIsInstance(cast, Models.Core.Simulations,
                              "casting to Models.Core.Simulations failed")

    def test_cast_as(self):
        """tests the cast function compiled as .dll the pythonic way"""
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
