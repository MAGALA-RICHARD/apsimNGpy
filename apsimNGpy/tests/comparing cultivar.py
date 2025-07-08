from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core._modelhelpers import Models, ModelTools

class CompareCultivar(ApsimModel):
    def __init__(self, model, out_path=None):
        super().__init__(model=model, out_path=out_path)
        self.base_simulations = None

    def refresh_base_simulations(self):
        if self.base_simulations is None:
            base_sim = self.Simulations.FindInScope[Models.Core.Simulation]()
            base_sim = ModelTools.CLONER(base_sim)
            self.base_simulations = base_sim
        return self.base_simulations

    def simulate_different_cultivars(self, cultivar_names):
        cultivars = self.inspect_model('Cultivar', fullpath=False)
        lower = dict(zip([i.lower() for i in cultivars], cultivars))

        return lower


    model = ApsimModel('Maize')
    model.add_factor(specification="[Sow using a variable rule].Script.CultivarName = B_110, A_90")



if __name__ == '__main__':
    #model = CompareCultivar(model='Maize')
    model = ApsimModel('Maize')
    model.create_experiment(permutation=False)
    model.add_factor(specification="[Sow using a variable rule].Script.CultivarName =  'Laila', B_110, A_90")