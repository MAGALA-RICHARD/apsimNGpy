import gc
import os

import pandas as pd

from apsimNGpy.core_utils.database_utils import read_db_table
from data_server import merge_soil_statistics
import matplotlib.pyplot as plt
import seaborn as sns

sob = merge_soil_statistics()

data = sob[
    (sob['Indices'] != 'Total') &
    (sob['ColumnName'].isin(['AGB', 'Yield', 'TopN2O', 'soc0_10cm']))
]


for soil in data['SoilType'].unique():
    # for crop in set(data['Crops']):
        crop =''
        file_name = f"{crop}{soil}_heatmap.png"
        tmp = data[(data['SoilType'] == soil) ].copy()

        pivot = tmp.pivot_table(
            index='Parameter',
            columns='ColumnName',
            values='original',
            aggfunc='mean'
        ).copy()

        plt.figure(figsize=(8, 10))
        sns.heatmap(
            pivot,
            cmap='viridis_r',
            annot=True,
            fmt='.2f'
        )
        plt.title(f"{crop} {soil}")
        plt.ylabel('')
        plt.tight_layout()
        plt.savefig(file_name)
        os.startfile(file_name)
        plt.close()
        tmp['cn'] = pd.Categorical(tmp['ColumnName'], ordered=True).copy()
        sns.catplot(tmp, x='Parameter', y='original', hue='cn', showfliers=False,  kind='box', height=10, )
        plt.xticks(rotation=60)
        plt.tight_layout()
        plt.title(f"{crop} {soil}")
        file_name = f"b_{crop}{soil}_heatmap.png"
        plt.savefig(file_name)
        #os.startfile(file_name)
        plt.close()
        del tmp, pivot
        gc.collect()