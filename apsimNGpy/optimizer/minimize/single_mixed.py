import subprocess
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from apsimNGpy.settings import logger
from apsimNGpy.optimizer._one_obj import SING_OBJ_MIXED_VAR
from scipy.optimize import minimize, differential_evolution

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

            wrapped_obj = self.problem_desc.wrap_objectives()
            bounds = wrapped_obj.bounds

            # Handle initial guess
            initial_guess = self.problem_desc.start_values

            encoded_initial = wrapped_obj.encode(initial_guess)

            logger.info(f"[DE] Starting optimization with {len(bounds)} variables, {[*kwargs.items()]}")
            result = minimize(wrapped_obj, x0=encoded_initial, bounds=bounds, **kwargs)

            # Attach a labeled solution
            decoded_solution = wrapped_obj.decode(result.x)
            result.x_vars = dict(zip(self.problem_desc.var_names, decoded_solution))
            self.results = result
            return result

        finally:
            pass

    def minimize_with_de(
            self,
            use_threads=False,
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
            updating='deffered',
            workers=1,
            constraints=(),
            x0=None,
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

        wrapped_obj = self.problem_desc.wrap_objectives()
        initial_guess = self.problem_desc.start_values
        bounds = wrapped_obj.bounds

        # Prepare initial population if given
        x0 = wrapped_obj.encode(initial_guess) if initial_guess is not None else None

        if disp:
            logger.info(f"[DE] Starting optimization with {len(bounds)} variables, seed={seed}, popsize={popsize}")
        select_process = ThreadPoolExecutor if use_threads else ProcessPoolExecutor
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

        # Attach a labeled, decoded solution
        decoded_solution = wrapped_obj.decode(result.x)
        result.x_vars = dict(zip(self.problem_desc.var_names, decoded_solution))
        self.outcomes = result

        return result

    def optimization_type(self):
        return SING_OBJ_MIXED_VAR

    # tests


if __name__ == '__main__':
    example_param3 = {
        # one per factor
        "path": ".Simulations.Simulation.Field.Soil.Organic",
        "vtype": [UniformVar(0, 2)],
        "start_value": [1.0],
        "candidate_param": ['Carbon'],

        'other_params': {'FBiom': 0.03, "Carbon": 1.89}
    }

    if __name__ == '__main__':
        from apsimNGpy.tests.unittests.test_factory import obs
        from optimizer.problems.smp import MixedProblem
        mp = MixedProblem(model='Maize', trainer_dataset=obs, pred_col='Yield', method='ccc',
                          index='year', trainer_col='observed')
        mp.submit_factor(**example_param3)

        minim = MixedVariableOptimizer(problem=mp)
        # min.minimize_with_de(workers=3, updating='deferred')
        minim.minimize_with_alocal_solver(method='Nelder-Mead')
