from apsimNGpy.optimizer.problems.smp import MixedProblem
from apsimNGpy.tests.unittests.test_factory import obs
import unittest

vtyped = {
    "path": ".Simulations.Simulation.Field.Soil.Organic1",
    "vtype": ['UniformVar(1, 2)'],
    "start_value": ["1"],
    "candidate_param": ["FOM"],
    "other_params": {"FBiom": 2.3, "Carbon": 1.89},
}
pure = {
    "path": ".Simulations.Simulation.Field.Soil.Organic2",
    'bounds': [(1, 500), ],
    "start_value": ["1"],
    "candidate_param": ["FOM"],
    "other_params": {"FBiom": 2.3, "Carbon": 1.89},
}


class TestMixedProblem(unittest.TestCase):
    def setUp(self):
        mp = MixedProblem(
            model="Maize",
            trainer_dataset=obs,
            pred_col="Yield",
            index="year",
            trainer_col="observed",
            table='Report'
        )
        self.mp = mp

    def test_submit_factors_pure(self):
        self.mp.submit_factor(**pure)
        cp = self.mp.apsim_params
        self.assertTrue(cp, 'apsim paramters not populated')
        self.assertEqual(self.mp.n_factors, 1, msg='factor not submitted successfully')
        self.assertEqual(self.mp.start_values, pure['start_value'], msg='start values are different why')
        self.assertEqual(self.mp.var_names, vtyped['candidate_param'])


    def test_submit_factors_vtyped(self):
        self.mp.submit_factor(**vtyped)
        cp = self.mp.apsim_params
        self.assertTrue(cp, 'apsim paramters not populated')
        self.assertEqual(self.mp.n_factors, 1, msg='factor not submitted successfully')
        self.assertEqual(self.mp.start_values, vtyped['start_value'], msg='start values are different why')
        self.assertEqual(self.mp.var_names, vtyped['candidate_param'])

    def assert_raise_type_error(self):
        self.assertRaises(TypeError, msg='expected to raise TypeError when both pure and vtyped factors are submitted')
        self.mp.submit_factor(**vtyped)
        self.mp.submit_factor(**pure)


    def test_submit(self):
        import gc
        gc.collect()


if __name__ == '__main__':
    unittest.main(verbosity=0)
