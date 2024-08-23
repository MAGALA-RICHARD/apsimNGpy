import logging
import random
import warnings

import numpy as np


class Sample:
    def __init__(self, distributions):
        self.distributions = distributions

    @property
    def get_distribution(self):
        dists = {'choice': np.random.choice, 'uniform': np.random.uniform, 'normal': np.random.normal,
                 'lognormal': np.random.lognormal}
        return dists[self.distributions]


class Variable(object):

    def __init__(self) -> None:
        super().__init__()
        self.manager_script = None
        self.manager = None
        self.parameter = None
        self.variables = None
        self.sample_size = None

    @property
    def get_script_manager(self):
        if self.manager is None:
            raise TypeError("script manager name not set")
        return {'Name': self.manager, self.parameter: None}  # hust put a dummy variable for now


class BoundedVariable(Variable):
    """
        for setting components for continuous variables
        manager and parameters can be set after initialization of the class or keywords argument parameter =? manager = /
        """

    def __init__(self, bounds=(None, None), interval=None, place_holder_name=None, **kwargs) -> None:
        """
         >> interval (integer or float):  is the step size between two consecutive values
         >> bounds (array like) is the lower and upper VALUES OF THE TARGET VARIABLE SUPPLIED A TUPLE
         >> place_holder_name (str), could be the name of your variable; preferred to be without spaces
         kwargs:
         - distribution (str): describe the shape of the variable e.g normal, uniform lognormal. default is uniform
         - manager (str): name of the manager script in the simulation
         - parameter (str): parameter name
         - sample_size (int): to specify the number of samples to sample from the distribution
         - mean, sigma (int, int): mean and standard deviation of the distribution
         - random_state to set the seed of the random number generator defaults to 1
         - var_type (int, float): the data type of variable to sample

        """

        assert place_holder_name, "Place holder name is not set and can not be none"
        super().__init__()
        self.name = place_holder_name
        self.bounds = bounds
        self._upper = bounds[1]
        self._lower = bounds[0]
        self.step = interval
        self._sigma = None

        self.seed = kwargs.get('random_state', 1)
        self._var_type = kwargs.get('var_type', float)
        if interval is None:
            self.variables = np.arange(bounds[0], bounds[1])
        else:
            self.variables = np.arange(bounds[0], bounds[1], interval)
        if kwargs.get('parameter', None) is not None:
            self._parameter = kwargs.get('parameter', None)
        if kwargs.get('manager', None) is not None:
            self._manager = kwargs.get('manager')
        if kwargs.get('sample_size', None) is not None:
            self._sample_size = kwargs.get('sample_size')
        self.distribution = kwargs.get('distribution', 'uniform')
        self._sigma = kwargs.get('sigma', None)
        self._mean = kwargs.get('mean', None)
        self._samples = self._create_samples

    @property
    def sigma(self):
        """gets the standard deviation of the distribution"""
        return self._sigma

    @property
    def mean(self):
        """gets the standard deviation of the distribution"""
        return self._mean

    @property
    def var_type(self):
        return self._var_type

    @var_type.setter
    def var_type(self, value):
        self._var_type = value

    @mean.setter
    def mean(self, value):
        """sets the standard deviation of the distribution"""
        self._mean = value

    @sigma.setter
    def sigma(self, value):
        """sets the standard deviation of the distribution"""
        self._sigma = value

    @property
    def _create_samples(self):
        np.random.seed(self.seed)
        """use samples for a sampling
        :return: Array object
        """
        dist = self.distribution
        if dist == 'uniform' and self.var_type == float:
            return Sample(self.distribution).get_distribution(low=self.lower, high=self.upper,
                                                              size=self._sample_size)
        elif dist == 'uniform' and self.var_type == int:
            return np.random.randint(self.lower, self.upper, size=self._sample_size)
        elif dist == 'normal':
            normal = Sample(self.distribution).get_distribution(self.mean, self.sigma, self.sample_size)
            if self.var_type == int:
                normal = normal.astype(int)
            return normal
        else:
            raise NotImplementedError('Distribution not implemented or supported')

    @property
    def samples(self):
        return self._samples

    @samples.setter
    def samples(self, value):
        if self.sample_size != len(value):
            warnings.warn('attempting to change samples without changing the sample size can be error prone')
        self._samples = value

    @property
    def distribution(self):
        return self._distribution

    @distribution.setter
    def distribution(self, value):
        self._distribution = value

    @property
    def lower(self):
        return self._lower

    @property
    def upper(self):
        return self._upper

    @lower.setter
    def lower(self, value):
        self._lower = value

    @upper.setter
    def upper(self, value):
        self._upper = value

    @property
    def manager(self):
        return self._manager

    @manager.setter
    def manager(self, value):
        self._manager = value

    @property
    def parameter(self):
        return self._parameter

    @parameter.setter
    def parameter(self, value):
        self._parameter = value

    @property
    def sample_size(self):
        return self._sample_size

    @sample_size.setter
    def sample_size(self, value):
        self._sample_size = value

    @distribution.setter
    def distribution(self, value):
        self._distribution = value


class DiscreteVariable(Variable):
    """
    for setting components for discrete variables
    manager and parameters can be set after initialization of the class or keywords argument parameter =? manager = /
    """

    def __init__(self, options=None, place_holder_name=None, **kwargs) -> None:
        """
        place_holder_name: str, could be the name of your variable; preferred to be without spaces
        options (list) of variables to consider
        """
        assert place_holder_name, "Place holder name is not set and can not be none"
        super().__init__()
        self._options = options
        self.variables = np.array(options)
        self.name = place_holder_name
        self.seed = kwargs.get('random_state', 1)
        if kwargs.get('parameter', None) is not None:
            self._parameter = kwargs.get('parameter', None)
        if kwargs.get('manager', None) is not None:
            self._manager = kwargs.get('manager')

        self._sample_size = kwargs.get('sample_size', 'None')

    @property
    def manager(self):
        return self._manager

    @manager.setter
    def manager(self, value):
        self._manager = value

    @property
    def parameter(self):
        return self._parameter

    @parameter.setter
    def parameter(self, value):
        self._parameter = value

    @property
    def sample_size(self):
        return self._sample_size

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, values):
        """
        values: lists
        """
        if not isinstance(values, (list, np.ndarray, tuple)):
            raise TypeError('Values must be array-like')
        self._options = values

    @sample_size.setter
    def sample_size(self, value):
        self._sample_size = value

    @property
    def samples(self):
        """
               Generates a sample of values from the given options.

               This method uses numpy's random. Choice to generate a sample of values
               from the provided options. It sets the random seed for reproducibility.

               If you want to set your own sample size and options, modify the
               attributes `sample_size` and `options` of the class instance.

               Returns:
               --------
               numpy.ndarray
                   An array of sampled values from the options.
               """
        np.random.seed(self.seed)
        return np.random.choice(self.options, self.sample_size)
    # @samples.setter
    # def samples(self, values):
    #     if not isinstance(values, (list, np.ndarray)):
    #         raise TypeError('samples should be a list or numpy array')
    #     if len(values) != self.sample_size:
    #         logging.warning('Sample size is not equal to the intiial sample size')
    #     self._samples = values


if __name__ == '__main__':
    DV = DiscreteVariable(options=[1, 2], place_holder_name='tillage', manager='simple rotation', sample_size=10)
    bv = BoundedVariable(bounds=[0, 100], place_holder_name='Nitrogen', manager='simple rotation')
    # change the distribution
    bv.distribution = 'uniform'
    # change the upper boundary
    bv.upper = 1
    # set the sample size
    bv.sample_size = 100
    # print the sample variables
    print(bv.samples)
    DV.parameter = 'Crops'
    xp = [DV, bv]
    print([i.get_script_manager for i in xp])
    from apsimNGpy.experiment.permutations import create_permutations

    ap = create_permutations([n.variables for n in xp], [i.name for i in xp])
