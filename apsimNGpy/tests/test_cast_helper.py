from apsimNGpy.core_utils.cs_utils import CastHelper as CastHelpers
from apsimNGpy.core.pythonet_config import Models
from apsimNGpy.core.model_loader import read_from_string

model = read_from_string("Maize")
if hasattr(model, 'Model'):  # incase it is an APSIM.Core.Node object
    model = model.Model
assert isinstance(CastHelpers.CastAs[Models.Core.Simulations](model), Models.Core.Simulations), "casting failed"

from apsimNGpy.core.config import get_apsim_bin_path, set_apsim_bin_path

tested_on = "C:\\Users\\rmagala\\AppData\\Local\\Programs\\APSIM2025.7.7807.0\\bin"

set_apsim_bin_path(r"C:\Program Files\APSIM2025.2.7655.0\bin")