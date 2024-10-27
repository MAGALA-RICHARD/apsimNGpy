from pathlib import Path

from apsimNGpy.experiment.main import Experiment

if __name__ == '__main__':
    path = Path.home().joinpath('scratchT')
    path.mkdir(exist_ok=True)
    from apsimNGpy.core.base_data import load_default_simulations

    # import the model from APSIM.
    # if we simulations_object it,
    # returns a simulation object of apsimNGpy, but we want the path only.
    # model_path = load_default_simulations(crop='maize', simulations_object=False, path=path.parent)
    model_path = load_default_simulations('maize').path

    FactorialExperiment = Experiment(database_name='test.db',
                                     datastorage='test.db',
                                     tag='th', base_file=model_path,
                                     wd=path,
                                     use_thread=False,
                                     skip_completed=False,
                                     verbose=False,
                                     test=False,
                                     n_core=6,
                                     reports={'Report'})

    FactorialExperiment.add_factor(parameter='Carbon', param_values=[1.4, 0.2, 0.4, 0.9, 2.4, 0.8], factor_type='soils',
                                   soil_node='Organic')

    FactorialExperiment.add_factor(parameter='FBiom', param_values=[0.045, 1.4, 2.4, 0.8], factor_type='soils',
                                   soil_node='Organic')

    # # cultivar is edited via the replacement module, any simulation file supplied without Replacements appended
    # # to Simulations node, this method will fail quickly
    # FactorialExperiment.add_factor(parameter='grain_filling', param_values=[300, 450, 650, 700, 500], cultivar_name='B_110',
    #                                commands='[Phenology].GrainFilling.Target.FixedValue', factor_type='cultivar')

    FactorialExperiment.clear_data_base()
    # os.remove(FactorialExperiment.datastorage)
    FactorialExperiment.start_experiment()
    sim_data = FactorialExperiment.get_simulated_data()[0]
    mn = sim_data.groupby(['FBiom', 'Carbon'])['Yield'].mean()
    "if we dont see any variation for each of the factors then it is not working configure again"
    # print(mn)
    print(len(FactorialExperiment.factors))
