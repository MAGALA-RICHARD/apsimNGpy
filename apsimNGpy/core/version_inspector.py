from apsimNGpy.starter.starter import CLR
from apsimNGpy.core.run_time_info import BASE_RELEASE_NO, GITHUB_RELEASE_NO


def is_higher_apsim_version(simulations_model):
    try:
        ap_version = simulations_model.get_ApsimVersion()
    except AttributeError:
        ap_version = CLR.get_apsim_version_no
    current_version = float(ap_version.replace(".", ''))
    base = BASE_RELEASE_NO.replace('.', '')
    base = float(base)
    github_version = float(GITHUB_RELEASE_NO.replace('.', ''))
    if current_version > base or current_version == github_version:
        return True
