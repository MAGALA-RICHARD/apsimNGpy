from functools import lru_cache


@lru_cache(maxsize=100)
def _is_within_USA_mainland(lonlat):
    lon_min, lon_max = -125.0, -66.9  # Approximate longitudes for the west and east coasts
    lat_min, lat_max = 24.4, 49.4  # Approximate latitudes for the southern and northern borders

    # Check if given coordinates are within the bounding box
    if lon_min <= lonlat[0] <= lon_max and lat_min <= lonlat[1] <= lat_max:
        return True
    else:
        return False


pythonic_key_map = {
    "winter_cona": "WinterCona",
    "psi_dul": "PSIDul",
    "depth": "Depth",
    "diffus_slope": "DiffusSlope",
    "diffus_const": "DiffusConst",
    "k_lat": "KLAT",
    "pore_interaction_index": "PoreInteractionIndex",
    "discharge_width": "DischargeWidth",
    "swcon": "SWCON",
    "cn_cov": "CNCov",
    "catchment_area": "CatchmentArea",
    "water": "Water",
    "salb": "Salb",
    "winter_u": "WinterU",
    "runoff": "Runoff",
    "cn2_bare": "CN2Bare",
    "winter_date": "WinterDate",
    "potential_infiltration": "PotentialInfiltration",
    "summer_date": "SummerDate",
    "sw_mm": "SWmm",
    "summer_cona": "SummerCona",
    "summer_u": "SummerU",
    "precipitation_interception": "PrecipitationInterception",

}


def soil_water_param_fill(
        model, simulations=None,
        *,
        winter_cona: float = None,
        psi_dul: float = None,
        depth: list = None,
        diffus_slope: float = None,
        diffus_const: float = None,
        k_lat: float = None,
        pore_interaction_index: float = None,
        discharge_width: float = None,
        swcon: list = None,
        cn_cov: float = None,
        catchment_area: float = None,
        water=None,
        salb: float = None,
        winter_u: float = None,
        runoff: float = None,
        cn2_bare: int = None,
        winter_date: str = None,
        potential_infiltration: float = None,
        summer_date: str = None,
        sw_mm: float = None,
        summer_cona: float = None,
        summer_u: float = None,
        precipitation_interception: float = None, ):
    """
        Merge user-provided soil and surface hydrology parameters into an
        APSIM-compatible parameter dictionary.

        This function accepts pythonic, keyword-only parameters corresponding
        to APSIM soil water, runoff, and evaporation settings. Only parameters
        explicitly provided by the user (i.e., not ``None``) are retained.
        Parameter names are automatically mapped to their APSIM schema names
        and returned as a clean dictionary suitable for direct insertion into
        an APSIMX file.

        Parameters
        ----------
        winter_cona : float, optional
            Drying coefficient for stage 2 soil water evaporation in winter
            (APSIM: ``WinterCona``).
            Scalar parameter.
        psi_dul : float, optional
            Matric potential at drained upper limit (DUL), in cm
            (APSIM: ``PSIDul``).
            Scalar parameter.
        depth : list of str, optional
            Soil layer depth intervals expressed as strings
            (e.g., ``"0-150"``, ``"150-300"``).
            Layered parameter.
        diffus_slope : float, optional
            Effect of soil water storage above the lower limit on soil water
            diffusivity (mm) (APSIM: ``DiffusSlope``).
            Scalar parameter.
        diffus_const : float, optional
            Constant in soil water diffusivity calculations
            (APSIM: ``DiffusConst``).
            Scalar parameter.
        k_lat : float, optional
            Lateral hydraulic conductivity parameter for catchment flow
            (APSIM: ``KLAT``).
            Scalar parameter.
        pore_interaction_index : float, optional
            Pore interaction index controlling soil water movement
            (APSIM: ``PoreInteractionIndex``).
            Scalar parameter.
        discharge_width : float, optional
            Basal width of the downslope boundary of the catchment used in
            lateral flow calculations (m) (APSIM: ``DischargeWidth``).
            Scalar parameter.
        swcon : list of float, optional
            Soil water conductivity parameter controlling root water uptake
            (APSIM: ``SWCON``).
            Layered parameter (one value per soil layer).
        cn_cov : float, optional
            Fractional cover at which maximum runoff curve number reduction
            occurs (APSIM: ``CNCov``).
            Scalar parameter.
        catchment_area : float, optional
            Catchment area used for runoff and lateral flow calculations (m²)
            (APSIM: ``CatchmentArea``).
            Scalar parameter.
        water : dict, optional
            Nested water balance configuration block
            (APSIM: ``Water``).
            Dictionary parameter.
        salb : float, optional
            Fraction of incoming solar radiation reflected by the soil surface
            (albedo) (APSIM: ``Salb``).
            Scalar parameter.
        winter_u : float, optional
            Cumulative soil water evaporation required to complete stage 1
            evaporation during winter (APSIM: ``WinterU``).
            Scalar parameter.
        runoff : float, optional
            Runoff fraction or runoff scaling factor
            (APSIM: ``Runoff``).
            Scalar parameter.
        cn2_bare : int or float, optional
            Runoff curve number for bare soil under average moisture conditions
            (APSIM: ``CN2Bare``).
            Scalar parameter.
        winter_date : str, optional
            Calendar date marking the switch to winter parameterization
            (APSIM: ``WinterDate``), e.g. ``"1-Apr"``.
            Scalar string parameter.
        potential_infiltration : float, optional
            Potential infiltration limit used in runoff calculations
            (APSIM: ``PotentialInfiltration``).
            Scalar parameter.
        summer_date : str, optional
            Calendar date marking the switch to summer parameterization
            (APSIM: ``SummerDate``), e.g. ``"1-Nov"``.
            Scalar string parameter.
        sw_mm : float, optional
            Total soil water storage (mm) if explicitly specified
            (APSIM: ``SWmm``).
            Scalar parameter.
        summer_cona : float, optional
            Drying coefficient for stage 2 soil water evaporation in summer
            (APSIM: ``SummerCona``).
            Scalar parameter.
        summer_u : float, optional
            Cumulative soil water evaporation required to complete stage 1
            evaporation during summer (APSIM: ``SummerU``).
            Scalar parameter.
        precipitation_interception : float, optional
            Fraction or amount of precipitation intercepted before reaching
            the soil surface (APSIM: ``PrecipitationInterception``).
            Scalar parameter.


        Returns
        -------
        dict
            Dictionary of APSIM-formatted parameter names and values containing
            only parameters explicitly provided by the user. All ``None`` values
            are omitted.

        Notes
        -----
        - Layered parameters (e.g., ``Depth``, ``SWCON``) must match the number
          of soil layers defined elsewhere in the soil profile.
        - Scalar parameters apply uniformly across the profile or surface.
        - This function performs no unit conversion or physical validation;
          it assumes APSIM-compatible units.
        """

    user_params = dict(locals())
    # 2. merge + rename ONLY non-None values
    apsim_params = {
        pythonic_key_map[k]: v
        for k, v in user_params.items()
        if v is not None and k in pythonic_key_map}

    model.edit_model(model_type='Models.WaterModel.WaterBalance', model_name='SoilWater', simulations=simulations,
                     **apsim_params)
    # out = model.inspect_model_parameters_by_path('.Simulations.Simulation.Field.Soil.SoilWater')


if __name__ == '__main__':
    from apsimNGpy.core.apsim import ApsimModel

    with ApsimModel('Maize') as fixed_model:
        soil_water_param_fill(fixed_model, summer_date='1-May', precipitation_interception=13.5)
