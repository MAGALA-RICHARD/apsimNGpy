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
        ids = []
        for sim_name, manager in self.managers.items():
            if full_path:
                ids.extend([i.FullPath for i in manager])
            elif not full_path:
                ids.extend([i.Name for i in manager])
            if verbose:
                pprint(ids, indent=4)
            return ids

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


if __name__ == '__main__':
    from apsimNGpy.core.base_data import load_default_simulations

    mod = Inspector(load_default_simulations(crop="maize", simulations_object=False))
    xt = mod.get_manager_ids(False)
    print(xt)
