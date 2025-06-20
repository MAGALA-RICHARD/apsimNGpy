"""
This allows for mixed variable optimization by encoding the categorical _variables
"""
from pathlib import Path

import numpy as np

from apsimNGpy.core_utils.utils import timer
from scipy.optimize import minimize, differential_evolution
import subprocess

from apsimNGpy.optimizer.one_obj import AbstractProblem, SIMULATIONS, ContinuousVariableProblem, cache, VarDesc
from apsimNGpy.core_utils.progbar import ProgressBar
try:
    import wrapdisc
except ModuleNotFoundError as mnf:
    print('installing wrapdisc package')
    package_name = "wrapdisc"
    command = ["pip", "install", package_name]
    # Running the command
    subprocess.run(command, check=True)

import operator
from typing import Any

import scipy.optimize

from wrapdisc import Objective
from wrapdisc.var import ChoiceVar, GridVar, QrandintVar, QuniformVar, RandintVar, UniformVar


@cache
def _variable_type(type_name: str) -> str:
    variable_types = {
        'choice': ChoiceVar,
        'grid': GridVar,
        'qrandint': QrandintVar,
        'quniform': QuniformVar,
        'randint': RandintVar,
        'uniform': UniformVar
    }
    try:
        return variable_types[type_name.lower()]
    except KeyError:
        raise ValueError(f"Invalid type '{type_name}'. Use one of: {', '.join(var_map)}")


class MixedVariableProblem(ContinuousVariableProblem):
    """
           Defines an optimization problem for continuous variables in APSIM simulations.

           This class enables the user to configure and solve optimization problems involving continuous
           control variables in APSIM models. It provides methods for setting up control variables,
           applying bounds and starting values, inserting variable values into APSIM model configurations,
           and running optimization routines using local solvers or differential evolution.

           Inherits from:
               ``ContinuousVariableProblem``

           Parameters:
               ``model (str):`` The name or path of the APSIM template file.
               .
               ``simulation (str or list, optional)``: The name(s) of the APSIM simulation(s) to target.
                                                   Defaults to all simulations.

               ``control_vars`` (list, optional): A list of VarDesc instances defining variable metadata.

               ``labels (list, optional)``: Variable labels for display and results tracking.

               ``cache_size (int):`` Maximum number of results to store in the evaluation cache.

           Attributes:
               ``model (str):`` The APSIM model template file name.
               ``simulation (str):`` Target simulation(s).
               ``controls (list):`` Defined control variables.
               ``control_vars (list):`` List of VarDesc instances for optimization.
               ``labels (list): Labels`` for variables.
               ``pbar (tqdm):`` Progress bar instance.
               ```cache (bool):`` Whether to cache evaluation results.
               ```cache_size (int):`` Size of the local cache.

           Methods:
               ``add_control(...):`` Add a new control variable to the optimization problem.
               ``bounds:`` Return the bounds for all control variables as a tuple.
               ``starting_values():`` Return the initial values for all control variables.
               ``minimize_with_local_solver(...):`` Optimize using `scipy.optimize.minimize`.
               ``optimize_with_differential_evolution(...):`` Optimize using `scipy.optimize.differential_evolution`.
               ``_open_pbar(labels, maxiter):`` Open a progress bar.
               ``_close_pbar():`` Close the progress bar.

           Example:
               >>> class Problem(ContinuousVariableProblem):
               ...     def evaluate(self, x):
               ...         return -self.run(verbose=False).results.Yield.mean()

               >>> problem = Problem(model="Maize", simulation="Sim")
               >>> problem.add_control("Manager", "Sow using a rule", "Population", int, 5, bounds=[2, 15])
               >>> result = problem.minimize_with_local_solver(method='Powell')
               >>> print(result.x_vars)
           """

    def __init__(self, model: str,
                 simulation=SIMULATIONS,
                 controls=None,
                 control_vars=None,

                 func=None,
                 cache_size=400):

        # Initialize parent classes explicitly
        AbstractProblem.__init__(self, model, simulation)
        self.model = model
        self.simulation = simulation if simulation is not SIMULATIONS else 'all'
        self.controls = controls or []
        self.control_vars = control_vars or []
        self.labels = []
        self.cache = False
        self.cache_size = cache_size
        self.max_cache_size = cache_size
        self.pbar = None

    def add_control(
            self,
            model_type,
            model_name,
            parameter_name,
            vtype,
            start_value,
            bounds=None,
            categories=None,
            values=None,
            q=None, **kwargs
    ) -> "MixedVariableProblem":
        """
        Adds a control variable to the optimization problem. Under the hood, the variables are edited using ``edit_method``.
        So, take note of the similarities in the requested parameters

        Parameters:
            ``model_type (str)``: APSIM model type (e.g., 'Manager').
            ``model_name (str)``: Name of the model instance.
            ``parameter_name (str)``: Name of the parameter to control.
            ``vtype (type)``: Variable type class (e.g., 'choice, grid, qrandint, quniform, randint, uniform'
           ).
            ``start_value``: Initial value for the variable.
            ``bounds (tuple, optional)``: Lower and upper bounds for numeric variables.
            ``categories (list, optional)``: Category names for categorical variables.
            ``values (list, optional)``: Grid values for GridVar.
            ``q (float, optional)``: Quantization value for quantized variables.

        Returns:
            self: Enables method chaining.
        """

        self._evaluate_args(model_type, model_name, parameter_name, vtype)

        label = f"{parameter_name}"
        vtype_cls = _variable_type(vtype)

        if vtype_cls == ChoiceVar:
            _vtype = ChoiceVar(categories=categories)
        elif vtype_cls == GridVar:
            _vtype = GridVar(values)
        elif vtype_cls == QuniformVar:
            if not bounds or q is None:
                raise ValueError("QuniformVar requires bounds and q.")
            _vtype = QuniformVar(lower=bounds[0], upper=bounds[1], q=q)
        elif vtype_cls == RandintVar:
            if not bounds:
                raise ValueError("RandintVar requires bounds.")
            _vtype = RandintVar(lower=bounds[0], upper=bounds[1])
        elif vtype_cls == QrandintVar:
            if not bounds or q is None:
                raise ValueError("QrandintVar requires bounds and q.")
            _vtype = QrandintVar(lower=bounds[0], upper=bounds[1], q=q)
        elif vtype_cls == UniformVar:
            _vtype = UniformVar(lower=bounds[0], upper=bounds[1])
        else:
            raise TypeError(f"Unsupported variable type: {vtype_cls}")
        self.labels.append(label)
        self.control_vars.append(
            VarDesc(
                model_type=model_type,
                model_name=model_name,
                parameter_name=parameter_name,
                vtype=_vtype,
                label=label,
                start_value=start_value,
                bounds=bounds
            )
        )

        return self  # Enable method chaining

    def _insert_controls(self, x) -> None:

        edit = self.edit_model

        for i, varR in enumerate(self.control_vars):
            value = x[i]
            edit(
                model_type=varR.model_type,
                simulations=self.simulation,
                model_name=varR.model_name,
                cacheit=True,
                **{varR.parameter_name: value}
            )

        return x

    @property
    def _variables(self):
        var_s = []
        for index, value in enumerate(self.control_vars):
            var_s.append(value.vtype)
        return var_s

    def _set_objective_function(self, x):
        self._insert_controls(x)
        SCORE = self.evaluate()
        return SCORE

    def optimize_with_differential_evolution(self,
                                             args=(),
                                             strategy='best1bin',
                                             maxiter=1000,
                                             popsize=15,
                                             tol=0.01,
                                             mutation=(0.5, 1),
                                             recombination=0.7,
                                             rng=None,
                                             callback=None,
                                             disp=True,
                                             polish=True,
                                             init='latinhypercube',
                                             atol=0,
                                             updating='immediate',
                                             workers=1,
                                             constraints=(),
                                             x0=None,
                                             *,
                                             integrality=None,
                                             vectorized=False):
        """
        Runs differential evolution on the wrapped objective function.
        Reference: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html
        """

        try:

            self._open_pbar(labels=[l.label for l in self.control_vars])
            call_counter = {"count": 0}
            func = getattr(self, '_set_objective_function')

            def wrapped_obj(x, *args):
                call_counter["count"] += 1
                self.pbar.update(1)
                return self._set_objective_function(x)

            wrapped = Objective(
                func=wrapped_obj,
                variables=self._variables
            )

            bounds = wrapped.bounds

            # Handle initial guess
            initial_guess = self.starting_values()

            encoded_initial = wrapped.encode(initial_guess)

            # Run optimization
            result = differential_evolution(
                wrapped,
                bounds=wrapped.bounds,
                args=args,
                strategy=strategy,
                maxiter=maxiter,
                popsize=10,
                tol=tol,
                mutation=mutation,
                recombination=recombination,
                seed=0,
                disp=disp,
                polish=polish,
                init=init,
                atol=atol,
                updating='deferred',
                workers=workers,
                constraints=constraints,
                x0=encoded_initial,
                integrality=integrality,
                vectorized=vectorized
            )

            # Attach a labeled solution
            decoded_solution = wrapped.decode(result.x)
            result.x_vars = dict(zip(self.labels, decoded_solution))
            self.outcomes = result
            return result

        finally:
            self.clear_cache()
            self._close_pbar()

    def minimize_with_local_solver(self, **kwargs):
        """
            Run a local optimization solver (e.g., Powell, L-BFGS-B, etc.) on given defined problem.

            This method wraps ``scipy.optimize.minimize`` and handles mixed-variable encoding internally
            using the `Objective` wrapper from ``wrapdisc``. It supports any method supported by SciPy's
            `minimize` function and uses the encoded starting values and variable bounds. This decoding implies that you can optimize categorical variable such as start dates or
            cultivar paramter with xy numerical values.

            Progress is tracked using a progress bar, and results are automatically decoded and stored
            in ``self.outcomes``.

            Parameters:
                **kwargs: Keyword arguments passed directly to `scipy.optimize.minimize`.
                          Important keys include:
                            - ``method (str)``: Optimization algorithm (e.g., 'Powell', 'L-BFGS-B').
                            - ``options (dict)``: Dictionary of solver options like maxiter, disp, etc.
        scipy.optimize.minimize provide a number of optimization algorithms see table below or for details check their website:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html#scipy.optimize.minimize

        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
        | Method           | Type                   | Gradient Required | Handles Bounds | Handles Constraints | Notes                                        |
        +==================+========================+===================+================+=====================+==============================================+
        | Nelder-Mead      | Local (Derivative-free)| No                | No             | No                  | Simplex algorithm                            |
        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
        | Powell           | Local (Derivative-free)| No                | Yes            | No                  | Direction set method                         |
        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
        | CG               | Local (Gradient-based) | Yes               | No             | No                  | Conjugate Gradient                           |
        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
        | BFGS             | Local (Gradient-based) | Yes               | No             | No                  | Quasi-Newton                                 |
        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
        | Newton-CG        | Local (Gradient-based) | Yes               | No             | No                  | Newton's method                              |
        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
        | L-BFGS-B         | Local (Gradient-based) | Yes               | Yes            | No                  | Limited memory BFGS                          |
        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
        | TNC              | Local (Gradient-based) | Yes               | Yes            | No                  | Truncated Newton                             |
        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
        | COBYLA           | Local (Derivative-free)| No                | No             | Yes                 | Constrained optimization by linear approx.   |
        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
        | SLSQP            | Local (Gradient-based) | Yes               | Yes            | Yes                 | Sequential Least Squares Programming         |
        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
        | trust-constr     | Local (Gradient-based) | Yes               | Yes            | Yes                 | Trust-region constrained                     |
        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
        | dogleg           | Local (Gradient-based) | Yes               | No             | No                  | Requires Hessian                             |
        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
        | trust-ncg        | Local (Gradient-based) | Yes               | No             | No                  | Newton-CG trust region                       |
        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
        | trust-exact      | Local (Gradient-based) | Yes               | No             | No                  | Trust-region, exact Hessian                  |
        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+
        | trust-krylov     | Local (Gradient-based) | Yes               | No             | No                  | Trust-region, Hessian-free                   |
        +------------------+------------------------+-------------------+----------------+---------------------+----------------------------------------------+

            Returns:
                result (OptimizeResult): The result of the optimization, with an additional
                                         `x_vars` attribute that provides a labeled dict of optimized
                                         control variable values.

            Raises:
                Any exceptions raised by `scipy.optimize.minimize`.

            Example:
            --------
            The following example shows how to use this method, the evaluation is very basic, but you
            can add a more advanced evaluation by adding a loss function e.g RMSE os NSE by comparing with the observed and predicted,
            and changing the control variables::

            class Problem(MixedVariableProblem):
                def __init__(self, model=None, simulation='Simulation'):
                    super().__init__(model, simulation)
                    self.simulation = simulation

                def evaluate(self, x, **kwargs):
                    # All evlauations can be defined inside here, by taking into accound the fact that the results object returns a data frame
                    # Also, you can specify the database table or report name holding the ``results``
                    return -self.run(verbose=False).results.Yield.mean() # A return is based on your objective definition, but as I said this could a ``RRMSE`` error or any other loss function

            # now we are ready to initialise the problem
            >>> problem = Problem(model="Maize", simulation="Simulation")
            >>> problem.add_control("Manager", "Sow using a variable rule", "Population", vtype="grid",
            ...                     start_value=5, values=[5, 9, 11])
            >>> problem.add_control("Manager", "Sow using a variable rule", "RowSpacing", vtype="grid",
            ...                     start_value=400, values=[400, 800, 1200])
            >>> result = problem.minimize_with_local_solver(method="Powell")
            >>> print(result.x_vars)
            {'Population': 11, 'RowSpacing': 800}
            """
        try:

            self._open_pbar(labels=[i.label for i in self.control_vars])
            call_counter = {"count": 0}

            def wrapped_obj(x, *args):
                call_counter["count"] += 1
                self.pbar.update(1)
                return self._set_objective_function(x)

            wrapped = Objective(
                func=wrapped_obj,
                variables=self._variables
            )

            bounds = wrapped.bounds

            # Handle initial guess
            initial_guess = self.starting_values()

            encoded_initial = wrapped.encode(initial_guess)

            result = minimize(wrapped, x0=encoded_initial, bounds=bounds, **kwargs)

            # Attach labeled solution
            decoded_solution = wrapped.decode(result.x)
            result.x_vars = dict(zip(self.labels, decoded_solution))
            self.outcomes = result
            return result

        finally:
            self.clear_cache()
            self._close_pbar()


if __name__ == "__main__":
    maize_model = "Maize"


    class Problem(MixedVariableProblem):
        def __init__(self, model=None, simulation='Simulation'):
            super().__init__(model, simulation)
            self.simulation = simulation

        def evaluate(self, **kwargs):
            return -self.run(verbose=False).results.Yield.mean()


    problem = Problem(maize_model, simulation='Simulation')
    problem.add_control('Manager', "Sow using a variable rule", 'Population', vtype='grid',
                        start_value=5, values=[2, 11, 12.5, 12, 10, 13, 5, 15])
    problem.add_control('Manager', "Sow using a variable rule", 'RowSpacing', vtype='grid', start_value=400,
                        values=[400, 600, 750, 800, 900, 1000, 1100, 1200])
    # de_res = problem.optimize_with_differential_evolution()
    res = problem.minimize_with_local_solver(method='Powell', )
    de = problem.optimize_with_differential_evolution(popsize=20, polish =True)
