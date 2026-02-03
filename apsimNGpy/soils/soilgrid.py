import numpy as np
import requests
from itertools import chain
import pandas as pd
from apsimNGpy.core_utils.utils import timer
from scipy.interpolate import interp1d
from apsimNGpy.soils.soilmanager import vary_soil_var_by_layer
from apsimNGpy.soils.saxon_rawls import (sat, cal_dul_from_sand_clay_OM,
                                         ks_from_soilgrids,
                                         cal_l15_from_sand_clay_OM)
from tenacity import retry_if_exception_type, retry, stop_after_attempt, wait_exponential, wait_fixed

PARTICLE_DENSITY = 2.65  # g/cm³
PHYSICAL_PROPERTIES = physic = {"BD", "LL15", "DUL", "SAT", "KS", "Sand", "Silt", "Clay", "AirDry", }
control_param_a, control_param_b = 0, 0.2,
default_crop_KL_XF = {'Maize': (0.08, 1), 'Wheat': (0.08, 1), 'Soybean': (0.08, 1)}
TME_OUT_ERROR = requests.exceptions.ConnectTimeout
HTTPError = requests.exceptions.HTTPError


def extract_layers(data, property, stat="mean"):
    layers = data.get("properties", {}).get("layers", [])

    for layer in layers:
        if layer.get("name") == property:
            out = {
                d["label"]: d["values"].get(stat)
                for d in layer.get("depths", [])
                if stat in d.get("values", {})
            }
            return [
                {"depth": k, 'value': v, 'name': property}
                for k, v in out.items()
            ]

    raise KeyError(
        f"Property '{property}' not found. "
        f"Available: {[l.get('name') for l in layers]}"
    )


URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
from functools import cache

params = {
    "lat": 42.0,
    "lon": -92.5,
    "property": ("soc", "clay", "sand", 'silt', 'cec', 'phh2o', 'bdod', 'wv0033', 'wv1500', 'nitrogen'),
    "depth": ("0-5cm",
              "5-15cm",
              "15-30cm",
              "30-60cm",
              "60-100cm",),
    "value": "mean"
}


def soil_grid_thickness():
    return {
        "0-5cm": 50,
        "5-15cm": 100,
        "15-30cm": 150,
        "30-60cm": 300,
        "60-100cm": 400,
        "100-200cm": 1000,
    }


def generate_thickness(data):
    """
    Generate a thickness array or a sequence first get the thickness column fom the soil grid data and match it to the expected
    @param data: soil grid data as pd.DataFrame
    @return: list
    """
    depth = data.get("depth")
    thickness = soil_grid_thickness()
    return [thickness[d] for d in depth]


def generate_params(**kwargs):
    return kwargs


@retry(stop=stop_after_attempt(2), retry=retry_if_exception_type((HTTPError, TME_OUT_ERROR)))
@cache
def get_soil_grid_by_lonlat(**_params):
    response = requests.get(URL, params=_params)
    response.raise_for_status()
    meta = response.json()
    data: list = [extract_layers(meta, i) for i in _params.get("property", {})]
    return data, meta


def base_soil_grid_data(reset_index=True, **_params, ):
    data, meta = get_soil_grid_by_lonlat(**params)
    data_chain: list = list(chain.from_iterable(data))
    df_long = pd.DataFrame(data_chain)
    wide = df_long.pivot(index="depth", columns="name", values="value")
    if reset_index:
        wide = wide.reset_index()
    return wide


def separate_depth(depth_thickness):
    thickness_array = np.array(depth_thickness)
    bottom_depth = np.cumsum(thickness_array)  # bottom depth should not have zero
    top_depth = bottom_depth - thickness_array
    return bottom_depth, top_depth


def get_depth(depth_thickness_mm):
    bottom_depth, top_depth = separate_depth(depth_thickness_mm)
    return [f"{t}-{b}" for t, b in zip(top_depth, bottom_depth)]


def extend_soil_profile(
        var: str,
        soil_data,
        thickness_mm,
        kind="linear",
):
    """
    Interpolate / extrapolate a soil variable onto APSIM layers.

    Parameters
    ----------
    var : str
        Column name (e.g. 'soc', 'clay').
    soil_data : DataFrame
        Must contain 'depth' and var columns.
    thickness_mm : sequence
        APSIM layer thicknesses in mm.
    """

    # use bottom depth (cm) as interpolation axis
    depths = soil_data["depth"].astype(str)
    x = np.array([
        int(d.split("-")[1].replace("cm", ""))
        for d in depths
    ])

    y = soil_data[var].to_numpy()

    # APSIM target depths = cumulative thickness midpoints
    thickness_cm = np.asarray(thickness_mm) / 10
    bottoms = np.cumsum(thickness_cm)
    tops = np.concatenate([[0], bottoms[:-1]])
    x_new = (tops + bottoms) / 2

    def interp(method):
        f = interp1d(
            x,
            y,
            kind=method,
            fill_value="extrapolate",
            bounds_error=False,
        )
        return f(x_new)

    arr = interp(kind)
    if np.any(arr < 0):
        kind = 'nearest'
        arr = interp(kind)
    return arr


def transform_soil_grid_data(soil_data: pd.DataFrame):
    sdf = soil_data.copy()

    sdf['OM'] = sdf['soc'] * 1.72
    sdf[['soc', 'BD']] = sdf[['soc', 'bdod']] / 100
    sdf['SAT'] = sat(bd=sdf['BD'], particle_density=PARTICLE_DENSITY)
    sdf[['sand', 'clay', 'silt', 'phh2o']] = sdf[['sand', 'clay', 'silt', 'phh2o']] / 10
    sdf[['Sand', 'Clay', 'Silt', 'PH']] = sdf[['sand', 'clay', 'silt', 'phh2o']]
    if not sdf['wv1500'].empty:
        ll15 = sdf['wv1500'] / 1000
    else:
        ll15 = cal_l15_from_sand_clay_OM(sdf)
    if not sdf['wv0033'].empty:
        dul = sdf['wv0033'] / 1000
    else:
        dul = cal_dul_from_sand_clay_OM(sdf)

    ks = ks_from_soilgrids(sdf)
    sdf['DUL'] = dul
    sdf['LL15'] = ll15
    sdf['AirDry'] = ll15 / 2
    sdf['KS'] = ks
    return sdf


def organic(data, thickness_values: list, top_finert=0.88, top_fom=180, top_fbiom=0.04, fom_cnr=40, soil_cnr=12):
    n_layers = len(thickness_values)
    SoilCNRatio = np.full(shape=n_layers, fill_value=soil_cnr, dtype=np.int64)
    FOM = top_fom * vary_soil_var_by_layer(n_layers, a=control_param_a, b=control_param_b)
    FOM_CN = np.full(shape=n_layers, fill_value=fom_cnr, dtype=np.int64)
    fbiom = top_fbiom * vary_soil_var_by_layer(n_layers, a=control_param_a, b=control_param_b)
    finert = top_finert * vary_soil_var_by_layer(n_layers, a=control_param_a, b=-0.01)

    carbon = extend_soil_profile(var='soc', soil_data=data, thickness_mm=thickness_values)

    return pd.DataFrame({'SoilCNRatio': SoilCNRatio, 'FInert': finert, 'FOM': FOM, 'FBIOM': fbiom, 'FOM.CN': FOM_CN,
                         'Thickness': thickness_values,
                         'Carbon': carbon, })


def physical(transform_data, thickness_values):
    out = {k: extend_soil_profile(var=k, thickness_mm=thickness_values, soil_data=transform_data) for k in
           PHYSICAL_PROPERTIES}
    out["Thickness"] = thickness_values
    return pd.DataFrame(out)


def pH(transform_data, thickness_values):
    return extend_soil_profile(soil_data=transform_data, var='PH', thickness_mm=thickness_values)


def soil_crop_params(transformed_data, thickness_values_mm, crops: dict = None):
    if isinstance(crops, dict):
        crops = crops
    elif crops is None:
        crops = default_crop_KL_XF
    else:
        raise ValueError(f"crops must be a dict, got {type(crops)} see example {default_crop_KL_XF}")
    n_layers = len(thickness_values_mm)

    def _calculate(kl_xf):
        kl, xf = kl_xf
        cropKL = kl * vary_soil_var_by_layer(n_layers, a=control_param_a, b=control_param_b)
        cropXF = xf * vary_soil_var_by_layer(n_layers, a=control_param_a, b=0)[:n_layers]
        return cropKL, cropXF

    cropLL = extend_soil_profile(soil_data=transformed_data, var='LL15', thickness_mm=thickness_values_mm)
    names = []
    _frame = []
    for i in crops:
        names.append([i + "KK", i + 'LL ', i + 'XF'])
        cropKL, cropXF = _calculate(crops[i])
        dfs = pd.DataFrame({'KL': cropKL, 'LL': cropLL, 'XF': cropXF})
        _frame.append(dfs)

    crop_frame = []
    for i, dfc in zip(names, _frame):
        crop_frame.append(dfc.rename(columns={"kl": i[0], "ll": i[1], "xf": i[2]}))
    crop_df = pd.concat(crop_frame, join='outer', axis=1)
    return crop_df, tuple(crops.keys())


def adjust_dul(physical_data):
    """
    Adjust the dul TO MATCH WITH APSIM requirements
    @param physical_data: data with DUL and SAT variables
    @return:
    """

    dul = physical_data.DUL
    saT = physical_data.SAT
    dul = np.asarray(dul)
    saT = np.asarray(saT)
    for idx, (d, s) in enumerate(zip(dul, saT)):
        if d > s:
            diff = d - s
            dul[idx] = d - (diff + 0.002)
    return dul


def aggregate_data(transformed_data, *, thickness_mm, crops=None, metadata=None, swim=None,
                   top_finert=0.65, top_fom=180, top_fbiom=0.04, fom_cnr=40, soil_cnr=12, swcon=0.3, top_urea=0,
                   top_nh3=0.5, top_nh4=0.05):
    n_layers = len(thickness_mm)
    depth = get_depth(thickness_mm)
    # set some meta_info
    meta_default = {'thickness sequence': thickness_mm, 'Depth': depth}
    if isinstance(metadata, dict):
        metadata = metadata | {'thickness sequence': thickness_mm}
    elif metadata is None:
        metadata = meta_default
    else:
        raise TypeError("metadata must be a dictionary or None")
    # collect soil organic data
    _organic = organic(thickness_values=thickness_mm, data=transformed_data, top_finert=top_finert, top_fom=top_fom,
                       top_fbiom=top_fbiom, fom_cnr=fom_cnr,
                       soil_cnr=soil_cnr)
    # collect soil physical data
    _physical = physical(transformed_data, thickness_mm)

    # po = 1 - (_physical["BD"].values / 2.65)
    # swi_con = (po - _physical['DUL'].values) / po
    swi_con = np.full(shape=n_layers, fill_value=swcon, dtype=np.float64)

    # soil water data
    soil_water = pd.DataFrame({'Thickness': thickness_mm, 'SWCON': swi_con})
    NO3N = top_nh3 * vary_soil_var_by_layer(n_layers, a=control_param_a, b=0.01)
    NH4N = top_nh4 * vary_soil_var_by_layer(n_layers, a=control_param_a, b=0.01)
    NO3 = pd.DataFrame({'Thickness': thickness_mm, 'InitialValues': NO3N, 'Depth': depth})
    NH4 = pd.DataFrame({'Thickness': thickness_mm, 'InitialValues': NH4N, 'Depth': depth})
    chemical = pd.DataFrame(
        {'Thickness': thickness_mm, 'NO3N': NO3N, 'NH4N': NH4N, 'Depth': depth,
         'PH': pH(transform_data=transformed_data, thickness_values=thickness_mm)})
    Urea = pd.DataFrame(
        {'Thickness': thickness_mm, 'Depth': depth, 'InitialValues': np.full(n_layers, top_urea)})
    # crop specific parameters e.g KL, XF
    cp_df, _crops = soil_crop_params(transformed_data, thickness_mm, crops=crops)
    # initial waters
    _physical['DUL'] = adjust_dul(_physical)
    water = pd.DataFrame(
        {'Depth': depth, 'Thickness': thickness_mm,
         'InitialValues': _physical['DUL'].values})
    out = {
        'meta_info': metadata,
        'csr': pd.Series([]),
        'organic': _organic,
        'physical': _physical,
        'swcon': swi_con,
        'Urea': Urea, 'NH4': NH4,
        'NO3': NO3,
        'soil_crop': cp_df,
        'chemical': chemical,
        'crops': _crops,
        'soil_water': soil_water,
        'water': water,
        'swim': swim,
    }
    return out


@timer
def get_soil_profile_soil_grid(lonlat,
                               thickness_values_mm,
                               top_finert=0.88,
                               top_fom=180,
                               top_fbiom=0.04,
                               fom_cnr=40,
                               soil_cnr=12,
                               swcon=0.3,
                               top_urea=0,
                               top_nh3=0.5,
                               top_nh4=0.05
                               ):
    """
    Retrieve and construct an APSIM-ready soil profile from SoilGrids data
    for a given geographic location.

    This function queries SoilGrids using longitude and latitude, transforms
    raw SoilGrids outputs into APSIM-compatible soil physical and chemical
    properties, and aggregates them into user-defined soil layer thicknesses.
    Surface soil carbon and nitrogen pools are initialized using APSIM
    conventions and user-specified parameters.

    Parameters
    ----------
    lonlat : tuple(float, float)
        Geographic coordinates as (longitude, latitude) in decimal degrees.
    thickness_values_mm : sequence of int or float
        Target soil layer thicknesses in millimeters used to aggregate
        SoilGrids depth intervals.
    top_finert : float, optional
        Fraction of inert organic matter (FInert) in the surface soil layer.
        Default is 0.88.
    top_fom : float, optional
        Fresh organic matter (FOM) content of the surface soil layer
        in kg C ha⁻¹. Default is 180.
    top_fbiom : float, optional
        Fraction of microbial biomass carbon (FBiom) in the surface layer.
        Default is 0.04.
    fom_cnr : float, optional
        Carbon-to-nitrogen ratio (C:N) of fresh organic matter.
        Default is 40.
    soil_cnr : float, optional
        Carbon-to-nitrogen ratio (C:N) of soil organic matter (humic pool).
        Default is 12.
    swcon : float, optional
        Soil water conductivity parameter controlling water extraction
        rate by roots (APSIM `SWCON`). Typical values range from 0.1–1.
        Default is 0.3.
    top_urea : float, optional
        Initial urea nitrogen in the surface soil layer (kg N ha⁻¹).
        Default is 0.
    top_nh3 : float, optional
        Initial nitrate nitrogen (NO₃⁻–N) in the surface soil layer
        in kg N ha⁻¹. Default is 0.5.
    top_nh4 : float, optional
        Initial ammonium nitrogen (NH₄⁺–N) in the surface soil layer
        in kg N ha⁻¹. Default is 0.05.

    Returns
    -------
    dict
        Aggregated soil profile containing APSIM-compatible physical,
        water,organic and nitrogen parameters structured by soil layer.

    Notes
    -----
    - SoilGrids does not provide mineral nitrogen; nitrate, ammonium,
      and urea pools are initialized using user-defined assumptions.
    - Organic carbon and nitrogen pools are derived from SoilGrids SOC
      using APSIM-standard pool partitioning and C:N ratios.
    - Returned data are suitable for direct insertion into an APSIM
      soil model (`Soil`, `SoilWater`, `SoilOrganicMatter`, `SoilNitrogen`).

    See Also
    --------
    base_soil_grid_data
    transform_soil_grid_data
    aggregate_data
    """
    PARAMS = {**params}
    lon, lat = lonlat
    PARAMS['lat'] = lat
    PARAMS['lon'] = lon
    base_data = base_soil_grid_data(**PARAMS)
    transformed = transform_soil_grid_data(base_data)
    return aggregate_data(transformed, thickness_mm=thickness_values_mm,
                          top_finert=top_finert,
                          top_fom=top_fom, top_fbiom=top_fbiom,
                          fom_cnr=fom_cnr,
                          soil_cnr=soil_cnr, swcon=swcon,
                          top_urea=top_urea,
                          top_nh3=top_nh3, top_nh4=top_nh4
                          )


if __name__ == "__main__":
    TH = [10, 100, 200, 200, 300, 300, 400, 500]
    df = base_soil_grid_data(**params)
    sd = transform_soil_grid_data(df)
    phys = physical(sd, TH)
    extend_soil_profile(soil_data=sd, var='bdod', thickness_mm=[10, 100, 200, 200, 300, 300, 400, 500], kind='linear')
    aggregate_data(sd, thickness_mm=TH)
    sp = get_soil_profile_soil_grid(lonlat=(-93.312, 43.012), thickness_values_mm=TH)['organic']
