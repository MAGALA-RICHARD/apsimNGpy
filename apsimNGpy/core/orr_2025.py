import logging
import os
import traceback

import matplotlib.pyplot as plt
from pygments.lexers import nit
import copy
from config import *

logger = DualLogger()
cap = ORR
info = 'info'
error = 'error'
SoilTable = 'ORR'


def _filter_Comp(_sdata, comp_name):
    return _sdata[_sdata['componentname'] == comp_name].copy()


series = 'soilseriesname1'

Thickness = [200, 100, 200, 200, 200, 250, 300, 300, 350, 250]
comp_names = ['Osco', 'Sable', 'Muscatune', 'Drummer', 'Denny', 'Edgington',
              'Ipava', 'Elburn', 'Buckhart']

getSoils = pd.read_excel(cap, sheet_name='Soil')
_soils = getSoils.dropna(subset=['plotid']).copy()


def cleanLoadSoilDf(cap_xlsx_path, soil_table_db_name, filter_from: int = 2012):
    Cp_names = COMPS[soil_table_db_name]
    """ a dat frame of soils form a cap experimental sites
     soil_df: pandas dataframe containing soils properties or results from the experiment
     filter_from:int - the year to filter out defaults to 2011
     """
    # load plot data
    #########################################################
    try:
        Sdata_tables = read_db_table(wdi.path(name='NWREC_db.DB_MP'), report_name=soil_table_db_name)

        SPdata = Sdata_tables.copy(deep=True)
        cn = SPdata.componentname.unique().tolist()

        STables = {comps: _filter_Comp(SPdata, comps) for comps in cn}

        soilProfiles = {}
        for Comps in STables.keys():
            try:
                des = OrganizeAPSIMsoil_profile(STables[Comps], thickness=20, state='Michigan').cal_missingFromSurgo()
                soilProfiles[Comps] = des
            except ValueError as e:
                pass
        newValidComps = soilProfiles.keys()

        plots = pd.read_excel(cap_xlsx_path, sheet_name='Plot Identifiers')
        plots = plots[(plots['soil_data'] == 'yes') & (plots['agro_data'] == 'yes') & (
                plots['tillage'] == 'TIL2')]
        if plots.empty:
            raise ValueError('plots empty+++++++++++++++++')
        else:
            print(plots)
        plt_soil = plots.drop_duplicates(['plotid', 'soilseriesname1'])
        print(plt_soil['soilseriesname1'].unique())
        new_sdf = plt_soil.loc[plt_soil['soilseriesname1'].isin(newValidComps)]

        crop_data = ['2011crop', '2012crop', '2013crop', '2014crop', '2015crop']
        rep = {'Corn': 'Maize'}
        plt_soil = plt_soil
        plt_soil.replace(rep, inplace=True)
        cps = plt_soil[crop_data].copy()
        cropSequences = [create_crop_sequence(cps, n) for n in cps.index.to_list()]
        print(plt_soil.shape)
        plt_soil['cropSequences'] = cropSequences
        # load soils data sheet name is soils
        ###########################################################################
        soil_dff = pd.read_excel(cap_xlsx_path, sheet_name='Soil')
        soilDF = soil_dff.copy(deep=True)
        _soiD = soilDF.drop([0, 1], axis=0).copy()
        soils = _soiD[_soiD['year'] == filter_from]
        print(_soiD.year.unique())
        print(soils.shape)
        soc = 'SOIL13'
        ph = 'SOIL11'
        bd = 'SOIL01'
        nitrates = 'SOIL15'
        dul = 'SOIL31'
        l15 = 'SOIL32'
        # new_sdf['plotid'] = new_sdf['plotid'].astype('float')
        # soils['plotid'] =  soils['plotid'].astype('float')
        grad_x = new_sdf.merge(soils, on='plotid', how='inner')
        print('merge_succeeded')
        grad_x.rename(columns={soc: 'Carbon', ph: 'PH', bd: 'BD', nitrates: 'N03', dul: 'DUL', l15: 'LL15'},
                      inplace=True)
        kpSoils = soil_dff.rename(columns={soc: 'Carbon', ph: 'PH', bd: 'BD', nitrates: 'N03', dul: 'DUL', l15: 'LL15'},
                                  inplace=False).copy()
        cpd = new_sdf[crop_data].copy()
        new_sdf['cropSequences'] = [create_crop_sequence(cps, n) for n in cpd.index.to_list()]
        dtm = grad_x, kpSoils, soilProfiles, new_sdf

        return dtm
    except Exception as e:
        logger('info', f" {traceback.format_exc()}, {repr(e)}")


def _ratio(ar):
    return ar / ar[0]


grad_x, kpSoils, soilProfiles, new_sdf = cleanLoadSoilDf(XLs[SoilTable], soil_table_db_name=SoilTable)


def organize(df, plotid):
    try:
        if df.shape[0] == 0:
            raise ValueError('No data to organize, \n')
        """
        Organize the soils by plotid
        :param df:
        :param plotid:
        :return:
        """
        _df = df[df['plotid'] == plotid].copy()

        cp_id = _df['soilseriesname1'].iloc[0]
        till = _df['tillage'].iloc[0]

        _df.drop_duplicates(['depth'], inplace=True)
        _df = _df.copy()
        _df = _df[(_df['depth'] == '10 to 20') | (_df['depth'] == '0 to 10')].copy()
        _df = _df[['DUL', "BD", 'LL15', 'PH', 'Carbon']].copy()

        variable = _df
        variable.replace('M', -999, inplace=True)
        variable = variable.astype(float)
        variable = variable.mean(numeric_only=True).to_frame().T.copy()
        data_2 = soilProfiles.get(cp_id)

        data_ = copy.deepcopy(data_2)
        bd = np.array(data_[0]['BD'])
        dul = np.array(data_[0]['DUL'])
        l15 = np.array(data_[0]['LL15'])
        _carbon = np.array(data_[1]['Carbon'])
        ad = np.array([0.5, 0.8, 0.8, 1, 1, 1, 1, 1, 1, 1])
        assert len(ad) == 10, 'Length not equal to target'

        def _check_naN(param):
            varT = variable[param].to_list()
            if varT[0] == -999:
                # print(param, 'will not be imputed because it is empty or missing')
                return None
            else:
                print(f"{param}: passed")
                return True

        if _check_naN('BD'):
            data_[0]['BD'] = _ratio(bd) * np.array(variable.get('BD')).tolist()
        if _check_naN('DUL'):
            data_[0]['DUL'] = _ratio(dul) * np.array(variable.get('DUL')).tolist()
        if _check_naN('LL15'):
            data_[0]['LL15'] = _ratio(l15) * np.array(variable.get('LL15')).tolist()
        if _check_naN('Carbon'):
            data_[1]['Carbon'] = _ratio(_carbon) * np.array(variable.get('Carbon') / 10).tolist()
        # adjust SAT according to Bulk-density
        data_[0]['SAT'] = 1 - (data_[0]['BD'] / 2.65)
        saT, duL = data_[0]['SAT'].copy(), data_[0]['DUL'].copy()
        if till == 'TIL1':
            print('No tillage detected')
            data_[0].loc[0, 'BD'] = data_[0].loc[0, 'BD'] * 0.97
            data_[1].loc[0, 'FBiom'] = 0.4
            data_[1].loc[0, 'FInert'] = 0.8
            data_[1].loc[1, 'FInert'] = 0.9
        print('adjusting SAT & DUL')

        def adjustSatDul(sat_, dul_):
            for enum, (s, d) in enumerate(zip(sat_, dul_)):
                # first check if they are equal
                # if d is greater than s, then by what value?, we need this value to add it to 0.02
                #  to be certain all the time that dul is less than s we subtract the summed value
                if d >= s:

                    diff = d - s
                    if diff == 0:
                        dul_[enum] = d - 0.02
                    else:
                        duL[enum] = d - (diff + 0.02)


                else:
                    dul_[enum] = d
            return dul

        duL = adjustSatDul(saT, duL)
        data_[0]['DUL'] = list(duL)

        data_[0]['AirDry'] = list(np.array(data_[0]['LL15']) * ad)
        return data_
    except (IndexError, TypeError) as ide:
        pass


# od = organize(grad_x, plotid= 1071.0)

calSoilProfiles = {}
for i in new_sdf['plotid']:
    print('filling missing data')
    try:

        xp = organize(grad_x, i)
        calSoilProfiles[i] = xp
    # vc= xp[0].SAT
    except Exception as e:
        logger(error, f"Full traceback: {traceback.format_exc()}")
        pass

from apsimNGpy.core.apsim import ApsimModel

run = True
PLots = [1052.0,
         1081.0,
         1092.0,
         2012.0,
         2052.0,
         2071.0,
         3011.0,
         3062.0,
         3101.0,
         4031.0,
         4062.0,
         4082.0]
if __name__ == '__main__' and run:
    apsi_m = wdi.path(name='apsim/baseC.apsimx')
    directory = wdi.path(name='NWREC_edited')
    wdi.mkdir('NWREC_edited')
    model = ApsimModel(apsi_m)
    plot_path = {}
    Crops = 'Maize'


    # NREW N fertilizer was 246
    def _mgt(crop, depth=350, n_amount=220):

        if 'Soybean' in crop:
            n_amount = 170
        sowManager = {"Name": 'MaizeNitrogenManager', 'Amount': n_amount}
        return [{"Name": 'Simple Rotation', 'Crops': crop},
                {'Name': 'Tillage', 'Depth': depth, 'AppplyTillageOption': 'no', 'Fraction': 0.65}, sowManager]


    predicted = []
    pYield = []
    those = []
    for i in PLots:
        pp = [i]
    for soils_s in PLots:  # calSoilProfiles.keys():#calSoilProfiles.keys():
        # th = str(soils_s)
        # if th.count('31')> 0:
        try:
            croP = new_sdf[new_sdf['plotid'] == soils_s]['cropSequences'].iloc[0]

            out_path = os.path.join(directory, f"{soils_s}.apsimx")
            _model = ApsimModel(apsi_m, thickness_values=Thickness)
            sdp = copy.deepcopy(calSoilProfiles[soils_s])
            _model.replace_downloaded_soils(sdp, simulation_names=_model.extract_simulation_name)
            # _model.replace_met_file(mETS[SoilTable], simulations=model.extract_simulation_name)
            _model.update_mgt(_mgt(croP))
            mf = _model.show_met_file_in_simulation()
            # print(croP)
            if croP.count('Maize') > 4:
                print(croP, '++_________')
                _model.save_edited_file(outpath=out_path)
                # _model = ApsimModel(out_path)
                _model.run(dynamicReportSpec(croP, Maize=['Annual', 'MaizeR']))
                pc, Yield = _model.results
                pc['plotid'] = soils_s
                # pc['year'] = pc['an_Year'].astype(float)
                pc['CropSequences'] = croP
                Yield['year'] = Yield['Year'].astype(float)
                Yield['plotid'] = soils_s
                Yield['CropSequences'] = croP
                plot_path[soils_s] = out_path
                those.append(soils_s)
                predicted.append(pc)
                # os.startfile(_model.path)
                print(soils_s, ":::", croP)

                pYield.append(Yield)
        except IndexError:
            pass
    import joblib

    predicted_ = pd.concat(predicted)
    Yield = pd.concat(pYield)
    joblib.load(os.path.join(directory, 'orr_edited_files.joblib'))
    apprent_plots = plot_path.keys()
    soc = kpSoils[kpSoils['plotid'].isin(apprent_plots)].copy()
    soc1 = soc.drop_duplicates(subset=['plotid', 'depth', 'year'])
    soc2 = soc1[soc1['Carbon'] != 'M'].copy()
    soc3 = soc2[['plotid', 'depth', 'year', 'Carbon', 'BD']].copy()
    soc4 = soc3[(soc3['depth'] == '10 to 20') | (soc3['depth'] == '0 to 10')].copy()

    soc4['Carbon'] = soc4['Carbon'].astype('float')
    soc4 = soc4[soc4 != 'M'].dropna().copy()
    soc4['BD'] = soc4['BD'].astype('float')
    grp_agg = {"Carbon": 'mean', 'BD': 'mean'}
    soc5 = soc4.groupby(['plotid', 'year']).agg(grp_agg)
    soc5.reset_index(inplace=True)
    soc5['depth'] = 20
    df = soc5.copy()
    df['soc'] = df['depth'] * df['BD'] * (df['Carbon'] / 10)
    predicted_.rename(columns={'an_Year': 'year'}, inplace=True)
    df.to_csv(wdi.path(name='observed_soc.csv'))
    data = df.merge(predicted_, on=['plotid', 'year'], how='inner')
    data['socx'] = data['SOC1'] / (data['BD'] * data['depth'])
    data['Carbon'] = data['Carbon'] / 10
    data.to_csv(wdi.path(name='carbon.csv'))
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

    # print(C_yield)
    plot_po(xx=data.year, predicted=data.socx, observed=data.Carbon, anotate_with=None)
    data.to_csv(wdi.path(name='ccs.csv'))

    print(those)
