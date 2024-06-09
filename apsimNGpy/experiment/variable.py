import random

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

        """

        assert place_holder_name, "Place holder name is not set and can not be none"
        super().__init__()
        self.name = place_holder_name
        self.bounds = bounds
        self._upper = bounds[1]
        self._lower = bounds[0]
        self.step = interval
        self._sigma = None
        self.seed= kwargs.get('random_state', 1)
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

    @property
    def sigma(self):
        """gets the standard deviation of the distribution"""
        return self._sigma

    @property
    def mean(self):
        """gets the standard deviation of the distribution"""
        return self._mean

    @mean.setter
    def mean(self, value):
        """sets the standard deviation of the distribution"""
        self._mean = value

    @sigma.setter
    def sigma(self, value):
        """sets the standard deviation of the distribution"""
        self._sigma = value

    @property
    def samples(self):
        np.random.seed(self.seed)
        """use samples for a sampling
        :return: Array object
        """
        dist = self.distribution
        if dist == 'uniform':
            return Sample(self.distribution).get_distribution(low=self.lower, high=self.upper,
                                                              size=self._sample_size)
        elif dist == 'normal':
            return Sample(self.distribution).get_distribution(self.mean, self.sigma, self.sample_size)
        else:
            raise NotImplementedError('Distribution not implemented or supported')

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
        self.options = options
        self.variables = np.array(options)
        self.name = place_holder_name
        if kwargs.get('parameter', None) is not None:
            self._parameter = kwargs.get('parameter', None)
        if kwargs.get('manager', None) is not None:
            self._manager = kwargs.get('manager')

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


if __name__ == '__main__':
    DV = DiscreteVariable(options=[1, 2], place_holder_name='tillage', manager='simple rotation')
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
