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
from apsimNGpy.optimizer.variables import auto_guess
from apsimNGpy.core.apsim import ApsimModel
from typing import Iterable


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
        self.n_workers = 1
        self.evaluation_sign = None
        self.out_path = None
        self.model = None
        self.options = None
        self.func = None
        self.observed = None

    def set_up_data(self, model: str, func: callable, ws: os.PathLike, observed_values: np.ndarray = None,
                    options: dict = None, n_workers=1):
        """
        model: APSIM model file, apsimNGpy object, apsim file str or dict we want to use in the minimization func: an
        evaluation function, which is callable.
        This is something you should write for your self.
        A typical evaluation function takes on the functional signature func(apsimNGpy.CoreModel.model, *args) Additional
        arguments can be passed as a tuple.
        Example of this could be observed _variables to be compared with the
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
        self.n_workers = n_workers
        self.observed = observed_values
        self.user_ws = ws

        self.evaluation_sign = _fun_inspector(func)

        # make sure the user is consistent with extra argument
        if 'args' in self.evaluation_sign and not self.options.get('args'):
            raise ValueError("function evaluator has extra arguments not specified")
        self.func = func

        return self

    def add_control_variable(self, control: Any):
        self.controls.append(control)
    def add_control(self, model_type, model_name, simulation_name, variable_name):
        self.controls.append((model_type, model_name, simulation_name, variable_name))
    def update_predictors(self, x: tuple):
        if len(self.controls) < 1:
            raise ValueError("No control _variables added yet")
        vals = '_'.join(str(v) for v in x)
        # we want a unique out_path name for parallel processing
        if self.n_workers > 1:
            new_path = self.WS.joinpath(f"{vals}.apsimx")

        if not isinstance(self.model, Iterable):
            model_s = [self.model]
        else:
            model_s = self.model
        MODELs = []
        for model_x in model_s:
            model = ApsimModel(model_x)
            try:

                for predictor, x_to_fill in zip(self.controls, x):
                    # update main param for the function updator
                    predictor.params[predictor.main_param] = x_to_fill

                    getattr(model, predictor.updater)(**predictor.params)
                    ui = model.extract_user_input('SowMaize')

                    # xit loop and run
                    # model.run(report_name='MaizeR')
                    MODELs.append(model)
            finally:
                pass

        try:
            if 'args' in self.evaluation_sign:
                ans = self.func(MODELs, *self.options['args'])
            else:
                ans = self.func(MODELs)

            return ans
        finally:
            for model in MODELs:
                try:
                    datastore = model.datastore

                    os.remove(model.path)
                    print(f"Removed: {datastore}")
                    os.remove(datastore)
                    del model
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

        minim = minimize(self.update_predictors, **kwargs)
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

        return self

    def set_ws(self, ws):
        self.WS = Path(ws).joinpath('out_files')
        if self.WS.exists():
            try:
                shutil.rmtree(self.WS)
            except (FileNotFoundError, PermissionError):
                ...
        self.WS.mkdir(exist_ok=True)

    def _freeze_data(self):
        """
        # make the data unchangeable after editing.
        # Please note that this only works during execution.
        # I expect some leakages before
         """
        self.controls = tuple([i for i in self.controls])


# initialized before it is needed
SingleProblem = Problem()
