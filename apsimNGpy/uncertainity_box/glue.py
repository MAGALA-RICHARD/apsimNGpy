

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from apsimNGpy.experiment.variable import BoundedVariable, DiscreteVariable
import logging
import numpy
a_true = 3
b_true = 6
sigma_true = 2
from apsimNGpy.parallel.process import custom_parallel
from multiprocessing import cpu_count
import math
NCORE= math.ceil(cpu_count() / 2)
n = 100  # Length of data series

# For the independent variable, x, we will choose n values equally spaced
# between 0 and 10
x = np.linspace(0, 10, n)

# Calculate the dependent (observed) values, y
y = a_true * x + b_true + np.random.normal(loc=0, scale=sigma_true, size=n)


# Define quasi maximum loss function
#####################################################################
def NSE(params, obs, simulator_func):
    """ Nash-Sutcliffe efficiency.
    """
    # Run simulation
    sim = simulator_func(*params)

    # NS
    num = np.sum((sim - obs) ** 2)
    denom = np.sum((obs - obs.mean()) ** 2)
    ns = 1 - (num / denom)

    return [ns, sim]


def weighted_quantiles(values, quantiles, sample_weight=None):
    """ based on : https://nbviewer.org/github/JamesSample/enviro_mod_notes/blob/master/notebooks/07_GLUE.ipynb
    """
    # Convert to arrays
    values = np.array(values)
    quantiles = np.array(quantiles)

    # Assign equal weights if necessary
    if sample_weight is None:
        sample_weight = np.ones(len(values))

    # Otherwise use specified weights
    sample_weight = np.array(sample_weight)

    # Check quantiles specified OK
    assert np.all(quantiles >= 0) and np.all(quantiles <= 1), 'quantiles should be in [0, 1]'

    # Sort
    sorter = np.argsort(values)
    values = values[sorter]
    sample_weight = sample_weight[sorter]

    # Compute weighted quantiles
    weightedQuantiles = np.cumsum(sample_weight) - 0.5 * sample_weight
    weightedQuantiles /= np.sum(sample_weight)

    return np.interp(quantiles, weightedQuantiles, values)


class GlueRunner:
    def __init__(self, simulator_func, params, observed =None):
        """
        :param simulator_func: a customized function that takes in parameters and return the simulation results
        :param params:  list of parameter samples use BoundedVariable objects or DiscreteVariable objects classes to specify their distributions
        raises:
        value errors if param lists are not of equal size
        """

        self._loss = None
        self._observed = observed
        assert isinstance(params, (list, tuple)), 'should be a list or  tuple'
        assert callable(simulator_func), 'simulator_func should be a callable to run the simulation'
        self.simulator_func = simulator_func
        self._params = params
        self._loss  =None
        self._loss = self.NSE



    @property
    def params(self):
        return self._params
    @property
    def param_names(self):
        return [v.name for v in self.params]
    @params.setter
    def params(self, params):
        assert isinstance(params, (list, tuple)), 'should be a list or  tuple'
        self._params = params
    def __call__(self):
        return 3

    @property
    def observed(self):
        return self._observed
    @observed.setter
    def observed(self, value):
        self._observed = value
    def NSE(self, params):
        """ Nash-Sutcliffe efficiency.
        """
        # Run simulation
        sim = self.simulator_func(*params)


        # NS
        num = np.sum((sim - self.observed) ** 2)
        denominator_value = np.sum((self.observed - self.observed.mean()) ** 2)
        nse = 1 - (num / denominator_value)

        return nse, sim
    #users can define their own loss function
    @property
    def loss_function(self):
        return self._loss
    @loss_function.setter
    def loss_function(self, _loss_function):
        """
           If you are changing the default loss function from NSE (Nash-Sutcliffe Efficiency) to a
           custom loss function, you need to modify your simulator function accordingly. The custom
           simulator function should return a tuple containing the loss value and the simulated values.
           Notes:
              >> set this before you run gle
              >> the function should take in the prameters as a tuple
              >> should be about calculating the loss value between the simulation and the observed

           """
        if not callable(_loss_function):
            raise TypeError(' objects passed is not callable or a function')
        self._loss = _loss_function
        print(222)

    def run_glue(self, threshold, parallel =None, **kwargs):
        """
        Run simulations using the default Nash-Sutcliffe Efficiency (NSE) loss function,
        or a user-defined loss function if specified during class instantiation.

        This method allows for running the simulator in parallel, where the model running
        the data may be defined in another script.

        Returns:
            pd.DataFrame: A DataFrame containing all "behavioral" parameter sets and associated model outputs.

        Parameters:
            ncores (int): Specifies the number of processors to use for parallel processing.
            process (bool): Determines whether to run the processes in threads.

        Kwargs:
            ncores: int
                The number of processors to use for parallel processing.
            process: bool
                Whether to run the processes in threads.
        """

        # we need to store the outputs
        out_params = []
        out_sims = []
        loss_func = self.loss_function
        cores = kwargs.get('ncores', NCORE)
        process = kwargs.get('process', True)
        generator = (il for il in zip(*[obj.samples for obj in self.params]))
        if parallel is None:
            for parameters in generator:

                #Extract the loss function
                fitness, sim = loss_func(parameters)
                # keep those that exceed the behavioral threshold
                if  fitness >= threshold:

                    prm = dict(zip(self.param_names,parameters))
                    fit = {'eval_index':fitness}
                    nd = {**prm, **fit }
                    out_params.append(nd)

                    out_sims.append(sim)

        else:
            futures = custom_parallel(loss_func, generator, use_thread=process, ncores=cores)

            for parameters in futures:
                #Extract the loss function
                fitness, sim = loss_func(parameters)
                # keep those that exceed the behavioral threshold
                if  fitness >= threshold:

                    prm = dict(zip(self.param_names,parameters))
                    fit = {'eval_index':fitness}
                    nd = {**prm, **fit }
                    out_params.append(nd)

                    out_sims.append(sim)

        # Build df
        paramDF = pd.DataFrame(data=out_params)
        print(paramDF.shape)
        if  len(out_params) < 0:
            logging.info('No behavioural parameter sets found.')
            raise ValueError('No behavioural parameter sets were found found.')

        # Number of behavioral sets
        print(f"Found: {len(paramDF)} behavioural sets out of:: {self.params[0].samples.size} runs")

        # DF of behavioral simulations
        print(np.shape(out_sims))
        behaviorDF = pd.DataFrame(out_sims)
        return paramDF, behaviorDF

    def coverage(self, ci_data):
        """ Prints coverage from GLUE analysis.
        """
        #print(ci_data.shape)
        # Add observations to df
        ci_data['obs'] = self.observed

        # Are obs within CI?
        ci_data['In_CI'] = ((ci_data['2.5%'] < ci_data['obs']) &
                            (ci_data['97.5%'] > ci_data['obs']))

        # Coverage
        cov = 100. * ci_data['In_CI'].sum() / len(ci_data)

        print('Coverage: %.1f%%' % cov)

    @staticmethod
    def glue_confidence_interval(param_df, sims):
        Qua_nt_is = [0.025, 0.5, 0.975]
        weights = param_df['eval_index']
        # List to store output
        out = []

        # Loop over points in x
        for col in sims.columns:
            values = sims[col]
            out.append(weighted_quantiles(values, Qua_nt_is, sample_weight=weights))

        # Build df
        glue_CI = pd.DataFrame(data=out, columns=['2.5%', '50%', '97.5%'])
        return glue_CI

    @staticmethod
    def visualize_estimates(params_data, simulated_data, observed, x, **kwargs):
        """ Plot median simulation and confidence intervals for GLUE.
        """
        # Get weighted quantiles for each point in x from behavioral simulations
        weights = params_data['eval_index']
        Qua_nt_is = [0.025, 0.5, 0.975]

        # List to store output
        out = []

        # Loop over points in x
        for col in simulated_data.columns:
            values = simulated_data[col]
            out.append(weighted_quantiles(values, Qua_nt_is, sample_weight=weights))

        # Build df
        glue_CI = pd.DataFrame(data=out, columns=['2.5%', '50%', '97.5%'])

        # Plot predicted
        plt.fill_between(x, glue_CI['2.5%'], glue_CI['97.5%'], color='r', alpha=0.3)
        plt.plot(x, glue_CI['50%'], 'r-', label='Estimated')
        plt.title('GLUE')

        # Plot true line
        plt.plot(x, observed, 'bo')
        plt.plot(x, a_true * x + b_true, 'b--', label='True')

        plt.legend(loc='best')

        plt.show()




def _check_params(params):
    """ Evaluate if all params lists are of equal length"""
    lp = [np.shape(para)[0] for para in params]
    lpa = lp[0]
    for it in lp:
        if it !=lpa:
            return False
    return True





if __name__ == '__main__':

    bv = BoundedVariable([20, 20], place_holder_name='rue', sample_size=5500, distribution='uniform')
    bv.mean = 10.5
    bv.sigma = 3.57


    from tools import model
    # TODO test if ran in a package the model can be defined  in main script
    n_sample = 550
    x = np.linspace(0, 10, n_sample)
    a = BoundedVariable([-10, 10], place_holder_name='a', sample_size=100, distribution='uniform')
    b = BoundedVariable([-10, 10], place_holder_name='b', sample_size=100, distribution='uniform')
    b.mean  =6
    b.sigma= 3
    a.mean = 6
    a.sigma = 3
    a_true = 3
    b_true = 7
    sigma_true = 2
    gle = GlueRunner(simulator_func=model, params=[a, b])
    gle.observed = a_true * x + b_true + np.random.normal(loc=0, scale=sigma_true, size=n_sample)
    df = gle.run_glue(threshold=0, parallel=False)
    ci= gle.glue_confidence_interval(*df)
    gle.coverage(ci)
    aa, dfc = df
    # test changing the loss function
    #not below that i sued the same fucntion but only changed the name
    def nls(params, **kwargs):
        """ Nash-Sutcliffe efficiency.
        """
        # Run simulation
        sim = model(*params)

        observed = kwargs.get('observed', gle.observed)
        # NS
        num = np.sum((sim - observed) ** 2)
        denominator_value = np.sum((observed - observed.mean()) ** 2)
        nse = 1 - (num / denominator_value)

        return nse, sim
    gle.loss_function = nls
    df = gle.run_glue(threshold=0.5, parallel=True)