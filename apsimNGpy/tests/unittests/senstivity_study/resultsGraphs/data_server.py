import os

from apsimNGpy.core_utils.database_utils import read_db_table, get_db_table_names
import sys
from pathlib import Path

base_path = str(Path(__file__).parent.parent)
sys.path.append(base_path)
from main import DataBAse, soilPrefixes, cultivarDB
import seaborn as sns
from matplotlib import pyplot as plt
from xlwings import view
import pandas as pd

CROPROTATIONS = ['Maize', 'Maize, Soybean', 'Maize, Wheat']
PREFIXEs = ['S', 'N', 'F']
soil_type = dict(zip(PREFIXEs, ['sharspburg', 'Nicollet', "Fayette"]))

#print(get_db_table_names(cultivarDB))


def merge_soil_statistics():
    stats = []
    for p in PREFIXEs:
        df = read_db_table(cultivarDB, f'{p}SobolStatistics')
        df['SoilType'] = soil_type[p]
        stats.append(df)
    return pd.concat(stats)


def merge_crop_rotation_statistics(crop):
    crp = []
    for cp in PREFIXEs:
        df = read_db_table(cultivarDB, f'{cp}SobolStatistics')
        cdf = df[df['Crops'] == crop].copy()
        crp.append(cdf)
    return pd.concat(crp)


tabs = get_db_table_names(DataBAse)
if __name__ == '__main__':
    sob = merge_soil_statistics()
    data = sob[sob['Indices'] != 'FirstOrder'].copy()
    data = data[data['ColumnName'].isin(['AGB', 'Yield', "TopN2O", 'soc0_10cm'])]
    sns.catplot(data=data, x='Parameter', y='original', hue='ColumnName', kind='box', showfliers=False, aspect=1.5,
                col='SoilType', col_wrap=2,
                height=10)
    plt.xticks(rotation=270)
    plt.tight_layout()
    plt.savefig('box_plots.png')
    os.startfile('box_plots.png')
    data = sob[
        (sob['Indices'] != 'FirstOrder') &
        (sob['ColumnName'].isin(['AGB', 'Yield', 'TopN2O', 'soc0_10cm']))
        ]

    for soil in data['SoilType'].unique():
        tmp = data[data['SoilType'] == soil]

        pivot = tmp.pivot_table(
            index='Parameter',
            columns='ColumnName',
            values='original',
            aggfunc='mean'
        )

        plt.figure(figsize=(8, 10))
        sns.heatmap(
            pivot,
            cmap='viridis',
            annot=True,
            fmt='.2f'
        )
        plt.title(soil)
        plt.tight_layout()
        plt.savefig('b.png')
        os.startfile('b.png')
    result = (
        sob.groupby(['Parameter', 'ColumnName', 'Indices'])
        .mean(numeric_only=True)
        .unstack(['ColumnName']))
