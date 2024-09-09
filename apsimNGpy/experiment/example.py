from pathlib import Path
from set_ups import define_factor
from apsimNGpy.experiment.permutations import create_permutations
from apsimNGpy.experiment.set_ups import Factors

from experiment_utils import _run_experiment
from set_ups import set_experiment, DeepChainMap

if __name__ == '__main__':
    path = Path(r'G:/').joinpath('scratchT')

    reports = ['Annual', 'Annual']
    carbon = define_factor(parameter="Carbon", param_values=[1.4, 2.4, 0.8], factor_type='soils', soil_node='Organic')
    Amount = define_factor(parameter="Amount", param_values=[200, 324, 100], factor_type='Management',
                           manager_name='MaizeNitrogenManager')
    Crops = define_factor(parameter="Crops", param_values=[200, 324, 100], factor_type='Management',
                          manager_name='Simple Rotation')

    ap = set_experiment(factors=[carbon, Amount, Crops],
                        database_name='sbb.db',
                        datastorage='sbx.db',
                        tag='th', base_file='ed.apsimx',
                        wd=path,
                        use_thread=True,
                        children=['manager'],
                        by_pass_completed=False,
                        reports={'Maize': 'Annual', 'Wheat, Maize': 'Annual'})

    df = _run_experiment(**next(ap))

    xp = create_permutations(facs, ['a', 'b'])
    xm = DeepChainMap(xp[0])
    from apsimNGpy.utililies.database_utils import read_db_table
