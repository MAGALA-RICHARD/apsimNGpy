import requests
import pandas as pd
import xmltodict


def get_gssurgo_soil_soil_table_at_lonlat(lonlat, select_componentname=None, summarytable=False):
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
    url = "https://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx"
    # headers = {'content-type': 'application/soap+xml'}
    headers = {'content-type': 'text/xml'}
    body = """<?xml version="1.0" encoding="utf-8"?>
              <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:sdm="http://SDMDataAccess.nrcs.usda.gov/Tabular/SDMTabularService.asmx">
       <soap:Header/>
       <soap:Body>
          <sdm:RunQuery>
             <sdm:Query>SELECT co.cokey as cokey, ch.chkey as chkey, comppct_r as prcent, compkind as compkind_series, wsatiated_r as wat_r,partdensity as pd, dbthirdbar_h as bb, musym as musymbol, compname as componentname, muname as muname, slope_r, slope_h as slope, hzname, hzdept_r as topdepth, hzdepb_r as bottomdepth, awc_r as PAW, ksat_l as KSAT,
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
                        WHERE mu.mukey IN (SELECT * from SDA_Get_Mukey_from_intersection_with_WktWgs84('point(""" + lonLat + """)')) 

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
            # print("the following{0} soil components were found". format(list(soil_df.componentname.unique())))
        elif select_componentname is None:
            # print("the following{0} soil components were found". format(list(soil_df.componentname.unique())))
            return soil_df
        elif select_componentname != 'domtcp' and select_componentname not in soil_df.componentname.unique() or select_componentname != None:
            print(
                f'Ooops! we realised that your component request: {select_componentname} does not exists at the '
                f'specified location. We have returned the dorminant component name')
            return dom_component


def get_gssurgo_soil_soil_table_at_polygon(_coordinates):
    """
        Function to get al soil mapunit keys or components intersection a polygon
    :param _coordinates: a list returned by get_polygon_bounds function
    :return: data frame
    """
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

def get_polygon_points(row):
    """Extract points from a polygon geometry."""
    if row.geometry.geom_type == 'Polygon':
        return list(row.geometry.exterior.coords)
    elif row.geometry.geom_type == 'MultiPolygon':
        points = []
        for polygon in row.geometry.geoms:
            points.extend(list(polygon.exterior.coords))
        return points
    else:
        return None  # not sure of other polygon types

# Apply the function to each row in the GeoDataFrame
def get_polygon_bounds(gdf_):
    gdf = gdf_.copy()
    crs = gdf.crs
    gdf.to_crs(4326, inplace=True)
    #print(f"coordinate system changed from: {crs} to: {gdf.crs}")
    return gdf.apply(get_polygon_points, axis=1)