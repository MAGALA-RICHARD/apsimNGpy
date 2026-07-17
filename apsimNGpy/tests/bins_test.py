from apsimNGpy import Apsim

with Apsim(r"C:\Users\rmagala\AppData\Local\Programs\APSIM2026.2.7990.0\bin") as sim:
    with sim.ApsimModel('Maize') as model:
        model.run(verbose=True)