from apsimNGpy.exceptions import NodeNotFoundError

from apsimNGpy.core.experiment_tools import factor_spec
import unittest


class TestExperimentTools(unittest.TestCase):
    def test_raise_node_not_found_error(self):
        with self.assertRaises(NodeNotFoundError):
            population = factor_spec(
                "Maize",
                param_node_location="Sow using a variable rule1",
                node_type="Manager",
                param_identifier="Population",
                values=[1, 5, 10],
                rename="population",
            )

    def test_spec_from_a_manager(self):
        expected = {'population': '[Sow using a variable rule].Script.Population = 1, 5, 10'}
        population = factor_spec(
            "Maize",
            param_node_location="Sow using a variable rule",
            node_type="Manager",
            param_identifier="Population",
            values=[1, 5, 10],
            rename="population",
        )
        self.assertEqual(expected, population)

    def test_spec_from_a_manager_with_a_full_path(self):
        expected = {'nitrogen': '[Fertilise at sowing].Script.Amount = 0, 100, 200'}
        nitrogen = factor_spec(
            "Maize",
            param_node_location=(
                ".Simulations.Simulation.Field.Fertilise at sowing"
            ),
            node_type="Manager",
            param_identifier="Amount",
            values=[0, 100, 200],
            rename="nitrogen",
        )
        self.assertEqual(expected, nitrogen)

    def test_a_soil_relatedProperty(self):
        expected = {'initial_carbon': '[Organic].Carbon[1] = 0.45, 1, 3'}
        carbon = factor_spec(
            "Maize",
            param_node_location="Organic",
            node_type="Organic",
            param_identifier="Carbon[1]",
            values=[0.45, 1, 3],
            rename="initial_carbon",
        )
        self.assertEqual(expected, carbon)

    def test_bounds_and_steps(self):
        expected = {'fom': '[Organic].FOM[1] = 100 to 4000 step 500'}
        fom = factor_spec(
            "Maize",
            param_node_location="Organic",
            node_type="Organic",
            param_identifier="FOM[1]",
            bounds=(100, 4000),
            step=500,
            rename="fom",
        )
        self.assertEqual(expected, fom)


if __name__ == "__main__":
    unittest.main()
