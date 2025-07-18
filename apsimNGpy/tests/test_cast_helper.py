from apsimNGpy.core_utils.cs_utils import CastHelper as CastHelpers
from apsimNGpy.core.pythonet_config import Models
from apsimNGpy.core.model_loader import read_from_string
import unittest
model = read_from_string("Maize")
if hasattr(model, 'Model'):  # incase it is an APSIM.Core.Node object
    model = model.Model

from apsimNGpy.tests.base_test import BaseTester


class TestCoreModel(BaseTester):
    def test_cast(self):
        """tests the cast function compiled as .dll"""
        cast = CastHelpers.CastAs[Models.Core.Simulations](model)
        self.assertIsInstance(cast, Models.Core.Simulations), "casting to Models.Core.Simulations failed"


# initialize the model
if __name__ == '__main__':
    unittest.main()
