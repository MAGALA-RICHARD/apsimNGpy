Testing your pull request or your contribution
----------------------------------------------

After making any code improvements, it is important to ensure that all modules are still working correctly. This calls for an explicit test of the added code changes.

`apsimNGpy` tests are implemented via Python's ``unittest`` module. We provide a testing framework as shown below.

First, navigate to your `apsimNGpy` repository or the directory containing ``setup.py`` in your terminal, and run the following command:

.. code-block:: python

    pip install -e .  # Installs apsimNGpy as an editable package, enabling direct imports
                    #and reflecting code changes without re-installation

Import the necessary modules as follows:

.. code-block:: python

    import unittest
    from apsimNGpy.tests.tester_main import suite, loader, run_suite
    from apsimNGpy.core.base_data import load_default_simulations

Set up the test and add any test case as shown below:

.. code-block:: python

    class TestCaseAddModule(unittest.TestCase):
        # Set up the model to use
        def setUp(self):
            self.model = load_default_simulations('Maize')
            self.out = 'test_edit_model.apsimx'

        # Add test case
        def test_add_crop_replacement(self):
            """+++test adding crop replacement++"""
            self.model.add_crop_replacements(_crop='Maize')
            # test logic goes here

Finally, run the test suite. It is recommended to use the ``run_suite`` method, which executes all registered tests and ensures that dependent modules are functioning correctly. You may need to add your test case before running

.. code-block:: python

    if __name__ == '__main__':
        suite.addTests(loader.loadTestsFromTestCase(TestCaseAddModule))
        run_suite(2) # 0 turns off the verbosity

The test output should include a summary at the end, showing the total number of tests, the number passed, the number failed, and the failure rate.


----------------------------------------------------------------------
Ran 54 tests in 96.975s
OK
  [INFO]
 Test Summary:
  [INFO]   ✅ Passed  : 54
  [INFO]   ❌ Failures: 0
  [INFO]   💥 Errors  : 0
  [INFO]   📉 Failure Rate: 0.00%
=====================================



