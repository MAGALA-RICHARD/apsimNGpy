from shapely import wkt


def convert_df_to_gdf(df, CRS):
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, crs=CRS)
    return gdf


def remove_missing_tables(sp):
    print(len(sp))
    before = len(sp)
    for counter, i in enumerate(sp):
        if df_has_nan(i[0]) or df_has_nan(i[1]) or df_has_nan(i[2]):
            sp.pop(counter)
    after = len(sp)
    print(before - after, "had empty columns")
    return sp
