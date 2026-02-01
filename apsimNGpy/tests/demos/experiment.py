import os
from apsimNGpy.core.experimentmanager import ExperimentManager
from matplotlib import pyplot as plt

exp = ExperimentManager("Maize",)
exp.init_experiment(permutation=True)
exp.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 50",
               factor_name='Nitrogen')
exp.add_factor(specification="[Sow using a variable rule].Script.Population = 4, 6, 10",
               factor_name='Population')

exp.run()
exp.cat_plot(x='Population', y='Yield', hue='Nitrogen', table='Report', kind='box',)
plt.savefig('Maize_experiment.png')
os.startfile('Maize_experiment.png')
