import numpy as np
import pytest
from apsimNGpy.optimizer.evol.sampler import float_random_sampling, integer_random_sampling, boolean_random_sampling


def test_float_random_sampling_default_bounds():
    n_var, n = 3, 5
    samples = float_random_sampling(n_var, n)
    assert samples.shape == (n, n_var)
    assert np.all(samples >= 0.0) and np.all(samples < 1.0)


def test_float_random_sampling_custom_bounds():
    n_var, n = 2, 10
    xl = np.array([10, 20])
    xu = np.array([20, 30])
    samples = float_random_sampling(n_var, n, bounds=(xl, xu))
    assert samples.shape == (n, n_var)
    assert np.all(samples >= xl) and np.all(samples <= xu)


def test_float_random_sampling_invalid_bounds_shape():
    with pytest.raises(ValueError):
        float_random_sampling(3, 5, bounds=(np.array([1, 2]), np.array([3, 4])))


def test_float_random_sampling_invalid_bounds_order():
    with pytest.raises(ValueError):
        float_random_sampling(2, 5, bounds=(np.array([5, 10]), np.array([4, 9])))


def test_integer_random_sampling_shape_and_range():
    n_var, n = 2, 50
    bounds = ((10, 20), (100, 200))
    samples = integer_random_sampling(n_var, n, bounds)
    assert samples.shape == (n, n_var)
    for i in range(n_var):
        assert np.all(samples[:, i] >= bounds[0][i])
        assert np.all(samples[:, i] <= bounds[1][i])


def test_boolean_random_sampling_shape_and_values():
    n_var, n = 4, 10
    samples = boolean_random_sampling(n_var, n)
    assert samples.shape == (n, n_var)
    assert samples.dtype == bool
    assert np.all(np.logical_or(samples == True, samples == False))


if __name__ == "__main__":
        ...
        import sys

        pytest.main([__file__])
