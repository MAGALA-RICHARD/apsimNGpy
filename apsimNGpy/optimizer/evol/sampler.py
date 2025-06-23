import numpy as np
import numpy as np
from typing import Optional, Tuple

def float_random_sampling(
    n_var: int,
    n: int,
    bounds: Optional[Tuple[np.ndarray, np.ndarray]] = None,
    **kwargs
) -> np.ndarray:
    """
    Generate random float samples in [0, 1) or within provided bounds.

    Parameters:
        n_var (int): Number of variables (dimensions).
        n (int): Number of samples.
        bounds (tuple of ndarray, optional): Tuple (xl, xu) with lower and upper bounds.
        **kwargs: Additional keyword arguments (ignored).

    Returns:
        np.ndarray: An (n, n_var) array of sampled values.
    """
    X = np.random.rand(n, n_var)

    if bounds is not None:
        xl, xu = bounds
        xl, xu = np.asarray(xl), np.asarray(xu)
        if xl.shape != (n_var,) or xu.shape != (n_var,):
            raise ValueError(f"Bounds must be arrays of shape ({n_var},), got {xl.shape} and {xu.shape}")
        if not np.all(xu >= xl):
            raise ValueError("Upper bounds must be greater than or equal to lower bounds.")
        X = xl + (xu - xl) * X

    return X



def integer_random_sampling(n_var:int, n:int, bounds:tuple):
    """
    Generate random integer samples within problem bounds.

    Parameters:
            - n_var: int, number of variables
            - bounds:(xl, xu), the lower and upper bounds as arrays e.g., ((10, 10), (100, 50)) for n-var =2
            - n: int, number of samples to generate

    Returns:
        np.ndarray: A (n_samples, n_var) array of integer samples.
    """
    xl, xu = bounds
    return np.column_stack([
        np.random.randint(xl[k], xu[k] + 1, size=n)
        for k in range(n_var)
    ])


def bin_random_sampling(n_var, n):
        val = np.random.random((n, n_var))
        return (val < 0.5).astype(bool)

if __name__ == '__main__':
    float_random_sampling(4,20, (10, 50))
    bin_random_sampling(4,20)
    integer_random_sampling(2, 100, ((10, 10), (100, 50)))