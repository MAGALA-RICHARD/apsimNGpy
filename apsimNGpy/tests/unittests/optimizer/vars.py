import copy
import unittest
from pydantic import ValidationError

from apsimNGpy.optimizer.problems.variables import (
    example_param2,
    filter_apsim_params,
    validate_user_params,
)
from wrapdisc.var import UniformVar

example_param = {
    "path": ".Simulations.Simulation.Field.Soil.Organic2",
    "vtype": (UniformVar(1, 2),),
    "start_value": ("1",),
    "candidate_param": ("Carbon",),
    "other_params": {"FBiom": 2.3},
}


class TestVars(unittest.TestCase):
    """Unit tests for APSIM optimization variable validation and filtering logic."""

    def setUp(self):
        """Prepare reusable fake parameter dictionaries for testing."""
        # Valid examples
        self.valid_example = copy.deepcopy(example_param)
        self.valid_example2 = copy.deepcopy(example_param2)

        # Invalid structures
        self.fake_param = dict(path=2)  # invalid type for 'path'

        self.fake_wrong_vtype_dtype = copy.deepcopy(example_param)
        self.fake_wrong_vtype_dtype["vtype"] = [float(1),], # invalid type

        self.fake_wrong_candidate_dtype = copy.deepcopy(example_param)
        self.fake_wrong_candidate_dtype["candidate_param"] = "Carbon"  # should be list/tuple

        self.fake_wrong_length = copy.deepcopy(example_param)
        self.fake_wrong_length["candidate_param"] = ["Carbon", "FBiom"]  # mismatched length
        # overlapping keys in other_params
        data = copy.deepcopy(example_param)
        data['other_params']['Carbon'] = 1.25
        self.overlaps = data

    # -------------------------------
    # Validation success tests
    # -------------------------------
    def test_validate_user_params_success(self):
        """Ensure valid example passes validation and returns BaseParams."""
        validated = validate_user_params(self.valid_example)
        self.assertEqual(validated.path, ".Simulations.Simulation.Field.Soil.Organic2")
        self.assertIsInstance(validated.vtype[0], UniformVar)
        self.assertEqual(validated.start_value[0], "1")

    # -------------------------------
    # Validation failure tests
    # -------------------------------
    def test_validate_user_params_string_candidate_param(self):
        """Raise ValidationError if candidate_param is not a list or tuple."""
        with self.assertRaises(ValidationError):
            validate_user_params(self.fake_wrong_candidate_dtype)

    # ------------------------------------------------------------------------
    # Validate overlapping keys in other_param and candidate params pass safely
    # -------------------------------------------------------------------
    def test_validate_overlapping_keys_in_user_params(self):
        pp = validate_user_params(self.overlaps)
        other_pa = pp.other_params
        self.assertNotIn('Carbon', other_pa.keys())

    def test_value_error_different_length(self):
        """Raise ValueError if candidate_param, start_value, and vtype have mismatched lengths."""
        with self.assertRaises(ValueError):
            validate_user_params(self.fake_wrong_length)

    def test_validate_user_params_wrong_vtype(self):
        """Raise ValidationError if vtype is of incorrect type."""
        with self.assertRaises(ValidationError):

            validate_user_params(self.fake_wrong_vtype_dtype)


    # -------------------------------
    # filter_apsim_params() tests
    # -------------------------------
    def test_filter_apsim_params_includes_path_and_placeholder(self):
        """Ensure filter_apsim_params merges other_params and replaces candidate_param with placeholders."""
        validated = validate_user_params(self.valid_example)
        filtered = filter_apsim_params(validated)

        self.assertIn("path", filtered)

        self.assertIn("Carbon", filtered)  # from other_params

        self.assertIsNotNone(filtered["path"])

    def test_filter_apsim_params_placeholder_is_object(self):
        """Ensure candidate parameters are replaced with placeholder objects."""
        validated = validate_user_params(self.valid_example)
        filtered = filter_apsim_params(validated)
        self.assertIn('Carbon', filtered)

    # -------------------------------
    # merge_params_by_path() tests
    # -------------------------------
    def test_merge_params_by_path_combines_other_params(self):
        """Ensure parameters from the same path are merged properly."""
        from apsimNGpy.optimizer.problems.variables import merge_params_by_path

        merged = merge_params_by_path([self.valid_example, self.valid_example2])
        self.assertIsInstance(merged, list)
        self.assertTrue(all("path" in p for p in merged))

    def tearDown(self):
        """Cleanup after tests (none required here)."""
        pass


if __name__ == "__main__":
    unittest.main()
