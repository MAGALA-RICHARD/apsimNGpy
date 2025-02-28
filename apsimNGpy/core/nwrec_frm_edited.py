import logging
import os
import traceback
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pygments.lexers import nit
import copy
from config import *

info = 'info'
error = 'error'
SoilTable = 'SERF'

from apsimNGpy.core.apsim import ApsimModel

run = True
if __name__ == '__main__' and run:
    apsi_m = wdi.path(name='apsim/baseC.apsimx')
    directory = wdi.path(name='NWREC_edited')
    wdi.mkdir('NWREC_edited')
    model = ApsimModel(apsi_m)
    plot_path = {}
    Crops = 'Maize'
    nw_csv = pd.read_csv(wdi.path(name='observed_soc.csv'))


    # NREW N fertilizer was 246
    def _mgt(crop, depth=350, n_amount=200):
        print(crop)
        if 'Soybean' in crop:
            n_amount = 170
        sowManager = {"Name": 'MaizeNitrogenManager', 'Amount': n_amount}
        return [{"Name": 'Simple Rotation', 'Crops': crop},
                {'Name': 'Tillage', 'Depth': depth, 'AppplyTillageOption': 'no', 'Fraction': 0.65}, sowManager]


    apsim_edited_files = joblib.load(os.path.join(directory, 'edited_files.joblib'))
    scratch = Path.cwd() / 'scratch'
    scratch.mkdir(exist_ok=True)
    DATA = [ApsimModel(filename).run(['MaizeR', "Carbon", "Annual"]).results for filename in
            apsim_edited_files.values()]
    for data, plot in zip(DATA, apsim_edited_files.keys()):
        data['plotid'] = plot
    predicted = pd.concat(DATA)
    mYield = predicted[~np.isnan(predicted['Maize_Yield'])].copy()
    mYield.dropna(subset='Year', inplace=True)
    mYield.rename(columns={'Year': 'year'}, inplace=True)
    socP = predicted[~np.isnan(predicted['SOC1'])].copy()
    socP['year'] = pd.DatetimeIndex(socP.Date).year.to_list()
    all_df = pd.merge([socP, nw_csv], how=inner, on=['plotid', 'year'])
    df_merged = nw_csv.drop_duplicates(subset=['plotid', 'depth', 'year'])

    data = df_merged.copy()

    data['socx'] = data['SOC1'] / (data['BD'] * data['depth'])
    data['Carbon'] = data['Carbon'] / 10
    # data.to_csv(wdi.path(name='carbon.csv'))
    dat = data.copy()
    # data = dat[dat['year']==2014.0].copy()
    val = validate(actual=data.Carbon, predicted=data.socx)
    ev_all = val.evaluate_all(verbose=True)
    X = data[['Carbon']].values
    y = data['socx'].values
    plot_reg_fit(X, y, data=data)

    C_yield = load_AGRON(Yield, XLs[SoilTable])
    mY = validate(actual=C_yield.obs / 1000, predicted=C_yield.Maize_Yield / 1000)
    mY.evaluate_all(verbose=True)
    from apsimNGpy.visual.visual import quick_plot

    print(C_yield)
    plot_po(xx=data.year, predicted=data.socx, observed=data.Carbon, anotate_with=data.plotid)
    data.to_csv(wdi.path(name='ccs.csv'))
