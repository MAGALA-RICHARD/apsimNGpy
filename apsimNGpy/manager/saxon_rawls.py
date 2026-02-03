import numpy as np


def cal_organic_matter(oc):
    """
    Convert organic carbon to organic matter using
    the Van Bemmelen factor (Brady & Weil, 2016).
    """
    return oc * 1.724


def sat(bd, particle_density=2.65):
    """
    Estimate soil saturation (porosity) from bulk density.

    Parameters
    ----------
    bd : float or array-like
        Bulk density (g/cm³ or kg/dm³).
    particle_density : float
        Particle density (default = 2.65 g/cm³).

    Returns
    -------
    float or array-like
        Saturation (volumetric fraction).
    """
    sat = 1.0 - (np.array(bd) / particle_density) - 0.02
    return sat


def cal_dul_from_sand_clay_OM(data):  # has potential to cythonize
    clay = np.asarray(data.clay) * 0.01
    sand = np.asarray(data.sand) * 0.01
    om = np.asarray(data.OM) * 0.01
    ret1 = -0.251 * sand + 0.195 * clay + 0.011 * om + (0.006) * sand * om - 0.027 * clay * om + 0.452 * (
            sand * clay) + 0.299
    dul = ret1 + 1.283 * np.float_power(ret1, 2) - 0.374 * ret1 - 0.015

    return dul


def cal_l15_from_sand_clay_OM(data):  # has potential to cythonize
    clay = np.asarray(data.clay) * 0.01
    sand = np.asarray(data.sand) * 0.01
    om = np.asarray(data.OM) * 0.01
    ret1 = -0.024 * sand + (
            0.487 * clay) + 0.006 * om + 0.005 * sand * om + 0.013 * clay * om + 0.068 * sand * clay + 0.031
    out = ret1 + 0.14 * ret1 - 0.02

    return out


def ks_from_soilgrids(data):
    """
    Estimate APSIM KS (mm/day) from SoilGrids properties
    using Saxton & Rawls (2006).
    """

    sand = data.sand
    clay = data.clay
    bd= data.BD

    SAT = sat(bd)

    log_ks_hr = (
            12.012
            - 0.0755 * sand
            - 3.895 * (SAT - 0.01)
            + 0.157 * clay
    )

    ks_mm_day = (10 ** log_ks_hr) * 24
    return np.clip(ks_mm_day, 1.0, 1000.0)
