from logger import logger
from exceptions import ApsimRuntimeError
from apsimNGpy.core.apsim import ApsimModel
from pathlib import Path
import pandas as pd

ID = 'ID'


def create_simulations(base_file: str | Path, pps: pd.DataFrame, base_simulation: str = None, index: str = 'index'):
    from apsimNGpy.core.model_tools import clone_simulation

    copy_pps = pps.copy()
    copy_pps[ID] = pps[index]
    grps = copy_pps.groupby(index)
    for k, g in grps:
        sim_id = [f"S_{ID}_{i}_" for i in zip(g[ID], range(g.shape[0]))]
        lon_lats = [(XY.x, XY.y) for XY in g.sampled_points]
        with ApsimModel(base_file) as model:
            model.edit_model(model_type='Models.Manager', model_name='Sow using a variable rule',
                             StartDate='28-apr',
                             EndDate='28-may',
                             Population=8.65,
                             CultivarName='B_110')
            model.edit_model(model_type='Models.Manager', model_name='Fertilise at sowing',
                             Amount=280,
                             )
            if len(model.simulations) > 1:
                raise ValueError(f'Base simulation file should have only base simulation under its node')
            base_simulation = base_simulation or model.simulations[0].Name
            new_sims_names = sim_id[:]
            new_sims_names[-1] = base_simulation
            [clone_simulation(model, sim_name=base_simulation, rename=ren) for ren in sim_id[:-1]]
            th = [50, 150, 150, 200, 200, 200, 300, 350, 400]
            model.get_weather_from_web(lonlat=lon_lats[-2], start=1986, end=2016, simulations=None,
                                       filename=f'{Path(base_file).resolve().parent}_{lon_lats[-2]}.met',
                                       source='daymet')
            for sim_name, ll in zip(new_sims_names, lon_lats):

                try:
                    model.get_soil_from_web(simulations=sim_name, lonlat=ll, source='ssurgo',
                                            top_fom=2010,
                                            top_urea=0.07, top_finert=0.05,
                                            thickness_sequence=th, summer_date='1-Jun', winter_date='1-Nov')
                    model.run(verbose=False)

                    df = model.results
                    print(k, ' = ', df.Yield.mean(), df.Yield.median(), df.Yield.max())
                    mn = df.groupby('SimulationID')['Yield'].max()
                    print(mn)
                except (AttributeError, ApsimRuntimeError):
                    pass
                except ApsimRuntimeError:
                    pass


# mets = Path(r'D:\package\apsimNGpy\apsimNGpy\w').parent.parent.rglob('*.met')
# for i in mets:
#     i.unlink()

from apsimNGpy import get_apsim_bin_path, apsim_bin_context

get_apsim_bin_path()
