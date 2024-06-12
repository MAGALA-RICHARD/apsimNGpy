from SALib import ProblemSpec
import numpy as np

def parabola(x, a, b):
    """Return y = a + b*x**2."""
    return a + b*x**2

sp = ProblemSpec({
    'names': ['a', 'b'],
    'bounds': [[0, 1]]*2,
})

# Create "bins" of x
x = np.linspace(-1, 1, 100)

# Create wrapper (runs each a, b combination separately)
def wrapped_parabola(ab, x=x):
    y = np.zeros((ab.shape[0], x.shape[0]))
    for i, (a, b) in enumerate(ab):
        print(i)
        y[i,:] = parabola(x, a, b)

    return y

(
    sp.sample_sobol(1**6)
    .evaluate(wrapped_parabola)
    .analyze_sobol()
)

# Get first order sensitivities for all outputs
S1s = np.array([sp.analysis[_y]['S1'] for _y in sp['outputs']])

# Get model outputs
y = sp.results