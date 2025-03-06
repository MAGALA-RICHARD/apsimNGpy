import os.path

import requests
import xmltodict
import pandas as pd
from apsimNGpy.manager.soilmanager import OrganizeAPSIMsoil_profile

def DownloadsurgoSoiltables(lonlat, select_componentname=None, summarytable=False):
    '''
    TODO this is a duplicate File. Duplicate of soils/soilmanager
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
    # lat = "37.54189"
    # lon = "-120.96683"
    lonLat = "{0} {1}".format(lonlat[0], lonlat[1])
    import requests

    url = "https://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx"
    headers = {'content-type': 'application/soap+xml'}

    body = """<?xml version="1.0" encoding="utf-8"?>
                 <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:sdm="http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx">
          <soap:Header/>
          <soap:Body>
             <sdm:RunQuery>
                <sdm:Query>SELECT co.cokey as cokey, ch.chkey as chkey, comppct_r as prcent, compkind as compkind_series, lg.areasymbol, wsatiated_r as wat_r,partdensity as pd, dbthirdbar_h as bb, musym as musymbol, compname as componentname, muname as muname, slope_r, slope_h as slope, hzname, hzdept_r as topdepth, hzdepb_r as bottomdepth, awc_r as PAW, ksat_l as KSAT,
                           claytotal_r as clay, silttotal_r as silt, sandtotal_r as sand, texcl, drainagecl, om_r as OM, iacornsr as CSR, dbthirdbar_r as BD, wfifteenbar_r as L15, wthirdbar_h as DUL, ph1to1h2o_r as pH, ksat_r as sat_hidric_cond,
                           (dbthirdbar_r-wthirdbar_r)/100 as bd FROM sacatalog sc
                           FULL OUTER JOIN legend lg  ON sc.areasymbol=lg.areasymbol
                           FULL OUTER JOIN mapunit mu ON lg.lkey=mu.lkey
                           FULL OUTER JOIN component co ON mu.mukey=co.mukey
                           FULL OUTER JOIN chorizon ch ON co.cokey=ch.cokey
                           FULL OUTER JOIN chtexturegrp ctg ON ch.chkey=ctg.chkey
                           FULL OUTER JOIN chtexture ct ON ctg.chtgkey=ct.chtgkey
                           FULL OUTER JOIN copmgrp pmg ON co.cokey=pmg.cokey
                           FULL OUTER JOIN corestrictions rt ON co.cokey=rt.cokey
                           WHERE mu.mukey IN (
                         SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('polygon((
                        -121.77100 37.368402,
                        -121.77100 37.373473,
                        -121.76000 37.373473,
                        -121.76000 37.368402,
                        -121.77100 37.368402))')
                ) 
                           AND sc.areasymbol != 'US' 
                           order by co.cokey, ch.chkey, prcent, topdepth, bottomdepth, muname
               </sdm:Query>
             </sdm:RunQuery>
          </soap:Body>
       </soap:Envelope>"""

    response = requests.post(url, data=body, headers=headers, timeout=140)
    # Put query results in dictionary format
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
    return response, soil_df
sd = DownloadsurgoSoiltables([-119.72330,
                               36.92204])

coordinates = (
    (-121.77100, 37.368402),
    (-121.77100, 37.373473),
    (-121.76000, 37.373473),
    (-121.76000, 37.368402),
    (-121.77100, 37.368402)

)


def DownloadsurgoSoilTables(_coordinates):
    formatted_coordinates = ",".join([f"{lon} {lat}" for lon, lat in _coordinates])
    url = "https://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx"
    headers = {'content-type': 'application/soap+xml'}
    body = f"""<?xml version="1.0" encoding="utf-8"?>
                    <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:sdm="http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx">
             <soap:Header/>
             <soap:Body>
                <sdm:RunQuery>
                   <sdm:Query>SELECT co.cokey as cokey, ch.chkey as chkey, comppct_r as prcent, compkind as compkind_series, lg.areasymbol, wsatiated_r as wat_r,partdensity as pd, dbthirdbar_h as bb, musym as musymbol, compname as componentname, muname as muname, slope_r, slope_h as slope, hzname, hzdept_r as topdepth, hzdepb_r as bottomdepth, awc_r as PAW, ksat_l as KSAT,
                              claytotal_r as clay, silttotal_r as silt, sandtotal_r as sand, texcl, drainagecl, om_r as OM, iacornsr as CSR, dbthirdbar_r as BD, wfifteenbar_r as L15, wthirdbar_h as DUL, ph1to1h2o_r as pH, ksat_r as sat_hidric_cond,
                              (dbthirdbar_r-wthirdbar_r)/100 as bd FROM sacatalog sc
                              FULL OUTER JOIN legend lg  ON sc.areasymbol=lg.areasymbol
                              FULL OUTER JOIN mapunit mu ON lg.lkey=mu.lkey
                              FULL OUTER JOIN component co ON mu.mukey=co.mukey
                              FULL OUTER JOIN chorizon ch ON co.cokey=ch.cokey
                              FULL OUTER JOIN chtexturegrp ctg ON ch.chkey=ctg.chkey
                              FULL OUTER JOIN chtexture ct ON ctg.chtgkey=ct.chtgkey
                              FULL OUTER JOIN copmgrp pmg ON co.cokey=pmg.cokey
                              FULL OUTER JOIN corestrictions rt ON co.cokey=rt.cokey
                              WHERE mu.mukey IN (
                            SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('polygon((
                           {formatted_coordinates}))')
                   ) 
                              AND sc.areasymbol != 'US' 
                              order by co.cokey, ch.chkey, prcent, topdepth, bottomdepth, muname
                  </sdm:Query>
                </sdm:RunQuery>
             </soap:Body>
          </soap:Envelope>"""
    
    response = requests.post(url, data=body, headers=headers, timeout=140)
    # Put query results in dictionary format
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
    return soil_df
    

from apsimNGpy.utililies.utils import bounding_box_corners

am =   42.060650, -93.885490
bounds = bounding_box_corners(am, 500)
bounds= [i for i in bounds]
print(bounds)
print(coordinates)
df = DownloadsurgoSoilTables(coordinates)

from pathlib import Path


path = Path('D:\ACPd\Onion creek watershed')

class WDir:
    def __init__(self, path_dir=None):
        assert path_dir, "path dir_path is required"
        self.ROOT_path =Path(path)
    def path(self, name = None):
        """
        
        :param name: name of the new file
        :return: realpath for the new file name
        """
        assert name, "name is required"
        return os.path.realpath(self.ROOT_path.joinpath(name))
    
    def mkdir(self, name):
       new_dir = self.ROOT_path.joinpath(name)
       new_dir.mkdir(exist_ok=True)
       return new_dir

    def make_this_cwd(self):
        wd = os.path.realpath(self.ROOT_path)
        if os.getcwd() != wd:
          os.chdir(os.path.realpath(self.ROOT_path))
        else: print(f"this path: {wd} is already the current working dir_path")

gis_data = WDir(path)

shp = [i for i in gis_data.ROOT_path.glob('*305.shp')]
import geopandas as gpd
from apsimNGpy.settings import SOIL_THICKNESS
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.base_data import LoadExampleFiles
import sys
MAIZE = r'D:\ndata\source\sw.apsimx'
model = ApsimModel(MAIZE, thickness_values=SOIL_THICKNESS)
fb_gdf = gpd.read_file(os.path.realpath(shp[0]))
dfa  = df.drop_duplicates(subset = ['bottomdepth', 'cokey'])
gd  = gpd.read_file(r'D:\ndata\soils_data_mukey_305.shp')
# calculate the area under each polygon

print('map unit keys that intersect with the field boundaries')
gdf_j = fb_gdf.sjoin(gd, how="inner", predicate='intersects')
# drop duplicates by MUKEY and Field boundary
df = gdf_j.drop_duplicates(['FBndID', 'MUKEY'])
df_u = df.loc[df['isAG'] ==1].copy()
df_u['area'] = df_u.geometry.area/4000
df_u.to_file(gis_data.path(name = 'mu_intersect.shp'))
DF = df_u.drop_duplicates(['FBndID']).copy()
print(DF.shape)
DF.reset_index(inplace=True)
# get points from the polygons
def get_polygon_points(row):
    """Extract points from a polygon geometry."""
    if row.geometry.geom_type == 'Polygon':
        return list(row.geometry.exterior.coords)
    elif row.geometry.geom_type == 'MultiPolygon':
        points = []
        for polygon in row.geometry:
            points.extend(list(polygon.exterior.coords))
        return points
    else:
        return None  # Or handle other geometry types if necessary

# Apply the function to each row in the GeoDataFrame
def get_polygon_bounds(gdf_):
    gdf = gdf_.copy()
    crs = gdf.crs
    gdf.to_crs(4326, inplace=True)
    #print(f"coordinate system changed from: {crs} to: {gdf.crs}")
    return gdf.apply(get_polygon_points, axis=1)
DF['points'] = get_polygon_bounds(DF)
from apsimNGpy.utililies.utils import exception_handler

def is_soil_profile(row):
    points= get_polygon_points(row)
    sdf =  DownloadsurgoSoilTables(demo)
    def convert(row_):
        return int(row_)

    sdf['prcent'] = sdf['prcent'].apply(convert)
    max = sdf.prcent.max()
    cok_ = sdf[sdf['prcent'] == max].copy()
    if cok_.shape[0] > 2:
        csr = int(cok_['CSR'].iloc[0]) / 100
    return 



@exception_handler()
def simulate_in_pipeline(id):
    try:
        demo =  DF['points'].loc[id]

        def convert(row_):
            return int(row_)
        sdf = DownloadsurgoSoilTables(demo)
        sdf['prcent'] = sdf['prcent'].apply(convert)
        # what about this
        max = sdf.prcent.max()
        cok_ = sdf[sdf['prcent']==max].copy()
        csr = None
        if cok_.shape[0] >2:
            csr = int(cok_['CSR'].iloc[0])/100
            cok = cok_
            dom = OrganizeAPSIMsoil_profile(cok, 20)
            grand = dom.cal_missingFromSurgo()
            aps = gis_data.mkdir('apsim')
            files = model.replicate_file( path = aps, k= 1, tag = 'testt')
            file_m = files.copy()
            soils = grand.copy()

            models = []

            md = ApsimModel(files[0], thickness_values=SOIL_THICKNESS)


            # models = [mod.replace_downloaded_soils(sls, model.extract_simulation_name) for sls in grand for mod in models]
            mode = md

            mode.replace_downloaded_soils(grand, mode.extract_simulation_name)
            #mode.adjust_rue(csr)
            mode.run('Annual')
            res= mode.results.mean(numeric_only =True).to_frame().T
            res_f = res
            res_f['CSR'] = csr


            res_f.reset_index(inplace=True)
            row = DF.iloc[id].to_frame().T.copy()
            row.reset_index(inplace=True)
            del [soils, dom, sdf, csr]
            return pd.concat([row,res_f], axis =1)
        print(f"corresponding data for location: {id} is incomplete, skipping it")
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        # Extract the line number
        line_number = exc_traceback.tb_lineno
        print(type(e).__name__, e)
        print(f"An error occurred on line {line_number}: {e}")
        if type(e).__name__ == 'ValueError':
            print(cok_)
        raise



# daf = []
# for i in range(DF.shape[0]):
#     try:
#       sim= simulate_in_pipeline(i)
#       if isinstance(sim, pd.DataFrame):
#           daf.append(sim)
#       print(f"{i} : completed",end = '\r')
#     except Exception as e:
#       print(type(e).__name__, e)
#       exc_type, exc_value, exc_traceback = sys.exc_info()
#       # Extract the line number
#       line_number = exc_traceback.tb_lineno
#       print(f"An error occurred on line {line_number}: {e}")
#       print("skipping {}".format(i))
#       raise
# dfl = pd.concat(daf, axis=0)
#
# SD =dfl.drop(['OBJECTID', 'index'], axis =1)
#
# gdf = gpd.GeoDataFrame(SD, geometry='geometry', crs='EPSG:4326')
# p = gis_data.path(name = 'simulate.shp')
# import numpy as np
# for col in DF.columns:
#     if DF[col].dtype == np.int64:
#        DF[col] = DF[col].astype(int)
# DF.drop('points', axis = 1, inplace = True)
# Dfl = dfl[['FBndID', 'Yield', 'TopN2O', 'NO3Total', 'NH4Total', 'SOC10_30cm']].copy()
# dfm = DF.merge(Dfl, on  = "FBndID", how = 'inner')
# dfm.to_file(p)


# import system modules 
import arcpy

# Set environment settings
#arcpy.env.workspace = gis_data.mkdir('soil_toolbox')
#  Set local variables
import arcpy
arcpy.env.overwriteOutput = True
arcpy.env.workspace = r'D:\ACPd\Base_files\acpf_huc070801050305\acpf070801050305.gdb'
# Setting the input parameters for the SummarizeWithin tool
polys = os.path.realpath(shp[0])  # This should be a GeoDataFrame or a feature class path
mu_key_poly = r'D:\ndata\soils_data_mukey_305.shp'  # Input feature class
outFeatureClass = 'soil_aggregated'  # Output feature class path
keepAll = 'ONLY_INTERSECTING'  # Option to determine how features are treated
sumFields = [['Damages', 'SUM'], ['VICTIM_AGE', 'MEAN']]  # Fields to summarize
addShapeSum = 'ADD_SHAPE_SUM'  # Adds geometry statistics to output
groupField = 'MUKEY'  # Field used to group features for separate summaries
addMinMaj = 'ADD_MIN_MAJ'  # Adds statistics for minority and majority case
addPercents = 'ADD_PERCENT'  # Adds percentage fields to output
outTable = 'crimes_aggregated_groups'  # Output table name for the summary

# Executing the SummarizeWithin function
# arcpy.analysis.SummarizeWithin(
#     in_polygons=polys,
#     in_sum_features=mu_key_poly,
#     out_feature_class=outFeatureClass,
#     keep_all_polygons=keepAll,
#     sum_fields='',
#     sum_shape=addShapeSum,
#     shape_unit='ACRES',
#     group_field=groupField,
#     add_min_maj=addMinMaj,
#     add_group_percent=addPercents,
#     out_group_table=outTable
# )

intersections = gpd.overlay(fb_gdf, gd, how='intersection')
intersections['area'] = intersections.area/4000
import matplotlib.pyplot as plt

intersections.plot(column='area', legend=True)
plt.show()

# apparently we do not expect any differences in location except the MUKEY,
# so we first run the unique mukeys and merge to all the field boundaries, the
# results are then weighted by the field boundary, but first we need to assess if there is  difference
