from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.base_data import LoadExampleFiles
from apsimNGpy.utililies.utils import Path
hom_dir = Path.home()
maize  = LoadExampleFiles(hom_dir).get_maize
class Custom(ApsimModel):
    def __init__(self, model):
        super().__init__(model)
    def predict(self, lonlat):
        self.replace_met_from_web(lonlat=lonlat, start_year=1990, end_year=2021)
        return self.run("MaizeR")

custom = Custom(maize)
lonlat = [-93.620369, 42.034534]
cm =custom.predict(lonlat)