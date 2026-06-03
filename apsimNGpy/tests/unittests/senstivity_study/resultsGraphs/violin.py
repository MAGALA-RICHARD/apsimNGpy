import os

from data_server import merge_soil_statistics
import seaborn as sns
import matplotlib.pyplot as plt
sob = merge_soil_statistics()

sns.catplot(
    data=sob,
    x='Parameter',
    y='original',
    hue='ColumnName',
    kind='violin',
    cut=0,
    inner='quartile',
    col='SoilType',
    col_wrap=2,
    height=8,
    aspect=1.5
)
plt.tight_layout()
plt.xticks(rotation=45)
plt.savefig('violin.png')
os.startfile('violin.png')

