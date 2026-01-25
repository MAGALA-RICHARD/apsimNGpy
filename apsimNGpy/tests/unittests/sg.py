import ee


def ensure_ee_initialized(auth_mode="auto"):
    """
    Initialize Google Earth Engine safely and idempotently.

    auth_mode:
      - "auto"    -> try initialize, authenticate only if needed
      - "oauth"   -> force interactive OAuth
      - "service" -> service account only
    """
    try:
        ee.Initialize()
        return
    except Exception:
        pass

    if auth_mode == "service":
        raise RuntimeError("Earth Engine not initialized and service account required")

    ee.Authenticate()
    ee.Initialize()


def fetch_collections(mode):
    ensure_ee_initialized(mode)
    COLLECTIONS = {

        "ksat": ee.ImageCollection("projects/sat-io/open-datasets/HiHydroSoilv2_0/ksat"),
        "satfield": ee.ImageCollection("projects/sat-io/open-datasets/HiHydroSoilv2_0/sat-field"),
        "N": ee.ImageCollection("projects/sat-io/open-datasets/HiHydroSoilv2_0/N"),
        "alpha": ee.ImageCollection("projects/sat-io/open-datasets/HiHydroSoilv2_0/alpha"),
        "crit_wilt": ee.ImageCollection("projects/sat-io/open-datasets/HiHydroSoilv2_0/crit-wilt"),
        "field_crit": ee.ImageCollection("projects/sat-io/open-datasets/HiHydroSoilv2_0/field-crit"),
        "ormc": ee.ImageCollection("projects/sat-io/open-datasets/HiHydroSoilv2_0/ormc"),
        "stc": ee.ImageCollection("projects/sat-io/open-datasets/HiHydroSoilv2_0/stc"),
        "wcavail": ee.ImageCollection("projects/sat-io/open-datasets/HiHydroSoilv2_0/wcavail"),
        "wcpf2": ee.ImageCollection("projects/sat-io/open-datasets/HiHydroSoilv2_0/wcpf2"),
        "wcpf3": ee.ImageCollection("projects/sat-io/open-datasets/HiHydroSoilv2_0/wcpf3"),
        "wcpf4_2": ee.ImageCollection("projects/sat-io/open-datasets/HiHydroSoilv2_0/wcpf4-2"),
        "wcres": ee.ImageCollection("projects/sat-io/open-datasets/HiHydroSoilv2_0/wcres"),
        "wcsat": ee.ImageCollection("projects/sat-io/open-datasets/HiHydroSoilv2_0/wcsat"),
        "hydrologic_soil_group": ee.Image("projects/sat-io/open-datasets/HiHydroSoilv2_0/Hydrologic_Soil_Group_250m")
        # Single Image

    }
    return COLLECTIONS
