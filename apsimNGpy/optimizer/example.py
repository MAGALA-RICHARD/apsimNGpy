from pathlib import Path

from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.optimizer.optimizer import Problem, Solvers, SingleProblem

if __name__ == '__main__':
    mode = Path.home() / 'Maize.apsimx'

    maize = load_default_simulations(crop='maize', simulations_object=False)


    # first step is to define the loss function
    # here we use a simple function which will take in apsimNG object class
    # in kost cases we compare predicted to the observed for lack of data this
    # example is simple just maximizing the yield based on N input
    def func(model, ob):
        sm = model.results.Yield.sum()
        mn = model.results.Yield.mean()
        ans = sm * sm / mn
        return -ans


    # initialize the problem and supply the func and path to the apsim Model
    prob = SingleProblem.set_up_data(model=r'Maize.apsimx', out_path='out.apsimx', func=func)
    man = {'path': "Simulation.Manager.Fertilise at sowing.None.Amount"}
    prob.add_control_var(updater='update_mgt_by_path', params=man, main_param='param_values',
                         label='nitrogen_fertilizer')
    # example of how to optimize soil related paramters
    si = {'parameter': 'Carbon',
          'soil_child': 'Organic',
          'simulations': 'Simulation',
          'indices': [0], }
    #prob.add_control_var(params=si, updater='replace_soil_property_values', main_param='param_values', label='carbon')
    options = {'maxiter': 8000, 'disp': True}

    mn = prob.minimize_problem(bounds=[(100, 320)], x0=[100], method=Solvers.L_BFGS_B, options=options)

