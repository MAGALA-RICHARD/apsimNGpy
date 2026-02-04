.. rubric:: Table of Contents

.. contents::
   :local:
   :depth: 2
   :class: compact

.. _experiment_api:


.. note::

    ⚠️ Note: The Experiment module, introduced in apsimNGpy v0.3.9.7, addresses recent structural changes in APSIM file structure changes. While the older ``create_experiment`` method in ApsimModel is retained for backward compatibility,
    users working with newer APSIM models should use the :class:`~apsimNGpy.core.experimentmanager.ExperimentManager` class for building factorial designs. It offers full support for modern model experiment editing

The :class:`~apsimNGpy.core.experimentmanager.ExperimentManager`: API in ``apsimNGpy`` provides a high-level interface to build factorial experiments
programmatically using APSIM. It is ideal for users who want to automate the creation of simulation treatments
by varying input parameters or management scripts — all without manually editing ``.apsimx`` files.

.. note::
   This feature is especially useful for agronomists and researchers running large design-of-experiment (DoE) simulations.

Quick Overview
==============

The :class:`~apsimNGpy.core.experimentmanager.ExperimentManager`: class wraps an existing APSIM model and allows you to:

- Clone and isolate a base simulation
- Add multiple input factors (e.g., fertilizer rate, sowing density)
- Generate permutations or combinations of those factors
- Export the updated ``.apsimx`` file with fully configured experiments

Getting Started
===============

First, create an `Experiment` object by loading a base model:

.. code-block:: python

   from apsimNGpy.core.experimentmanager import ExperimentManager

   exp = ExperimentManager("Maize", out_path="Maize_experiment.apsimx")

Then initialize the experiment block:

.. code-block:: python

   exp.init_experiment(permutation=True)

.. seealso::

  :meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.init_experiment`:

Adding Input Factors
====================

Each factor describes a script path and a set of values to assign in the experiment. You can add one or more
factors like this:

.. code-block:: python

   exp.add_factor("[Manager Script].Script.Amount = 0 to 200 step 50")
   exp.add_factor("[Sowing Rule].Script.RowSpacing = 100, 300, 600", factor_name="RowSpacing")

.. seealso::

   API description: :meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.add_factor`

Finalizing the Experiment
=========================

Once all factors are defined, finalize the setup and save the modified model. Please note this is entirely optional,
:meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.add_factor` is a stand alone method, once you have finished adding factors, you can call the ``run`` to retrieve the results, without calling finalize. finalize is wa built as safe guard for immutability

@deprecated:

.. code-block:: python

    exp.finalize()

This writes a new `.apsimx` file that contains a complete factorial experiment,
ready to run in APSIM or via automation tools.

API Summary
===========

- :class:`~apsimNGpy.core.experimentmanager.ExperimentManager`: Main entry point to create and manipulate factorial designs.
- :meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.init_experiment`: Prepares the experiment node structure in the model.
- :meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.add_factor`: Adds a new varying parameter or script-defined rule.
- :meth:`~apsimNGpy.core.experimentmanager.ExperimentManager.finalize`: Validates and commits the experiment structure to the model.

Further Reading
===============

For advanced usage (e.g., linked script validation, mixed designs), refer to the API reference section.

.. seealso::

   - :ref:`comp_cultivar`
   - :ref:`api_ref`


