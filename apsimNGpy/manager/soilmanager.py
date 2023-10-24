import json, os, sys
from os.path import join as opj
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

def DownloadsurgoSoiltables(lonlat, select_componentname =None, summarytable=False):
    '''
    Downloads SSURGO soil tables
    
    parameters
    ------------------
    lon: longitude 
    lat: latitude
    select_componentname: any componet name within the map unit e.g 'Clarion'. the default is None that mean sa ll the soil componets intersecting a given locationw il be returned
      if specified only that soil component table will be returned. in case it is not found the dominant componet will be returned with a caveat meassage.
        use select_componentname = 'domtcp' to return the dorminant component
    summarytable: prints the component names, their percentages
    '''
    
    total_steps = 3
    #lat = "37.54189"
    #lon = "-120.96683"
    lonLat = "{0} {1}".format(lonlat[0], lonlat[1])
    url="https://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx"
    #headers = {'content-type': 'application/soap+xml'}
    headers = {'content-type': 'text/xml'}
    body = """<?xml version="1.0" encoding="utf-8"?>
              <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:sdm="http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx">
       <soap:Header/>
       <soap:Body>
          <sdm:RunQuery>
             <sdm:Query>SELECT co.cokey as cokey, ch.chkey as chkey, comppct_r as prcent, compkind as compkind_series, wsatiated_r as wat_r,partdensity as pd, dbthirdbar_h as bb, musym as musymbol, compname as componentname, muname as muname, slope_r, slope_h as slope, hzname, hzdept_r as topdepth, hzdepb_r as bottomdepth, awc_r as PAW, ksat_l as KSAT,
                        claytotal_r as clay, silttotal_r as silt, sandtotal_r as sand, om_r as OM, iacornsr as CSR, dbthirdbar_r as BD, wfifteenbar_r as L15, wthirdbar_h as DUL, ph1to1h2o_r as pH, ksat_r as sat_hidric_cond,
                        (dbthirdbar_r-wthirdbar_r)/100 as bd FROM sacatalog sc
                        FULL OUTER JOIN legend lg  ON sc.areasymbol=lg.areasymbol
                        FULL OUTER JOIN mapunit mu ON lg.lkey=mu.lkey
                        FULL OUTER JOIN component co ON mu.mukey=co.mukey
                        FULL OUTER JOIN chorizon ch ON co.cokey=ch.cokey
                        FULL OUTER JOIN chtexturegrp ctg ON ch.chkey=ctg.chkey
                        FULL OUTER JOIN chtexture ct ON ctg.chtgkey=ct.chtgkey
                        FULL OUTER JOIN copmgrp pmg ON co.cokey=pmg.cokey
                        FULL OUTER JOIN corestrictions rt ON co.cokey=rt.cokey
                        WHERE mu.mukey IN (SELECT * from SDA_Get_Mukey_from_intersection_with_WktWgs84('point(""" + lonLat + """)')) 
                        
                        AND sc.areasymbol != 'US' 
                        order by co.cokey, ch.chkey, prcent, topdepth, bottomdepth, muname
            </sdm:Query>
          </sdm:RunQuery>
       </soap:Body>
    </soap:Envelope>"""
    
    response = requests.post(url,data=body,headers=headers, timeout =140)
    # Put query results in dictionary format
    my_dict = xmltodict.parse(response.content)
    
    # Convert from dictionary to dataframe format
   
    soil_df = pd.DataFrame.from_dict(my_dict['soap:Envelope']['soap:Body']['RunQueryResponse']['RunQueryResult']['diffgr:diffgram']['NewDataSet']['Table'])
    if summarytable:
      df = soil_df.drop_duplicates(subset=['componentname'])
      summarytable = df[["componentname",'prcent', 'chkey']]
      print("summary of the returned soil tables \n")
      print(summarytable)
    # selec the dominat componet
    dom_component = soil_df[soil_df.prcent ==soil_df.prcent.max()]
    #select by component name
    if select_componentname in soil_df.componentname.unique():
      componentdf = soil_df[soil_df.componentname ==select_componentname]
      return componentdf
    elif select_componentname == 'domtcp':
      return dom_component
      #print("the following{0} soil components were found". format(list(soil_df.componentname.unique())))
    elif select_componentname == None:
      #print("the following{0} soil components were found". format(list(soil_df.componentname.unique())))
      return soil_df
    elif select_componentname != 'domtcp' and select_componentname  not in soil_df.componentname.unique() or select_componentname !=None:
      print(f'Ooops! we realised that your component request: {select_componentname} does not exists at the specified location. We have returned the dorminant component name')
      return dom_component
      

# test the function
#aa= DownloadsurgoSoiltables([-90.72704709, 40.93103233],'Osco', summarytable = True)


##Making APSIM soil profile starts here=============================
len_layers = 10
a =1.35
b = 1.4
# create a variable profile constructor
def soilvar_perdep_cor(nlayers, soil_bottom =200, a = 0.5, b= 0.5):# has potential to cythonize
         depthn = np.arange(1, nlayers+1, 1)
         if a < 0:
               print("Target parameter can not be negative") # a * e^(-b * x).
         elif (a > 0 and  b != 0):
            ep = -b*depthn
            term1 = (a *depthn)*np.exp(ep)
            result = term1/term1.max()
            return(result)
         elif (a == 0 and b != 0):
           ep = -b *depthn
           result  = np.exp(ep)/np.exp(-b)
           return result
         elif (a==0, b==0):
             ans = [1]*len_layers
             return ans
def set_depth(depththickness):
  """
  parameters
  depththickness (array):  an array specifying the thicknness for each layer
  nlayers (int); number of layers just to remind you that you have to consider them
  ------
  return
bottom depth and top depth in a turple
  """
  #thickness  = np.tile(thickness, 10
  thickness_array  = np.array(depththickness)
  bottomdepth = np.cumsum(thickness_array) # bottom depth should nothave zero
  top_depth  = bottomdepth - thickness_array  
  return bottomdepth, top_depth
distparms = {'a': 0, 'b': 0.2}
class OrganizeAPSIMsoil_profile:
  # Iinitiate the soil object and covert all into numpy array and change them to floating values
      def __init__(self, sdf, thickness, thickness_values =None,bottomdepth = 200):
         """_summary_

        Args:
            sdf (pandas data frame): soil table downloaded from SSURGO_
            thickness double: _the thickness of the soil depth e.g 20cm_
            bottomdepth (int, optional): _description_. Defaults to 200.
            thickness_values (list or None) optional if provided extrapolation will be based on those vlue and should be the same length as the existing profile depth
         """
         sdf1= sdf.drop_duplicates(subset = ["topdepth"])
         surgodf  = sdf1.sort_values('topdepth', ascending = True)
         self.clay = npar(surgodf.clay).astype(np.float16)
         self.sand = npar(surgodf.sand).astype(np.float16)
         self.silt = npar(surgodf.silt).astype(np.float16)
         self.OM  = npar(surgodf.OM).astype(np.float16)
         self.topdepth = npar(surgodf.topdepth).astype(np.float16)
         self.bottomdepth = npar(surgodf.bottomdepth).astype(np.float16)
         self.BD = npar(surgodf.bb).astype(np.float16)
         self.DUL = npar(surgodf.DUL).astype(np.float64)
         self.L15 = npar(surgodf.L15).astype(np.float64)
         self.PH  = npar(surgodf.pH).astype(np.float64)
         self.PAW = npar(surgodf.PAW).astype(np.float16)
         self.saturatedhudraulic_conductivity = npar(surgodf.sat_hidric_cond).astype(np.float16)
         self.KSAT  = npar(surgodf.KSAT).astype(np.float16)
         self.particledensity  = npar(surgodf.pd).astype(np.float16)
         self.muname = surgodf.muname
         self.musymbol = surgodf.musymbol
         self.cokey = surgodf.cokey
         self.slope = surgodf.slope_r
         self.componentname = surgodf.componentname
         self.Nlayers = bottomdepth/thickness          
         self.thickness = thickness *10
         self.wat_r = surgodf.wat_r
         self.chkey = surgodf.chkey
         self.componentpercent = surgodf.prcent
         self.newtopdepth  = np.arange(0, bottomdepth, thickness)
         self.newbottomdepth  = np.arange(thickness, bottomdepth + thickness, thickness)
         # trial
         self.thickness_values = np.array(thickness_values)
         
      # create a function that creates a variable profile of the provide variables
      @staticmethod
      def set_depth(depththickness):
        """
        parameters
        depththickness (array):  an array specifying the thicknness for each layer
        nlayers (int); number of layers just to remind you that you have to consider them
        ------
        return
      bottom depth and top depth in a turple
        """
        #thickness  = np.tile(thickness, 10
        thickness_array  = np.array(depththickness)
        bottomdepth = np.cumsum(thickness_array) # bottom depth should nothave zero
        top_depth  = bottomdepth - thickness_array  
        return bottomdepth, top_depth
      def variable_profile(self, y, kind = 'linear'):  #has potential to cythonize
              # use the lower depth boundary because divinding by zeros is nearly impossible
            x = self.bottomdepth
            # replace x with the anticipated value of the the new soil depth
            nlayers  = self.Nlayers
            xranges = x.max() - x.min()
            newthickness  = xranges/nlayers
            # new depth variable for interpolation
            xnew = np.arange(x.min(), x.max(), newthickness)
            # create an interpolation function
            yinterpo  = interpolate.interp1d(x, y, kind = kind, assume_sorted=False, fill_value='extrapolate')
            if isinstance(self.thickness_values, str): # just put a strign to evaluate to false i will fix it later
               tv= np.array(self.thickness_values)
               tv= tv.astype('float64')
               xnew, top_dep = OrganizeAPSIMsoil_profile.set_depth(tv)
            apsimvar = yinterpo(xnew)
            return apsimvar
          
      def decreasing_exponential_function(self, x, a, b): #has potential to cythonize
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
      def  optimize_exponetial_data(self, x_data, y_data, initial_guess = [0.5, 0.5] , bounds =([0.1, 0.01], [np.inf, np.inf]) ): #defaults for carbon
         
          best_fit_params, _ = curve_fit(self.decreasing_exponential_function, x_data, y_data, p0= initial_guess, bounds = bounds)
          a_fit, b_fit = best_fit_params
          predicted = self.decreasing_exponential_function(x_data, a_fit, b_fit)
          return predicted

          
      def cal_satfromBD (self):#has potential to cythonize
            if any(elem is None for elem in self.particledensity):
              pd = 2.65
              bd =  npar(self.BD)
              sat = ((2.65-bd)/2.65)-0.02
              sat = self.variable_profile(sat)
              return sat
            else:
              pd  = self.particledensity
              bd =  npar(self.BD)
              sat = ((2.65-bd)/pd)-0.02
              sat = self.variable_profile(sat)
              return sat 
          # Calculate DUL from sand OM and clay
      def cal_dulFromsand_clay_OM(self): #has potential to cythonize
            clay =  self.clay * 0.01
            sand  = self.sand * 0.01
            om  = self.OM * 0.01
            ret1 = -0.251 * sand + 0.195 * clay + 0.011 * om + (0.006) * sand * om - 0.027 * clay * om + 0.452 * (sand * clay) +  0.299
            dul = ret1 + 1.283 * np.float_power(ret1, 2) - 0.374 * ret1 - 0.015
            dulc  = self.soil.variable_profile(dul)
            return dulc
      def cal_l15Fromsand_clay_OM(self): #has potential to cythonize
            clay =  self.clay * 0.01
            sand  = self.sand * 0.01
            om  = self.OM * 0.01
            ret1 = -0.024 * sand + (0.487 * clay) + 0.006 * om + 0.005 * sand * om + 0.013 * clay * om + 0.068 * sand * clay + 0.031
            ret2  = ret1 + 0.14 * ret1- 0.02
            l151  = self.variable_profile(ret2)
            return l151  
      def calculateSATfromwat_r(self): #has potential to cythonize
          if all(elem is None for elem in npar(self.particledensity)) ==False:
            wat = self.wat_r
            return self.variable_profile(wat)
      def cal_KS(self): #has potential to cythonize
           ks =  self.saturatedhudraulic_conductivity * npar([1e-06]) * (60*60*24)*1000
           n = int(self.Nlayers)
           KS = np.full(shape=n, fill_value=ks[1],  dtype=np.float64)
           return KS
      def cal_Carbon(self): #has potential to cythonize
            ## Brady and Weil (2016)
            carbonn = self.variable_profile(self.OM)/1.72
            # if carbonans >=3.5:
            #   carbonn = carbonans *0.3
            # else:
            #   carbonn = carbonans
            #print(carbonn)
            
            xdata  = self.newbottomdepth
            try:
              predicted = self.optimize_exponetial_data(xdata, carbonn)
              
              
              return predicted
            except Exception as e:
              print("error occured while optimizing soil carbon to the new depth \nplease see:", repr(e))
              return carbonn
              
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
           L15  = self.variable_profile(l1)
           return L15    
      def get_DUL(self):
         if any(np.isnan(self.L15)):
           L15i = self.cal_l15Fromsand_clay_OM()
          
         else:
           l1 = self.L15 * 0.01
           L15i  = self.variable_profile(l1)
           
         if any(np.isnan(self.DUL)):
           DUL = self.cal_dulFromsand_clay_OM()
           return DUL
         else:
           if not any(np.isnan(self.PAW)):
            paw =  self.variable_profile(self.PAW)
            DUL = L15i + paw
            return DUL
      def get_AirDry(self):
          if any(np.isnan(self.L15)):
             air= self.cal_l15Fromsand_clay_OM()
             air[:3] = air[:3]*0.5
             return air
          else:
            air = self.L15 * 0.01
            airl  = self.variable_profile(air)
            airl[:3]  = airl[:3]*0.5
            return airl
      def getBD(self):
          return self.variable_profile(self.BD)
      def create_soilprofile(self):
            n = int(self.Nlayers)
            Depth = []
            for i in range(len(self.newbottomdepth)):
                Depth.append(str(self.newtopdepth[i]) + "-" + str(self.newbottomdepth[i]))
            Depth = Depth
            #Thickness  = [self.thickness]*self.Nlayers
            Carbon  = self.cal_Carbon()
            AirDry = self.get_AirDry()
            L15 = self.get_L15()
            DUL  = self.get_DUL()
            if all(elem is None for elem in npar(self.wat_r)) ==False:
              
              SAT = self.calculateSATfromwat_r() *0.01
              
              for i in range(len(SAT)):
                  if SAT[i] <DUL[i]:
                    SAT[i] = DUL[i] + 0.001
              else:
                SAT[i] = SAT[i] 
              BD= (1-SAT)*2.65
            else:
              SAT = self.cal_satfromBD()
              BD = self.getBD()
              for i in range(len(SAT)):
                if SAT[i] <DUL[i]:
                  SAT[i] = DUL[i] + 0.001
              else:
                SAT[i] = SAT[i] 
              for i in range(len(SAT)):# added it
                if SAT[i] > 0.381 and BD[i] >= 1.639:
                  SAT[i] = 0.381
                  
            KS = self.cal_KS()
            PH = self.interpolate_PH()
            ParticleSizeClay = self.interpolate_clay()
            ParticleSizeSilt = self.interpolate_silt()
            ParticleSizeSand = self.interpolate_sand()
            df= pd.DataFrame({"Depth":Depth, "Thickness": [self.thickness]*n, "BD":BD, "AirDry":AirDry, "LL15":L15, "DUL":DUL, "SAT":SAT, "KS":KS, "Carbon":Carbon, 
            "PH":PH, "ParticleSizeClay":ParticleSizeClay, "ParticleSizeSilt":ParticleSizeSilt, "ParticleSizeSand": ParticleSizeSand})
            return(df)
      def exponential_function_inc_yvalue(x, a, b):
           return a * np.exp(-b * x)
      def optimize_exp_increasing_y_values(self, y_data):
         if isinstance(self.thickness_values, np.ndarray):
            
               xdata = np.cumsum(np.array(self.thickness_values))
         else:
              xdata  = np.cumsum(np.array(self.newbottomdepth))
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
         
         #Plot the original data and the fitted curve
         plt.scatter(xdata, y_data, label='Original Data')
         plt.plot(xdata, self.exponential_function_inc_yvalue(xdata, a_fit, b_fit), label='Fitted Curve', color='red')
         plt.xlabel('x')
         plt.ylabel('y')
         plt.legend()
         plt.show()
         return predcited
      def cal_missingFromSurgo(self, curveparam_a = 0, curveparam_b = 0.2, crops = ["Wheat", "Maize", "Soybean", "Rye"], metadata = None, soilwat = None, swim = None, soilorganicmatter = None):
            nlayers  = int(self.Nlayers)
            #ad  = self.get_AirDry()[1]
            cropLL = self.get_AirDry()
            #Original thought
            #ad * soilvar_perdep_cor(nlayers, a = curveparam_a, b = curveparam_b) 
            cropKL =0.06 * soilvar_perdep_cor(nlayers, a =curveparam_a,  b = curveparam_b) 
            cropXF = 1 * soilvar_perdep_cor(nlayers, a = curveparam_a,  b = 0)
            # create a data frame for these three variables
            dfs = pd.DataFrame({'kl': cropKL, 'll':cropLL, 'xf':cropXF })
            SoilCNRatio = np.full(shape=nlayers, fill_value=12.2,  dtype=np.int64)
            FOM = 160 * soilvar_perdep_cor(nlayers, a = curveparam_a, b = curveparam_b)
            FOMCN = np.full(shape=nlayers, fill_value=40,  dtype=np.int64)
            FBiom = 0.045 * soilvar_perdep_cor(nlayers, a = curveparam_a, b = curveparam_b)
            Fi = 0.83 * soilvar_perdep_cor(nlayers, a = curveparam_a, b = -0.01) 
            # to do later
            # try:
            #   predicted= self.optimize_exp_increasing_y_values(np.array(Fi))
            #   FInert = predicted
            # except Exception as e:
            #   print("error optiming FInert value encountered;", repr(e))
            FInert = Fi
              
            NO3N = 0.5 * soilvar_perdep_cor(nlayers, a = curveparam_a, b = 0.01)
            NH4N = 0.05 * soilvar_perdep_cor(nlayers, a = curveparam_a, b = 0.01)
            FInert[0]= 0.65
            FInert[1] = 0.668
            FBiom[0] = 0.0395
            FBiom[1] =0.035
            # from above
            Carbon  = self.cal_Carbon()
            PH = self.interpolate_PH()
            # vn = npar
            #PH = 6.5 * soilvar_perdep_cor(nlayers, a = curveparam_a, b = 0)
            organic = pd.DataFrame({'Carbon':Carbon, 'SoilCNRatio': SoilCNRatio,'cropLL': cropLL, 'cropKL':cropKL,'FOM' :FOM, 'FOM.CN': FOMCN, 'FBiom': FBiom, 'FInert': FInert, 'NO3N': NO3N, 'NH4N': NH4N, 'PH': PH})
            # create a list to store the crop names
            names = []
            for i in crops:
                 names.append([i + "KK", i+ 'LL ',  i + 'XF'])
            cropframe = []
            for i in names:
               cropframe.append(dfs.rename(columns={"kl": i[0], "ll":i[1], "xf": i[2]}))
            #print(cropframe)
               # pd.concat is faster
            cropdf = pd.concat(cropframe, join='outer', axis=1)
            physical = self.create_soilprofile()
            
            # create a alist
            frame = [physical, organic, cropdf, metadata]
            # All soil data frames
            resultdf = pd.concat(frame, join = 'outer', axis = 1)
            finalsp = {'soil ':resultdf, 'crops':  crops, 'metadata': metadata, 'soilwat': soilwat, 'swim':  swim, 'soilorganicmatter ': soilorganicmatter}
            #return pd.DataFrame(finalsp)
            return frame

# class soil_profile:
#    def __init__(self, df):
#          self.soil = df

# profile = OrganizeAPSIMsoil_profile(soildownload, 20) # takes in surgo returned data frame and the thickness
# 
# pp = xp.cal_missingFromSurgo()
# physical  = ps[0]
# organic = ps[1]
# cropdf  = ps[2]

def Replace_Soilprofile(apsimxfile, path2apsimx, series, lonlat, crop = None):
        '''
        Replaces APASIMX soil properties
        
        parameters
        ------------
        apsimxfile: apsimx file name string with the extension .apsimx
        path2apsimx: path string to apsimx file
        lonlat a tupple or a list with the longitude and latitude in the order as the name
        '''
        print('dowloading soils')
        soildownload = DownloadsurgoSoiltables(lonlat, series)
        print('Organising soil profile')
        profile = OrganizeAPSIMsoil_profile(soildownload, 20)
        pp = profile.cal_missingFromSurgo()
        physical  = pp[0]
        organic = pp[1]
        cropdf  = pp[2]
        print("Writing soil profile")
        if not apsimxfile.endswith(".apsimx"):
          print("apsimx extension required")
        else:
            pathstring = opj(path2apsimx,apsimxfile)
            if not os.path.isfile(pathstring):
              print("APSIMX file entered does not exist")
            else:
              app_ap = None
              with open(pathstring, "r+") as apsimx:
                  app_ap = json.load(apsimx) 
              # search for the Core simulation node
              # the challenge is that the nodes may not be in the correct oder everytime. so we loop through using enumeration fucntion
              for counter, root in enumerate(app_ap["Children"]):
                 if root['$type'] == 'Models.Core.Simulation, Models':
                   if not counter:
                    print("No core simulation node found")
                   else: 
                      coresimulationNode = counter
                      print('searching for the main core simulation node')
                      for counter, root in enumerate(app_ap["Children"][coresimulationNode]["Children"]):
                            if root['$type'] == 'Models.Core.Zone, Models':
                              if not counter:
                                print("No field zone found: ", app_ap["Children"][coresimulationNode]["Name"])
                              else: 
                                  fieldzone = counter
                                  # remember zone has many nodes
                                  # now lets look for soils
                                  for counter, root in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"]):
                                    if root['$type'] == 'Models.Soils.Soil, Models':
                                      if not counter:
                                        print("no soils found: ", app_ap["Children"][coresimulationNode]["Name"])
                                      else: 
                                          soilnode = counter
                                  # now we have a dictionary for soil node we need its children
                                          for counterr, roott in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"]):
                                            if roott["$type"] =='Models.Soils.Physical, Models':
                                              if not counter:
                                                print("no soils found: ", app_ap["Children"][coresimulationNode]["Name"])
                                              else: 
                                                  soilpysical = counterr
                                                  # code to edit soilphysical
                                                  print('replacing soil physical properties')
                                                  soilphysicalnode = app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Thickness'] = list(np.full(shape=int(profile.Nlayers), fill_value=profile.thickness,  dtype=np.float64))
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['ParticleSizeClay'] = list(physical.ParticleSizeClay)
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['ParticleSizeSand'] = list(physical.ParticleSizeSand)
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['ParticleSizeSilt'] = list(physical.ParticleSizeSilt)
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['BD'] = list(physical.BD)
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['AirDry'] =list(physical.AirDry)
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['LL15'] = list(physical.LL15)
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['DUL'] = list(physical.DUL)
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['SAT'] =  list(physical.SAT)
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['KS']  = list(physical.KS)
                                                  # write meta info
                                                  comment = "cockey = " + profile.cokey.values[1] + " " + profile.muname.values[1] + " " + 'Component percentage: ' + profile.componentpercent.values[1] + "%"
                                                  #timewritten = datetime.date.today()
                                                  ct =datetime.datetime.now()
                                                  formattime = "Date downloaded: {0}".format(ct)
                                                  
                                                  url="https://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx"
                                                  soiltype = profile.componentname.values[1] + ":" +  profile.chkey.values[1]
                                                  datasource = f'SSURGO {url} through PyAPSIMX function Replace_Soilprofile. {formattime}'
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]['Latitude'] = lonlat[1]
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]['Longitude'] =lonlat[0]
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]['DataSource'] = datasource
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]['Comments'] = comment
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]['SoilType'] = soiltype
                                                  
                                                  # add crop
                                                  if crop:
                                                      
                                                      dup = copy.deepcopy(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'][0])
                                                      dup["Name"] = crop +"Soil"
                                                      print
                                                      # collect crop 1
                                                      cropnames = []
                                                      for i in range(len(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'])):
                                                          cropnames.append(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'][i]["Name"])
                                                      print(cropnames)
                                                      cp = crop + 'Soil'
                                                      if cp not in cropnames:
                                                        
                                                        length  = len(cropnames)
                                                        app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'].insert(3,dup)
                                                      # replace LL, KL, AND XF
                                                     
                                                  for i in range(len(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'])):
                                                    app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'][i]['LL'] =list(organic.cropLL)
                                                    app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'][i]['KL'] =list(organic.cropKL)
                                                    app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'][i]['XF'] ==list(np.full(shape=int(profile.Nlayers), fill_value=1,  dtype=np.float64))
                                                  # REPLICATE THE NODE
                                            for counterr, roott in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"]):
                                                        if roott["$type"] =='Models.WaterModel.WaterBalance, Models':
                                                          if not counter:
                                                            print("no soils found: ", app_ap["Children"][coresimulationNode]["Name"])
                                                          else: 
                                                              waterbalance = counterr
                                                              # code to edit soil water balance node
                                                              waterbalancenode = app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['SummerDate']
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['SummerU']
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['SummerCona']
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['WinterDate']
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['SWCON']
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['KLAT']
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['CN2Bare']
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['WinterU']
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['WinterCona']
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['DiffusConst']
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['Salb']
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['Thickness']
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['Salb']
                                            for counterr, roott in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"]):
                                                        if roott["$type"] =='Models.Soils.Organic, Models':
                                                          if not counter:
                                                            print("no soils found: ", app_ap["Children"][coresimulationNode]["Name"])
                                                          else:
                                                              
                                                              soilorganic = counterr
                                                              # print relacing soil organic properties
                                                               # code to edit soil soil organic node
                                                              soilorganicnode = app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]['Thickness'] = list(np.full(shape=int(profile.Nlayers), fill_value=profile.thickness,  dtype=np.float64))
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]['FOMCNRatio'] = 40
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]['Carbon'] = list(physical.Carbon)
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]['SoilCNRatio'] = list(organic.SoilCNRatio)
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]['FBiom'] = list(organic.FBiom)
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]['FOM'] =list(organic.FOM)
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]['FInert'] =list(organic.FInert)
                                            for counterr, roott in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"]):
                                                        if roott["$type"] =='Models.Soils.Chemical, Models':
                                                          if not counter:
                                                            print("no soils found: ", app_ap["Children"][coresimulationNode]["Name"])
                                                          else:
                                                              soilchemical = counterr
                                                               # code to edit soil to soil chemical node
                                                              soilchemicalnode = app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilchemical]
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilchemical]['Thickness'] = list(np.full(shape=int(profile.Nlayers), fill_value=profile.thickness,  dtype=np.float64))
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilchemical]['PH'] = list(physical.PH)
                                            for counter, root in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"]):
                                                  if root["$type"] == 'Models.Soils.Water, Models':
                                                    if not counter:
                                                      print('no soil water node found')
                                                    else:
                                                      soilwater = counter
                                                      app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilwater]['Thickness'] = list(np.full(shape=int(profile.Nlayers), fill_value=profile.thickness,  dtype=np.float64))
                                            for counter, root in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"]):
                                                  if root["$type"] == 'Models.Soils.Solute, Models':
                                                    if not counter:
                                                      print('No soil solute node found')
                                                    else:
                                                      soilsolute = counter
                                                      app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilsolute]['Thickness'] = list(np.full(shape=int(profile.Nlayers), fill_value=profile.thickness,  dtype=np.float64))
                                                      if app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilsolute]['Name'] =='NH4':
                                                        app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilsolute]['InitialValues'] = list(physical.Carbon)
                                                      if app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilsolute]['Name'] =='NO3':
                                                        app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilsolute]['InitialValues'] = list(physical.Carbon)
                                            for counterr, roott in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"]):
                                                        if roott["$type"] =='Models.Soils.Water, Models':
                                                          if not counter:
                                                            print("no soils found: ", app_ap["Children"][coresimulationNode]["Name"])
                                                          else:
                                                              print('replacing soil water')
                                                              soilwater= counterr
                                                               # code to edit soil to edit soil water node
                                                              soilwaternode = app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilwater]
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilwater]['Thickness']
                                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilwater]['InitialValues'] =list(physical.DUL)
                                                              print("***Done----")
                                                              print("xxx")
                                                              apsix = json.dumps(app_ap)
                                                              filename = "edit_" + str(time.perf_counter())[-5:]+"_" +  apsimxfile
                                                              nameout =os.path.join(os.getcwd(), filename)
                                                              with open(nameout, "w+") as openfile:
                                                                openfile.write(apsix)
                                                              return nameout

def Replace_Soilprofile2(path2apsimx, series, lonlat, filename = 0, gridcode = 0, Objectid = 0, crop = None):
        '''
        Replaces APASIMX soil properties
        
        parameters
        ------------
        apsimxfile: apsimx file name string with the extension .apsimx
        path2apsimx: path string to apsimx file
        lonlat a tupple or a list with the longitude and latitude in the order as the name
        '''
        soildownload = DownloadsurgoSoiltables(lonlat, series)
        profile = OrganizeAPSIMsoil_profile(soildownload, 20)
        pp = profile.cal_missingFromSurgo()
        physical  = pp[0]
        organic = pp[1]
        cropdf  = pp[2]
        if not os.path.isfile(path2apsimx):
          print("APSIMX file entered does not exist")
        else:
          pathstring = path2apsimx
          with open(pathstring, "r+") as apsimx:
              app_ap = json.load(apsimx) 
          # search for the Core simulation node
          # the challenge is that the nodes may not be in the correct oder everytime. so we loop through using enumeration fucntion
          for counter, root in enumerate(app_ap["Children"]):
             if root['$type'] == 'Models.Core.Simulation, Models':
               if not counter:
                print("No core simulation node found")
               else: 
                  coresimulationNode = counter
                  #print('searching for the main core simulation node')
                  for counter, root in enumerate(app_ap["Children"][coresimulationNode]["Children"]):
                        if root['$type'] == 'Models.Core.Zone, Models':
                          if not counter:
                            print("No field zone found: ", app_ap["Children"][coresimulationNode]["Name"])
                          else: 
                              fieldzone = counter
                              # remember zone has many nodes
                              # now lets look for soils
                              for counter, root in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"]):
                                if root['$type'] == 'Models.Soils.Soil, Models':
                                  if not counter:
                                    print("no soils found: ", app_ap["Children"][coresimulationNode]["Name"])
                                  else: 
                                      soilnode = counter
                              # now we have a dictionary for soil node we need its children
                                      for counterr, roott in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"]):
                                        if roott["$type"] =='Models.Soils.Physical, Models':
                                          if not counter:
                                            print("no soils found: ", app_ap["Children"][coresimulationNode]["Name"])
                                          else: 
                                              soilpysical = counterr
                                              # code to edit soilphysical
                                             # print('replacing soil physical properties')
                                              soilphysicalnode = app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Thickness'] = list(np.full(shape=int(profile.Nlayers), fill_value=profile.thickness,  dtype=np.float64))
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['ParticleSizeClay'] = list(physical.ParticleSizeClay)
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['ParticleSizeSand'] = list(physical.ParticleSizeSand)
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['ParticleSizeSilt'] = list(physical.ParticleSizeSilt)
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['BD'] = list(physical.BD)
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['AirDry'] =list(physical.AirDry)
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['LL15'] = list(physical.LL15)
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['DUL'] = list(physical.DUL)
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['SAT'] =  list(physical.SAT)
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['KS']  = list(physical.KS)
                                              # write meta info
                                              comment = "cockey = " + profile.cokey.values[1] + " " + profile.muname.values[1] + " " + 'Component percentage: ' + profile.componentpercent.values[1] + "%"
                                              #timewritten = datetime.date.today()
                                              ct =datetime.datetime.now()
                                              formattime = "Date downloaded: {0}".format(ct)
                                              #print(formattime)
                                              url="https://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx"
                                              soiltype = profile.componentname.values[1] + ":" +  profile.chkey.values[1]
                                              datasource = f'SSURGO {url} through PyAPSIMX function Replace_Soilprofile. {formattime}'
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]['Latitude'] = lonlat[1]
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]['Longitude'] =lonlat[0]
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]['DataSource'] = datasource
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]['Comments'] = comment
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]['SoilType'] = soiltype
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]['Site'] = gridcode
                                              app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]['RecordNumber'] = Objectid
                                          
                                              # add crop
                                              if crop:
                                                  
                                                  dup = copy.deepcopy(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'][0])
                                                  dup["Name"] = crop +"Soil"
                                                  print
                                                  # collect crop 1
                                                  cropnames = []
                                                  for i in range(len(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'])):
                                                      cropnames.append(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'][i]["Name"])
                                                  print(cropnames)
                                                  cp = crop + 'Soil'
                                                  if cp not in cropnames:
                                                    
                                                    length  = len(cropnames)
                                                    app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'].insert(3,dup)
                                                  # replace LL, KL, AND XF
                                                 
                                              for i in range(len(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'])):
                                                app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'][i]['LL'] =list(organic.cropLL)
                                                app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'][i]['KL'] =list(organic.cropKL)
                                                app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilpysical]['Children'][i]['XF'] ==list(np.full(shape=int(profile.Nlayers), fill_value=1,  dtype=np.float64))
                                              # REPLICATE THE NODE
                                        for counterr, roott in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"]):
                                                    if roott["$type"] =='Models.WaterModel.WaterBalance, Models':
                                                      if not counter:
                                                        print("no soils found: ", app_ap["Children"][coresimulationNode]["Name"])
                                                      else: 
                                                          waterbalance = counterr
                                                          # code to edit soil water balance node
                                                          waterbalancenode = app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['SummerDate']
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['SummerU']
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['SummerCona']
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['WinterDate']
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['SWCON']
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['KLAT']
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['CN2Bare']
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['WinterU']
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['WinterCona']
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['DiffusConst']
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['Salb']
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['Thickness']
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][waterbalance]['Salb']
                                        for counterr, roott in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"]):
                                                    if roott["$type"] =='Models.Soils.Organic, Models':
                                                      if not counter:
                                                        print("no soils found: ", app_ap["Children"][coresimulationNode]["Name"])
                                                      else:
                                                          #print('replacing soil organic matter node', flush =True)
                                                          soilorganic = counterr
                                                          # print relacing soil organic properties
                                                           # code to edit soil soil organic node
                                                          soilorganicnode = app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]['Thickness'] = list(np.full(shape=int(profile.Nlayers), fill_value=profile.thickness,  dtype=np.float64))
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]['FOMCNRatio'] = 40
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]['Carbon'] = list(physical.Carbon)
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]['SoilCNRatio'] = list(organic.SoilCNRatio)
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]['FBiom'] = list(organic.FBiom)
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]['FOM'] =list(organic.FOM)
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilorganic]['FInert'] =list(organic.FInert)
                                        for counterr, roott in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"]):
                                                    if roott["$type"] =='Models.Soils.Chemical, Models':
                                                      if not counter:
                                                        print("no soils found: ", app_ap["Children"][coresimulationNode]["Name"])
                                                      else:
                                                          #print("replacing soil chemical node")
                                                          soilchemical = counterr
                                                           # code to edit soil to soil chemical node
                                                          soilchemicalnode = app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilchemical]
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilchemical]['Thickness'] = list(np.full(shape=int(profile.Nlayers), fill_value=profile.thickness,  dtype=np.float64))
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilchemical]['PH'] = list(physical.PH)
                                        for counter, root in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"]):
                                              if root["$type"] == 'Models.Soils.Water, Models':
                                                if not counter:
                                                  print('no soil water node found')
                                                else:
                                                  soilwater = counter
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilwater]['Thickness'] = list(np.full(shape=int(profile.Nlayers), fill_value=profile.thickness,  dtype=np.float64))
                                        for counter, root in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"]):
                                              if root["$type"] == 'Models.Soils.Solute, Models':
                                                if not counter:
                                                  print('No soil solute node found')
                                                else:
                                                  soilsolute = counter
                                                  app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilsolute]['Thickness'] = list(np.full(shape=int(profile.Nlayers), fill_value=profile.thickness,  dtype=np.float64))
                                                  if app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilsolute]['Name'] =='NH4':
                                                    app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilsolute]['InitialValues'] = list(physical.Carbon)
                                                  if app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilsolute]['Name'] =='NO3':
                                                    app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilsolute]['InitialValues'] = list(physical.Carbon)
                                        for counterr, roott in enumerate(app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"]):
                                                    if roott["$type"] =='Models.Soils.Water, Models':
                                                      if not counter:
                                                        print("no soils found: ", app_ap["Children"][coresimulationNode]["Name"])
                                                      else:
                                                          #print('replacing soil water')
                                                          soilwater= counterr
                                                           # code to edit soil to edit soil water node
                                                          soilwaternode = app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilwater]
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilwater]['Thickness']
                                                          app_ap["Children"][coresimulationNode]["Children"][fieldzone]["Children"][soilnode]["Children"][soilwater]['InitialValues'] =list(physical.DUL)
                                                          
                                                          apsix = json.dumps(app_ap)
                                                          filenamee = "edit_" + str(filename)+"_" +  pathstring.split("\\")[-1]
                                                          nameout =os.path.join(os.getcwd(), filenamee)
                                                          openfile = open(nameout, "w+")
                                                    
                                                          openfile.write(apsix)
                                                          
                                                          openfile.close()
                                                         
                                                          return nameout


# Example
# path = r'C:\Users\rmagala\Box\simulations\objective_2\illnois\DATA'
# test4 = Replace_Soilprofile('covercrop.apsimx', path, [-90.72704709, 40.93103233], "Wheat")
# 
# a = json.dumps(test4)
# p =opj(path, "cover.apsimx")
# ap = open(p, "w+")
# ap.write(a)
# ap.close()
# # create a list
# os.startfile(p)
# with open(p, "r+") as apsimx:
#       app_ap = json.load(apsimx)
