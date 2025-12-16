import subprocess
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from apsimNGpy.settings import logger
from apsimNGpy.optimizer._one_obj import SING_OBJ_MIXED_VAR
from scipy.optimize import minimize, differential_evolution, NonlinearConstraint
from tqdm import tqdm

__all__ = ['MixedVariableOptimizer']
try:
    import wrapdisc
except ModuleNotFoundError as mnf:
    print('installing wrapdisc package')
    package_name = "wrapdisc"
    command = ["pip", "install", package_name]
    # Running the command
    subprocess.run(command, check=True)

from wrapdisc.var import UniformVar


class MixedVariableOptimizer:
    def __init__(self, problem):
        """
        @param problem:
        """

        self.results = None
        self.outcomes = None
        self.problem_desc = problem
        self.pbar = None
        self.counter = 0
        self.maxiter = 0
        # Ensure setup
        if not hasattr(self, "problem_desc"):
            raise AttributeError("problem_desc must be initialized before calling minimize_with_de")

    def minimize_with_alocal_solver(self, **kwargs):
        return self.minimize_with_local(**kwargs)

    def minimize_with_local(self, **kwargs):
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

            # Ready to initialize the problem

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
             Attributes of the returned object
            ------------------------------------
            x : ndarray
                The solution of the optimization.
            success : bool
                Whether or not the optimizer exited successfully.
            status : int
                Termination status of the optimizer. Its value depends on the
                underlying solver. Refer to `message` for details.
            message : str
                Description of the cause of the termination.
            fun, jac, hess: ndarray
                Values of objective function, its Jacobian and its Hessian (if
                available). The Hessians may be approximations, see the documentation
                of the function in question.
            hess_inv : object
                Inverse of the objective function's Hessian; may be an approximation.
                Not available for all solvers. The type of this attribute may be
                either np.ndarray or scipy.sparse.linalg.LinearOperator.
            nfev, njev, nhev : int
                Number of evaluations of the objective functions and of its
                Jacobian and Hessian.
            nit : int
                Number of iterations performed by the optimizer.
            maxcv : float
                The maximum constraint violation.
            data: DataFrame
                 This DataFrame represents the index columns, with the predicted and observed values

            Notes
            -----
            Depending on the specific solver being used, `OptimizeResult` may
            not have all attributes listed here, and they may have additional
            attributes not listed here. Since this class is essentially a
            subclass of dict with attribute accessors, one can see which
            attributes are available using the `OptimizeResult.keys` method.
            """
        try:
            options = kwargs.get('options')
            if options:
                maxiter = options.get('maxiter', self.problem_desc.n_factors * 200)
            else:
                maxiter = self.problem_desc.n_factors * 200

            pbar = tqdm(total=maxiter)

            def callback(xk):
                pbar.update(1)

            kwargs.setdefault('callback', callback)
            wrapped_obj, x0, bounds = self._submit_objective()
            # Handle initial guess
            initial_guess = self.problem_desc.start_values
            kwargs.setdefault("method", 'Nelder-Mead')
            logger.info(
                f"[{kwargs.get('method')}] Starting optimization with {len(bounds)} variables,\n initial values: {initial_guess}")
            result = minimize(wrapped_obj, x0=x0, bounds=bounds, **kwargs)

            result = self._extract_solution(result)
            return result

        finally:
            pass

    def _submit_objective(self):
        if not self.problem_desc._detect_pure_vars():
            objective = self.problem_desc.wrap_objectives()
            initial_guess = self.problem_desc.start_values
            bounds = objective.bounds
            # Prepare initial population if given
            x0 = objective.encode(initial_guess) if initial_guess is not None else None

        else:
            objective = self.problem_desc.evaluate_objectives
            bounds = self.problem_desc.bounds
            x0 = self.problem_desc.start_values
        return objective, x0, bounds

    def _extract_solution(self, result):
        wrapped_obj = self._submit_objective()
        if not self.problem_desc._detect_pure_vars():
            decoded_solution = wrapped_obj[0].decode(result.x)
            result.x_vars = dict(zip(self.problem_desc.var_names, decoded_solution))
            result.x = decoded_solution

        self.outcomes = result
        self.problem_desc.plug_optimal_values(result)
        return result

    def minimize_with_de(
            self,
            use_threads=False,
            args=(),
            strategy='rand1bin',  # 'rand1bin' is the canonical baseline DE variant described in Storn & Price (1997).
            maxiter=1000,
            popsize=None,
            tol=0.01,
            mutation=(0.5, 1),
            recombination=0.9,
            rng=None,
            callback=None,
            disp=True,
            polish=True,
            init='latinhypercube',
            atol=0,
            updating='deffered',
            workers=1,
            constraints=(),
            x0=None,  # implimented internally
            seed=1,
            *,
            integrality=None,
            vectorized=False,
    ):
        """
        Run differential evolution on the wrapped APSIM objective function.
        Finds the global minimum of a multivariate function.

        The differential evolution method [1]_ is stochastic in nature. It does
        not use gradient methods to find the minimum, and can search large areas
        of candidate space, but often requires larger numbers of function
        evaluations than conventional gradient-based techniques.

        The algorithm is due to Storn and Price [2]_.

        Parameters
        ----------
        func : callable
            The objective function to be minimized. Must be in the form
            ``f(x, *args)``, where ``x`` is the argument in the form of a 1-D array
            and ``args`` is a tuple of any additional fixed parameters needed to
            completely specify the function. The number of parameters, N, is equal
            to ``len(x)``.
        bounds : sequence or `Bounds`
            Bounds for variables. There are two ways to specify the bounds:

                1. Instance of `Bounds` class.
                2. ``(min, max)`` pairs for each element in ``x``, defining the
                   finite lower and upper bounds for the optimizing argument of
                   `func`.

            The total number of bounds is used to determine the number of
            parameters, N. If there are parameters whose bounds are equal the total
            number of free parameters is ``N - N_equal``.

        args : tuple, optional
            Any additional fixed parameters needed to
            completely specify the objective function.
        strategy : {str, callable}, optional
            The differential evolution strategy to use. Should be one of:

                - 'best1bin'
                - 'best1exp'
                - 'rand1bin'
                - 'rand1exp'
                - 'rand2bin'
                - 'rand2exp'
                - 'randtobest1bin'
                - 'randtobest1exp'
                - 'currenttobest1bin'
                - 'currenttobest1exp'
                - 'best2exp'
                - 'best2bin'

            The default is 'best1bin'. Strategies that may be implemented are
            outlined in 'Notes'.
            Alternatively the differential evolution strategy can be customized by
            providing a callable that constructs a trial vector. The callable must
            have the form ``strategy(candidate: int, population: np.ndarray, rng=None)``,
            where ``candidate`` is an integer specifying which entry of the
            population is being evolved, ``population`` is an array of shape
            ``(S, N)`` containing all the population members (where S is the
            total population size), and ``rng`` is the random number generator
            being used within the solver.
            ``candidate`` will be in the range ``[0, S)``.
            ``strategy`` must return a trial vector with shape `(N,)`. The
            fitness of this trial vector is compared against the fitness of
            ``population[candidate]``.

            .. versionchanged:: 1.12.0
                Customization of evolution strategy via a callable.

        maxiter : int, optional
            The maximum number of generations over which the entire population is
            evolved. The maximum number of function evaluations (with no polishing)
            is: ``(maxiter + 1) * popsize * (N - N_equal)``
        popsize : int, optional
            A multiplier for setting the total population size. The population has
            ``popsize * (N - N_equal)`` individuals. This keyword is overridden if
            an initial population is supplied via the `init` keyword. When using
            ``init='sobol'`` the population size is calculated as the next power
            of 2 after ``popsize * (N - N_equal)``.
        tol : float, optional
            Relative tolerance for convergence, the solving stops when
            ``np.std(pop) <= atol + tol * np.abs(np.mean(population_energies))``,
            where and `atol` and `tol` are the absolute and relative tolerance
            respectively.
        mutation : float or tuple(float, float), optional
            The mutation constant. In the literature this is also known as
            differential weight, being denoted by F.
            If specified as a float it should be in the range [0, 2].
            If specified as a tuple ``(min, max)`` dithering is employed. Dithering
            randomly changes the mutation constant on a generation by generation
            basis. The mutation constant for that generation is taken from
            ``U[min, max)``. Dithering can help speed convergence significantly.
            Increasing the mutation constant increases the search radius, but will
            slow down convergence.
        recombination : float, optional
            The recombination constant, should be in the range [0, 1]. In the
            literature this is also known as the crossover probability, being
            denoted by CR. Increasing this value allows a larger number of mutants
            to progress into the next generation, but at the risk of population
            stability.
        seed : {None, int, `numpy.random.Generator`, `numpy.random.RandomState`}, optional
            If `seed` is None (or `np.random`), the `numpy.random.RandomState`
            singleton is used.
            If `seed` is an int, a new ``RandomState`` instance is used,
            seeded with `seed`.
            If `seed` is already a ``Generator`` or ``RandomState`` instance then
            that instance is used.
            Specify `seed` for repeatable minimizations.
        disp : bool, optional
            Prints the evaluated `func` at every iteration.
        callback : callable, optional
            A callable called after each iteration. Has the signature:

                ``callback(intermediate_result: OptimizeResult)``

            where ``intermediate_result`` is a keyword parameter containing an
            `OptimizeResult` with attributes ``x`` and ``fun``, the best solution
            found so far and the objective function. Note that the name
            of the parameter must be ``intermediate_result`` for the callback
            to be passed an `OptimizeResult`.

            The callback also supports a signature like:

                ``callback(x, convergence: float=val)``

            ``val`` represents the fractional value of the population convergence.
            When ``val`` is greater than ``1.0``, the function halts.

            Introspection is used to determine which of the signatures is invoked.

            Global minimization will halt if the callback raises ``StopIteration``
            or returns ``True``; any polishing is still carried out.

            .. versionchanged:: 1.12.0
                callback accepts the ``intermediate_result`` keyword.

        polish : bool, optional
            If True (default), then `scipy.optimize.minimize` with the `L-BFGS-B`
            method is used to polish the best population member at the end, which
            can improve the minimization slightly. If a constrained problem is
            being studied then the `trust-constr` method is used instead. For large
            problems with many constraints, polishing can take a long time due to
            the Jacobian computations.
        init : str or array-like, optional
            Specify which type of population initialization is performed. Should be
            one of:

                - 'latinhypercube'
                - 'sobol'
                - 'halton'
                - 'random'
                - array specifying the initial population. The array should have
                  shape ``(S, N)``, where S is the total population size and N is
                  the number of parameters.
                  `init` is clipped to `bounds` before use.

            The default is 'latinhypercube'. Latin Hypercube sampling tries to
            maximize coverage of the available parameter space.

            'sobol' and 'halton' are superior alternatives and maximize even more
            the parameter space. 'sobol' will enforce an initial population
            size which is calculated as the next power of 2 after
            ``popsize * (N - N_equal)``. 'halton' has no requirements but is a bit
            less efficient. See `scipy.stats.qmc` for more details.

            'random' initializes the population randomly - this has the drawback
            that clustering can occur, preventing the whole of parameter space
            being covered. Use of an array to specify a population could be used,
            for example, to create a tight bunch of initial guesses in an location
            where the solution is known to exist, thereby reducing time for
            convergence.
        atol : float, optional
            Absolute tolerance for convergence, the solving stops when
            ``np.std(pop) <= atol + tol * np.abs(np.mean(population_energies))``,
            where and `atol` and `tol` are the absolute and relative tolerance
            respectively.
        updating : {'immediate', 'deferred'}, optional
            If ``'immediate'``, the best solution vector is continuously updated
            within a single generation [4]_. This can lead to faster convergence as
            trial vectors can take advantage of continuous improvements in the best
            solution.
            With ``'deferred'``, the best solution vector is updated once per
            generation. Only ``'deferred'`` is compatible with parallelization or
            vectorization, and the `workers` and `vectorized` keywords can
            over-ride this option.

            .. versionadded:: 1.2.0

        workers : int or map-like callable, optional
            If `workers` is an int the population is subdivided into `workers`
            sections and evaluated in parallel
            (uses `multiprocessing.Pool <multiprocessing>`).
            Supply -1 to use all available CPU cores.
            Alternatively supply a map-like callable, such as
            `multiprocessing.Pool.map` for evaluating the population in parallel.
            This evaluation is carried out as ``workers(func, iterable)``.
            This option will override the `updating` keyword to
            ``updating='deferred'`` if ``workers != 1``.
            This option overrides the `vectorized` keyword if ``workers != 1``.
            Requires that `func` be pickleable.

            .. versionadded:: 1.2.0

        constraints : {NonLinearConstraint, LinearConstraint, Bounds}
            Constraints on the solver, over and above those applied by the `bounds`
            kwd. Uses the approach by Lampinen [5]_.

            .. versionadded:: 1.4.0

        x0 : None or array-like, optional
            Provides an initial guess to the minimization. Once the population has
            been initialized this vector replaces the first (best) member. This
            replacement is done even if `init` is given an initial population.
            ``x0.shape == (N,)``.

            .. versionadded:: 1.7.0

        integrality : 1-D array, optional
            For each decision variable, a boolean value indicating whether the
            decision variable is constrained to integer values. The array is
            broadcast to ``(N,)``.
            If any decision variables are constrained to be integral, they will not
            be changed during polishing.
            Only integer values lying between the lower and upper bounds are used.
            If there are no integer values lying between the bounds then a
            `ValueError` is raised.

            .. versionadded:: 1.9.0

        vectorized : bool, optional
            If ``vectorized is True``, `func` is sent an `x` array with
            ``x.shape == (N, S)``, and is expected to return an array of shape
            ``(S,)``, where `S` is the number of solution vectors to be calculated.
            If constraints are applied, each of the functions used to construct
            a `Constraint` object should accept an `x` array with
            ``x.shape == (N, S)``, and return an array of shape ``(M, S)``, where
            `M` is the number of constraint components.
            This option is an alternative to the parallelization offered by
            `workers`, and may help in optimization speed by reducing interpreter
            overhead from multiple function calls. This keyword is ignored if
            ``workers != 1``.
            This option will override the `updating` keyword to
            ``updating='deferred'``.
            See the notes section for further discussion on when to use
            ``'vectorized'``, and when to use ``'workers'``.

            .. versionadded:: 1.9.0

        Returns
        -------
        res : OptimizeResult
            The optimization result represented as a `OptimizeResult` object.
            Important attributes are: ``x`` the solution array, ``success`` a
            Boolean flag indicating if the optimizer exited successfully,
            ``message`` which describes the cause of the termination,
            ``population`` the solution vectors present in the population, and
            ``population_energies`` the value of the objective function for each
            entry in ``population``.
            See `OptimizeResult` for a description of other attributes. If `polish`
            was employed, and a lower minimum was obtained by the polishing, then
            OptimizeResult also contains the ``jac`` attribute.
            If the eventual solution does not satisfy the applied constraints
            ``success`` will be `False`.

    Notes
    -----
    Differential evolution is a stochastic population based method that is
    useful for global optimization problems. At each pass through the
    population the algorithm mutates each candidate solution by mixing with
    other candidate solutions to create a trial candidate. There are several
    strategies [3]_ for creating trial candidates, which suit some problems
    more than others. The 'best1bin' strategy is a good starting point for
    many systems. In this strategy two members of the population are randomly
    chosen. Their difference is used to mutate the best member (the 'best' in
    'best1bin'), :math:`x_0`, so far:

    .. math::

        b' = x_0 + mutation * (x_{r_0} - x_{r_1})

    A trial vector is then constructed. Starting with a randomly chosen ith
    parameter the trial is sequentially filled (in modulo) with parameters
    from ``b'`` or the original candidate. The choice of whether to use ``b'``
    or the original candidate is made with a binomial distribution (the 'bin'
    in 'best1bin') - a random number in [0, 1) is generated. If this number is
    less than the `recombination` constant then the parameter is loaded from
    ``b'``, otherwise it is loaded from the original candidate. The final
    parameter is always loaded from ``b'``. Once the trial candidate is built
    its fitness is assessed. If the trial is better than the original candidate
    then it takes its place. If it is also better than the best overall
    candidate it also replaces that.

    The other strategies available are outlined in Qiang and
    Mitchell (2014) [3]_.

    .. math::
            rand1* : b' = x_{r_0} + mutation*(x_{r_1} - x_{r_2})

            rand2* : b' = x_{r_0} + mutation*(x_{r_1} + x_{r_2}
                                                - x_{r_3} - x_{r_4})

            best1* : b' = x_0 + mutation*(x_{r_0} - x_{r_1})

            best2* : b' = x_0 + mutation*(x_{r_0} + x_{r_1}
                                            - x_{r_2} - x_{r_3})

            currenttobest1* : b' = x_i + mutation*(x_0 - x_i
                                                     + x_{r_0} - x_{r_1})

            randtobest1* : b' = x_{r_0} + mutation*(x_0 - x_{r_0}
                                                      + x_{r_1} - x_{r_2})

    where the integers :math:`r_0, r_1, r_2, r_3, r_4` are chosen randomly
    from the interval [0, NP) with `NP` being the total population size and
    the original candidate having index `i`. The user can fully customize the
    generation of the trial candidates by supplying a callable to ``strategy``.

    To improve your chances of finding a global minimum use higher `popsize`
    values, with higher `mutation` and (dithering), but lower `recombination`
    values. This has the effect of widening the search radius, but slowing
    convergence.

    By default the best solution vector is updated continuously within a single
    iteration (``updating='immediate'``). This is a modification [4]_ of the
    original differential evolution algorithm which can lead to faster
    convergence as trial vectors can immediately benefit from improved
    solutions. To use the original Storn and Price behaviour, updating the best
    solution once per iteration, set ``updating='deferred'``.
    The ``'deferred'`` approach is compatible with both parallelization and
    vectorization (``'workers'`` and ``'vectorized'`` keywords). These may
    improve minimization speed by using computer resources more efficiently.
    The ``'workers'`` distribute calculations over multiple processors. By
    default the Python `multiprocessing` module is used, but other approaches
    are also possible, such as the Message Passing Interface (MPI) used on
    clusters [6]_ [7]_. The overhead from these approaches (creating new
    Processes, etc) may be significant, meaning that computational speed
    doesn't necessarily scale with the number of processors used.
    Parallelization is best suited to computationally expensive objective
    functions. If the objective function is less expensive, then
    ``'vectorized'`` may aid by only calling the objective function once per
    iteration, rather than multiple times for all the population members; the
    interpreter overhead is reduced.

    .. versionadded:: 0.15.0


        Reference:
            https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html
        """

        wrapped_obj, x0, bounds = self._submit_objective()
        initial_guess = self.problem_desc.start_values

        if disp:
            logger.info(f"[DE] Starting optimization with {len(bounds)} variables,\n mutation: {mutation}," \
                        f" seed={seed}, popsize={popsize}, strategy: {strategy}, starting values: {initial_guess}")
        from tqdm.contrib.concurrent import thread_map
        from tqdm.contrib.concurrent import process_map

        if isinstance(constraints, tuple) and constraints:
            if len(constraints) != 2:
                raise ValueError(f"constraints must be a tuple of length 2, got {len(constraints)}")
            upper_constraint = constraints[1]
            lower_constraint = constraints[0]

            if upper_constraint < lower_constraint:
                raise ValueError(
                    f'Upper constraint `{upper_constraint}` at index 1 is less than the lower constraint `{lower_constraint}` at index 0')
            constraints = self.problem_desc.define_nlc(lower_constraint, upper_constraint, )
        popsize = popsize or self.problem_desc.n_factors * 10
        if popsize < 4:
            logger.error(f"[DE] Population size {popsize}, is too loo")
        from tqdm import tqdm

        pbar = tqdm(total=maxiter)
        x=1
        if not callback:
            def callback(xk, convergence):
                print(xk)
                pbar.update(1)

        arguments = dict(bounds=bounds, args=args, strategy=strategy,
                         maxiter=maxiter, popsize=popsize, tol=tol, mutation=mutation,
                         recombination=recombination, seed=seed, disp=disp,
                         polish=polish, init=init,
                         atol=atol,updating=updating,callback=callback,
                         workers=1,constraints=constraints, x0=x0, integrality=integrality,
                         vectorized=vectorized,
                         )
        if workers == 1:
            result = differential_evolution(
                wrapped_obj,
                **arguments)
        else:
            select_process = ThreadPoolExecutor if use_threads else ProcessPoolExecutor
            updating = 'deferred'
            with select_process(max_workers=workers) as executor:
                workers = executor.map
                arguments['workers'] = workers
                arguments['updating'] = updating
                result = differential_evolution(
                    wrapped_obj,
                    **arguments)

        return self._extract_solution(result)

    def optimization_type(self):
        return SING_OBJ_MIXED_VAR

    # tests


if __name__ == '__main__':
    from apsimNGpy.optimizer.problems.variables import QrandintVar

    # define all factors under main if more than one process will be involved
    fom_params = {
        "path": ".Simulations.Simulation.Field.Soil.Organic",
        "vtype": ['continuous(1, 500)', 'continuous(0.02, 0.06)'],
        "start_value": [100, 0.021],
        "candidate_param": ["FOM", 'FBiom'],
        "other_params": {"Carbon": 1.2},
    }
    cultivar_param = {
        "path": ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82",
        "vtype": [QrandintVar(400, 600, q=5), ],
        "start_value": [550, ],
        "candidate_param": ["[Grain].MaximumGrainsPerCob.FixedValue", ],
        "other_params": {"sowed": True},
        # other params must be on the same node or associated or extra arguments, e.g., target simulation name classified simulations
        'cultivar': True
    }
    cultivar_param_p = {
        "path": ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82",
        "start_value": [550, ],
        'bounds':[(400, 800)],
        "candidate_param": ["[Grain].MaximumGrainsPerCob.FixedValue", ],
        "other_params": {"sowed": True},
        # other params must be on the same node or associated or extra arguments, e.g., target simulation name classified simulations
        'cultivar': True
    }

    # _______________________________________
    # use cases
    # ---------------------------------------
    from apsimNGpy.tests.unittests.test_factory import obs
    from optimizer.problems.smp import MixedProblem

    mp = MixedProblem(model='Maize', trainer_dataset=obs, pred_col='Yield', metric='RRMSE', table='Report',
                      index='year', trainer_col='observed')

    mp.submit_factor(**fom_params)
    # mp.submit_factor(**cultivar_param)
    minim = MixedVariableOptimizer(problem=mp)
    print(mp.n_factors, 'factors submitted')
    # # min.minimize_with_de(workers=3, updating='deferred')
    # # minim.minimize_with_alocal_solver(method='Nelder-Mead')
    #
    # res = minim.minimize_with_de(use_threads=False, updating='deferred', workers=14, popsize=10, constraints=(0, 0.2))
    # print(res)
    # out = minim.minimize_with_local()
    # print(out)

    mp = MixedProblem(model='Maize', trainer_dataset=obs, pred_col='Yield', metric='RRMSE', table='Report',
                      index='year', trainer_col='observed')
    optimizer = MixedVariableOptimizer(problem=mp)
    mp.submit_factor(**cultivar_param_p)
    print(mp.n_factors, 'factors submitted for the pure variables')
    out = optimizer.minimize_with_local()
    print(out)
    res = optimizer.minimize_with_de(use_threads=False, updating='deferred', workers=15, popsize=10,
                                     constraints=(0, 0.2))
    print(res)
