
Sensitivity analysis workflow
=============================

Sensitivity analysis follows a three-stage workflow triad:

1. **Sampling**
2. **Model evaluation**
3. **Analysis**

In this framework, **sampling** and **analysis** are handled by
`SALib`, while **model evaluation** is performed by **APSIM**.

Conceptual overview
-------------------

The logical process begins by **defining the problem**, which includes
identifying the input parameters to be varied, their ranges, and the
model outputs of interest. This problem definition is then passed to
SALib, which generates a structured set of parameter samples according
to the selected sensitivity analysis method.

These sampled parameter sets are subsequently **evaluated by APSIM**.
For each sample, APSIM executes a full simulation and produces the
corresponding model outputs. Once all simulations have completed, the
evaluated results are returned to SALib, where sensitivity indices are
computed and summarized.

In simplified terms, the data flow is:

- define the sensitivity problem and model inputs,
- generate parameter samples using SALib,
- evaluate each sample by running APSIM,
- analyze the results using SALib.


Computational considerations
----------------------------

The **model evaluation stage** is by far the most computationally
expensive component of the workflow. Each APSIM simulation may take
several seconds or more to complete, and sensitivity analyses typically
require hundreds to thousands of model evaluations.

To mitigate this computational cost, APSIM simulations are executed
**in parallel**, allowing multiple parameter sets to be evaluated
simultaneously. Parallel execution substantially reduces total runtime
and makes large-scale sensitivity analysis feasible in practice.

The first step is to import the necessary libraries

.. code-block:: python

    from SALib.sample import saltelli
    from SALib.analyze import sobol
    from apsimNGpy.sensitivity.sensitivity import ConfigProblem, run_sensitivity


Define APSIM model inputs
--------------------------

.. code-block:: python

     params = {
            ".Simulations.Simulation.Field.Sow using a variable rule?Population": (2, 10),
            ".Simulations.Simulation.Field.Fertilise at sowing?Amount": (0, 300),
            # ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82?[Leaf].Photosynthesis.RUE.FixedValue": (
            #     1.2, 2.2),
        }
.. tip::

   The **base parameter path** and the **specific parameter name or sub-path**
   are separated using one of the following delimiters: ``?``, ``::``, or ``@``.

   The values associated with each parameter define the **lower and upper
   bounds** of the sampling space used during sensitivity analysis.

Initialize the problem
--------------------------

.. code-block:: python

        runner = ConfigProblem(
            base_model="Maize",
            params=params,
            outputs=["Yield", "Maize.AboveGround.N"],
        )



