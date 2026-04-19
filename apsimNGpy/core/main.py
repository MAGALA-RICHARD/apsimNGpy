# this is a work in progress
import datetime

from apsimNGpy import timer
from apsimNGpy.core.apsim import ApsimModel, CLR
from apsimNGpy.core.config import configuration
from diskcache import Cache
from pathlib import Path
from apsimNGpy.core.ce import create_new_cultivar
from apsimNGpy.core_utils.fert_helpers import (fertilize_at_fixed_dates, fertilize_at_sowing
                                               )

cache = Cache(directory='../.cached')
CROPS = primary_simulations = {
    'AgPasture',
    'Barley',
    'Canola',
    'CanolaGrazing',
    'Chickpea',
    'Chicory',
    'Eucalyptus',
    'EucalyptusRotation',
    'FodderBeet',
    'Grapevine',
    'Maize',
    'Mungbean',
    'Oats',
    'OilPalm',
    'Peanut',
    'Pinus',
    'PlantainForage',
    'Potato',
    'RedClover',
    'Sorghum',
    'Soybean',
    'Sugarcane',
    'Wheat',
    'WhiteClover'
}

no_nit = {}


@cache.memoize()
def _get_fertilizer_scripts():
    def _search(sub_word, manager_list):
        """Return first matching manager containing sub_word."""
        for p in manager_list:
            if sub_word in p:
                return p
        return None

    fertilizers = {}
    sowers = {}
    harvesters = {}

    for crop in CROPS:
        with ApsimModel(crop) as model:
            managers = model.inspect_model('Models.Manager', fullpath=False)

            fertilizers[crop] = _search('Ferti', managers)
            sowers[crop] = _search('Sow', managers)
            harvesters[crop] = _search('Harvest', managers)

    return {
        "fertilizers": fertilizers,
        "sowers": sowers,
        "harvesters": harvesters,
    }


@timer
@cache.memoize()
def load_model(crop, bin_path=configuration.bin_path):
    data = Path(bin_path).parent.joinpath(f'.copied_apsimx_{CLR.apsim_compiled_version}')
    data.mkdir(parents=True, exist_ok=True)
    output_path = data / f"{crop}.apsimx"
    p = str(bin_path)
    mod = ApsimModel(crop, out_path=output_path)
    simulations = mod.Simulations
    plant = CLR.Models.PMF.Plant()
    plant.Name = crop
    plant.ResourceName = crop

    if 'Replacements' not in {i.Name for i in mod.Simulations.Children}:
        replacements = CLR.Models.Core.Folder()
        replacements.Name = 'Replacements'
        simulations.Children.Add(replacements)
        replacements.Children.Add(plant)
    else:
        rep = [i for i in mod.Simulations.Children if i.Name == 'Replacements'][0]
        replacements = rep
        if crop not in {i.Name for i in replacements.Children}:
            plant = CLR.Models.PMF.Plant()
            plant.Name = crop
            replacements.Children.Add(plant)
    return mod.path


def _insert_weather(mod, weather: dict, start: int, end: int):
    if not isinstance(weather, dict):
        raise TypeError(f"`weather` must be dict, got {type(weather)}")

    met_file = weather.get("met_file")
    lonlat = weather.get("lonlat")
    source = weather.get("source", "nasa")
    # ❌ Trying to prevent ambiguous config
    if met_file and lonlat:
        raise ValueError("Provide only one of 'met_file' or 'lonlat', not both")
    if met_file:
        return mod.get_weather_from_file(weather_file=met_file)

    elif lonlat:
        if not isinstance(lonlat, (list, tuple)) or len(lonlat) != 2:
            raise ValueError(f"`lonlat` must be (lat, lon), got {lonlat}")

        return mod.get_weather_from_web(
            lonlat=lonlat,
            start=start,
            end=end,
            source=source
        )


with ApsimModel('Sugarcane') as gv:
    p = gv.inspect_model_parameters(model_type='Models.Manager', model_name='Fertilise on fixed date')
    print(p)
    fertilize_at_fixed_dates(gv,  missing_ok=False, Amount=10,)

    print(gv.results)


@timer
@cache.memoize()
def simulate(
        crop,  # e.g. "wheat", "maize"
        plant_date=None,  # sowing date

        # Location & environment
        weather: dict | None = None,
        met_file=None,  # weather file path (rain, temp, radiation)

        # Soil configuration
        soil_type=None,
        soil_water=None,  # initial soil water (e.g. "full", %, or profile)
        soil_nitrogen=None,  # initial nitrogen levels

        # Crop management
        sowing_depth=30,  # mm
        row_spacing=250,  # mm
        plant_density=None,  # plants/m²
        # Fertilization & irrigation
        fertilize: dict | None = None,
        nitrogen_date=None,
        irrigation_amount=0,
        irrigation_schedule=None,
        # Simulation control
        start_date='1990-01-01',
        end_date='2000-12-30',
        cultivar: dict | None = 2,
        som: dict | None = None,
        tillage: dict | None = None,
        report: dict | None = None,
        table: tuple | str | set | list = None):
    loaded = load_model(crop)
    print(loaded)
    mod = ApsimModel(loaded)
    # create simulation node
    simulation = mod[0]
    import datetime

    START = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    END = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    # weather data
    if weather is not None:
        _insert_weather(mod, weather, START.year, END.year)
    mod.add_new_model(parent_type='Simulation', parent_identifier=simulation.FullPath, replace=True,
                      source=dict(type='Models.Clock', Start=start_date, End=end_date, Name='Clock'))
    if cultivar is not None:
        pass
    if tillage is not None:
        pass
    if report is not None:
        pass
    if som is not None:
        pass
    with mod.run():
        report_df = mod.get_simulated_output(table) if table else mod.results
        return report_df


def set_up_crop_rotation(sequence='Maize'):
    with ApsimModel(r'D:\Elimin_rye_cover_crop_2026\APSIMX\cc_cover_edited_rue.apsimx') as model:
        model.open_in_gui(watch=True)


from nodes import simple_rotation

res = simulate('Soybean', 2, table='Report', irrigation_amount={'0': 1})
mn = res.Yield.mean()
res2 = simulate('Barley', 2, table='Report', weather={"lonlat": (-93.0145, 41.097)})
mn = res2.Yield.mean()
crops = []
# for i in Path(configuration.bin_path).parent.joinpath('Examples').rglob("*"):
#     if i.stem in CROPS:
#         with ApsimModel(i) as model:
#             man = model.inspect_model('Models.Manager')
#
#             print(f'{i.name}: ')
#             print('------------------')
#             print(*man, sep='\n')
#             crops.append(i.stem)
