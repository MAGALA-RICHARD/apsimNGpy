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
    import pandas as pd

    pd.set_option('display.max_columns', None)

    model = ApsimModel('Maize')
    model.create_experiment(permutation=False)
    model.add_factor(specification="[Sow using a variable rule].Script.CultivarName =  Dekalb_XL82, Melkassa, Pioneer_34K77, Laila, B_110, A_90")
    model.run()
    df = model.results
    from matplotlib import pyplot as plt

    ax = df.boxplot(column='Yield', by='CultivarName',figsize=(10,8), grid=False)

    # Customize the plot
    plt.title('Maize yield boxplot grouped by Cultivar', fontsize=20)
    plt.suptitle('')  # Remove the default automatic title
    plt.xlabel('Cultivar Name', fontsize=20)
    plt.ylabel('Maize Yield (kg ha$^{-1}$)',fontsize=20 )

    plt.savefig(r'D:\PACKAGES\apsimNGpy-documentations\images/Cultivar_Maize.png', dpi=600)

    import seaborn as sns
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 6))

    # Lineplot grouped by CultivarName
    df['Year'] = [date.year for date in pd.to_datetime(df['Clock.Today'])]
    sns.lineplot(data=df, x='Year', y='Yield', hue='CultivarName', marker='o')

    # Labels and formatting
    plt.title('Maize Yield Over Years by Cultivar', fontsize=16)
    plt.xlabel('Year', fontsize=14)
    plt.ylabel('Maize Yield (kg ha$^{-1}$)', fontsize=14)
    plt.legend(title='Cultivar', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    # Save before showing
    plt.savefig(r'./Cultivar_Maize_Yield_Lineplot.png', dpi=600)
    plt.show()

