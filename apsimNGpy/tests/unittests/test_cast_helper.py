from core.cs_resources import CastHelper as CastHelpers
from apsimNGpy.core.pythonet_config import Models
from apsimNGpy.core.model_loader import model_from_string
import unittest
from tests.unittests.base_unit_tests import BaseTester


model = model_from_string("Maize")
if hasattr(model, 'Model'):  # incase it is an APSIM.Core.Node object
    model = model.Model


class TestCoreModel(BaseTester):
    def test_cast(self):
        """tests the cast function compiled as .dll"""
        cast = CastHelpers.CastAs[Models.Core.Simulations](model)
        self.assertIsInstance(cast, Models.Core.Simulations), "casting to Models.Core.Simulations failed"


# initialize the model
if __name__ == '__main__':
    unittest.main()
