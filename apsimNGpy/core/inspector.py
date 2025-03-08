from pprint import pprint

from apsimNGpy.core.core import APSIMNG, Models


class Inspector(APSIMNG):
    def __init__(self, model, out_path=None, **kwargs):
        super().__init__(model, out_path, **kwargs)

    @property
    def in_simulations(self):
        return self.find_simulations()

    @property
    def managers(self):
        """
        Returns a list of managers by simulations
        @return:
        """
        managers = {}
        for sim in self.in_simulations:
            managers[sim.Name] = sim.FindAllDescendants[Models.Manager]()
            return managers

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
        datastorage= self.Simulations.FindAllDescendants[Models.Report]()
        print(datastorage)


if __name__ == '__main__':
    from pathlib import Path
    from apsimNGpy.core.base_data import load_default_simulations

    xp = Path(r"D:\package\ApsimX\Models").rglob('*.cs')
    models = []
    mod = Inspector(load_default_simulations(crop="maize", simulations_object=False))
    xt = mod.get_manager_ids(True, verbose=True)
    print(xt)
