"""
MixedProblem: a reusable interface for defining mixed-variable optimization problems
with APSIM Next Generation models and wrapdisc-compatible variable types.

This module supports dynamic factor definition, parameter validation, and
objective wrapping for use with Python-based optimization solvers such as
scipy.Optimize and differential evolution.

Author: Richard Magala
"""

import copy
import gc
from collections import OrderedDict
from typing import Optional, List, Dict, Any

import numpy as np

from apsimNGpy.exceptions import ApsimRuntimeError
import pandas as pd
from apsimNGpy.optimizer.problems.variables import (
    validate_user_params,
    filter_apsim_params,
)
from apsimNGpy.optimizer.problems.back_end import runner, eval_observed
from wrapdisc import Objective
from wrapdisc.var import UniformVar  # can be generalized for other variable types

__all__ = ['MixedProblem']


class MixedProblem:
    """
    Defines a single-objective mixed-variable optimization problem for APSIM models.

    This class integrates APSIM simulations, observed data comparison,
    and user-defined factors (parameters) into a single reusable problem description
    suitable for optimization with scipy or pymoo solvers.

    Parameters
    ----------
    model : str
        APSIM model identifier or path to the .apsimx file.
    trainer_dataset : pd.DataFrame or None
        Observed dataset for calibration or evaluation.
    pred_col : str
        Column in APSIM output corresponding to predicted values.
    trainer_col : str
        Column in observed dataset corresponding to observed values.
    index : str
        Column used for aligning predicted and observed values (e.g., 'year').
    metric : str, default='RMSE'
        Evaluation metric to use (e.g., 'RMSE', 'R2', 'WIA').
    table : str or None, optional
        APSIM output table name (if applicable).
    func : callable or None, optional
        Custom evaluation function to override the built-in validation workflow. if provided should leave room for predicted argument

    Notes
    -----
    - Each factor defines a modifiable APSIM node parameter and can have its own
      variable type (e.g., continuous, integer, categorical).
    - The resulting object can be wrapped into a callable Objective
      via `wrap_objectives()` for integration with optimization solvers.
    """

    def __init__(
            self,
            model: str,
            trainer_dataset: Optional[pd.DataFrame] = None,
            pred_col: str = None,
            trainer_col: str = None,
            index: str = None,
            metric: str = "RMSE",
            table: Optional[str] = None,
            func: Optional[Any] = None,
    ):
        datas = all([trainer_dataset is not None, pred_col, trainer_col, index]) or callable(func)
        if not datas:
            raise ValueError(
                "Either provide an evaluation function or a valid dataset with columns for observed and predicted values."
            )
        if trainer_dataset is not None:
            assert isinstance(
                trainer_dataset, pd.DataFrame
            ), f"trainer_dataset must be a pandas DataFrame containing column '{index}'"

        self.model = model
        self.obs = trainer_dataset
        self.predicted_col = pred_col
        self.obs_column = trainer_col
        self.index = index
        self.accuracy_indicator = metric
        self.table = table
        self.func = func
        self.inputs_ok = False

        # internal containers
        self.ordered_factors = OrderedDict()
        self.var_types: List = []
        self.var_names: List[str] = []
        self.candidate_params: List[str] = []
        self.start_values: List[Any] = []
        self.apsim_params: List[Dict[str, Any]] = []

        # objective wrapper
        self.wrapped_objectives = None

    # -------------------------------------------------------------------------
    # Basic Properties and Helpers
    # -------------------------------------------------------------------------
    def __hash__(self):
        """Provide a deterministic hash for problem configurations."""
        return hash(
            (
                self.model,
                self.accuracy_indicator,
                tuple(self.var_names),
                tuple(self.start_values),
                self.predicted_col,
                self.obs_column,
            )
        )

    @property
    def n_apsim_nodes(self) -> int:
        """Number of submitted optimization APSIM factors nodes."""
        return len(self.ordered_factors)

    @property
    def n_factors(self) -> int:
        """Number of submitted optimization factors."""
        return len(self.var_names)

    # -------------------------------------------------------------------------
    # Factor Submission and Validation
    # -------------------------------------------------------------------------
    def submit_factor(self, *, path, vtype, start_value, candidate_param, cultivar=False, other_params=None):
        """
            Add a new factor (parameter) to be optimized.

            Each factor corresponds to a modifiable APSIM node attribute and its
            variable type (e.g., UniformVar, RandintVar, ChoiceVar). Factors define
            the search space and starting points for parameter optimization.

            Parameters
            ----------
            path : str
                APSIM node path where the parameter resides, e.g.
                ``".Simulations.Simulation.Field.Soil.Organic"``.
                This node typically contains variables like FBiom, Carbon, and FINert.

            vtype : list or tuple of wrapdisc.var
                Variable types defining the search domain for each candidate parameter.
                These can include discrete, quantized, or continuous domains (see table below).

            start_value : list or tuple of (str | int | float)
                Initial values for each parameter, in the same order as ``candidate_param``.

            candidate_param : list or tuple of str
                The names of APSIM variables (e.g., ``"FOM"``, ``"FBiom"``) to be optimized.
                These should exist within the APSIM node path provided.

            cultivar : bool, optional, default=False
                Signal to the API whether the parameter belongs to a cultivar node.
                Set this flag to ``True`` when defining cultivar-related optimization factors.

            other_params : dict, optional
                Additional APSIM constants to fix during optimization (non-optimized parameters).
                These must belong to the same node path.
                For example, when optimizing *FBiom* while also modifying *Carbon*, you can
                supply *Carbon* as a constant under ``other_params`` (see Example 1 below).

            .. tip::

               As a rule of thumb, group all parameters belonging to the same APSIM node
               into a single factor by providing them as lists. Submitting parameters from
               the same node as separate factors will raise a validation error.

               Values must be provided with key word argument style to support json data structures across platforms

            .. note::

               All input factors are first validated using **Pydantic** to ensure conformity
               to the expected data structures and types — for instance, confirming that
               ``vtype`` consists of recognized variable types (e.g., ``UniformVar``, ``GridVar``),
               that ``path`` is a valid string, and that numeric tuples follow expected
               range conventions. This guarantees type safety and consistency across
               optimization runs.

               After Pydantic validation, an additional structural check verifies
               that the **lengths** of ``vtype``, ``start_value``, and ``candidate_param``
               collections are identical. This ensures that each parameter to be optimized
               has a corresponding variable type and initial value.

               If you select an optimization method that **does not rely on bounded or
               initialized start values**, you may safely provide dummy entries for
               ``start_value``. These placeholders will be accepted without raising errors
               and will not affect the optimization process. The validation framework is
               designed to remain flexible for both stochastic (randomized) and
               deterministic search methods.



           The variable types follow the ``wrapdisc`` library conventions.
           Each type defines how sampling and decoding are handled during optimization.

           +----------------+--------------------------------+-------------------------------------------------------------+---------------------------+--------------------------------------------------------------------------------+
           | **Space**      | **Variable Type**              | **Usage / Description**                                     | **Decoder**               | **Examples**                                                                    |
           +================+================================+=============================================================+===========================+================================================================================+
           | **Discrete**   | ``ChoiceVar(items)``           | Nominal (unordered categorical)                             | one-hot via *max*         | ``ChoiceVar(["USA", "Panama", "Cayman"])``                                     |
           +----------------+--------------------------------+-------------------------------------------------------------+---------------------------+--------------------------------------------------------------------------------+
           | **Discrete**   | ``GridVar(values)``            | Ordinal (ordered categorical)                               | round                     | ``GridVar([2, 4, 8, 16])``<br>``GridVar(["good", "better", "best"])``          |
           +----------------+--------------------------------+-------------------------------------------------------------+---------------------------+--------------------------------------------------------------------------------+
           | **Discrete**   | ``RandintVar(lower, upper)``   | Integer from *lower* to *upper*, inclusive                  | round                     | ``RandintVar(0, 6)``, ``RandintVar(3, 9)``, ``RandintVar(-10, 10)``            |
           +----------------+--------------------------------+-------------------------------------------------------------+---------------------------+--------------------------------------------------------------------------------+
           | **Discrete**   | ``QrandintVar(lower, upper, q)`` | Quantized integer from *lower* to *upper* in multiples of q | round to nearest multiple | ``QrandintVar(0, 12, 3)``, ``QrandintVar(1, 10, 2)``, ``QrandintVar(-10, 10, 4)`` |
           +----------------+--------------------------------+-------------------------------------------------------------+---------------------------+--------------------------------------------------------------------------------+
           | **Continuous** | ``UniformVar(lower, upper)``   | Float from *lower* to *upper*                               | passthrough               | ``UniformVar(0.0, 5.11)``, ``UniformVar(0.2, 4.6)``, ``UniformVar(-10.0, 10.0)`` |
           +----------------+--------------------------------+-------------------------------------------------------------+---------------------------+--------------------------------------------------------------------------------+
           | **Continuous** | ``QuniformVar(lower, upper, q)`` | Quantized float from *lower* to *upper* in multiples of q   | round to nearest multiple | ``QuniformVar(0.0, 5.1, 0.3)``, ``QuniformVar(-5.1, -0.2, 0.3)``                |
           +----------------+--------------------------------+-------------------------------------------------------------+---------------------------+--------------------------------------------------------------------------------+

            Reference
            ----------
            - ``wrapdisc`` documentation: https://pypi.org/project/wrapdisc/

            Examples
            --------
            Example 1 — Continuous variable (``UniformVar``)
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            .. code-block:: python

                mp.submit_factor(
                    path=".Simulations.Simulation.Field.Soil.Organic",
                    vtype=[UniformVar(1, 2)],
                    start_value=["1"],
                    candidate_param=["FOM"],
                    other_params={"FBiom": 2.3, "Carbon": 1.89},
                )

            Example 2 — Quantized continuous variable (``QuniformVar``)
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            .. code-block:: python

                mp.submit_factor(
                    path=".Simulations.Simulation.Field.Soil.Organic",
                    vtype=[QuniformVar(0.0, 1.0, 0.005)],  # 0.005 is the quantization interval
                    start_value=["0.035"],
                    candidate_param=["FBiom"],
                )

            Example 3 — Integer variable (``RandintVar``)
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            .. code-block:: python

                mp.submit_factor(
                    path=".Simulations.Simulation.Field.Soil.Plant",
                    vtype=[RandintVar(1, 10)],
                    start_value=[5],
                    candidate_param=["Population"],
                )

            Example 4 — Quantized integer variable (``QrandintVar``)
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            .. code-block:: python

                mp.submit_factor(
                    path=".Simulations.Simulation.Field.Soil.Labile",
                    vtype=[QrandintVar(0, 12, 3)],
                    start_value=[3],
                    candidate_param=["Carbon"],
                )

            Example 5 — Categorical variable (``ChoiceVar``)
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            This is suitable for exploring categorical management options, such as selecting the best
            cultivar for a region or testing sowing date strategies.

            .. code-block:: python

                mp.submit_factor(
                    path=".Simulations.Simulation.Sow using a variable rule",
                    vtype=[ChoiceVar(["B_100", "A90", "B110"])],
                    start_value=["B_100"],
                    candidate_param=["CultivarName"],
                )

            Example 6 — Ordinal grid variable (``GridVar``)
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            .. code-block:: python

                mp.submit_factor(
                    path=".Simulations.Simulation.Field.Management",
                    vtype=[GridVar(["Low", "Medium", "High"])],
                    start_value=["Medium"],
                    candidate_param=["FertilizerRate"],
                )

            Submitting cultivar-related variables
            -------------------------------------
            When defining optimization factors for cultivar-specific parameters, you must explicitly
            signal to the APSIMNGpy API that the parameter belongs to a cultivar node.
            This is done by including the keyword ``cultivar=True`` in the factor definition.

            By default, this flag is ``False``, meaning the optimizer assumes the factor is not
            cultivar-related and treats it as a regular parameter (e.g., soil, management, or
            plant-level attribute).

            Internally, this flag is validated as a boolean field through Pydantic to ensure
            consistent interpretation and error checking.

            The cultivar flag enables APSIMNGpy to route the parameter to the correct editing
            pipeline for cultivar commands and properties under APSIM’s *Replacements* or
            *CultivarFolder* nodes.

            .. code-block:: python

                from wrapdisc.var import QrandintVar

                cultivar_param = {
                    # Full APSIM path to the target cultivar node
                    "path": ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82",

                    # Quantized integer variable (range: 400–550, step size: 5)
                    "vtype": [QrandintVar(400, 550, q=5)],

                    # Starting value for optimization
                    "start_value": [550],

                    # APSIM command or property to be optimized within the cultivar
                    "candidate_param": ["[Grain].MaximumGrainsPerCob.FixedValue"],

                    # Fixed or contextual parameters associated with the same node
                    "other_params": {"sowed": True},

                    # Signal that this parameter belongs to a cultivar node
                    "cultivar": True
                }

                mp.submit_factor(**cultivar_param)
            """

        out = validate_user_params(
            dict(
                path=path,
                vtype=vtype,
                start_value=start_value,
                candidate_param=candidate_param,
                other_params=other_params,
                cultivar=cultivar,
            )
        )
        apsim_out = filter_apsim_params(out)
        key_hashable = (tuple(apsim_out.keys()), tuple(apsim_out.values()))
        self.ordered_factors[key_hashable] = out
        self._validate_factor()
        self._scan()
        gc.collect()

    def submit_all(self, all_factors: List[Dict[str, Any]]):
        """
        Batch-add multiple factors for optimization.

        This method provides a convenient way to register several parameter factors
        (e.g., multiple APSIM node attributes) at once, instead of calling
        :meth:`submit_factor` repeatedly for each parameter.
        Each item in the input list must follow the same structure expected by
        :meth:`submit_factor`.

        Parameters
        ----------
        all_factors : list of dict
            A list (or tuple) of dictionaries, where each dictionary defines a single
            optimization factor with the following required keys:

            path: str
              The APSIM node path where the variable resides.
            vtype: list or tuple of wrapdisc.var
              The variable type(s) defining the sampling space (e.g., `UniformVar`, `ChoiceVar`).
            start_value: list or tuple of str, int, or float
              The starting value(s) corresponding to each candidate parameter.
            candidate_param : list or tuple of str
              The APSIM variable names to optimize.
            other_params: dict, optional
              Any additional parameters belonging to the same APSIM node that
              should remain constant during optimization.
            cultivar: bool, default=False
              Whether the factor being submitted is cultivar specific or resides on the cultivar node

        Notes
        -----
        This method internally calls :meth:`submit_factor` for each element in
        ``all_factors``. Each factor is individually validated using Pydantic
        type checks and structural consistency rules to ensure that all required
        fields are properly defined.

        Returns
        -------
        self : MixedProblem
            Returns the same instance for method chaining.
            This enables expressions like:
            ``mp.submit_all(factors).wrap_objectives().minimize_with_de()``

        Examples
        --------
        .. code-block:: python

            # Define multiple parameter factors
            all_factors = [
                {
                    "path": ".Simulations.Simulation.Field.Soil.Organic",
                    "vtype": [UniformVar(1, 2)],
                    "start_value": ["1.0"],
                    "candidate_param": ["FOM"],
                    "other_params": {"FBiom": 2.3, "Carbon": 1.89},
                },
                {
                    "path": ".Simulations.Simulation.Field.Plant",
                    "vtype": [RandintVar(1, 10)],
                    "start_value": [5],
                    "candidate_param": ["Population"],
                },
            ]

            # Batch register all factors at once
            mp.submit_all(all_factors)
        """
        for factor in all_factors:
            self.submit_factor(**factor)
        return self

    def _validate_factor(self, verbose=False):
        """
        Ensure that multiple factors belonging to the same APSIM node
        are defined only once unless grouped as tuples.
        """
        seen_paths = set()
        if self.n_factors > 1:
            for idx, factor in enumerate(self.ordered_factors.values()):
                path = getattr(factor, "path", None)
                if verbose:
                    print(f"[{idx}] Checking factor path: {path}")
                if not path:
                    raise ValueError(f"Factor at index {idx} missing 'path'.")
                if path in seen_paths:
                    raise ValueError(
                        f"Duplicate path detected: {path!r}. Use tuples for multi-factor nodes."
                    )
                seen_paths.add(path)

    # -------------------------------------------------------------------------
    # Factor Scanning and Variable Tracking
    # -------------------------------------------------------------------------
    def _scan(self):
        """
        Rebuild variable arrays (types, names, start values) from submitted factors.
        This resets and reconstructs all optimizations-relevant data structures.
        """
        self.apsim_params.clear()
        self.candidate_params.clear()
        self.var_types.clear()
        self.var_names.clear()
        self.start_values.clear()

        for _, factor in self.ordered_factors.items():

            apsim_var = filter_apsim_params(factor)

            self.apsim_params.append(apsim_var)
            self.var_types.extend(factor.vtype)
            self.start_values.extend(factor.start_value)
            if not factor.cultivar:
                self.var_names.extend(factor.candidate_param)
            else:
                self.var_names.extend(factor.candidate_param)

    # -------------------------------------------------------------------------
    # Optimization Interface
    # -------------------------------------------------------------------------

    def _insert_x_vars(self, x_vars: List[Any]) -> List[Dict[str, Any]]:
        """
        Insert optimized or sampled values into APSIM parameters efficiently.

        Parameters
        ----------
        x_vars : list
            List of numerical values corresponding to each variable in var_names.

        Returns
        -------
        list of dict
            Updated APSIM parameter sets ready for model execution.
        """
        name_value_map = dict(zip(self.var_names, x_vars))
        apsim_params = copy.deepcopy(self.apsim_params)
        for param in apsim_params:

            if 'cultivar' not in param:
                keys = param.keys() & name_value_map.keys()
                if keys:
                    param.update({k: name_value_map[k] for k in keys})
            else:
                keys = param.keys() & name_value_map.keys()
                if keys:
                    param['values'] = [name_value_map[k] for k in keys]
                    param['commands'] = [k for k in keys]
                    # pop all keys here
                    [param.pop(k, None) for k in keys]

            # now we can also pop 'cultivar' key
            param.pop('cultivar', None)

        return apsim_params

    def evaluate_objectives(self, x):
        """
        Evaluate the APSIM model’s objective function for a given parameter vector.

        This method inserts the provided input parameters into the APSIM model,
        executes the simulation, and evaluates the predicted outputs against
        the observed dataset using a selected performance metric
        (e.g., RMSE, R², ME, CCC).
        It serves as the core evaluation routine for optimization and
        sensitivity analysis workflows.

        Parameters
        ----------
        x : array-like
            A numeric vector (list, tuple, or NumPy array) representing parameter values
            to be inserted into the APSIM model.
            The vector must match the order and dimensionality of the
            defined optimization factors (as specified through
            :meth:`submit_factor` or :meth:`submit_all`).

        Workflow
        --------
        1. The provided parameter vector ``x`` is mapped onto APSIM input variables
           using the internal :meth:`_insert_x_vars` method.
        2. The model is executed via the :func:`runner` interface, which
           runs the APSIM simulation with the updated parameters.
        3. Simulation outputs (predicted data) are compared against the
           reference observations (``self.obs``) using the
           :func:`eval_observed` evaluator.
        4. The chosen performance metric, defined in ``self.method``, is computed
           and returned.

        Notes
        -----
        The supported evaluation metrics include:

        - ``RMSE`` : Root Mean Square Error
        - ``MAE`` : Mean Absolute Error
        - ``RRMSE`` : Relative Root Mean Square Error
        - ``R2`` : Coefficient of Determination
        - ``ME`` : Modeling Efficiency
        - ``WIA`` : Willmott’s Index of Agreement
        - ``CCC`` : Concordance Correlation Coefficient
        - ``BIAS`` : Mean Bias Error

        These metrics are implemented in the :class:`apsimNGpy.validation.evaluator.Validate`
        module and are used to assess how well the simulated values replicate observed data.



        Returns
        -------
        float
            The computed performance score based on the selected metric.
            For metrics such as RMSE or MAE, **lower values indicate better performance**,
            whereas for R², WIA, or CCC, **higher values indicate better model fit**.

        The magnitude of the minimization is determined automatically in the back_end.py, thus if you are
        using eval_observed method, no need to worry about multiplying with -1 for loss function indices such as CCC

        Examples
        --------
        .. code-block:: python

            # Evaluate APSIM model performance using a sample parameter vector
            x = [1.5, 0.8, 3.2, 0.1]
            score = mp.evaluate_objectives(x)

            print(f"Model evaluation ({mp.method}):", score)
        """
        if not self.inputs_ok:
            self._test_inputs(x)
        try:
            predicted = runner(self.model, self._insert_x_vars(x))
            if callable(self.func):
                return self.func(predicted)
            eval_out = eval_observed(
                self.obs,
                predicted,
                pred_col=self.predicted_col,
                obs_col=self.obs_column,
                index=self.index,
                method=self.accuracy_indicator)

            return eval_out
        except ApsimRuntimeError:
            # not all sampled x inputs will always be APSIM compatible
            from apsimNGpy.optimizer.problems.back_end import metric_direction

            from apsimNGpy.settings import logger
            logger.warning(f"Simulation failed for x variables {x} method '{self.accuracy_indicator}', returning penalty value.")
            direction = metric_direction.get(self.accuracy_indicator.lower(), -1)
            # If the metric is minimized, return +inf (bad)
            # If the metric is maximized, return -inf (bad)
            return -direction * np.inf

    def _test_inputs(self, x, verbose=False) -> None:
        """
        Validate optimization input vector before running the objective function.

        This function performs a pre-execution test by attempting a dry run of
        the APSIM model with the provided parameter vector ``x``. It ensures that
        all variables can be successfully inserted into the model and that the
        model runs without raising a runtime error.

        The test prevents invalid configurations from being passed into the
        optimization loop, thereby isolating simulation errors from optimizer
        logic. These include wrong paramters paths, absence of required models in the simulation file etc
        Parameters
        ----------
        x : array-like
            A parameter vector (sample) to be tested before full optimization.
        verbose : bool, optional default=False
            prints success message on the screen if set to true

        Raises
        ------
        FailedInputTestError
            If the test simulation fails due to invalid parameterization or model
            structure.
        """
        from apsimNGpy.exceptions import ApsimRuntimeError
        from apsimNGpy.settings import logger
        import pandas as pd

        class FailedInputTestError(ApsimRuntimeError):
            """Raised when APSIM input validation fails before optimization i.e., APSIM fails to run correctly"""
            pass

        try:
            res = runner(self.model, self._insert_x_vars(x))
            self.inputs_ok = True  # update internal validation flag

            if isinstance(res, pd.DataFrame) and not res.empty:
                if verbose:
                    logger.info("Input validation passed — proceeding with optimization.")

        except ApsimRuntimeError as ape:
            self.inputs_ok = False
            logger.error(
                "APSIM Input validation failed — model could not be executed with the provided parameters.\n"
                "Ensure that all APSIM node paths and variable types are correctly defined,"
                "The model has weather file with correct start dates"
            )
            raise FailedInputTestError(str(ape)) from ape

    def wrap_objectives(self) -> Objective:
        """
        Wrap the evaluation function into a `wrapdisc.Objective`
        instance compatible with mixed-variable optimizers.

        Returns
        -------
        Objective
            A callable objective that accepts encoded variable vectors.
        """
        wrapper = Objective(
            self.evaluate_objectives, variables=self.var_types
        )
        self.wrapped_objectives = wrapper
        return wrapper


# -------------------------------------------------------------------------
# Example usage
# -------------------------------------------------------------------------
if __name__ == "__main__":
    from apsimNGpy.tests.unittests.test_factory import obs

    example_param3 = {
        "path": ".Simulations.Simulation.Field.Soil.Organic1",
        "vtype": [UniformVar(1, 2)],
        "start_value": ["1"],
        "candidate_param": ["FOM"],
        "other_params": {"FBiom": 2.3, "Carbon": 1.89},
    }

    mp = MixedProblem(
        model="Maize",
        trainer_dataset=obs,
        pred_col="Yield",
        index="year",
        trainer_col="observed",
    )

    mp.submit_factor(**example_param3)
    mp._insert_x_vars([1.88])
    print(mp.var_names, mp.start_values)
