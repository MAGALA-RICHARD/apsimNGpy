from apsimNGpy.model.soilmodel import SoilModel
from contextlib import contextmanager
import os


class ApsimModel():
    def __init__(self, model, copy=True):
        self.model = SoilModel(model, copy)

    def start(self):
        self.model.run()
        self.results = self.model.results

    def stop(self):

        print(self.model.Model)
        self.model.Model.FileName = None
        self.model.Model.datastore = None
        self.model.clear()
#todo add flexibility to excute many other soilmodel methordor add other methods

@contextmanager
def apsim_model_context(model, copy=True):
    apsim_model = ApsimModel(model, copy)
    apsim_model.start()
    try:
        yield apsim_model
    finally:
        apsim_model.stop()


if __name__ == '__main__':
    model = r'C:\Users\rmagala\OneDrive\PEWI and Prairie Modeling\Nitrous_Oxide_Paper\edited_apsim\no_cover_w_replaced.apsimx'
    pat = r'C:\Users\rmagala\OneDrive\PEWI and Prairie Modeling\Nitrous_Oxide_Paper\edited_apsim'
    os.chdir(pat)
    ty = SoilModel(model)
    with apsim_model_context(model) as apsim:
        pass
