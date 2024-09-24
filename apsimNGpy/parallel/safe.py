from apsimNGpy.manager.soilmanager import get_surgo_soil_tables, APSimSoilProfile
from apsimNGpy.manager.weathermanager import daymet_bylocation_nocsv
from apsimNGpy.core.apsim import ApsimModel

def initialise(model, reports):
    model = ApsimModel(model)
    model.simulate(report_name=reports)
    return model.results

def download_soil_table(x):
    try:
        cod = x
        table = get_surgo_soil_tables(cod)
        th = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
        sp = APSimSoilProfile(table, thickness=20, thickness_values=th).cal_missingFromSurgo()
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
        wf = daymet_bylocation_nocsv(location, start=stat, end=end, filename=wname)
        simulator_model.replace_met_file(wf, sim_names)

    if kwargs.get("replace_soil", False):
        table = get_surgo_soil_tables(location)
        sp = APSimSoilProfile(table, thickness=20, thickness_values=th)
        sp = sp.cal_missingFromSurgo()
        simulator_model.replace_downloaded_soils(sp, sim_names)

    if kwargs.get("mgt_practices"):
        simulator_model.update_mgt(kwargs.get('mgt_practices'), sim_names)
    try:
        simulator_model.simulate(report_name=report)
        return simulator_model.results
    except Exception as e:
        print(type(e))
        print('+_____________________________________\n')
        print(e)


