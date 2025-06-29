from apsimNGpy.optimizer.base import AbstractProblem, VarDesc
from apsimNGpy.core.apsim import ApsimModel
from dataclasses import dataclass, field
from scipy.optimize import minimize, differential_evolution
import wrapdisc
from functools import cache
from apsimNGpy.core_utils.progbar import ProgressBar
from typing import Union
SIMULATIONS = object()



new_maxiter  =0
class ContinuousVariableProblem(AbstractProblem):
    """
        Defines an optimization problem for continuous variables in APSIM simulations.

        This class enables the user to configure and solve optimization problems involving continuous
        control variables in APSIM models. It provides methods for setting up control variables,
        applying bounds and starting values, inserting variable values into APSIM model configurations,
        and running optimization routines using local solvers or differential evolution.

        Inherits from:
            AbstractProblem: A base class providing caching and model-editing functionality.

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
                 labels=None,

                 func = None,
                 cache_size=400):

        # Initialize parent classes explicitly
        AbstractProblem.__init__(self, model,max_cache_size=cache_size)
        self.model = model
        self.simulation = simulation if simulation is not SIMULATIONS else 'all'
        self.controls = controls or []
        self.control_vars = control_vars or []
        self.labels = labels or []
        self.cache = True
        self.cache_size = cache_size
        self.pbar = None
        self.counter = 0
        self.maxiter = 0

    def add_control(self, model_type, model_name, parameter_name,
                    vtype, start_value, bounds=None):
        """
        Adds a continuous control variable to the optimization problem.

        This method allows the user to specify a parameter in the APSIM model
        that will be treated as a variable during optimization. It helps ensure
        that parameters are consistently defined and validated.

        Parameters
        ----------
        model_type : str
            The section of the APSIM model where the parameter resides
            (e.g., 'Manager', 'Organic', 'IPlant').

        model_name : str
            The name of the specific model or module within APSIM where the parameter
            is defined (e.g., "Sow on fixed date", "Fertiliser").

        parameter_name : str
            The name of the parameter to control (e.g., 'Population', 'Amount').

        vtype : type
            The Python type of the variable. Should be either `int` or `float` to indicate
            whether the parameter is discrete or continuous.

        start_value : int or float
            The initial value to use for the parameter in optimization routines.

        bounds : tuple of (float, float), optional
            Lower and upper bounds for the parameter (used in bounded optimization).
            Must be a tuple like (min, max). If None, the variable is considered unbounded.

        Returns
        -------
        self : object
            Returns self to support method chaining.

        Raises
        ------
        ValueError
            If the provided arguments do not pass validation via `_evaluate_args`.

        Notes
        -----
        - This method is typically used before running optimization to define which
          parameters should be tuned.
        - Only continuous variables (`int` or `float`) are supported by this method.
          Use other methods for categorical or grid variables.


        """
        _evaluate_args(model_type, model_name, parameter_name)
        label = f"{parameter_name}"
        self.control_vars.append(
            VarDesc(model_type, model_name, parameter_name, vtype, label, start_value, bounds)
        )
        return self  # Enables method chaining

    @property
    def bounds(self):
        bounds = []
        for var in self.control_vars:
            bounds.append(var.bounds)
        return tuple(bounds)

    def starting_values(self):
        starting_values = []
        for var in self.control_vars:
            starting_values.append(var.start_value)
        return tuple(starting_values)
    def _insert_controls(self, x) -> None:
        @cache
        def editable_model():
          return self.edit_model

        for i, varR in enumerate(self.control_vars):
            vtype = varR.vtype
            value = x[i]
            if vtype==int or vtype =='int':
                value = int(value)
            else:
                value = round(value, 4)
            editable_model()(
                model_type=varR.model_type,
                simulations=self.simulation,
                model_name=varR.model_name,
                cacheit=True,
                **{varR.parameter_name: value}
            )
            x[i] =value

        return x.tolist()


    def _set_objective_function(self, x):
        xl = self._insert_controls(x)
        # Try local per-instance results cache first
        if self.cache and (cached := self.get_cached(*xl)):
        # Evaluation is expensive because it involves running APSIM, so the call for caching before evaluation
               return cached

        SCORE  = self.evaluate()
        if self.cache:
            self._insert_cache_result(*xl, result=SCORE)
        self._last_score = SCORE
        return SCORE

    def minimize_with_local_solver(self, **kwargs):
        """
        Run a local optimization solver using `scipy.optimize.minimize`.

        This method wraps ``scipy.optimize.minimize`` to solve APSIM optimization problems
        defined using APSIM control variables and variable encodings. It tracks optimization progress via a progress bar,
        and decodes results into user-friendly labeled dictionaries.

        Optimization methods available in `scipy.optimize.minimize` include:

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

          from apsimNGpy.optimizer.one_objective import ContinuousVariableProblem
          class Problem(ContinuousVariableProblem):
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

        try:
            x0 = kwargs.pop("x0", [1] * len(self.control_vars))
            if 'bounds' not in kwargs.keys():
                kwargs['bounds'] = self.bounds
            max_iter = kwargs.get("options", {}).get("maxiter", 400)
            labels = [i.label for i in self.control_vars]
            self._open_pbar(labels, maxiter=max_iter)
            call_counter = {"count": 0}
            def wrapped_obj(x):
                call_counter["count"] += 1
                self.pbar.update(1)
                #pbar.set_postfix({"score": round(self._last_score, 2)})
                return self._set_objective_function(x)

            result = minimize(wrapped_obj, x0=self.starting_values(), **kwargs)
            labels = [c.label for c in self.control_vars]
            result.x_vars = dict(zip(labels, result.x))
            self.outcomes = result
            return result
        finally:
            self.pbar.close()
            self.clear_cache()

    def _open_pbar(self, labels, maxiter =400):

        #self.pbar = tqdm(total=maxiter, desc=f"Optimizing:: {', '.join(labels)}", unit=" iterations", colour="green")
        self.pbar = ProgressBar(total=maxiter, prefix=f"Optimizing:: {', '.join(labels)}", suffix='Complete', color='cyan')

    def update_pbar(self, labels, extend_by=None):
        """
        Extends the tqdm progress bar by `extend_by` steps if current progress exceeds the known max.

        Parameters:
            labels (list): List of variable labels used for tqdm description.
            extend_by (int): Number of additional steps to extend the progress bar.
        """
        total  = extend_by or int(0.4 * self.pbar.total)
        self.pbar.refresh(new_total=total)

        return self


    def _close_pbar(self):
        if self.pbar is not None:
           self.pbar.close()

    def optimize_with_differential_evolution(self, args=(), strategy='best1bin',
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

            labels = [i.label for i in self.control_vars]
            self.labels = [i.label for i in self.control_vars]
            self.maxiter = maxiter
            self._open_pbar(labels, maxiter=maxiter)
            self.update_pbar(labels, extend_by=50)
            call_counter = {"count": 0}


            def wrapped_obj(x):
                lm =maxiter
                call_counter["count"] += 1
                xc  =  call_counter["count"]
                self.counter = xc
                if xc > maxiter:
                    lm +=1

                self.update_pbar(labels, extend_by=50)
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
            labels = [c.label for c in self.control_vars]
            result.x_vars = dict(zip(labels, result.x))
            self.outcomes =result
            return result
        finally:
            self._close_pbar()
            self.clear_cache()
    def setup_obj(self):
        labels = [i.label for i in self.control_vars]
        self.labels = [i.label for i in self.control_vars]
        self.maxiter = maxiter
        self._open_pbar(labels, maxiter=maxiter)
        self.update_pbar(labels, extend_by=50)
        call_counter = {"count": 0}

        def wrapped_obj(x):
            lm = maxiter
            call_counter["count"] += 1
            xc = call_counter["count"]
            self.counter = xc
            if xc > maxiter:
                lm += 1

            self.update_pbar(labels, extend_by=50)
            self.pbar.update(1)
            # pbar.set_postfix({"score": round(self._last_score, 2)})
            return self._set_objective_function(x)

    def start_optimization(self, algarithm,):
        ...
def problemspec(model, simulation, factors):
    ...
if __name__ == "__main__":
    ##xample
    maize_model = "Maize"
    obs = [
        7000.0,
        5000.505,
        1000.047,
        3504.000,
        7820.075,
        7000.517,
        3587.101,
        4000.152,
        8379.435,
        4000.301
    ]
    class Problem(ContinuousVariableProblem):
        def __init__(self, model=None, simulation='Simulation'):
            super().__init__(model, simulation)
            self.simulation = simulation

        def evaluate(self, **kwargs):
            predicted = self.run(verbose=False).results.Yield.mean()
            ans = self.rmse(obs, predicted)
            return ans
    problem  = Problem(maize_model, simulation='Simulation')
    problem.add_control('Manager', "Sow using a variable rule", 'Population',  int,5, bounds=[2, 15])
    problem.add_control('Manager', "Sow using a variable rule", 'RowSpacing', int, 500, bounds=[400, 800])

    # res = problem.minimize_with_local_solver( method  ='Powell',  options={
    #     # 'xatol': 1e-4,      # absolute error in xopt between iterations
    #     # 'fatol': 1e-4,      # absolute error in func(xopt) between iterations
    #     'maxiter': 100,    # maximum number of iterations
    #     'disp': True ,      # display optimization messages
    #
    # })
   # de = problem.optimize_with_differential_evolution(popsize=10, maxiter=100)
   # dep = problem.optimize_with_differential_evolution(popsize=10, maxiter=100, polish=False)



