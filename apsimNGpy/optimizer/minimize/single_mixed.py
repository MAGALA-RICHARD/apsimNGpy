import subprocess
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from apsimNGpy.settings import logger
from apsimNGpy.optimizer._one_obj import SING_OBJ_MIXED_VAR
from scipy.optimize import minimize, differential_evolution, NonlinearConstraint

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

            """
        try:


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
            objective = self.problem_desc.evaluate_objective()
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

        Reference:
            https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html
        """

        wrapped_obj, x0, bounds = self._submit_objective()
        initial_guess = self.problem_desc.start_values

        if disp:
            logger.info(f"[DE] Starting optimization with {len(bounds)} variables,\n mutation: {mutation}," \
                        f" seed={seed}, popsize={popsize}, strategy: {strategy}, starting values: {initial_guess}")
        select_process = ThreadPoolExecutor if use_threads else ProcessPoolExecutor
        if workers > 1:
            updating = 'deferred'
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
        assert popsize > 4, 'popsize must be greater than at least 5'
        with select_process(max_workers=workers) as executor:
            result = differential_evolution(
                wrapped_obj,
                bounds=bounds,
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
                workers=executor.map,
                constraints=constraints,
                x0=x0,
                integrality=integrality,
                vectorized=vectorized,
            )

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

    # _______________________________________
    # use cases
    # ---------------------------------------
    from apsimNGpy.tests.unittests.test_factory import obs
    from optimizer.problems.smp import MixedProblem

    mp = MixedProblem(model='Maize', trainer_dataset=obs, pred_col='Yield', metric='RRMSE', table='Report',
                      index='year', trainer_col='observed')

    mp.submit_factor(**fom_params)
    #mp.submit_factor(**cultivar_param)
    minim = MixedVariableOptimizer(problem=mp)
    print(mp.n_factors, 'factors submitted')
    # min.minimize_with_de(workers=3, updating='deferred')
    # minim.minimize_with_alocal_solver(method='Nelder-Mead')
    res = minim.minimize_with_de(use_threads=True, updating='deferred', workers=15, popsize=10, constraints=(0, 0.2))
    print(res)
    out = minim.minimize_with_local()
    print(out)
