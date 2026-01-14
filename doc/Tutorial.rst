.. sens_salib

Sensitivity analysis workflow Part 2 (SALib driven workflow)
============================================================
In response to requests for a cross-platform sensitivity analysis
workflow, apsimNGpy has been integrated with SALib. As explained below

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

Perform Analysis
--------------------
With the model outputs loaded into Python memory, the final step is to
compute the sensitivity indices. In this example, we use
``sobol.analyze``, which computes first-order, second-order, and
total-order sensitivity indices.

Additional details on the Sobol analysis workflow are available
`here <https://salib.readthedocs.io/en/latest/user_guide/basics.html#an-example>`_.

.. code-block:: python

   Si = [sobol.analyze(runner.problem, Y[:, i], print_to_console=True) for i in range(Y.ndim)]

Each element in the result is returned as a Python dictionary containing
the keys ``S1``, ``S2``, ``ST``, ``S1_conf``, ``S2_conf``, and ``ST_conf``.
The ``*_conf`` entries represent the confidence intervals associated with
each sensitivity index, typically computed at a 95 percent confidence
level.

To display all sensitivity indices at once, set the keyword argument
``print_to_console=True``. Alternatively, individual indices can be
accessed directly from the results object, as shown below. Using grain yield as example hence index 0

.. code-block:: python

    Si[0]['S1']

.. code-block:: none

   array([0.43932783, 0.84502346])

Amount which is Nitrogen fertilizer quantity have a higher first order effect than the planting population density.

we can also retrieve the total effect

.. code-block:: python

   Si[0]['S1']

.. code-block:: python

  array([0.44579877, 0.91875446])

The larger total-order effects relative to the first-order effects
suggest potential interactions between the two factors

.. code-block:: python

    Si[0]['S2'][0,1]

.. code-block:: none

   np.float64(0.025099857475360032)

.. code-block:: python

 Si = [sobol.analyze(runner.problem, Y[:,i], print_to_console=True) for i in range(Y.ndim)]

.. code-block:: none

         ST   ST_conf
    Population  0.445799  0.447337
    Amount      0.918754  0.492323
                      S1   S1_conf
    Population  0.439328  0.471019
    Amount      0.845023  0.589469
                              S2   S2_conf
    [Population, Amount]  0.0251  0.338638
                      ST   ST_conf
    Population  0.342162  0.386487
    Amount      0.948013  0.527931
                      S1   S1_conf
    Population  0.334605  0.493981
    Amount      0.898494  0.579069
                               S2   S2_conf
    [Population, Amount]  0.04358  0.397149

SALib provides utilities that allow each sensitivity index to be
converted into a pandas DataFrame, which can then be used for further
analysis or visualization.

.. code-block:: python

  total_y, s1_y, s2_y  = Si[0].to_df()
  total_gn, s1_gn, s2_n  = Si[1].to_df()

.. code-block:: python

   print(total_y)

.. code-block:: python
                       ST   ST_conf
    Population  0.445799  0.447337
    Amount      0.918754  0.492323

SALib provides an object-oriented interface that simplifies the
sensitivity analysis triad of sampling, evaluation, and analysis.
In apsimNGpy, this workflow is further streamlined by wrapping all
three steps into a single method,
:meth:`~apsimNGpy.sensitivity.sensitivity.run_sensitivity`.

By keeping the initialized runner or problem definition constant,
the complete sensitivity analysis demonstrated above can be executed
in a concise and reproducible manner, as shown below.

.. code-block:: python

    Si_sobol = run_sensitivity(
        runner,
        method="sobol",
        N=2 ** 5,  # ← base sample size should be power of 2
        sample_options={
            "calc_second_order": True,
            "skip_values": 1024,
             "seed": 42,
        },
        analyze_options={
            "conf_level": 0.95,
            "num_resamples": 1000,
            "print_to_console": True,
            "calc_second_order": True,
        },
    )


The returned object is an instance of the
``SALib.util.problem.ProblemSpec`` class. When evaluated in the Python
console, this object displays a summary of the problem definition and
the computed sensitivity indices, as shown below.

.. code-block:: none

      Out[4]:
    Samples:
        2 parameters: ['Population', 'Amount']
        96 samples
    Outputs:
        2 outputs: ['Y1', 'Y2']
        96 evaluations
    Analysis:
    Y1:
                      ST   ST_conf
    Population  0.308278  0.291488
    Amount      1.089438  0.522208:
                      S1   S1_conf
    Population  0.394278  0.374126
    Amount      0.780433  0.644199:
                                S2   S2_conf
    [Population, Amount] -0.024841  0.561135:
    Y2:
                      ST   ST_conf
    Population  0.230316  0.245983
    Amount      1.073707  0.475261:
                      S1   S1_conf
    Population  0.307134  0.290722
    Amount      0.772897  0.628444:
                               S2   S2_conf
    [Population, Amount] -0.06778  0.422351:

The presence of negative sensitivity indices usually indicates an
insufficient sample size. Increasing the base sample size can help
mitigate this issue.

Converting outputs to pandas
----------------------------
If we use `to_df` a list of Pandas Dataframes is returned

.. code-block:: none
     [[                  ST   ST_conf
      Population  0.308278  0.291488
      Amount      1.089438  0.522208,
                        S1   S1_conf
      Population  0.394278  0.374126
      Amount      0.780433  0.644199,
                                  S2   S2_conf
      [Population, Amount] -0.024841  0.561135],
     [                  ST   ST_conf
      Population  0.230316  0.245983
      Amount      1.073707  0.475261,
                        S1   S1_conf
      Population  0.307134  0.290722
      Amount      0.772897  0.628444,
                                 S2   S2_conf
      [Population, Amount] -0.06778  0.422351]]

Key important attributes for  samples, model results and analyses extraction available on the returned instance are shown below.

.. code-block:: python

    print( Si_sobol.samples)
    print( Si_sobol.results)
    print( Si_sobol.analysis)


Basic plotting functionality is also provided

.. code-block:: python

    Si_sobol.plot()

We can try another method known as Morris.   The Morris method is typically used as a *screening tool* to identify influential
parameters with relatively low computational cost. It is well suited for high-dimensional
problems where the goal is to rank parameters rather than quantify precise sensitivities.

.. code-block:: python

  Si_morris = run_sensitivity(
        runner,
        method="morris", n_cores=10,
        sample_options={
            'seed': 42,
            "num_levels": 6,
            "optimal_trajectories": 6,
        },
        analyze_options={
            'conf_level': 0.95,
            "num_resamples": 1000,
            "print_to_console": True,
            'seed': 42
        },
    )
.. code-block:: none

   Out[7]:
    Samples:
        2 parameters: ['Population', 'Amount']
        18 samples
    Outputs:
        2 outputs: ['Y1', 'Y2']
        18 evaluations
    Analysis:
    Y1:
                          mu       mu_star         sigma  mu_star_conf
    Population  11394.831001  14289.237399  17359.167016  10309.394014
    Amount      28441.782977  29864.030018  31160.051327  22045.514695:
    Y2:
                       mu    mu_star      sigma  mu_star_conf
    Population  33.702220  35.548789  35.455297     23.199723
    Amount      78.486127  78.486127  73.559727     55.214639:

The final sensitivity analysis method demonstrated in this tutorial is
the FAST method. FAST is a variance-based approach that estimates the
influence of each input parameter by systematically varying inputs
across the parameter space and analyzing the resulting model response.

.. code-block:: python

    si_fast = run_sensitivity(
        runner,
        method="fast",
        sample_options={
            "M": 2,

        },
        analyze_options={
            'conf_level': 0.95,
            "num_resamples": 1000,
            "print_to_console": True,
        },
    )

.. code-block:: none

    Out[9]:
    Samples:
        2 parameters: ['Population', 'Amount']
        130 samples
    Outputs:
        2 outputs: ['Y1', 'Y2']
        130 evaluations
    Analysis:
    Y1:
                      S1        ST   S1_conf   ST_conf
    Population  0.211503  0.332158  0.206649  0.165346
    Amount      0.585945  0.742978  0.206981  0.163964:
    Y2:
                      S1        ST   S1_conf   ST_conf
    Population  0.151057  0.243790  0.208318  0.158650
    Amount      0.708005  0.819993  0.200030  0.162489:

Ideally, the analysis could begin with the Morris method to screen out
less influential factors, particularly when a large number of inputs
are under consideration. However, even without this initial screening,
the results are consistent across methods.

In this case, both FAST and Sobol analyses indicate that yield is more
sensitive to nitrogen fertilizer rate than to population density.

To extend the analysis beyond the Sobol, Morris, and FAST methods, follow
the same workflow demonstrated in the first example and consult the
SALib documentation for additional sensitivity analysis techniques and
their usage.

.. versionadded:: 1.0.0

References

Iwanaga, T., Usher, W., & Herman, J. (2022). Toward SALib 2.0: Advancing the accessibility and interpretability of global sensitivity analyses. Socio-Environmental Systems Modelling, 4, 18155. doi:10.18174/sesmo.18155

Herman, J. and Usher, W. (2017) SALib: An open-source Python library for sensitivity analysis. Journal of Open Source Software, 2(9). doi:10.21105/joss.00097