import sys
from pathlib import Path

import pandas as pd
from utils import rmse, fit_pearson
from apsimNGpy import SensitivityManager, ApsimModel
from maize_parameters import maize_params
from xlwings import view
from itertools import combinations
import winsound
from sqlalchemy import create_engine

DataBAse = Path(__file__).parent / 'sens.db'
soilPrefixes = ['N', 'F', 'S']


def get_last_two_from_path(path: str, step) -> str:
    ap = path.split('.')[-step:]
    return '.'.join(ap)


def get_soil_parameters(model):
    su_om_name = model.inspect_model('Models.Surface.SurfaceOrganicMatter', fullpath=True)[0]
    su_om_name = get_last_two_from_path(su_om_name, 2)
    organic_name = model.inspect_model('Models.Soils.Organic', fullpath=True)[0]
    organic_name = get_last_two_from_path(organic_name, 3)
    surfom = [
        {'Path': f'{su_om_name}.InitialResidueMass', 'LowerBound': 500, 'UpperBound': 5000, 'Name': 'ResidueMass'},
        {'Path': f'{su_om_name}.InitialCNR', 'LowerBound': 40, 'UpperBound': 180, 'Name': 'CNR'}]
    organic = [
        {'Path': f"{organic_name}.FBiom[1]", 'LowerBound': 0.03, 'UpperBound': 0.045, 'Name': 'FBiom'},
        {'Path': f"{organic_name}.Carbon[1]", 'LowerBound': 0.9, 'UpperBound': 3.5, 'Name': 'InitialCarbon'},
        {'Path': f"{organic_name}.FOM[1]", 'LowerBound': 500, 'UpperBound': 8000, 'Name': 'FOM'}]

    organic.extend(surfom)
    return organic


if __name__ == '__main__':
    Engine = create_engine(f'sqlite:///{str(DataBAse)}')

    CROPS = ['Maize', 'Maize, Soybean', 'Maize, Wheat']
    for prefix in soilPrefixes:
        DATA = []
        RawResults = []
        sobolDataTable = []
        print(f'Testing {prefix}...', file=sys.stderr)
        for crop in CROPS:
            with ApsimModel(r"D:\Elimin_rye_cover_crop_2026\APSIMX\F_sobol.apsimx") as sobol:
                soil_params = get_soil_parameters(sobol)
                sobol.edit_model('Models.Sobol', model_name='Sobol', Parameters=soil_params, clear_old=True)
                sim_name = sobol[0].Name
                sobol.edit_model_by_path(f'.Simulations.Sobol.{sim_name}.Field1.Simple Rotation', Crops=crop, )
                sobol.edit_model('Models.Sobol', 'Sobol', NumPaths=200)
                sobol.run(timeout=60 * 60)
                df = sobol.get_simulated_output('SobolStatistics')
                sobolDataTable.append(df)
                df.reset_index(inplace=True, drop=True)

                result = (
                    df.groupby(['Parameter', 'ColumnName', 'Indices'])
                    .mean(numeric_only=True)
                    .unstack(['Indices'])
                )
                result.columns = [
                    f"{col}_{idx}"
                    for col, idx in result.columns
                ]
                result['crops'] = crop
                winsound.Beep(1200, 450)
                DATA.append(result)
                RawResults.append(sobol.results)
        data = pd.concat(DATA)
        RawDf = pd.concat(RawResults)
        sobolStatRawDF = pd.concat(sobolDataTable)
        data['soil'] = prefix
        raw_result_table = f'{prefix}_raw_results'
        statistics = f'{prefix}_summary_statistics'
        sobStaticsTable = 'SobolStatistics'
        data.to_sql(statistics, con=Engine, if_exists='replace')
        RawDf.to_sql(raw_result_table, con=Engine, if_exists='replace')
        sobolStatRawDF.to_sql(sobStaticsTable, con=Engine, if_exists='replace')

        d1 = DATA[0].sort_values(['ColumnName', 'Parameter'], ascending=False)
        d2 = DATA[1].sort_values(['ColumnName', 'Parameter'], ascending=False)

        d1['original_FirstOrder'] / d2['original_FirstOrder'] * 100
        rmse(d1['original_FirstOrder'], d2['original_FirstOrder'])
        fit_pearson(d1['original_FirstOrder'], d2['original_FirstOrder'])
        combs = list(combinations(['Maize', 'Maize, Soybean', 'Maize, Wheat'], 2))
        for comb in combs:
            first, end = comb
            idx1, idx2 = CROPS.index(first), CROPS.index(end)
            d1 = DATA[idx1].sort_values(['ColumnName', 'Parameter'], ascending=False)
            d2 = DATA[idx2].sort_values(['ColumnName', 'Parameter'], ascending=False)
            fit = fit_pearson(d1['original_FirstOrder'], d2['original_FirstOrder'])
            print(comb)
            print(fit)
            print(rmse(d1['original_FirstOrder'], d2['original_FirstOrder']))
        del data, DATA
        import gc

        gc.collect()

# selected = {}
# with SensitivityManager('Maize') as model:
#     # model.add_sens_factor()
#     counter = 0
#     for p, params in maize_params.items():
#         # if p != 'Grain':
#         #     continue
#         for path, value in params.items():
#             sp = path.split('.')
#             print(sp)
#             ap = hash(path)
#             try:
#                 # name = f"{sp[1]}_{counter}_{sp[-2]}"
#                 name = path.replace('.', '_')
#                 name = name.replace('[', '_').replace(']', '_')
#             except IndexError:
#                 name = path.replace('.', '_')
#                 name = name.replace('[', '_').replace(']', '_')
#             name = name.removeprefix('_Maize__')
#
#             pat = f'{path}.FixedValue'
#             v = round(float(value), 3)
#             upper, lower = 1.5 * v, round((0.5 * v), 4)
#             if lower == 0:
#                 continue
#             selected[name] = path
#             model.add_sens_factor(name=name, path=pat, lower_bound=lower, upper_bound=upper)
#             print(path, value)
#             counter += 1
#     model.build_sense_model(method='Morris',
#                             aggregation_column_name='Clock.Today',
#                             num_path=25,
#                             intervals=20,
#                             jumps=10)
#     # model.open_in_gui(watch=True)
#     model.run()
#     print(model.inspect_model('Models.Report'))
#     ms = model.get_simulated_output('MorrisStatistics').dropna()
#     ms.to_csv('MorrisStatistics.csv')
#     mpa = model.get_simulated_output('MorrisPathAnalysis').dropna()
#     mpa.to_csv('MorrisPathAnalysis.csv')
#     model.results.to_csv('results.csv')
#     import os
#
#     os.startfile('MorrisStatistics.csv')
#     os.startfile('MorrisPathAnalysis.csv')
#     fips = set(mpa.Parameter)
#     summary = mpa.groupby('Parameter').mean(numeric_only=True)
#     summary.sort_values(by='Yield.MuStar', ascending=False, inplace=True)
#     import time
#     time.sleep(2)
#     view(summary)
#     # analyze_from_dataframe(model.results, X= list(selected.keys()), Y='Yield')
#     # ============================================================
#     # EXAMPLE
#     # ============================================================
#     from salib_helpers import MorrisAnalyzer
#
#     pass
