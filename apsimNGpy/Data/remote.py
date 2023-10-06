from os.path import join, realpath, dirname, exists
base = realpath(dirname(__file__))
fil = join(base, 'basefiles')
apsimx_prototype = join(fil, 'corn_base.apsimx')
met_example = join(fil, 'NewMetrrr.met')
SWIM3 = join(fil, 'SWIM2.apsimx')
test =join(fil, 'testx.apsimx')
EXPERIMENT = join(fil, 'EXPERIMENT.apsimx')
EXPERIMENT_NT = join(fil, 'EXPERIMENT_NT.apsimx')
lonlat = [-93.620369, 42.034534]
class apsimx_examples:
    def __init__(self):
        self.corn = apsimx_prototype
        self.EXPERIMENT = EXPERIMENT
        self.EXPERIMENT_NT = EXPERIMENT_NT
        self.SWIM  = SWIM3
        self.test = test
        self.weather_file = met_example
        self.lonlat = lonlat
apsimx_examples = apsimx_examples()