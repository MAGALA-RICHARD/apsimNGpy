How to Contribute to apsimNGpy
=================================

.. rubric:: Table of Contents

.. contents::
   :local:
   :depth: 4
   :class: compact

We welcome contributions from the community, whether they are bug fixes, enhancements, documentation updates, or new features. Here's how you can contribute to ``apsimNGpy``:

Reporting Issues
----------------

.. note::
  apsimNGpy is developed and maintained by a dedicated team of volunteers. We kindly ask that you adhere to our community standards when engaging with the project. Please maintain a respectful tone when reporting issues or interacting with community members.

If you find a bug or have a suggestion for improving ``apsimNGpy``, please first check the `Issue Tracker <https://github.com/MAGALA-RICHARD/apsimNGpy/issues>`_ to see if it has already been reported. If it hasn't, feel free to submit a new issue. Please provide as much detail as possible, including steps to reproduce the issue, the expected outcome, and the actual outcome.

Contributing Code
-----------------


We accept code contributions via Pull Requests (PRs). Here are the steps to contribute:

Forking the Repository
------------------------

Start by forking the ``apsimNGpy`` repository on GitHub. This creates a copy of the repo under your GitHub account.

Clone Your Fork
----------------------

Clone your fork to your local machine:

  .. code-block:: bash

    git clone https://github.com/MAGALA-RICHARD/apsimNGpy.git
    cd apsimNGpy

Create a New Branch
  Create a new branch for your changes:

  .. code-block:: bash

    git checkout -b your-branch-name

Make Your Changes
  Make the necessary changes or additions to the codebase. Please try to adhere to the coding style already in place.

Test Your Changes
  Run any existing tests, and add new ones if necessary, to ensure your changes do not break existing functionality.

Commit Your Changes
  Commit your changes with a clear commit message that explains what you've done:

  .. code-block:: bash

    git commit -m "A brief explanation of your changes"

Push to GitHub
  Push your changes to your fork on GitHub:

  .. code-block:: bash

    git push origin your-branch-name

Submit a Pull Request
Go to the ``apsimNGpy`` repository on GitHub, and you'll see a prompt to submit a pull request based on your branch. Click on "Compare & pull request" and describe the changes you've made. Finally, submit the pull request.

Updating Documentation
----------------------
Improvements or updates to documentation are greatly appreciated. You can submit changes to documentation with the same process used for code contributions.

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
            self.model.create_experiment(permutation=True)

Finally, run the test suite. It is recommended to use the ``run_suite`` method, which executes all registered tests and ensures that dependent modules are functioning correctly. You may need to add your test case before running

.. code-block:: python

    if __name__ == '__main__':
        suite.addTests(loader.loadTestsFromTestCase(TestCaseAddModule))
        run_suite(2)

Running apsimNGpy Test Modules
==============================

This section describes how to execute apsimNGpy test modules from the command line.

Installation (Editable Mode)
-----------------------------

Navigate to the project root directory and install in editable mode:

.. code-block:: bash

   cd apsimNGpy
   pip install -e .

Core Test Suite
---------------

Run the main test suite (excluding sensitivity and multi-core modules):

.. code-block:: bash

   python -m apsimNGpy.tests.tester_main \
       -bp "C:\Users\username\AppData\Local\Programs\APSIM2026.2.7989.0\bin"

Multi-Core Test Module
----------------------

Run the multi-core performance test module:

.. code-block:: bash

   python -m apsimNGpy.tests.unittests.mcp \
       -bp "C:\Users\username\AppData\Local\Programs\APSIM2026.2.7989.0\bin" \
       -md p \
       -e csharp

Options
^^^^^^^

``-bp``
    Path to the APSIM ``bin`` directory.

``-md``
    Parallel execution mode:

    * ``p`` = processes
    * ``t`` = threads

``-e``
    Execution engine:

    * ``csharp``
    * ``python``

Sensitivity Test Module
-----------------------

Run the sensitivity analysis test module:

.. code-block:: bash

   python -m apsimNGpy.tests.unittests.test_sens \
       -bp "C:\Users\username\AppData\Local\Programs\APSIM2026.2.7989.0\bin"

Notes
-----

* The ``-bp`` argument specifies the APSIM binary directory under test.
* The path must point to the valid ``bin`` folder of an APSIM installation.
* Alternatively, set the environment variable ``TEST_APSIM_BINARY`` to avoid
  repeatedly specifying ``-bp``.

.. seealso::

    - :ref:`Frequently Asked Questions <faq>`
    - :ref:`API Reference <api_ref>`
    - :ref:`Go back to the home page<master>`
