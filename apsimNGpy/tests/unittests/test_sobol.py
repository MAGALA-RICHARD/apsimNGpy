from apsimNGpy.core.apsim import ApsimModel
from pathlib import Path

file_base_name = f'S_sobol.apsimx'
fp = Path(r"D:\Elimin_rye_cover_crop_2026\APSIMX").joinpath(file_base_name)
with ApsimModel(fp) as model:
    sob = model.inspect_model('Models.Sobol')
    man = model.inspect_model('Models.Manager')
    mp = model.edit_model('Models.Manager', model_name= 'Simple Rotation', Crops='Maize, Soybean, Soybean')
    sp = model.inspect_model_parameters('Models.Manager', model_name= 'Simple Rotation')