from shapely import wkt
import pandas as pd
import os


def convert_df_to_gdf(df, CRS):
    """
    Converts a pandas DataFrame to a GeoPandas GeoDataFrame with specified CRS.

    This function assumes that the input DataFrame contains a column named 'geometry'
    with WKT (Well-Known Text) representations of geometric objects. It converts these
    textual geometry representations into GeoPandas geometry objects and sets the
    coordinate reference system (CRS) for the resulting GeoDataFrame.

    Parameters:
    - df (pandas.DataFrame): The input DataFrame to convert. Must include a 'geometry'
      column with WKT representations of the geometries.
    - CRS (str or dict): The coordinate reference system to set for the GeoDataFrame.
      Can be specified as a Proj4 string, a dictionary of Proj parameters, an EPSG
      code, or a WKT string.

    Returns:
    - gpd.GeoDataFrame: A GeoDataFrame created from the input DataFrame with geometries
      converted from WKT format and the specified CRS.

    Example:
    ```
    import pandas as pd
    import geopandas as gpd
    from shapely import wkt

    # Sample DataFrame with WKT geometries
    data = {'geometry': ['POINT (12 34)', 'LINESTRING (0 0, 1 1, 2 1, 2 2)'],
            'value': [1, 2]}
    df = pd.DataFrame(data)

    # Convert DataFrame to GeoDataFrame with an EPSG code for CRS
    gdf = convert_df_to_gdf(df, CRS='EPSG:4326')
    ```

    Note:
    The 'wkt' module from 'shapely' needs to be imported to convert geometries from WKT.
    """
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, crs=CRS)
    return gdf


def match_crop(abb, add_wheat=None):
    """
    Converts agricultural abbreviations to a string of crop names, with an option to insert 'Wheat' at specified 
    intervals. The function interprets abbreviations where 'B' stands for Soybean, 'C' for Maize, 'P' for Pasture, 
    'U' for Developed areas, 'T' for Wetlands, 'F' for Forest, and 'R' for Other crops.

    This function takes an abbreviation string representing a sequence of crops and optionally inserts 'Wheat' into 
    the sequence at predetermined positions. It handles special cases where the abbreviation matches certain 
    patterns, returning None for these cases.

    Parameters:
    - abb (str): The abbreviation string representing a sequence of crops. Each character stands for a specific crop:
        'C' for Maize,
        'B' for Soybean,
        'W' for Wheat,
        'P' for Tropical Pasture.
      Characters 'U', 'R', 'T', and 'F' are ignored and removed from the abbreviation.
    - add_wheat (bool, optional): If True, 'Wheat' is inserted at positions 1, 3, 5, 7, 9, and 11 in the sequence. Defaults to None, which means 'Wheat' is not added.

    Returns:
    - str or None: A comma-separated string of crop names based on the abbreviation. Returns None if the abbreviation matches special cases 'TTTTTT' or 'UUUUUUU'.

    Example:
    ```
    # Convert abbreviation to crop names with additional 'Wheat'
    crop_sequence = match_crop("CBWP", add_wheat=True)
    print(crop_sequence)
    # Output: "Maize,Wheat,Soybean,Wheat,Wheat,Tropical Pasture"

    # Convert abbreviation without adding 'Wheat'
    crop_sequence = match_crop("CBWP")
    print(crop_sequence)
    # Output: "Maize,Soybean,Wheat,Tropical Pasture"
    ```

    Note:
    - The function returns None for special case abbreviations 'TTTTTT' and 'UUUUUUU' as an indication of non-standard sequences that should not be ran_ok.
    - The insertion of 'Wheat' at specified positions assumes the sequence is long enough to accommodate these insertions. If the sequence is shorter, 'Wheat' will only be inserted up to the length of the sequence.
    """
    # Reserve the original abbreviation
    reserve = abb

    # Check if abbreviation does not match special cases and contains certain characters
    if abb not in ['TTTTTT', 'UUUUUUU'] and ('C' in abb or 'B' in abb or 'W' in abb or 'P' in abb):
        # Remove specified characters from the abbreviation
        work = abb.replace("U", "").replace("R", "").replace("T", "").replace("F", "")

        # Replace abbreviations with crop names, adding commas between them
        rotation = work.replace("C", "Maize,").replace("B", "Soybean,").replace("W", "Wheat").replace('P',
                                                                                                      'TropicalPasture').rstrip(
            ",")
        rot2 = rotation.split(",")

        if add_wheat:
            # Insert "Wheat" at specified positions if add_wheat is True
            for i in [1, 3, 5, 7, 9, 11]:
                if i < len(rot2):
                    rot2.insert(i, "Wheat")
            crop = ",".join(rot2)
        else:
            # Join the rotation without additional "Wheat"
            crop = ",".join(rot2)
    else:
        # If abbreviation matches special cases, return it as is
        crop = None

    return crop


from functools import singledispatch


@singledispatch
def append(obj, x):
    print("Unsupported type")


@append.register
def _(obj: list, x: list):
    return obj + x


@append.register
def _(obj: set, x: set):
    return obj.union(x)


@append.register
def _(obj: str, x: str):
    return obj + x


print(append([1, 2, 3], [4, 5]))
print(append({1, 2, 3}, {4, 5}))
print(append("1 2 3", " 4 5"), "\n")

append(2, 3)

if __name__ == "__main__":
    al = match_crop('CBBBBC')

    print(al)
    csv = r'D:\ACPd\Long deek401 simulations\lu_table.csv'
    df = pd.read_csv(csv)
    col = df.CropRotatn

    df['rotation_cover_crop'] = df['CropRotatn'].apply(lambda x: match_crop(x, add_wheat=True))
    df['rotations'] = df['CropRotatn'].apply(lambda x: match_crop(x, add_wheat=False))

    print(df)
    df.to_csv("fin.csv")
    # os.startfile('fin.csv')
    from functools import total_ordering


   