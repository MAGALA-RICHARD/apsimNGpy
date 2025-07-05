import subprocess

from apsimNGpy.optimizer._one_obj import ContVarProblem, SING_OBJ_CONT_VAR, SING_OBJ_MIXED_VAR
from apsimNGpy.optimizer._mixed import MixedVarProblem
from scipy.optimize import minimize, differential_evolution

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

class ContinuousVariable(ContVarProblem):
    def __init__(self, apsim_model: 'apsimNGpy.core.apsim.ApsimModel', max_cache_size:int=400, objectives:list=None, decision_vars:list=None):
        # Initialize parent classes explicitly
        ContVarProblem.__init__(self, apsim_model, max_cache_size, objectives, decision_vars)
        self.model = apsim_model
        self.decision_vars = decision_vars or []
        self.objectives = objectives

        self.cache = True
        self.cache_size = max_cache_size
        self.pbar = None
        self.counter = 0
        self.maxiter = 0

    def optimimization_type(self):
        return SING_OBJ_CONT_VAR

    def minimize_with_a_local_solver(self, **kwargs):
        """
        Run a local optimization solver using `scipy.optimize.minimize`.

        This method wraps ``scipy.optimize.minimize`` to solve APSIM optimization problems
        defined using APSIM control variables and variable encodings. It tracks optimization progress via a progress bar,
        and decodes results into user-friendly labeled dictionaries.

        Optimization methods avail
        able in `scipy.optimize.minimize` include:

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

        Reference:

        https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html#scipy.optimize.minimize.

        Parameters::

        **kwargs:

            Arbitrary keyword arguments passed to `scipy.optimize.minimize`, such as:

            - ``method (str)``: The optimization method to use.

            - ``options (dict)``: Solver-specific options like `disp`, `maxiter`, `gtol`, etc.

            - ``bounds (list of tuple)``: Variable bounds; defaults to self.bounds if not provided.

            - ``x0 (list):`` Optional starting guess (will override default provided values with ``add_control_var`` starting values).

        Returns:
            result (OptimizeResult):
                The optimization result object with the following additional field:
                - result.x_vars (dict): A dictionary of variable labels and optimized values.

        Example::

          from apsimNGpy.optimizer.one_objective import ContVarProblem
          class Problem(ContVarProblem):
                def __init__(self, model=None, simulation='Simulation'):
                    super().__init__(model, simulation)
                    self.simulation = simulation
                def evaluate(self, x, **kwargs):
                   return -self.run(verbose=False).results.Yield.mean()

          problem = Problem(model="Maize", simulation="Sim")
          problem.add_control("Manager", "Sow using a rule", "Population", vtype="grid",
                                start_value=5, values=[5, 9, 11])
          problem.add_control("Manager", "Sow using a rule", "RowSpacing", vtype="grid",
                                start_value=400, values=[400, 800, 1200])
          result = problem.minimize_with_local_solver(method='Powell', options={"maxiter": 300})
          print(result.x_vars)
          {'Population': 9, 'RowSpacing': 800}
        """
        self.optimizer = self.minimize_with_a_local_solver.__name__
        try:
            x0 = kwargs.pop("x0", [1] * len(self.decision_vars))
            if 'bounds' not in kwargs.keys():
                kwargs['bounds'] = self.bounds
            max_iter = kwargs.get("options", {}).get("maxiter", 400)

            self._open_pbar(self.labels, maxiter=max_iter)
            call_counter = {"count": 0}
            def wrapped_obj(x):
                call_counter["count"] += 1
                self.pbar.update(1)
                #pbar.set_postfix({"score": round(self._last_score, 2)})
                return self._set_objective_function(x)

            result = minimize(wrapped_obj, x0=self.starting_values(), **kwargs)
            result.x_vars = dict(zip(self.labels, result.x))
            self.outcomes = result
            return result
        finally:
            self._close_pbar()
            self.clear_cache()

    def optimization_type(self):
        return SING_OBJ_CONT_VAR
    def minimize_with_de(self, args=(), strategy='best1bin',
                                             maxiter=1000, popsize=15,
                                             tol=0.01, mutation=(0.5, 1), recombination=0.7,
                                             rng=None, callback=None,
                                             disp=True, polish=True,
                                             init='latinhypercube', atol=0,
                                             updating='immediate', workers=1,
                                             constraints=(), x0=None, *,
                                             integrality=None, vectorized=False):
        """

        reference; https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html
        """

        try:

            self.maxiter = maxiter
            self._open_pbar(self.labels, maxiter=maxiter)
            self.update_pbar(self.labels, extend_by=50)
            call_counter = {"count": 0}


            def wrapped_obj(x):
                lm =maxiter
                call_counter["count"] += 1
                xc  =  call_counter["count"]
                self.counter = xc
                if xc > maxiter:
                    lm +=1

                self.update_pbar(self.labels, extend_by=50)
                self.pbar.update(1)
                #pbar.set_postfix({"score": round(self._last_score, 2)})
                return self._set_objective_function(x)

            result = differential_evolution(wrapped_obj, self.bounds, args=(), strategy='best1bin',
                                      maxiter=maxiter, popsize=popsize, tol=tol,
                                      mutation=mutation, recombination=recombination,
                                       callback=callback, disp=disp,
                                      polish=polish, init=init,
                                      atol=atol, updating=updating,
                                      workers=workers, constraints=constraints)

            result.x_vars = dict(zip(self.labels, result.x))
            self.outcomes =result
            return result
        finally:
            self._close_pbar()
            self.clear_cache()

class MixedVariable(MixedVarProblem):
    def __init__(self, apsim_model: 'ApsimNGpy.Core.Model', max_cache_size=400, objectives=None, decision_vars=None):
        # Initialize parent classes explicitly
        MixedVarProblem.__init__(self, apsim_model=apsim_model, max_cache_size=max_cache_size, objectives =objectives, decision_vars=decision_vars)
        self.model = apsim_model
        self.decision_vars = decision_vars or []
        self.objectives = objectives

        self.cache = True
        self.cache_size = max_cache_size
        self.pbar = None
        self.counter = 0
        self.maxiter = 0
    def minimize_with_alocal_solver(self, **kwargs):
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

            class Problem(MixedVarProblem):
                def __init__(self, model=None, simulation='Simulation'):
                    super().__init__(model, simulation)
                    self.simulation = simulation

                def evaluate(self, x, **kwargs):
                    # All evlauations can be defined inside here, by taking into accound the fact that the results object returns a data frame
                    # Also, you can specify the database table or report name holding the ``results``
                    return -self.run(verbose=False).results.Yield.mean() # A return is based on your objective definition, but as I said this could a ``RRMSE`` error or any other loss function

            # Ready to initialise the problem

            .. code-block:: python

                 problem.add_control(
                    path='.Simulations.Simulation.Field.Fertilise at sowing',
                    Amount="?",
                    bounds=[50, 300],
                    v_type="float",
                    start_value =50
                 )

                problem.add_control(
                    path='.Simulations.Simulation.Field.Sow using a variable rule',
                    Population="?",
                    bounds=[4, 14],
                    v_type="float",
                    start_value=5
                )

            """
        try:

            self._open_pbar(labels= self.labels)
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

    def minimize_with_de(self,
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
                                             seed =1,
                                             *,
                                             integrality=None,
                                             vectorized=False):
        """
        Runs differential evolution on the wrapped objective function.
        Reference: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html
        """

        try:

            self._open_pbar(labels=self.labels)
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
                popsize=popsize,
                tol=tol,
                mutation=mutation,
                recombination=recombination,
                seed=seed,
                disp=disp,
                polish=polish,
                init=init,
                atol=atol,
                updating=updating,
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

    def optimization_type(self):
        return SING_OBJ_MIXED_VAR

    # tests
