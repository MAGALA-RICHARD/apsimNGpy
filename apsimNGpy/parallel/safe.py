from apsimNGpy.manager.soilmanager import DownloadsurgoSoiltables, OrganiseSoilProfile
from apsimNGpy.manager.weathermanager import get_met_from_day_met
from apsimNGpy.core.apsim import ApsimModel


def initialise(model, reports):
    model = ApsimModel(model)
    model.run(report_name=reports)
    return model.results


def download_soil_table(x):
    try:
        cod = x
        table = DownloadsurgoSoiltables(cod)
        th = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
        sp = OrganiseSoilProfile(table, thickness=20, thickness_values=th).cal_missingFromSurgo()
        return {x: sp}
    except Exception as e:
        print("Exception Type:", type(e), "has occured")
        print(repr(e))


def simulator_worker(row, dictio):
    kwargs = dictio
    report = kwargs.get('report_name')
    ID = row['ID']
    model = row['file_name']
    thi = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
    th = kwargs.get("thickness_values", thi)
    simulator_model = ApsimModel(
        model, copy=kwargs.get('copy'), read_from_string=True, lonlat=None, thickness_values=th)
    sim_names = simulator_model.extract_simulation_name
    location = row['location']
    stat, end = kwargs.get('start'), kwargs.get('end')
    if kwargs.get('replace_weather', False):
        wname = model.strip('.apsimx') + '_w.met'
        wf = get_met_from_day_met(location, start=stat, end=end, filename=wname)
        simulator_model.replace_met_file(wf, sim_names)

    if kwargs.get("replace_soil", False):
        table = DownloadsurgoSoiltables(location)
        sp = OrganiseSoilProfile(table, thickness=20, thickness_values=th)
        sp = sp.cal_missingFromSurgo()
        simulator_model.replace_downloaded_soils(sp, sim_names)

    if kwargs.get("mgt_practices"):
        simulator_model.update_mgt(kwargs.get('mgt_practices'), sim_names)
    try:
        simulator_model.run(report_name=report)
        return simulator_model.results
    except Exception as e:
        print(type(e))
        print('+_____________________________________\n')
        print(e)
