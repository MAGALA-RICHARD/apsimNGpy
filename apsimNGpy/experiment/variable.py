import numpy as np


class Variable(object):

    def __init__(self) -> None:
        super().__init__()
        self.manager_script = None
        self.manager = None
        self.parameter = None
        self.variables = None

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
        interval: integer or float:  is the step size between two consecutive values
        bounds: array like is the lower and upper VALUES OF THE TARGET VARIABLE SUPPLIED A TUPLE
         place_holder_name: str, could be the name of your variable; preferred to be without spaces
        """
        assert place_holder_name, "Place holder name is not set and can not be none"
        super().__init__()
        self.name = place_holder_name
        self.bounds = bounds
        self.step = interval
        if interval is None:
            self.variables = np.arange(bounds[0], bounds[1])
        else:
            self.variables = np.arange(bounds[0], bounds[1], interval)
        if kwargs.get('parameter', None) is not None:
            self._parameter = kwargs.get('parameter', None)
        if kwargs.get('manager', None) is not None:
            self._manager = kwargs.get('manager')

    @property
    def lower(self):
        return self.bounds[0]

    @property
    def upper(self):
        return self.bounds[1]

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


class DiscreteVariable(Variable):
    """
    for setting components for discrete variables
    manager and parameters can be set after initialization of the class or keywords argument parameter =? manager = /
    """
    def __init__(self, options=None, place_holder_name=None,  **kwargs) -> None:
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
    DV = DiscreteVariable(options=[1, 2], place_holder_name='tillage', manager='sim')
    bv= BoundedVariable(bounds=[0, 100], place_holder_name='Nitrogen', manager='tillage')
    DV.parameter = 'Crops'
    xp = [DV, bv]
    print([i.get_script_manager for i in xp])
    from apsimNGpy.experiment.permutations import create_permutations
    ap= create_permutations([n.variables for n in xp], [i.name for i in xp])
