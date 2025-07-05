from apsimNGpy.optimizer.base import AbstractProblem, VarDesc
from apsimNGpy.core.apsim import ApsimModel
from dataclasses import dataclass, field
from scipy.optimize import minimize, differential_evolution
import wrapdisc
from apsimNGpy.optimizer.optutils import edit_runner
from functools import cache
from apsimNGpy.core_utils.progbar import ProgressBar
from typing import Union
import numpy as np
from collections.abc import Iterable
SIMULATIONS = object()
from abc import abstractmethod
from apsimNGpy.optimizer.base import SING_OBJ_MIXED_VAR, SING_OBJ_CONT_VAR


new_maxiter  =0
class ContVarProblem(AbstractProblem):
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

            ``decision_vars`` (list, optional): A list of VarDesc instances defining variable metadata.

            ``labels (list, optional)``: Variable labels for display and results tracking.

            ``cache_size (int):`` Maximum number of results to store in the evaluation cache.

        Attributes:
            ``model (str):`` The APSIM model template file name.

            ``simulation (str):`` Target simulation(s).

            ``decision_vars (list):`` Defined control variables.

            ``decission_vars (list):`` List of VarDesc instances for optimization.

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
            >>> class Problem(ContVarProblem):
            ...     def evaluate(self, x):
            ...         return -self.run(verbose=False).results.Yield.mean()

            >>> problem = Problem(model="Maize", simulation="Sim")
            >>> problem.add_control("Manager", "Sow using a rule", "Population", int, 5, bounds=[2, 15])
            >>> result = problem.minimize_with_local_solver(method='Powell')
            >>> print(result.x_vars)
        """
    def __init__(self, apsim_model: 'ApsimNGpy.Core.Model', max_cache_size=400, objectives = None, decision_vars=None):

        # Initialize parent classes explicitly
        AbstractProblem.__init__(self, apsim_model, max_cache_size, objectives, decision_vars)
        self.model = apsim_model
        self.decision_vars = decision_vars or []
        self.objectives = objectives

        self.cache = True
        self.cache_size = max_cache_size
        self.pbar = None
        self.counter = 0
        self.maxiter = 0
    @property
    @abstractmethod
    def  optimization_type(self):
         return 'single'

    @property
    def bounds(self):
        return self.extract_bounds()

    def starting_values(self):
        import random
        def get_start(var):
            if 'start_value' in var:
                stat= var.get('start_value', None)
                if stat:
                     return stat
            raise ValueError(f"No start value provided for variable: {var}")

        return tuple(get_start(var) for var in self.decision_vars)
    def _insert_controls(self, x) -> None:
        x = list(x)
        for i, varR in enumerate(self.decision_vars):
            vtype = varR['v_type']
            value = x[i]
            if vtype==int or vtype =='int':
                value = int(np.rint(value))

            else:
                value = round(value, 4)
            x[i] =value
            edit_runner(self.apsim_model, decision_specs=varR, x_values=x[i])

        return x


    def _set_objective_function(self, x):
        xl = self._insert_controls(x)
        # Try local per-instance results cache first
        if self.cache and (cached := self.get_cached(*xl)):
        # Evaluation is expensive because it involves running APSIM, so the call for caching before evaluation
               return cached

        SCORE  = self.evaluate_objectives()
        if self.cache:
            self._insert_cache_result(*xl, result=SCORE)
        self._last_score = SCORE
        return SCORE


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
    @abstractmethod
    def minimize_with_a_local_solver(self, **kwargs):
        'To be implimneted in sub class'
        pass

    @abstractmethod
    def minimize_with_de(self):
        """
        To be implimented in sub-class
        """

    def setup_obj(self):

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
    def extract_bounds(self):
        bould_list = []
        for var in self.decision_vars:
            bounds = tuple(var.get('bounds', []))
            bould_list.append(bounds)
        return bould_list

    def evaluate_objectives(self, objectives=None):
        obj = objectives or self.objectives

        if isinstance(obj, (list, tuple)):
            if len(obj) != 1:
                raise ValueError(
                    "Only one objective function is allowed. "
                    "Combine multiple objectives into a single scalar function."
                )
            obj = obj[0]

        if not callable(obj):
            raise TypeError("Objective function must be callable.")

        self.objectives = obj
        # get results
        df = self.apsim_model.run().results
        ans = self.objectives(df)
        return ans





