"""
Unit tests for verifying the lazy import architecture of apsimNGpy.

These tests ensure that:

1. Modules that depend on the APSIM runtime (e.g., ApsimModel) are not
   imported until the APSIM binary path is correctly configured.

2. The lazy import mechanism prevents runtime failures during initial
   package import when the APSIM runtime is unavailable.

This behavior is critical to ensure that users can still access helper
utilities (e.g., configuration functions) even when APSIM is not yet
installed or configured.
"""

from unittest import TestCase, main

from apsimNGpy import logger


class TestLazyImport(TestCase):
    """
    Tests for verifying the lazy-loading behavior implemented in apsimNGpy.

    The package intentionally delays importing modules that depend on the
    APSIM .NET runtime until they are explicitly accessed by the user.
    """

    def test_non_lazy_import(self):
        """
        Ensure that modules not dependent on the APSIM runtime can be imported
        normally.

        This verifies that basic utilities remain available regardless of the
        APSIM configuration state.
        """

        from apsimNGpy import load_crop_from_disk

        # Ensure the imported object exists
        self.assertIsNotNone(load_crop_from_disk)

    def test_not_a_directory_error(self):
        """
        Verify that importing APSIM-dependent modules fails when the APSIM
        binary path is invalid, while non-dependent utilities remain usable.

        This test simulates an invalid APSIM installation path and ensures that
        the lazy import mechanism prevents early runtime failures.
        """

        from apsimNGpy import config

        # ------------------------------------------------------------------
        # Step 1: Force an invalid APSIM binary path
        # ------------------------------------------------------------------
        cfb = config.configuration.bin_path
        config.configuration.bin_path = "2"  # intentionally invalid

        # Import apsimNGpy after modifying the configuration
        import apsimNGpy

        # Access test utilities namespace (should not trigger .NET imports)
        _ = apsimNGpy.unittests

        # ------------------------------------------------------------------
        # Step 2: Verify non-APSIM dependent utilities remain usable
        # ------------------------------------------------------------------
        from apsimNGpy import set_apsim_bin_path, custom_parallel, is_scalar

        self.assertTrue(is_scalar(2))
        self.assertTrue(callable(set_apsim_bin_path))
        self.assertTrue(callable(custom_parallel))

        # Ensure the invalid path is still present


        # ------------------------------------------------------------------
        # Step 3: Attempt to import APSIM runtime-dependent module
        # ------------------------------------------------------------------
        # This should fail because the APSIM binary path is invalid
        with self.assertRaises(NotADirectoryError):
            self.assertEqual(config.configuration.bin_path, "2")
            from apsimNGpy import ApsimModel
        config.configuration.bin_path = cfb

        # Step 4: Reset the temporary configuration
        # ------------------------------------------------------------------
        config.configuration.release_temporal_bin_path()

        # The path should now be different
        self.assertNotEqual(config.configuration.bin_path, "2")

        # ------------------------------------------------------------------
        # Step 5: Verify that APSIM modules can now be imported successfully
        # ------------------------------------------------------------------
        from apsimNGpy import ApsimModel

        self.assertTrue(callable(ApsimModel))
        logger.info('success importing')


if __name__ == "__main__":
    main()