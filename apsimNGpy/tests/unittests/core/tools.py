from apsimNGpy.core.apsim import Models, ApsimModel


class TestModels():
    def __init__(self):
        pass

    def __enter__(self):
        pass

    def mick_multiple_simulations(self):
        model = ApsimModel('Maize')
        model2 = ApsimModel('Soybean')
