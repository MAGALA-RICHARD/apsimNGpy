from apsimNGpy.core.pythonet_config import load_pythonnet
from Models.Soils import Soil, Physical, SoilCrop, Organic, Solute, Chemical


def soil_components(component):
    _comp = component.lower()
    comps = {'organic': Organic,
             'physical': Physical,
             'soilcrop': SoilCrop,
             'solute': Solute,
             'chemical': Chemical,
             }
    return comps[_comp]


# physical child parameters
physical_parameters = {'BD', "DUL", "Sand", 'Clay', 'Silt', "SAT", 'AirDry', 'LL15', 'SW', 'KS', 'Rocks', "Depth"}
physicals = {key: Physical for key in physical_parameters}
# organic child parameters
organic_parameters = {'Carbon', "FBiom", "FInert", 'FOM', "Depth", 'SoilCNRatio'}
organics = {key: Organic for key in organic_parameters}
