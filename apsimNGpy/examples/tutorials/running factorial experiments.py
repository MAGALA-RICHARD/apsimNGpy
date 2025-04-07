# Quick and simple way to run factorial experiments

import pandas as pd
import seaborn as sns
sns.set_style('whitegrid')
from matplotlib import pyplot as plt
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.core.core import CoreModel

_apsim = load_default_simulations(crop='Maize', simulations_object=False)
apsim = CoreModel(_apsim)
# create experiment initiate the experiment
apsim.create_experiment(permutation=True, verbose=False)  # by default it is a permutation experiment

apsim.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20", factor_name='Nitrogen')
# use categories
apsim.add_factor(specification="[Sow using a variable rule].Script.Population =4, 10, 2, 7, 6",
                 factor_name='Population')

# %%
apsim.run(report_name='Report')
df = apsim.results
df[['population']] = pd.Categorical(['Population'])
sns.catplot(x='Nitrogen', y='Yield', hue='Population', data=df, kind='box', )
plt.show()
# running a factorial experiment that involves editing the cultivar requires a replacement

# Add a crop replacement at the top of Models.Core.Simulations

_apsim = load_default_simulations(crop='Maize', simulations_object=False)
apsimC = CoreModel(_apsim)
# create experiment initiate the experiment
apsimC.create_experiment(permutation=True, verbose=False)  # by default it is a permutation experiment
apsimC.add_factor(specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20", factor_name='Nitrogen')
# use categories
apsimC.add_factor(specification="[Sow using a variable rule].Script.Population = 4, 10, 2, 7, 6",
                  factor_name='Population')

apsimC.add_crop_replacements(_crop='Maize')
# add factor and name rue
apsimC.add_factor(specification='[Maize].Leaf.Photosynthesis.RUE.FixedValue =1.0, 1.23, 4.3', factor_name='RUE')
apsimC.run()

sns.catplot(x='Nitrogen', y='Yield', hue='RUE', data=apsimC.results, kind='bar', )
plt.show()

