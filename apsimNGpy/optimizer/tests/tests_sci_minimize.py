
if __name__ == '__main__':
    from apsimNGpy.optimizer.single import  ContinuousVariable, MixedVariable
    from apsimNGpy.core.apsim import ApsimModel
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

    print('testing continous variable')
    # there are two ways to initialise a problem from both classes

    # 1. inherit from the classes as follows
    class Problem(ContinuousVariable):
        def __init__(self, apsim_model: 'ApsimNGpy.Core.Model', obs, max_cache_size=400, objectives=None,
                     decision_vars=None):
            super().__init__(apsim_model=apsim_model, max_cache_size=max_cache_size, objectives=objectives,
                             decision_vars=decision_vars)
            self.obs = obs

        def evaluate_objectives(self, **kwargs):
            # set up everything you need here. This will act as the objective function
            # tip run the apsim model here, get the results and decide on how to evaluate the objective
            predicted = self.apsim_model.run(verbose=False).results.Yield

            ans = self.rmse(self.obs, predicted)

            return -predicted.mean()

    # now intitialize the problem

    maize_model = ApsimModel('Maize')
    problem = Problem(maize_model, obs, objectives=None, decision_vars=None)

    # approach 2.
    # 2. define the objective and supply it directly. what is needed is to access the pandas data and decide on how to evaluate the objective function
    #define objective function, should take in a pandas data frame querry one the columns from the predicted table and return the evaluation results
    def maximize_yield(df):
        ans = -df.Yield.mean()
        return ans
    # Adding control variables
    # There are also two ways to add control variables, a. ka decision variables. using add control or supplying the decision variable directly during initialisation. we will get to the later later on, but
    # first let use add_control vars
    problem.add_control(
        **{'path': '.Simulations.Simulation.Field.Fertilise at sowing', 'Amount': "?", "bounds": [50, 300],
           "v_type": "qrandint"}, start_value=150)
    problem.add_control(
        **{'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': "?", 'v_type': 'int',
           'bounds': [4, 14]}, start_value=8)

    # ready to optimize you variables. no need to supply starting values, bounds etc as those are defined with the add_control method but you can concentrate on supplying other arguments such a smethod to use. the method to use depends on the nature of the problem

    resc = problem.minimize_with_alocal_solver( method  ='Powell',  options={
        # 'xatol': 1e-4,      # absolute error in xopt between iterations
        # 'fatol': 1e-4,      # absolute error in func(xopt) between iterations
        'maxiter': 100,    # maximum number of iterations
        'disp': True ,      # display optimization messages

    })

    depc = problem.minimize_with_de(popsize=10, maxiter=100, polish=False)

    print('testing mixed variable')
    # mixed problem takes in all types of variables from discrete to continnous and also provide some flexibility in guiding the sampling processing, which help to speed up the optimization pricess
    maize_model = ApsimModel('Maize')
    problem = MixedVariable(maize_model, objectives=maximize_yield)
    problem.add_control(
        **{'path': '.Simulations.Simulation.Field.Fertilise at sowing', 'Amount': "?", "bounds": None,
           "v_type": "choice"}, start_value=150, categories=[100,150, 200, 250, 300])
    problem.add_control(
        **{'path': '.Simulations.Simulation.Field.Sow using a variable rule', 'Population': "?", 'v_type': 'qrandint',
           'bounds': [4, 14]}, start_value=8, q=2, )
    # de_res = problem.optimize_with_differential_evolution()
    res_m = problem.minimize_with_alocal_solver(method='Powell', )
    de_m = problem.minimize_with_de(popsize=20, polish=True)
