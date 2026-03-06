import os
import time
import unittest
from apsimNGpy.config import apsim_bin_context, path_checker, configuration, Path, set_apsim_bin_path, \
    get_apsim_bin_path
from apsimNGpy.logger import logger
from apsimNGpy import Apsim

bin_path2 = os.environ.get('TEST_APSIM_BINARY')
if bin_path2:
    bin_path2 = Path(bin_path2.strip())


class TestConfigApsimBinContext(unittest.TestCase):
    def setUp(self):
        self.bin_path = get_apsim_bin_path()

    def skip(self):
        if not path_checker(self.bin_path):
            sub_msg = (
                f"is not set according to the env bin key 'TEST_APSIM_BINARY'"
                if self.bin_path is None
                else f"'{self.bin_path}' does not exist"
            )

            logger.warning(sub_msg)

            self.skipTest(sub_msg)

    def test_apsim_bin_context_no_direct_path(self):
        """
        Test context manager WHEN ONLY env path and bin key are provided

        """
        self.skip()
        with Apsim() as bin_run_time:
            with bin_run_time.ApsimModel('Maize') as model:
                model.run()
                self.assertFalse(model.results.empty, 'Results are empty')

    def test_apsim_direct_path(self):
        """
        Test context manager, WHEN BIN PATH is provided

        """
        self.skip()
        with Apsim(apsim_bin_path=self.bin_path) as bin_run_time:
            with bin_run_time.ApsimModel('Maize') as model:
                model.run()
                self.assertFalse(model.results.empty, 'Results are empty')

    def test_unittest_name_space(self):
        import apsimNGpy

        expected_modules = [
            "senstivitymanager",
            "experiment",
            "apsim",
            "core_edit_model",
            "edit_model_by_path",
            "runner",
            "starter",
            "weathermanager",
            "soilmanager",
        ]

        for module_name in expected_modules:
            with self.subTest(module=module_name):
                # attribute exists
                self.assertTrue(
                    hasattr(apsimNGpy.unittests, module_name),
                    msg=f"Missing unittest module: {module_name}",
                )

                module = getattr(apsimNGpy.unittests, module_name)

                # ensure the attribute is a module
                self.assertTrue(
                    hasattr(module, "__file__"),
                    msg=f"{module_name} is not a module-like object",
                )

    def test_apsim_no_context(self):
        """
              Test NO context manager

        """
        self.skip()
        bin_run_time = Apsim(apsim_bin_path=self.bin_path)
        with bin_run_time.ApsimModel('Maize') as model:
            model.run()
            self.assertFalse(model.results.empty, 'Results are empty')

    def test_attributes_attached_no_context(self):
        """Ensure required namespace attributes are exposed by apsim_bin_context."""
        self.skip()

        bin_runtime = Apsim(self.bin_path)

        # --- Attribute existence checks ---
        self.assertTrue(hasattr(bin_runtime, "ApsimModel"))
        self.assertTrue(hasattr(bin_runtime, "MultiCoreManager"))
        self.assertTrue(hasattr(bin_runtime, "run_apsim_by_path"))
        self.assertTrue(hasattr(bin_runtime, "run_sensitivity"))
        self.assertTrue(hasattr(bin_runtime, "ConfigProblem"))
        self.assertTrue(hasattr(bin_runtime, "ExperimentManager"))

        # --- Type / callable checks ---
        self.assertTrue(callable(bin_runtime.ApsimModel))
        self.assertTrue(callable(bin_runtime.MultiCoreManager))
        self.assertTrue(callable(bin_runtime.run_apsim_by_path))
        self.assertTrue(callable(bin_runtime.run_sensitivity))
        self.assertTrue(callable(bin_runtime.ConfigProblem))
        self.assertTrue(callable(bin_runtime.ExperimentManager))

    def test_attributes_attached_with_context(self):
        """Ensure required namespace attributes are exposed by apsim_bin_context."""
        self.skip()

        with Apsim(self.bin_path) as bin_runtime:
            # --- Attribute existence checks ---
            self.assertTrue(hasattr(bin_runtime, "ApsimModel"))
            self.assertTrue(hasattr(bin_runtime, "MultiCoreManager"))
            self.assertTrue(hasattr(bin_runtime, "run_apsim_by_path"))
            self.assertTrue(hasattr(bin_runtime, "run_sensitivity"))
            self.assertTrue(hasattr(bin_runtime, "ConfigProblem"))
            self.assertTrue(hasattr(bin_runtime, "ExperimentManager"))
            self.assertTrue(hasattr(bin_runtime, "SensitivityManager"))
            self.assertTrue(hasattr(bin_runtime, "MixedVariableOptimizer"))
            self.assertTrue(hasattr(bin_runtime, "MixedProblem"))

            # --- Type / callable checks ---
            self.assertTrue(callable(bin_runtime.ApsimModel))
            self.assertTrue(callable(bin_runtime.MultiCoreManager))
            self.assertTrue(callable(bin_runtime.run_apsim_by_path))
            self.assertTrue(callable(bin_runtime.run_sensitivity))
            self.assertTrue(callable(bin_runtime.ConfigProblem))
            self.assertTrue(callable(bin_runtime.ExperimentManager))
            self.assertTrue(callable(bin_runtime.SensitivityManager))
            self.assertTrue(callable(bin_runtime.MixedVariableOptimizer))
            self.assertTrue(callable(bin_runtime.MixedProblem))
            # --- Lazy loader caching test ---
            first_access = bin_runtime.ApsimModel
            second_access = bin_runtime.ApsimModel

            # should return the same object reference
            self.assertIs(first_access, second_access)

            # ensure attribute is now cached on the instance
            self.assertIn("ApsimModel", bin_runtime.__dict__)
            self.assertIn("MixedProblem", bin_runtime.__dict__)


if __name__ == '__main__':
    from apsimNGpy import config
    import apsimNGpy

    unittest.main(verbosity=2)
