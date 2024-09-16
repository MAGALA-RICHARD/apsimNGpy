# Why use this apsimNGpy factorial module
Factorial analysis is essential when performing sensitivity analysis, generating datasets for machine learning model training, or conducting uncertainty analysis. In these scenarios, a large volume of data is required, which can be handled by graphical user interfaces (GUIs). Still, they often face limitations regarding memory and performance as the number of factorial combinations increases. Moreover, GUIs may lack the flexibility for complex customizations. This is where the APSIMNGpy factorial module becomes invaluable. It allows for efficient handling of large factorial datasets, offering greater control, scalability, and customization without the constraints imposed by traditional GUI-based approaches.

# Examples

* Object-oriented approach

```python
    from pathlib import Path
    path = Path.home()
    from apsimNGpy.experiment.main import Experiment
    from apsimNGpy.core.base_data import load_default_simulations
    model_path = load_default_simulations(crop = 'Maize')
    # manadatory arguments include datastorage, tag, wd and reports the rest are very optional and are clearly passed as key word argument
    FactorialExperiment = Experiment(database_name='test.db',
                                         datastorage='test.db',
                                     tag='th', base_file=model_path,
                                     wd=path,
                                     use_thread=True,
                                     by_pass_completed=True,
                                     verbose=False,
                                     test=False,
                                     n_core=6,
                                     reports={'Report'})
    # Factors are replaced via the replacement module, we provide alot of abstractions
    # the factor can be either soils, management, cultvar, or surface organic matter factor, management factors are associated with the Manager module or scripts
    FactorialExperiment.add_factor(parameter='Carbon', param_values=[1.4, 2.4, 0.8], factor_type='soils', soil_node='Organic')
    FactorialExperiment.add_factor(parameter='Crops', param_values=['Maize', "Wheat"], factor_type='management', manager_name='Simple '
                                                                                                              'Rotation')
    # cultivar is edited via the replacement module, any simulation file supplied without Replacements for,
    # this method will fail quickly
    FactorialExperiment.add_factor(parameter='grain_filling', param_values=[300, 450, 650, 700, 500], cultivar_name='B_110',
                                   commands='[Phenology].GrainFilling.Target.FixedValue', factor_type='cultivar')
    # you may want to clear the data base before simulations
    FactorialExperiment.clear_data_base()
    # run the experiment
    FactorialExperiment.start_experiment()
    # get the simulated data
    sim_data = FactorialExperiment.get_simulated_data()[0]
    sim_data.groupby('grain_filling').agg({"Yield": 'mean'})
    print(len(FactorialExperiment.factors))

```

* Procedural oriented approach