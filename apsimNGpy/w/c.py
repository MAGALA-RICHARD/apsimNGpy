from apsimNGpy.core.apsim import ApsimModel

model = ApsimModel('Maize')
out_cultivar = 'B_110-e'
com_path = '[Phenology].Juvenile.Target.FixedValue'
model.edit_model(model_type='Cultivar', model_name='B_110', new_cultivar_name=out_cultivar,
                 commands=com_path, values=16, verbose=True,
                 cultivar_manager='Sow using a variable rule')
pc = model.inspect_model_parameters(model_type='Cultivar', model_name=out_cultivar)
print(pc[com_path])

model.edit_model(model_type='Cultivar', model_name='B_110-e', new_cultivar_name=out_cultivar,
                 commands=com_path, values=406, verbose=True,
                 cultivar_manager='Sow using a variable rule')
pc = model.inspect_model_parameters(model_type='Cultivar', model_name=out_cultivar)
print(pc[com_path])
