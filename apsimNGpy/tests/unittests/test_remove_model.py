import sys
import unittest
from apsimNGpy import ApsimModel
from apsimNGpy.exceptions import NodeNotFoundError


class TestRemoveModel(unittest.TestCase):
    def setUp(self):
        self.model_to_remove = 'Sow using a variable rule'
        self.model_to_remove_by_path = '.Simulations.Simulation.Field.Sow using a variable rule'
        self.path_not_found = "NotFound.Path.Sow using a variable rule"

    def assert_model_not_in(self, model, member, model_type, fullpath):
        mns = model.inspect_model(model_type=model_type, fullpath=fullpath)
        self.assertNotIn(member, mns)

    def assert_model_in(self, model, member, model_type, fullpath):
        mns = model.inspect_model(model_type=model_type, fullpath=fullpath)
        self.assertIn(member, mns)

    def test_remove_model(self):
        with ApsimModel('Maize') as model:
            model.remove_model(model_type='Models.Manager', model_name='Sow using a variable rule')
            self.assert_model_not_in(model, self.model_to_remove, model_type='Models.Manager', fullpath=False)

            model.remove_model(model_type='Models.Manager', model_name='Sow using a variable rule', missing_ok=True,
                               verbose=True)

    def test_remove_model_missing_ok_false(self):
        "supposed to fail if node not found and missing_ok=False "
        with self.assertRaises(NodeNotFoundError):
            with ApsimModel('Maize') as model:
                model.remove_model(model_type='Models.Manager', model_name='ModelNOTFOUnd.',
                                   missing_ok=False)

    def test_remove_model_missing_verbose(self):
        "test verbose is running normally"
        with ApsimModel('Maize') as model:
            model.remove_model(model_type='Models.Manager', model_name='ModelNOTFOUnd.',
                               missing_ok=True, verbose=True)

    def test_remove_model_by_path_nested_models(self):
        "test if we can delete from nested simulations"
        # for nested models, we use remove_model_by_path to be precise
        node2 = '.Simulations.sim2.Field.Sow using a variable rule'
        with ApsimModel('Maize') as model:
            # mock nested simulation
            model.clone_simulation('sim2')
            self.assert_model_in(model, 'sim2', model_type='Models.Core.Simulation', fullpath=False)
            self.assert_model_in(model, 'Simulation', model_type='Models.Core.Simulation', fullpath=False)
            model.remove_model_by_path(path='.Simulations.Simulation.Field.Sow using a variable rule')
            self.assert_model_not_in(model, '.Simulations.Simulation.Field.Sow using a variable rule',
                                     model_type='Models.Manager', fullpath=True)
            # test if a similar model of the same name in another simulation is not deleted
            self.assert_model_in(model, node2,
                                 model_type='Models.Manager', fullpath=True)

    def test_removing_a_simulation(self):
        'Test removing a simulation from the simulations tree'
        with ApsimModel('Maize') as model:
            # mock nested simulation
            model.clone_simulation('sim2')
            self.assert_model_in(model, 'sim2', model_type='Models.Core.Simulation', fullpath=False)
            self.assert_model_in(model, 'Simulation', model_type='Models.Core.Simulation', fullpath=False)
            model.remove_model_by_path(path='.Simulations.Simulation')
            self.assert_model_not_in(model, 'Simulation', model_type='Models.Core.Simulation', fullpath=False)

    def test_remove_model_by_path(self):
        with ApsimModel('Maize') as model:
            model.remove_model_by_path(self.model_to_remove_by_path)
            self.assert_model_not_in(model, self.model_to_remove_by_path, model_type='Models.Manager', fullpath=True)

    def test_remove_model_by_path_verbose(self):
        print("testing remove_model by path", file=sys.stderr)
        with ApsimModel('Maize') as model:
            model.remove_model_by_path(self.model_to_remove_by_path, verbose=True)
            self.assert_model_not_in(model, self.model_to_remove_by_path, model_type='Models.Manager', fullpath=True)

    def test_remove_model_by_path_missing(self):
        with ApsimModel('Maize') as model:
            with self.assertRaises(NodeNotFoundError):
                model.remove_model_by_path(self.path_not_found, verbose=True,
                                           missing_ok=False)


if __name__ == '__main__':
    unittest.main()

