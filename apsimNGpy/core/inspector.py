import doctest
from pathlib import Path
from pprint import pprint

from apsimNGpy.core.core import CoreModel, Models

NODES = dict(manager=Models.Manager, simulation=Models.Core.Simulation,
             plant=Models.PMF.Plant,
             clock=Models.Clock,
             weather=Models.Climate.Weather,
             soil=Models.Soils.Soil,
             physical=Models.Soils.Physical,
             replacements=Models.Core.Folder)


class Inspector(CoreModel):
    """
    Inspector class for APSIMNGPY modules. It inherits from the CoreModel class and
    therefore has access to a repertoire of methods from that class.

    This implies that you can still run the model and modify parameters as needed.

    Example:
        >>> from apsimNGpy.core.inspector import Inspector
        >>> from apsimNGpy.core.base_data import load_default_simulations
        >>> path_model = load_default_simulations(crop='Maize', simulations_object=False)
        >>> model = Inspector(path_model, set_wd=Path.home())
    """

    def __init__(self, model, out_path=None, set_wd=None, **kwargs):
        super().__init__(model, out_path, set_wd, **kwargs)

    @property
    def in_simulations(self):
        return self.find_simulations()

    def inspect(self, of_class):
        of_class = NODES[of_class]
        descendants = self.Simulations.FindAllDescendants[of_class]()
        return [i.FullPath for i in descendants]

    @property
    def path_to_managers(self):
        """
        Returns a list of node paths in the class Manager.

        @return: A list of node paths in the class Manager.

        Example:
            >>> from apsimNGpy.core.base_data import load_default_simulations
            >>> model_path = load_default_simulations(crop="Maize", simulations_object=False)
            >>> model = Inspector(model_path)
            >>> pm = model.path_to_managers
            >>> pprint(pm)
            ['.Simulations.Simulation.Field.Sow using a variable rule',
             '.Simulations.Simulation.Field.Fertilise at sowing',
             '.Simulations.Simulation.Field.Harvest']
        """
        return self.inspect(of_class='manager')

    @property
    def path_to_soil(self):
        """
        Returns a list of node paths in the class Soil.

        @return: A list of node paths in the class Soil.

        Example:
            >>> from apsimNGpy.core.base_data import load_default_simulations
            >>> model_path = load_default_simulations(crop="Maize", simulations_object=False)
            >>> model = Inspector(model_path)
            >>> ps = model.path_to_soil
            >>> print(ps)
            ['.Simulations.Simulation.Field.Soil']
        """
        return self.inspect(of_class='soil')

    @property
    def path_to_plants(self):
        """
        Returns a list of node paths in the class Plants.

        @return: A list of node paths in the class Plants.

        Example:
            >>> from apsimNGpy.core.base_data import load_default_simulations
            >>> model_path = load_default_simulations(crop="Maize", simulations_object=False)
            >>> model = Inspector(model_path)
            >>> pp = model.path_to_plants
            >>> print(pp)
            ['.Simulations.Simulation.Field.Maize']
        """
        return self.inspect(of_class='plant')

    @property
    def path_to_clock(self):
        """
        Returns a list of node paths in the class Clock.

        @return: A list of node paths in the class Clock.

        Example:
            >>> from apsimNGpy.core.base_data import load_default_simulations
            >>> model_path = load_default_simulations(crop="Maize", simulations_object=False)
            >>> model = Inspector(model_path)
            >>> pc = model.path_to_clock
            >>> print(pc)
            ['.Simulations.Simulation.Clock']
        """
        return self.inspect(of_class='clock')

    @property
    def path_to_weather(self):
        """
        RReturns a list of node path in the class Weather
        @return:
        """
        return self.inspect(of_class='weather')

    @property
    def path_to_simulation(self):
        """
        RReturns a list of node path in the class Simulation
        @return:
        """
        return self.inspect(of_class='simulation')

    def get_manager_ids(self, full_path: bool = True, verbose=False) -> list[str]:

        managers = self.Simulations.FindAllDescendants[Models.Manager]()
        if full_path:
            list_managers = [i.FullPath for i in managers]
        else:
            list_managers = [i.Name for i in managers]
        if verbose:
            pprint(list_managers, indent=4)
        return list_managers

    def get_manager_parameters(self, full_path, verbose=False) -> dict:
        params = {}
        manager = self.Simulations.FindByPath(full_path)
        for i in range(len(manager.Value.Parameters)):
            _param = manager.Value.Parameters[i].Key
            _values = manager.Value.Parameters[i].Value
            params[_param] = _values
        if verbose:
            pprint(params, indent=4)
        return params

    def report_ids(self):
        datastorage = self.Simulations.FindAllDescendants[Models.Report]()
        print(datastorage)


if __name__ == '__main__':
    import doctest
    from apsimNGpy.core.base_data import load_default_simulations, load_default_sensitivity_model

    mod = load_default_sensitivity_model(method='sobol')
    sob = mod.Simulations.FindInScope[Models.Sobol]()

    model = load_default_simulations(crop='Maize')


    def set_sensitivity_factor(name, path, LowerBound, UpperBound):
        parameter = Models.Sensitivity.Parameter()
        parameter.Name = name
        parameter.LowerBound = LowerBound
        parameter.UpperBound = UpperBound
        parameter.Path = path
        return parameter


    def create_sensitivity_model(method='Sobol', **kwargs):
        ses_model = model.find_model(method)
        parameter = set_sensitivity_factor(name="CN2", path="Field.Soil.SoilWater.CN2Bare", LowerBound=70.0,
                                           UpperBound=85.0)
        parameter2 = set_sensitivity_factor(name="CN2", path="Field.Soil.SoilWater.SummerCona", LowerBound=4.0,
                                           UpperBound=9)

        sens = ses_model()


        model.add_model(model_type=sens, adoptive_parent=Models.Core.Simulations)
        sens = model.Simulations.FindInScope[ses_model](method)
        sens.set_TableName("Report")
        sens.set_AggregationVariableName('[Clock].Today')
        sens.Parameters.Add(parameter2)
        sens.Parameters.Add(parameter)
        model.move_model(model_type=Models.Core.Simulation, new_parent_type=ses_model)
        model.save()
        return model


    sob.get_BaseSimulation
    # doctest.testmod()
    for i in dir(sob):
        if 'get' in i:
            print(i)
            att = getattr(sob, i)
            if callable(att):
                try:
                    print(att())
                except Exception as e:
                    ...
            else:
                print(att)
        else:
            print(i, '__')
    mo = create_sensitivity_model()



