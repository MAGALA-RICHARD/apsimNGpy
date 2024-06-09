import numpy as np
x = np.linspace(0, 10, 550)
def model(*params):
    a_est, b_est = params

    # Run simulation
    sim = a_est * x + b_est
    return sim