from apsimNGpy import ApsimModel

with ApsimModel('Maize') as model:
    model.remove_model(model_type='Models.Manager', model_name='Sow using a variable rule')
    model.remove_model(model_type='Models.Manager', model_name='Sow using a variable rule')
    managers= model.inspect_model('Models.Manager', fullpath=False)
    print(managers)
    # model.remove_node('.Simulations.Simulation.Field.Sow using a variable rule')
    # managers = model.inspect_model('Models.Manager')
    # print(managers)