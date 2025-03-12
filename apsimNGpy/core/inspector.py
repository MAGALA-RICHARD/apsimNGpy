from pprint import pprint

from apsimNGpy.core.core import APSIMNG, Models

NODES = dict(manager=Models.Manager, simulation=Models.Core.Simulation,
             plant=Models.PMF.Plant,
             clock=Models.Clock,
             weather=Models.Climate.Weather,
             soil=Models.Soils.Soil,
             physical=Models.Soils.Physical,
             replacements=Models.Core.Folder)


class Inspector(APSIMNG):
    def __init__(self, model, out_path=None, **kwargs):
        super().__init__(model, out_path, **kwargs)

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
       Returns a list of node path in the class Manager
        @return:
        """
        return self.inspect(of_class='manager')

    @property
    def path_to_soil(self):
        """
        Returns a list of node path in the class Soil
        @return:
        """
        return self.inspect(of_class='soil')

    @property
    def path_to_plants(self):
        """
        RReturns a list of node path in the class Clock
        @return:
        """
        return self.inspect(of_class='plant')

    @property
    def path_to_clock(self):
        """
        RReturns a list of node path in the class Clock
        @return:
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
    from pathlib import Path
    from apsimNGpy.core.base_data import load_default_simulations

    xp = Path(r"D:\package\ApsimX\Models").rglob('*.cs')
    models = []
    mod = Inspector(load_default_simulations(crop="maize", simulations_object=False))
    xt = mod.get_manager_ids(True, verbose=True)
    print(xt)
