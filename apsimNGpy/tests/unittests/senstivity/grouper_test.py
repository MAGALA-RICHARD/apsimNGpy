import unittest
from collections import defaultdict
from apsimNGpy.sensitivity.sensitivity import grouper
from apsimNGpy import NodeNotFoundError


# --- Unit Tests ---
class TestGrouper(unittest.TestCase):
    def setUp(self):
        self.fertilizer_node = '.Simulations.Simulation.Field.Fertilise at sowing'
        self.cultivar_node = '.Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82'

    def test_basic_grouping(self):
        data = [{
            'base': self.fertilizer_node, 'param': 'population', 'Amount': 200,
            'bounds': (0, 300)},
            {
                'base': '.Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82',
                'param': '[Leaf].Photosynthesis.RUE.FixedValue',

                'managers': {"Sow using a variable rule": "CultivarName"}
            }]
        result = grouper('Maize', data)

        self.assertEqual(result.others.get(self.fertilizer_node), {'Amount': 200})

    def test_cultivar_true_managers_not_found(self):
        data = [{
            'base': self.fertilizer_node, 'param': 'population', 'Amount': 200,
            'bounds': (0, 300)},
            {
                'base': '.Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82',
                'param': '[Leaf].Photosynthesis.RUE.FixedValue',

            }]
        with self.assertRaises(ValueError):
            result = grouper('Maize', data)

    def test_cultivar_true_managers_found(self):
        data = [{
            'base': self.fertilizer_node, 'param': 'population', 'Amount': 200,
            'bounds': (0, 300)},
            {
                'base': '.Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82',
                'param': '[Leaf].Photosynthesis.RUE.FixedValue',

            }]
        with self.assertRaises(ValueError):
            result = grouper('Maize', data)

    # self.assertEqual(result.others.get(base_1), {'Amount': 200})

    def test_cultivar_with_managers_dict(self):
        data = [
            {
                "base": self.fertilizer_node,
                "param": "growth",

                "managers": {"rule": "test"}
            }
        ]
        result = grouper('Maize', data)

        self.assertEqual(result.grouped_pairs[self.fertilizer_node], ["growth"])

    def test_NodeError(self):
        data = [
            {"base": "soil", "param": "ph", "x": 1},
            {"base": "soil", "param": "moisture", "y": 2},
        ]
        with self.assertRaises(NodeNotFoundError):
            result = grouper('Maize', data)


# --- Run tests ---
if __name__ == "__main__":
    unittest.main()
