from apsimNGpy.manager.soilmanager import DownloadsurgoSoiltables, OrganizeAPSIMsoil_profile


def download_soil_table(x):
    try:
        cod = x
        table = DownloadsurgoSoiltables(cod)
        th = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
        sp = OrganizeAPSIMsoil_profile(table, thickness=20, thickness_values=th).cal_missingFromSurgo()
        return {x: sp}
    except Exception as e:
        print("Exception Type:", type(e), "has occured")
        print(repr(e))