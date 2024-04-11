import os.path

import requests
import xmltodict
import pandas as pd

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
        assert path_dir, "path directory is required"
        self.ROOT_path =Path(path)
    def path(self, name = None):
        """
        
        :param name: name of the new file
        :return: realpath for the new file name
        """
        assert name, "name is required"
        return os.path.realpath(self.ROOT_path.joinpath(name))
    def mkdir(self, name) -> None:
       new_dir = self.ROOT_path.joinpath(name)
       new_dir.mkdir(parents=True, exist_ok=True)

    def make_this_cwd(self):
        os.mkdir(self.ROOT_path)

gis_data = WDir(path)

shp = [i for i in gis_data.ROOT_path.glob('*305.shp')]
import geopandas as gpd
DF = gpd.read_file(os.path.realpath(shp[0]))
dfa  = df.drop_duplicates(subset = ['bottomdepth', 'cokey'])

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
def get_polygon_bounds(gdf):
    crs = gdf.crs
    gdf.to_crs(4326, inplace=True)
    print(f"coordinate system changed from: {crs} to: {gdf.crs}")
    return gdf.apply(get_polygon_points, axis=1)
DF['points'] = get_polygon_bounds(DF)
demo =  DF['points'].loc[0]
sdf = DownloadsurgoSoilTables(demo)


