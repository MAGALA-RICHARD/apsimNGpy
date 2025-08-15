# running factorial experiments
if __name__ == '__main__':
    import os
    from matplotlib import pyplot as plt
    from apsimNGpy.core.experimentmanager import ExperimentManager as Experiment
    experiment = Experiment("Maize", )
    experiment.init_experiment(permutation=True)
    experiment.add_factor("[Fertilise at sowing].Script.Amount = 0, 300")
    experiment.add_factor(specification="[Sow using a variable rule].Script.CultivarName = \
                       Dekalb_XL82, Melkassa, B_110, Pioneer_34K77",
                          )
    experiment.run()
    df = experiment.results
    g = experiment.cat_plot(x='Amount', y="Yield", kind='bar', aspect=1, height=8, hue='CultivarName')
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.xlabel('Nitrogen fertilizers (kg ha $^{-1}$)', fontsize=16)
    plt.ylabel(r'Corn grain yield (kg ha $^{-1}$)', fontsize=16)
    plt.savefig("Maize_experiment.png")


    os.startfile("Maize_experiment.png")
    plt.close()
    df.groupby(['Amount', 'CultivarName'])['Yield'].mean()

