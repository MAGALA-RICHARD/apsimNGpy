import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from data_server import merge_soil_statistics

data = merge_soil_statistics()

outputs = ['AGB', 'Yield', 'soc0_10cm', 'TopN2O', 'NO3Total']

data = data[
    (data['Indices'] != 'FirstOrder') &
    (data['ColumnName'].isin(outputs))
].copy()

ranked = (
    data.groupby(
        ['SoilType', 'Crops', 'ColumnName', 'Parameter'],
        as_index=False
    )['original']
    .mean()
)

ranked['Rank'] = (
    ranked.groupby(['SoilType', 'Crops', 'ColumnName'])['original']
    .rank(ascending=False, method='first')
    .astype(int)
)

parameter_order = (
    ranked.groupby('Parameter')['Rank']
    .mean()
    .sort_values()
    .index
)

for soil in sorted(ranked['SoilType'].unique()):

    soil_data = ranked[ranked['SoilType'] == soil]

    for crop in sorted(soil_data['Crops'].unique()):

        tmp = soil_data[soil_data['Crops'] == crop]

        mat = (
            tmp.pivot(
                index='Parameter',
                columns='ColumnName',
                values='Rank'
            )
            .reindex(parameter_order)
        )

        mat = mat[outputs]  # keep output order

        n_parameters = mat.shape[0]

        plt.figure(figsize=(7, max(6, n_parameters * 0.4)))

        sns.heatmap(
            mat,
            annot=True,
            cmap='Blues_r',
            cbar=False,
            linewidths=0.5,
            fmt='d',
            vmin=1,
            vmax=n_parameters
        )

        plt.title(
            f'{soil} - {crop}\n'
            'Parameter Rank (1 = Most Influential)'
        )

        plt.xlabel('Output')
        plt.ylabel('Parameter')
        plt.tight_layout()

        fname = f'{soil}_{crop}_rank_heatmap.png'.replace(' ', '_')

        plt.savefig(fname, dpi=300, bbox_inches='tight')
        plt.close()

        os.startfile(fname)