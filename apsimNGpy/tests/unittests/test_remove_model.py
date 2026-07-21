import sys

from apsimNGpy import ApsimModel

with ApsimModel('Maize') as model:
    model.remove_model(model_type='Models.Manager', model_name='Sow using a variable rule')

    managers= model.inspect_model('Models.Manager', fullpath=False)
    print(managers)
    # model.remove_node('.Simulations.Simulation.Field.Sow using a variable rule')
    # managers = model.inspect_model('Models.Manager')
    # print(managers)
    model.remove_model(model_type='Models.Manager', model_name='Sow using a variable rule', missing_ok=True, verbose=True)
print("testing remove_model by path", file=sys.stderr)
with ApsimModel('Maize') as model:
    model.remove_model_by_path('.Simulations.Simulation.Field.Sow using a variable rule')

    managers= model.inspect_model('Models.Manager', fullpath=False)
    print(managers)
    # model.remove_node('.Simulations.Simulation.Field.Sow using a variable rule')
    # managers = model.inspect_model('Models.Manager')
    # print(managers)
    model.remove_model_by_path('.Simulations.Simulation.Field.Sow using a variable rule', verbose=True)
    managers = model.inspect_model('Models.Manager', fullpath=False)
    print(managers)