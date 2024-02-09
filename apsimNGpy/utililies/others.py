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


def match_crop(abb):
    if abb.count('C') >= 2 and abb.count("B") >= 2:
        return "Maize, Soybean" if abb.startswith('C') else "Soybean, Maize"
    if abb.count("C") >3:
        return "Maize"
    if abb.count("B") > 3:
        return 'Soybean'


al = match_crop('CCBBBC')
print(al)
