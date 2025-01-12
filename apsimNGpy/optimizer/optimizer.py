from pathlib import Path
import copy
from dataclasses import dataclass
import inspect
import numpy as np
from scipy.optimize import minimize

from apsimNGpy.core.apsim import ApsimModel


@dataclass
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


class Problem:

    def __init__(self):

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

    def set_up_data(self, model: str, func: callable, out_path: str = None, observed_values: np.ndarray = None,
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
        self.options = options
        self.model = model
        self.model = model
        self.observed = observed_values
        self.out_path = out_path
        self.evaluation_sign = _fun_inspector(func)
        # make sure the user is consistent with extra argument
        if 'args' in self.evaluation_sign and not self.options.get('args'):
            raise ValueError("function evaluator has extra arguments not specified")
        self.func = func
        return self

    def add_control_var(self, updater: str, main_param, params: dict, label: str, **kwargs):
        """
        Updater: Specifies the name of the APSIMNG method used to update values from the optimizer.
        Params: A dictionary containing arguments for the updater method, excluding the value to be optimized.
        For example, with `replace_soil_property_values`, params could be defined as:
            {
                'parameter': 'Carbon',
                'soil_child': 'Organic',
                'simulations': None,
                'indices': [1],
                'crop': None
            }
        Note that this main_param = 'param_values', which is excluded here.

        To optimize variables defined via the manager module, use `update_mgt_by_path` and define params as: {
        'path': "Simulation.Manager.script_name.None.parameter_name" } and main_parm  = 'param_values', Here,
        'None' represents the path to recompile the model to, and 'Simulation' is typically the name used in the
        simulation, though it can vary. For further information, refer to the APSIMNG API documentation.

        Kwargs: Contains additional arguments needed.

        Returns:
            None
        """
        parm = copy.deepcopy(params)
        self.updaters.add(updater)
        self.params.append(parm)
        self.main_params.add(main_param)
        self.predictor_names.add(label)

        print(f"existing vars are: {self.predictor_names}")

    def update_params(self, x):

        """This updates the parameters of the model during the optimization"""
        model = ApsimModel(self.model)
        # if len(x) != len(self.params):
        #     ve = ValueError('Data set up not complete \n'
        #                     'params must have the same length as the suggested predictors')
        #     raise ve

        for x_var, method, param, x_holder in zip(x, self.updaters, self.params, self.main_params):
            if 'soil' in method:
                x_var = x_var,
            # update the params
            param[x_holder] = x_var
            getattr(model, method)(**param)
        # # now time to run
        model.run(report_name='Report')
        if 'args' in self.evaluation_sign:
            ans = self.func(model, *self.options['args'])
        else:
            ans = self.func(model)
        print(ans, end='\r')
        return ans

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
        minim = minimize(self.update_params, initial_guess, **kwargs)
        ap = dict(zip(self.predictor_names, minim.x))
        setattr(minim, 'x_vars', ap)
        return minim

    def reset_data(self):
        """
        Resets the data for the optimizer. You don't need to call set up in the data again by calling the
        set_up_data_method in case your setup does need to change. After resting, you have to add the control vars
        @return:
        """
        self.params = []
        self.updaters = set()
        self.main_params = set()
        self.predictor_names = set()
        return self

    def _freeze_data(self):
        # make the data unchangeable after editing
        self.params = tuple([i for i in self.params])
        self.updaters = tuple([i for i in self.updaters])
        self.main_params = tuple([i for i in self.main_params])
        self.predictor_names = tuple([i for i in self.predictor_names])


# initialized before it is needed
SingleProblem = Problem()

if __name__ == '__main__':
    # define the problem
    from apsimNGpy.core.base_data import load_default_simulations

    mode = Path.home() / 'Maize.apsimx'

    maize = load_default_simulations(crop='maize', simulations_object=False)


    def func(model):
        sm = model.results.Yield.sum()
        mn = model.results.Yield.mean()
        ans = sm * sm / mn
        return -ans


    prob = SingleProblem.set_up_data(model=r'Maize.apsimx', out_path='out.apsimx', func=func)
    man = {'path': "Simulation.Manager.Fertilise at sowing.None.Amount"}
    prob.add_control_var(updater='update_mgt_by_path', params=man, main_param='param_values',
                         label='nitrogen_fertilizer')
    si = {'parameter': 'Carbon',
          'soil_child': 'Organic',
          'simulations': 'Simulation',
          'indices': [0], }
    prob.add_control_var(params=si, updater='replace_soil_property_values', main_param='param_values', label='carbon')
    options = {'maxiter': 1000, 'disp': True}

    mn = prob.minimize_problem(bounds=[(100, 320), (0, 1)], x0=[100, 0.1], method=Solvers.Nelder_Mead, options=options)

    prob.update_params([300, 3.3283740839260843e-09])
