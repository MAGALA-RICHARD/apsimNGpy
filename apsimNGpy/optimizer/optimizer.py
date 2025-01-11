from pathlib import Path

from dataclasses import dataclass
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


class Problem:

    def __init__(self, model, func, out_path=None, observed_values=None):
        self.model = model
        self.out_path = out_path
        self.params = []
        self.func = func
        self.observed = observed_values
        self.predictor_names = []

        """
       model: APSIM model file, apsimNGpy object, apsim file str or dict we want to use in the minimization
       func: is the callable that takes in apsimNGpy object and return the desired loss function. we will use it to extract 
       the result meaning the user can create a callable object to manipulate the results objects
        """

    def add_param(self, simulation_name: str, param_class: str,
                  param_name: str,
                  cultivar_info: dict = None,
                  soil_info: dict = None,
                  manager_info: dict = None, **kwargs):
        """
        it is one factor at a time
        @param soil_info dict: corresponding parameters for soil parameter. Accepted values:
                                     parameter: str,
                                     soil_child: str,
                                     simulations: list = None,
                                     indices: list = None,
                                     crop=None,
        also see replace_soil_property_values, param_values argument is not allowed in this dictionary

        @param cultivar_info: corresponding functional paramters for edit_cultivar method from APSIMNG object.
        Accepted values are CultivarName: str, commands: tuple, value arguments are not allowed here.

        @param param_class: parameters belong to classes like manager, Soil, Cultivar, this is useful for determining
        the replacement method.

        @param manager_info: info accompanying the parameters of the manager params, e.g.,
        {'Name': 'Fertilise at sowing', 'param_description': 'Amount'} script name and parameters going to it.

         @param simulation_name: e.g., Simulation, which is the default for apsim files @param param_class: includes, Manager,
        soil, cultivar
         @param param_name: name to hold in place the params, to optimize
         kwargs, contains extra arguments needed,
         @return: None
        """
        params = {
            'simulations': simulation_name,
            'param_class': param_class,
            'param_name': param_name,
            'manager_info': manager_info,
            'soil_info': soil_info,
            'cultivar_info': cultivar_info
        }

        self.params.append(params)

    def update_params(self, x):

        """This updates the parameters of the model during the optimization"""
        model = ApsimModel(self.model)

        for x_var, param in zip(x, self.params):

            if param['param_class'].lower() == 'manager':
                # create a new dictionary
                mgt_info = param['manager_info']
                mgt_info.update({mgt_info['param_description']: x_var})
                model.update_mgt(management=mgt_info, **param)
            if param['param_class'].lower() == 'cultivar':
                model.edit_cultivar(**param['cultivar_info'], values=x_var)
            if param['param_class'].lower() == 'soil':
                model.replace_soil_property_values(**param['soil_info'], param_values=[x_var ])
        # now time to run
        model.run(report_name='Report')
        ans = self.func(model, self.observed)
        print(ans, end='\r')
        return ans

    def minimize_problem(self, **kwargs):
        for pp in self.params:
            self.predictor_names.append(pp['param_name'])
        """
        kwargs: key word arguments as defined by the scipy minimize method
        see scipy manual for each method https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
        """

        minim = minimize(self.update_params,
                         **kwargs)
        ap = dict(zip(self.predictor_names, minim.x))
        setattr(minim, 'x_vars', ap)
        return minim


if __name__ == '__main__':
    # define the problem
    from apsimNGpy.core.base_data import load_default_simulations

    mode = Path.home() / 'Maize.apsimx'

    maize = load_default_simulations(crop='maize', simulations_object=False)


    def func(model, ob):
        return model.results.Yield.mean() * -1


    prob = Problem(model=r'Maize.apsimx', out_path='out.apsimx', func=func)
    prob.add_param(simulation_name='Simulation', param_name='Nitrogen',
                   manager_info={'Name': 'Fertilise at sowing', 'param_description': 'Amount'}, param_class='Manager')
    si = {'parameter': 'Carbon',
          'soil_child': 'Organic',
          'simulations': 'Simulation',
          'indices': [0], }
    prob.add_param(simulation_name='Simulation', param_name='carbon', param_class='soil', soil_info=si)
    options = {'maxiter': 10000}

    prob.update_params([100])
    mn = prob.minimize_problem(bounds=[(180, 280), (0, 1.8)], x0=[180, 0.8], method=Solvers.Nelder_Mead)
