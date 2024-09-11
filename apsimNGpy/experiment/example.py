from pathlib import Path
from experiment_utils import _run_experiment, experiment_runner
from set_ups import define_factor, define_cultivar
from set_ups import set_experiment
from apsimNGpy.parallel.process import custom_parallel

if __name__ == '__main__':
    path = Path(r'G:/').joinpath('scratchT')
    from apsimNGpy.core.base_data import load_default_simulations

    # import the model from APSIM.
    # if we simulations_object it,
    # returns a simulation object of apsimNGpy, but we want the path only.
    # model_path = load_default_simulations(crop='maize', simulations_object=False, path=path.parent)
    model_path = path.joinpath('m.apsimx')


    # define the factors


    carbon = define_factor(parameter="Carbon", param_values=[1.4, 2.4, 0.8], factor_type='soils', soil_node='Organic')
    Amount = define_factor(parameter="Amount", param_values=[200, 324, 100], factor_type='Management',
                           manager_name='MaizeNitrogenManager')
    Crops = define_factor(parameter="Crops", param_values=[200, 324, 100], factor_type='Management',
                          manager_name='Simple Rotation')
    grainFilling = define_cultivar(parameter="grain_filling", param_values=[600, 700, 500],
                                   cultivar_name='B_110',
                                   commands='[Phenology].GrainFilling.Target.FixedValue')

    ap = set_experiment(factors=[carbon, Amount, Crops, grainFilling],
                        database_name='sbb.db',
                        datastorage='sbx.db',
                        tag='th', base_file=model_path,
                        wd=path,
                        use_thread=True,
                        by_pass_completed=False,
                        verbose=True,
                        test=True,
                        reports={'Report', 'MaizeR'})

