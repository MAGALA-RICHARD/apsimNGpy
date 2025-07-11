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

    def simulate_different_locations(self, locations:list[tuple]):
        sim = self.refresh_base_simulations()

        sims = self.Simulations.FindAllInScope[Models.Core.Simulation]()
        for s in sims:

            ModelTools.DELETE(s)
        for lonlat in locations:
            sim_name = f"sim_{lonlat[0]}_{lonlat[1]}"
            clone_sim = ModelTools.CLONER(sim)
            print(clone_sim)
            clone_sim.Name = sim_name
            ModelTools.ADD(clone_sim, self.Simulations)



    def simulate_different_cultivars(self, cultivar_names):
        cultivars = self.inspect_model('Cultivar', fullpath=False)
        lower = dict(zip([i.lower() for i in cultivars], cultivars))

        return lower


    model = ApsimModel('Maize')
    model.add_factor(specification="[Sow using a variable rule].Script.CultivarName = B_110, A_90")



if __name__ == '__main__':
    #model = CompareCultivar(model='Maize')
    import pandas as pd
    mod = CompareCultivar('Maize')
    lonlat_iowa = [
        (-96.4003, 42.5006),  # Sioux City (NW)
        (-94.1680, 42.0347),  # Fort Dodge (N Central)
        (-96.7870, 41.2619),  # Council Bluffs (SW)
        (-93.6208, 41.5868),  # Des Moines (Central)
        (-93.0977, 41.0239),  # Osceola (South Central)
        (-91.5302, 41.6611),  # Iowa City (SE)
        (-91.1800, 42.5006),  # Dubuque (NE)
        (-94.7403, 41.3303),  # Atlantic (SW)
        (-92.9108, 42.0354),  # Marshalltown (Central East)
        (-92.4083, 41.2960),  # Ottumwa (SE)
        (-90.5736, 41.5236),  # Davenport (far East)
        (-92.4499, 41.5772),  # Oskaloosa (SE Central)
        (-95.8547, 41.7370),  # Harlan (West Central)
        (-93.7680, 43.3841),  # Northwood (North)
        (-94.1564, 43.0731),  # Estherville (Northwest)
        (-91.1129, 40.8075),  # Keokuk (far SE)
        (-95.0289, 42.0350),  # Carroll (Central West)
        (-93.9179, 42.4975),  # Humboldt (North Central)
        (-93.6020, 40.7398),  # Lamoni (South Central)
        (-91.6710, 41.2417),  # Washington (SE)
    ]
    mod.simulate_different_locations(lonlat_iowa)

    pd.set_option('display.max_columns', None)

    # model = ApsimModel('Maize')
    # model.create_experiment(permutation=False)
    # model.add_factor(specification="[Sow using a variable rule].Script.CultivarName =  Dekalb_XL82, Melkassa, Pioneer_34K77, Laila, B_110, A_90")
    # model.run()
    # df = model.results
    # from matplotlib import pyplot as plt
    #
    # ax = df.boxplot(column='Yield', by='CultivarName',figsize=(10,8), grid=False)
    #
    # # Customize the plot
    # plt.title('Maize yield boxplot grouped by Cultivar', fontsize=20)
    # plt.suptitle('')  # Remove the default automatic title
    # plt.xlabel('Cultivar Name', fontsize=20)
    # plt.ylabel('Maize Yield (kg ha$^{-1}$)',fontsize=20 )
    #
    # plt.savefig(r'D:\PACKAGES\apsimNGpy-documentations\images/Cultivar_Maize.png', dpi=600)
    #
    # import seaborn as sns
    # import matplotlib.pyplot as plt
    #
    # plt.figure(figsize=(10, 6))
    #
    # # Lineplot grouped by CultivarName
    # df['Year'] = [date.year for date in pd.to_datetime(df['Clock.Today'])]
    # sns.lineplot(data=df, x='Year', y='Yield', hue='CultivarName', marker='o')
    #
    # # Labels and formatting
    # plt.title('Maize Yield Over Years by Cultivar', fontsize=16)
    # plt.xlabel('Year', fontsize=14)
    # plt.ylabel('Maize Yield (kg ha$^{-1}$)', fontsize=14)
    # plt.legend(title='Cultivar', bbox_to_anchor=(1.05, 1), loc='upper left')
    # plt.tight_layout()
    #
    # # Save before showing
    # plt.savefig(r'./Cultivar_Maize_Yield_Lineplot.png', dpi=600)
    # plt.show()
    #
