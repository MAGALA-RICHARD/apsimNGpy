from apsimNGpy.core.apsim import ApsimModel, Models

model = ApsimModel('Maize')
model.edit_model(
    model_type='Cultivar',
    simulations='Simulation',
    commands='[Phenology].Juvenile.Target.FixedValue',
    values=206,
    new_cultivar_name='B_110-e',
    model_name='B_110',
    cultivar_manager='Sow using a variable rule')

model.inspect_model_parameters('Cultivar', simulations='Simulation', model_name='B_110-e')
res1 = model.run().results.Yield.mean()

model.edit_model(
    model_type='Cultivar',
    simulations='Simulation',
    commands='[Phenology].Juvenile.Target.FixedValue',
    values=100,
    new_cultivar_name='B_110-e',
    model_name='B_110',
    cultivar_manager='Sow using a variable rule')

res2 = model.run().results.Yield.mean()
assert res1 != res2
