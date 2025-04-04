from apsimNGpy.core.base_data import load_default_simulations, load_default_sensitivity_model
from apsimNGpy.core.apsim import ApsimModel

# initialize the model
if __name__ == '__main__':
    model = r"C:\Users\rmagala\AppData\Local\Programs\APSIM2025.2.7670.0\Examples\WhiteClover.apsimx"
    model = ApsimModel(model)

    sobol = load_default_sensitivity_model(method='sobol')
    # run the model
    model.run(report_name="Report")
