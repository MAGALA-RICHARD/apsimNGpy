from apsimNGpy.core.base_data import load_default_simulations, load_default_sensitivity_model
from apsimNGpy.core.apsim import ApsimModel

# initialize the model
if __name__ == '__main__':

    model = ApsimModel(model='whiteclover')

    sobol = load_default_sensitivity_model(method='sobol')
    defa = load_default_simulations('Maize')
    # run the model
    model.run(report_name="Report")

