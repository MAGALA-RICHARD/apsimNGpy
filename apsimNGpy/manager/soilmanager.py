import json, os, sys
from os.path import join as opj
from functools import lru_cache
from typing import Optional, Sequence, Any

import numpy as np
import numpy
import requests
import xmltodict
import pandas as pd
import time
from numpy import array as npar
import sys
from scipy import interpolate
import traceback
from datetime import datetime
import datetime
import copy
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from dataclasses import dataclass
from apsimNGpy.core_utils.soil_lay_calculator import layer_boundaries, auto_gen_thickness_layers, \
    gen_layer_bounds_from_single_thickness

from apsimNGpy.manager import show_module_deprecation
show_module_deprecation(__file__=__file__)

THICKNESS = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
hydro = {'A': 67, 'B': 78, 'C': 85, 'D': 89}

import requests
import xmltodict


@dataclass(order=True, slots=True)
class SoilsProfiles:
    """
    A class that that stores calculated soil profile data from gSSURGO
    """
    physical_properties: pd.DataFrame
    chemical_properties: pd.DataFrame
    organic_properties: pd.DataFrame
    soil_water_properties: pd.DataFrame
    meta_properties: pd.DataFrame
    swicon: pd.DataFrame
    csr: pd.DataFrame
    crops: tuple


@lru_cache(maxsize=5)
def DownloadsurgoSoiltables(lonlat, select_componentname=None, summarytable=False):
    '''
    Downloads SSURGO soil tables

    Parameters
    ------------------
    :param lonlat: tuple of (longitude, latitude)
    :param select_componentname: specific component name within the map unit, default None
    :param summarytable: if True, prints summary table of component names and their percentages
    '''

    lonLat = f"{lonlat[0]} {lonlat[1]}"
    url = "https://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx"

    # FIXED: Correct header name and value
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx/RunQuery'
    }

    body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:sdm="http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx">
       <soap:Header/>
       <soap:Body>
          <sdm:RunQuery>
             <sdm:Query>
             SELECT co.cokey as cokey, ch.chkey as chkey, comppct_r as prcent, compkind as compkind_series, 
             wsatiated_r as wat_r,partdensity as pd, dbthirdbar_h as bb, musym as musymbol, compname as componentname, 
             muname as muname, slope_r, slope_h as slope, hzname, hzdept_r as topdepth, hzdepb_r as bottomdepth, 
             awc_r as PAW, ksat_l as KSAT, claytotal_r as clay, silttotal_r as silt, sandtotal_r as sand, texcl, 
             drainagecl, om_r as OM, iacornsr as CSR, dbthirdbar_r as BD, wfifteenbar_r as L15, wthirdbar_h as DUL, 
             ph1to1h2o_r as pH, ksat_r as sat_hidric_cond, (dbthirdbar_r-wthirdbar_r)/100 as bd 
             FROM sacatalog sc
             FULL OUTER JOIN legend lg  ON sc.areasymbol=lg.areasymbol
             FULL OUTER JOIN mapunit mu ON lg.lkey=mu.lkey
             FULL OUTER JOIN component co ON mu.mukey=co.mukey
             FULL OUTER JOIN chorizon ch ON co.cokey=ch.cokey
             FULL OUTER JOIN chtexturegrp ctg ON ch.chkey=ctg.chkey
             FULL OUTER JOIN chtexture ct ON ctg.chtgkey=ct.chtgkey
             FULL OUTER JOIN copmgrp pmg ON co.cokey=pmg.cokey
             FULL OUTER JOIN corestrictions rt ON co.cokey=rt.cokey
             WHERE mu.mukey IN (
                 SELECT * from SDA_Get_Mukey_from_intersection_with_WktWgs84('point({lonLat})')
             ) 
             AND sc.areasymbol != 'US' 
             ORDER BY co.cokey, ch.chkey, prcent, topdepth, bottomdepth, muname
             </sdm:Query>
          </sdm:RunQuery>
       </soap:Body>
    </soap:Envelope>"""

    response = requests.post(url, data=body, headers=headers, timeout=140)

    if not response.ok:
        print(f"Request unsuccessful: {response.text}, response code: {response.status_code}")
        return None

    my_dict = xmltodict.parse(response.content)

    # Convert from dictionary to dataframe format
    soil_df = None
    try:
        soil_df = pd.DataFrame.from_dict(
            my_dict['soap:Envelope']['soap:Body']['RunQueryResponse']['RunQueryResult']['diffgr:diffgram'][
                'NewDataSet'][
                'Table'])
    except ValueError as e:
        pass
    if isinstance(soil_df, pd.DataFrame):
        if summarytable:
            df = soil_df.drop_duplicates(subset=['componentname'])
            summarytable = df[["componentname", 'prcent', 'chkey']]
            print("summary of the returned soil tables \n")
            print(summarytable)
        # select the dominat componet
        dom_component = soil_df[soil_df.prcent == soil_df.prcent.max()]
        # select by component name
        if select_componentname in soil_df.componentname.unique():
            componentdf = soil_df[soil_df.componentname == select_componentname]
            return componentdf
        elif select_componentname == 'domtcp':
            return dom_component

        elif select_componentname is None:

            return soil_df
        elif select_componentname != 'domtcp' and select_componentname not in soil_df.componentname.unique() or select_componentname != None:
            print(
                f'Ooops! we realised that your component request: {select_componentname} does not exists at the '
                f'specified location. We have returned the dorminant component name')
            return dom_component


# ================================Making APSIM soil profile starts here=============================
len_layers = 10
a = 1.35
b = 1.4


# create a variable profile constructor
def vary_soil_var_by_layer(nlayers, a=0.5, b=0.5):  # has potential to cythonize
    depths = np.arange(1, nlayers + 1, 1)
    if a < 0:
        print("Target parameter can not be negative")  # a * e^(-b * x).
    elif a > 0 and b != 0:
        ep = -b * depths
        term1 = (a * depths) * np.exp(ep)
        result = term1 / term1.max()
        return result
    elif a == 0 and b != 0:
        ep = -b * depths
        result = np.exp(ep) / np.exp(-b)
        return result
    elif a == 0 and b == 0:
        ans = [1] * len_layers
        return ans


def set_depth(depththickness):
    """
  parameters
  depth_thickness (array):  an array specifying the thicknness for each layer
  nlayers (int); number of layers just to remind you that you have to consider them
  ------
  return
bottom depth and top depth in a turple
  """
    # thickness  = np.tile(thickness, 10
    thickness_array = np.array(depththickness)
    bottomdepth = np.cumsum(thickness_array)  # bottom depth should nothave zero
    top_depth = bottomdepth - thickness_array
    return bottomdepth, top_depth


distparms = {'a': 0, 'b': 0.2}

from apsimNGpy.core_utils.soil_lay_calculator import layer_boundaries


@dataclass
class OrganiseSoilProfile:
    # Initiate the soil object and covert all into numpy array and change them to floating values
    sdf: pd.DataFrame
    thickness: int = None  # mm
    thickness_values: Optional[Sequence[Any]] = None
    max_depth: Optional[int] = 2000  # cm
    state: str = "Iowa"
    n_layers: Optional[int] = None
    depths: Optional[Sequence[Any]] = None

    def __post_init__(self):
        """_summary_

        Args:
            :param sdf (pandas data frame): soil table downloaded from SSURGO_
            :param thickness double: _the thickness of the soil depth e.g 20cm_
            :param bottomdepth (int, optional): _description_. Defaults to 200.
            :param thickness_values: (list or None) optional if provided extrapolation will be based on those vlue and should be the same length as the existing profile depth
         """
        sdf1 = self.sdf.drop_duplicates(subset=["topdepth"])
        surgodf = sdf1.sort_values('topdepth', ascending=True)
        csr = surgodf.get("CSR").dropna()
        if self.state == 'Iowa':
            if not csr.empty:
                self.CSR = csr.astype("float")

            else:
                self.CSR = None
        else:
            self.CSR = None
        self.clay = npar(surgodf.clay).astype(np.float16)
        self.sand = npar(surgodf.sand).astype(np.float16)
        self.silt = npar(surgodf.silt).astype(np.float16)
        self.OM = npar(surgodf.OM).astype(np.float16)
        self.topdepth = npar(surgodf.topdepth).astype(np.float16)
        self.bottomdepth = npar(surgodf.bottomdepth).astype(np.float16)
        self.BD = npar(surgodf.bb).astype(np.float16)
        self.DUL = npar(surgodf.DUL).astype(np.float64)
        self.L15 = npar(surgodf.L15).astype(np.float64)
        self.PH = npar(surgodf.pH).astype(np.float64)
        self.PAW = npar(surgodf.PAW).astype(np.float16)
        self.saturatedhudraulic_conductivity = npar(surgodf.sat_hidric_cond).astype(np.float16)
        self.KSAT = npar(surgodf.KSAT).astype(np.float16)
        self.K_SAT_r = npar(surgodf.sat_hidric_cond).astype(np.float16)
        self.particledensity = npar(surgodf.pd).astype(np.float16)
        self.muname = surgodf.muname
        self.musymbol = surgodf.musymbol
        self.cokey = surgodf.cokey
        self.slope = surgodf.slope_r
        self.componentname = surgodf.componentname

        self.wat_r = surgodf.wat_r
        self.chkey = surgodf.chkey
        self.componentpercent = surgodf.prcent
        assert any((self.thickness, self.thickness_values)), (f"one of the the thickness and thickness_values must not "
                                                              f"be {None}")
        if self.thickness_values:
            # generate from thickness values
            top, bottom = layer_boundaries(self.thickness_values)
            n__layers = len(self.thickness_values)

        else:
            # generate from a single thickness values, implying all layers have that thickness
            top, bottom = gen_layer_bounds_from_single_thickness(self.thickness, self.max_depth)
            n__layers = len(top)
            # update thickness for each depth, note that is now uniform everywhere
            self.thickness_values = list(np.full(n__layers, self.thickness))

        self.newtopdepth = top
        self.newbottomdepth = bottom
        self.Nlayers = n__layers
        self.n_layers = n__layers
        # update combined soil layer boundaries
        self.depths = [f"{a}-{b}" for a, b in zip(top, bottom)]

    # Create a function that creates a variable profile of the provided _variables
    @staticmethod
    def set_depth(depth_thickness):
        """
        parameters
        depth_thickness (array): an array specifying the thickness for each layer
        nlayers (int); number of layers just to remind you that you have to consider them
        ------
        return
      bottom depth and top depth in a turple
        """
        # thickness  = np.tile(thickness, 10
        thickness_array = np.array(depth_thickness)
        bottomdepth = np.cumsum(thickness_array)  # bottom depth should not have zero
        top_depth = bottomdepth - thickness_array
        return bottomdepth, top_depth

    def variable_profile(self, y, kind='linear'):  # has potential to cythonize
        # use the lower depth boundary because divinding by zeros is nearly impossible
        x = self.bottomdepth
        # replace x with the anticipated value of the the new soil depth
        nlayers = self.Nlayers
        xranges = x.max() - x.min()
        newthickness = xranges / nlayers
        # new depth variable for interpolation
        xnew = np.arange(x.min(), x.max(), newthickness)
        # create an interpolation function
        yinterpo = interpolate.interp1d(x, y, kind=kind, assume_sorted=False, fill_value='extrapolate')
        if isinstance(self.thickness_values, str):  # just put a string to evaluate to false i will fix it later
            tv = np.array(self.thickness_values)
            tv = tv.astype('float64')
            xnew, top_dep = OrganiseSoilProfile.set_depth(tv)
        apsimvar = yinterpo(xnew)
        return apsimvar

    def decreasing_exponential_function(self, x, a, b):  # has potential to cythonize
        """
          Compute the decreasing exponential function y = a * e^(-b * x).

          Parameters:
              x (array-like): Input values.
              a (float): Amplitude or scaling factor.
              b (float): Exponential rate.

          Returns:
              numpy.ndarray: The computed decreasing exponential values.
          """
        func = a * np.exp(-b * x)
        return func

    def optimize_exponetial_data(self, x_data, y_data, initial_guess=[0.5, 0.5],
                                 bounds=([0.1, 0.01], [np.inf, np.inf])):  # defaults for carbon

        best_fit_params, _ = curve_fit(self.decreasing_exponential_function, x_data, y_data, p0=initial_guess,
                                       bounds=bounds)
        a_fit, b_fit = best_fit_params
        predicted = self.decreasing_exponential_function(x_data, a_fit, b_fit)
        return predicted

    def interpolated_BD(self):
        if any(elem is None for elem in self.BD):
            return self.variable_profile(self.BD)
        else:
            return np.array(self.BD)

    def cal_satfromBD(self):  # has potential to cythonize
        if any(elem is None for elem in self.particledensity):
            pd = 2.65
            bd = self.interpolated_BD()

            sat = ((2.65 - bd) / 2.65) - 0.02
            sat = self.variable_profile(sat)
            return sat
        else:
            pd = self.particledensity
            bd = self.interpolated_BD()

            sat = ((2.65 - bd) / pd) - 0.02

            sat = self.variable_profile(sat)
            return sat
            # Calculate DUL from sand OM and clay

    def cal_dulFromsand_clay_OM(self):  # has potential to cythonize
        clay = self.clay * 0.01
        sand = self.sand * 0.01
        om = self.OM * 0.01
        ret1 = -0.251 * sand + 0.195 * clay + 0.011 * om + (0.006) * sand * om - 0.027 * clay * om + 0.452 * (
                sand * clay) + 0.299
        dul = ret1 + 1.283 * np.float_power(ret1, 2) - 0.374 * ret1 - 0.015
        dulc = self.variable_profile(dul)
        return dulc

    def cal_l15Fromsand_clay_OM(self):  # has potential to cythonize
        clay = self.clay * 0.01
        sand = self.sand * 0.01
        om = self.OM * 0.01
        ret1 = -0.024 * sand + (
                0.487 * clay) + 0.006 * om + 0.005 * sand * om + 0.013 * clay * om + 0.068 * sand * clay + 0.031
        ret2 = ret1 + 0.14 * ret1 - 0.02
        l151 = self.variable_profile(ret2)
        return l151

    def calculateSATfromwat_r(self):  # has potential to cythonize
        if not all(elem is None for elem in npar(self.particledensity)):
            wat = self.wat_r
            return self.variable_profile(wat)

    def cal_KS(self):  # has potential to cythonize
        ks = self.variable_profile(self.saturatedhudraulic_conductivity)

        ks = ks * (npar([1e-06]) * (60 * 60 * 24) * 1000)

        return ks

    def cal_Carbon(self):  # has potential to cythonize
        ## Brady and Weil (2016)
        carbon = self.variable_profile(self.OM) / 1.72
        return carbon
        xdata = self.newbottomdepth
        # try:
        #     predicted = self.optimize_exponetial_data(xdata, carbonn)
        #
        #     return predicted
        # except Exception as e:
        #     print("error occured while optimizing soil carbon to the new depth \nplease see:", repr(e))
        #     return carbonn

    def interpolate_clay(self):
        return self.variable_profile(self.clay)

    def interpolate_silt(self):
        return self.variable_profile(self.silt)

    def interpolate_sand(self):
        return self.variable_profile(self.sand)

    def interpolate_PH(self):
        return self.variable_profile(self.PH)

    def get_L15(self):
        if any(np.isnan(self.L15)):
            L15 = self.cal_l15Fromsand_clay_OM()
            return L15
        else:
            l1 = self.L15 * 0.01
            L15 = self.variable_profile(l1)
            return L15

    def get_DUL(self):
        if any(np.isnan(self.L15)):
            L15i = self.cal_l15Fromsand_clay_OM()

        else:
            l1 = self.L15 * 0.01
            L15i = self.variable_profile(l1)

        if any(np.isnan(self.DUL)):
            DUL = self.cal_dulFromsand_clay_OM()
            return DUL
        else:
            if not any(np.isnan(self.PAW)):
                paw = self.variable_profile(self.PAW)
                DUL = L15i + paw
                return DUL

    def get_AirDry(self):
        if any(np.isnan(self.L15)):
            air = self.cal_l15Fromsand_clay_OM()

            air[0] = air[0] * 0.5
            air[1] = air[1] * 0.9
            return air
        else:
            air = self.L15 / 100
            air[0] = air[0] * 0.5
            air[1] = air[1] * 0.9
            airl = self.variable_profile(air)

            return airl

    def getBD(self):
        return self.variable_profile(self.BD)

    def get_CSR(self):
        if self.CSR:
            return np.array(self.CSR)

    @staticmethod
    def adjust_SAT_BD_DUL(SAT, BD, DUL):
        """
        Adjusts saturation and bulk density values in a NumPy array to meet specific criteria.

        Parameters:
        SAT: 1-D numpy array
        BD: 1-D numpy array
        - target_saturation_a (float): The maximum acceptable saturation value for Soil water Module.
        - target_saturation_b (float): The maximum acceptable saturation value for SWIM
        - target_bulk_density (float): The maximum acceptable bulk density value.

        Returns:
        - np.array: Adjusted 2D NumPy array with saturation and bulk density values.
        """
        # Iterate through each row in the array
        for counter, (sat, dul) in enumerate(zip(SAT, DUL)):
            if dul >= sat:
                diff = dul - sat
                DUL[counter] = sat + diff + 0.02
        return SAT, BD, DUL

    def create_soilprofile(self):
        n = int(self.Nlayers)
        Depth = self.depths
        Carbon = self.cal_Carbon()
        AirDry = self.get_AirDry()
        L15 = self.get_L15()
        DUL = self.get_DUL()
        if not all(elem is None for elem in npar(self.wat_r)):

            SAT = self.calculateSATfromwat_r() * 0.01

            for i in range(len(SAT)):
                if SAT[i] < DUL[i]:
                    SAT[i] = DUL[i] + 0.02
            else:
                SAT[i] = SAT[i]
            BD = (1 - SAT) * 2.65
            for i in range(len(SAT)):  # added it
                if SAT[i] > 0.381 and BD[i] >= 1.639:
                    SAT[i] = 0.381 - 0.001
                    # print(SAT[i])
        else:
            SAT = self.cal_satfromBD()
            BD = self.getBD()
            for i in range(len(SAT)):
                if SAT[i] < DUL[i]:
                    SAT[i] = DUL[i] + 0.001
            else:
                SAT[i] = SAT[i]
            for i in range(len(SAT)):  # added it
                if SAT[i] > 0.381 and BD[i] >= 1.639:
                    SAT[i] = 0.381 - 0.01
                    # print(SAT[i])
        # adjust layer 9 issues associated with SAT and BD
        SAT, BD, DUL = self.adjust_SAT_BD_DUL(SAT, BD, DUL)
        KS = self.cal_KS()
        PH = self.interpolate_PH()
        ParticleSizeClay = self.interpolate_clay()
        ParticleSizeSilt = self.interpolate_silt()
        ParticleSizeSand = self.interpolate_sand()
        VA = [SAT, BD, DUL, KS, PH, ParticleSizeClay, ParticleSizeSilt, ParticleSizeSand, L15, Depth, Carbon, PH]
        DUL = np.sort(DUL)[::-1]
        SAT = np.sort(SAT)[::-1]

        def calculate_bd(sat):
            bd = 2.65 - (sat + 0.02) * 2.65
            return bd

        BD = calculate_bd(SAT)

        df = pd.DataFrame(
            {"Depth": Depth, "Thickness": [self.thickness] * n, "BD": BD, "AirDry": AirDry, "LL15": L15, "DUL": DUL,
             "SAT": SAT, "KS": KS, "Carbon": Carbon,
             "PH": PH, "ParticleSizeClay": ParticleSizeClay, "ParticleSizeSilt": ParticleSizeSilt,
             "ParticleSizeSand": ParticleSizeSand})

        return df

    def exponential_function_inc_yvalue(x, a, b):
        return a * np.exp(-b * x)

    def optimize_exp_increasing_y_values(self, y_data):
        if isinstance(self.thickness_values, np.ndarray):

            xdata = np.cumsum(np.array(self.thickness_values))
        else:
            xdata = np.cumsum(np.array(self.newbottomdepth))
        xdata = xdata.astype('float64')

        # Sort the data points by increasing y-values
        sorted_indices = np.argsort(y_data)
        sorted_x_data = xdata[sorted_indices]
        sorted_y_data = y_data[sorted_indices]
        # Perform curve fitting with the sorted data
        best_fit_params, _ = curve_fit(self.exponential_function_inc_yvalue, sorted_x_data, sorted_y_data)

        # Extract the best-fit parameters (a_fit and b_fit)
        a_fit, b_fit = best_fit_params
        predcited = self.exponential_function_inc_yvalue(xdata, a_fit, b_fit)

        # Plot the original data and the fitted curve
        plt.scatter(xdata, y_data, label='Original Data')
        plt.plot(xdata, self.exponential_function_inc_yvalue(xdata, a_fit, b_fit), label='Fitted Curve', color='red')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.legend()
        plt.show()
        return predcited

    def cal_missingFromSurgo(self, curveparam_a=0, curveparam_b=0.2, crops=("Wheat", "Maize", "Soybean", "Rye"),
                             metadata=None, soilwat=None, swim=None, soilorganicmatter=None,
                             top_finert=0.65, top_fom=180, top_fbiom=0.04, fom_cnr=40, soil_cnr=12, swcon=0.3,
                             top_urea=0, top_nh3=0.5, top_nh4=0.05):
        nlayers = int(self.Nlayers)

        cropLL = self.get_AirDry()
        cropKL = 0.08 * vary_soil_var_by_layer(nlayers, a=curveparam_a, b=curveparam_b)

        cropXF = 1 * vary_soil_var_by_layer(nlayers, a=curveparam_a, b=0)[:nlayers]

        # create a data frame for these three _variables
        # organic data calculation
        SoilCNRatio = np.full(shape=nlayers, fill_value=soil_cnr, dtype=np.int64)
        FOM = top_fom * vary_soil_var_by_layer(nlayers, a=curveparam_a, b=curveparam_b)
        FOMCN = np.full(shape=nlayers, fill_value=fom_cnr, dtype=np.int64)
        FBiom = top_fbiom * vary_soil_var_by_layer(nlayers, a=curveparam_a, b=curveparam_b)
        Fi = top_finert * vary_soil_var_by_layer(nlayers, a=curveparam_a, b=-0.01)
        FInert = Fi

        NO3N = top_nh3 * vary_soil_var_by_layer(nlayers, a=curveparam_a, b=0.01)
        NH4N = top_nh4 * vary_soil_var_by_layer(nlayers, a=curveparam_a, b=0.01)
        FInert[0] = 0.65
        FInert[1] = 0.668
        FBiom[0] = top_fbiom

        # from above
        Carbon = self.cal_Carbon()
        PH = self.interpolate_PH()

        # vn = npar
        # PH = 6.5 * soilvar_perdep_cor(nlayers, a = curveparam_a, b = 0)

        # ------------------------ organic df------------------------
        organic = pd.DataFrame({'Depth': self.depths, 'Thickness': self.thickness_values,
                                'Carbon': Carbon, 'SoilCNRatio': SoilCNRatio,
                                'FOM': FOM,
                                'FOM.CN': FOMCN, 'FBiom': FBiom, 'FInert': FInert, })
        # ------------------------ chemical df ------------------------
        chemical = pd.DataFrame(
            {'Depth': self.depths, 'Thickness': self.thickness_values, 'NO3N': NO3N, 'NH4N': NH4N, 'PH': PH})
        NO3 = pd.DataFrame({'Depth': self.depths, 'Thickness': self.thickness_values, 'InitialValues': NO3N})
        NH4 = pd.DataFrame({'Depth': self.depths, 'Thickness': self.thickness_values, 'InitialValues': NH4N})
        Urea = pd.DataFrame(
            {'Depth': self.depths, 'Thickness': self.thickness_values, 'InitialValues': np.full(len(self.depths), top_urea)})

        names = []
        # ------------------------crop soil info ------------------------
        for i in crops:
            names.append([i + "KK", i + 'LL ', i + 'XF'])
        crop_frame = []
        dfs = pd.DataFrame({'KL': cropKL, 'LL': cropLL, 'XF': cropXF})
        for i in names:
            crop_frame.append(dfs.rename(columns={"kl": i[0], "ll": i[1], "xf": i[2]}))

        # pd.concat is faster
        crop_df = pd.concat(crop_frame, join='outer', axis=1)
        physical = self.create_soilprofile()
        physical[['KL', 'LL', "XF"]] = dfs[['KL', 'LL', 'XF']]
        physical['Thickness'] = self.thickness_values

        po = 1 - (physical["BD"] / 2.65)
        swi_con = (po - physical['DUL']) / po
        # ------------------------ initial waters values ------------------------
        water = pd.DataFrame(
            {'Depth': self.depths, 'Thickness': self.thickness_values, 'InitialValues': physical['DUL'].values})
        soil_water = pd.DataFrame({'Depth': self.depths, 'Thickness': self.thickness_values, 'SWCON': swi_con})

        # create a alist
        frame = dict(physical=physical, organic=organic, cropdf=crop_df, metadata=metadata, swicon=swi_con)
        # ------------------------ corn suitability rating for iowa only ------------------------
        # this cosmetic, however
        if isinstance(self.CSR, (list, np.ndarray, pd.Series)):
            CSR = np.tile(self.CSR.iloc[0], int(self.Nlayers))
        else:
            CSR = None
        # resultdf = pd.concat(frame, join='outer', axis=1)
        # ------------------------ final dict data ------------------------
        meta_default = {'thickness sequence': self.thickness_values, 'Depth': self.depths}
        if isinstance(metadata, dict):
            metadata = metadata | {'thickness sequence': self.thickness_values}
        elif metadata is None:
            metadata = meta_default
        else:
            raise TypeError("metadata must be a dictionary or None")

        ret_data = {'physical': physical, 'chemical': chemical, 'organic': organic, 'crops': crops,
                    'meta_info': metadata, 'soilwat': soilwat, 'swim': swim, 'soil_crop': dfs, 'Urea': Urea, 'NH4': NH4,
                    'NO3': NO3, 'water': water,
                    'soilorganicmatter ': soilorganicmatter, 'swcon': swi_con, 'csr': pd.Series(CSR),
                    'soil_water': soil_water}

        return ret_data


OrganizeAPSIMsoil_profile = OrganiseSoilProfile  # for backward compatibility
if __name__ == '__main__':
    lonlat = -92.297702, 41.8780025
    dw = DownloadsurgoSoiltables(lonlat)
    sop = OrganiseSoilProfile(dw, thickness_values=[200, 200, 200, 200, 200, 200, 200, 200, 200])
    sop2 = OrganiseSoilProfile(dw, thickness=200)
    data = sop.cal_missingFromSurgo(metadata={'lonlat': lonlat})
    from apsimNGpy.core.apsim import ApsimModel
    from apsimNGpy.core.base_data import load_default_simulations
    from pathlib import Path
    from apsimNGpy import settings

    ap_sim = load_default_simulations(simulations_object=False)

    m = ApsimModel(ap_sim, thickness_values=settings.SOIL_THICKNESS)
    # m.replace_downloaded_soils(data, m.extract_simulation_name)

    m.run("MaizeR")
