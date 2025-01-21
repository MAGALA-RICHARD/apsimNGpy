import os
import shutil
from pathlib import Path
import copy
from dataclasses import dataclass
import inspect
from typing import Any
from abc import ABC, abstractmethod
import numpy as np
from scipy.optimize import minimize
from variables import _initial_guess
from apsimNGpy.core.apsim import ApsimModel


@dataclass(slots=True)
class Solvers:
    L_BFGS_B = 'L-BFGS-B'
    BFGS = 'BFGS'
    Powell = 'Powell'
    Newton_CG = 'Newton-CG'
    lm = 'lm'
    Nelder_Mead = 'Nelder-Mead'
    SLSQP = 'SLSQP'


def _fun_inspector(fun):
    assert callable(fun), 'method supplied is not a callable object'
    sign = inspect.signature(fun)
    params = [i.name for i in sign.parameters.values()]
    return params


class Problem(ABC):

    def __init__(self):

        self.WS = None
        self.user_ws = None
        self.controls = None
        self.var_desc = None
        self.evaluation_sign = None
        self.out_path = None
        self.model = None
        self.options = None
        self.params = None
        self.func = None
        self.observed = None
        self.predictor_names = None
        self.updaters = None
        self.main_params = None
        self.variable_type = None

    def set_up_data(self, model: str, func: callable, ws: os.PathLike, observed_values: np.ndarray = None,
                    options: dict = None):
        """
        model: APSIM model file, apsimNGpy object, apsim file str or dict we want to use in the minimization func: an
        evaluation function, which is callable.
        This is something you should write for your self.
        A typical evaluation function takes on the functional signature func(apsimNGpy.APSIMNG.model, *args) Additional
        arguments can be passed as a tuple.
        Example of this could be observed variables to be compared with the
        predicted, where a loss function like rmse errors can be computed.
        In case of extra argument, these should be
        passed via options e.g., options ={args: None}
         @return: an instance of problem class object.
        """
        # re-initialize all lists carrying the data
        self.reset_data()
        self.set_ws(ws)
        self.options = options
        self.model = model
        self.model = model
        self.observed = observed_values
        self.user_ws = ws

        self.evaluation_sign = _fun_inspector(func)
        self.var_desc = None
        # make sure the user is consistent with extra argument
        if 'args' in self.evaluation_sign and not self.options.get('args'):
            raise ValueError("function evaluator has extra arguments not specified")
        self.func = func

        return self

    def add_control_variable(self, control: Any):
        self.controls.append(control)

    def update_predictors(self, x: tuple, *args: Any):
        vals = '_'.join(str(v) for v in x)
        # we want a unique out_path name for parallel processing
        new_path = self.WS.joinpath(f"{vals}.apsimx")
        model = ApsimModel(self.model, out_path=new_path)
        try:

            for predictor, x_to_fill in zip(self.controls, x):
                # update main param for the function updator
                predictor.params[predictor.main_param] = x_to_fill
                getattr(model, predictor.updater)(**predictor.params)
            # xit loop and run
            # model.run(report_name='MaizeR')
            if 'args' in self.evaluation_sign:
                ans = self.func(model, *self.options['args'])
            else:
                ans = self.func(model)
            print(ans, end='\r')

            return ans
        finally:
            try:
                datastore = model.datastore
                del model
                os.remove(new_path)
                # os.remove(datastore)
            except (FileNotFoundError, PermissionError) as e:

                pass

    def minimize_problem(self, **kwargs):

        """
       
        Minimizes the defined problem using scipy.optimize.minimize.
        kwargs: key word arguments as defined by the scipy minimize method
        see scipy manual for each method https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
        
        Returns:
        Optimization result.
        
        """
        # freeze the data before optimization to make it immutable
        self._freeze_data()
        initial_guess = kwargs.get('x0') or np.zeros(len(self.params))
        if kwargs.get('x0'):
            kwargs.pop('x0')
        minim = minimize(self.update_predictors, initial_guess, **kwargs)
        labels = [i.label for i in self.controls]
        ap = dict(zip(labels, minim.x))
        setattr(minim, 'x_vars', ap)
        return minim

    def reset_data(self):
        """
        Resets the data for the optimizer. You don't need to call set up in the data again by calling the
        set_up_data_method in case your setup does need to change. After resting, you have to add the control vars
        @return:
        """
        self.controls = []
        self.params = []
        self.updaters = []
        self.main_params = []
        self.predictor_names = []
        self.variable_type = []
        self.var_desc = []
        return self

    def set_ws(self, ws):
        self.WS = Path(ws).joinpath('out_files')
        if self.WS.exists():
            try:
                shutil.rmtree(self.WS)
            except (FileNotFoundError, PermissionError):
                ...
        self.WS.mkdir()

    def _freeze_data(self):
        # make the data unchangeable after editing
        self.params = tuple([i for i in self.params])
        self.controls = tuple([i for i in self.controls])
        self.updaters = tuple([i for i in self.updaters])
        self.main_params = tuple([i for i in self.main_params])
        self.predictor_names = tuple([i for i in self.predictor_names])
        self.variable_type = type([i for i in self.variable_type])


# initialized before it is needed
SingleProblem = Problem()
