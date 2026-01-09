
Sensitivity analysis workflow
=============================

Sensitivity analysis follows a three-stage workflow triad:

1. **Sampling**
2. **Model evaluation**
3. **Analysis**

In this framework, **sampling** and **analysis** are handled by
`SALib` https://salib.readthedocs.io/en/latest/api.html, while **model evaluation** is performed by **APSIM**.

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
use the ``ConfigProblem`` problem configuration class to set the scene for the senstivity triad

.. code-block:: python

        runner = ConfigProblem(
            base_model="Maize",
            params=params,
            outputs=["Yield", "Maize.AboveGround.N"],
        )

Generate samples
----------------
Since we are performing a Sobol’ sensitivity analysis, we need to generate samples using the Saltelli sampler from SAlib, as shown below.

.. code-block:: python

    param_values = saltelli.sample(runner.problem, 2 ** 4)

Sample matrix and evaluation
============================

The variable ``param_values`` is a two-dimensional NumPy array.
Inspecting its shape using ``param_values.shape`` shows that the array
has dimensions **96 by 2**.

This means that **96 parameter samples** were generated, and each sample
contains values for **2 model parameters**.

---

Saltelli sampling behavior
--------------------------

The Saltelli sampler generates a fixed number of samples based on the
number of input parameters and the base sample size. In this example:

- the base sample size ``N`` is ``2**4`` (16),
- the number of model inputs ``D`` is 2.

By default, the Saltelli sampler generates ``N * (2D + 2)`` samples.
With the values above, this results in **96 samples**.

If the option ``calc_second_order=False`` is used, the number of samples
is reduced. In that case, the sampler generates ``N * (D + 2)`` samples,
which significantly lowers the computational cost.

---

Running the APSIM model
-----------------------

The model evaluation step is performed using the ``evaluate`` method of
the ``ConfigProblem`` object.

.. code-block:: python

   Y = runner.evaluate(param_values)

This method runs the APSIM model once for **each row** in
``param_values`` and collects the corresponding outputs.

---

Evaluation output
-----------------

The variable ``Y`` is returned as a NumPy array. Its dimensionality
depends on the number of outputs specified in ``ConfigProblem``.

- If a single output is selected, ``Y`` is a one-dimensional array.
- If multiple outputs are selected, ``Y`` is a two-dimensional array.

In this example, two outputs were specified, so ``Y`` has shape
``(96, 2)``. Each row corresponds to one parameter sample, and each
column corresponds to one model output.

In other words, the evaluation step applies APSIM to every sampled
parameter set and returns the simulated results in a structured array
that can be passed directly to SALib for analysis.
