import numpy as np
from pymoo.performance_indicator.hv import HV


def evaluate_hypervolume(F, reference_point=None, normalize=False, normalization_bounds=None):
    """
    Compute the hypervolume of a Pareto front.

    Parameters
    ----------
    F : np.ndarray
        A 2D array of shape (n_points, n_objectives), typically `result.F` from pymoo.

    reference_point : list or array, optional
        Reference point for hypervolume. If None:
        - Raw: uses max values in F + 10%
        - Normalized: uses [1.0, 1.0, ..., 1.0]

    normalize : bool, default=False
        Whether to normalize the objectives to [0, 1].

    normalization_bounds : tuple of arrays, optional
        (f_min, f_max) to normalize F. If None, uses min/max from F.

    Returns
    -------
    float
        Hyper volume value.
    """
    F = np.array(F)

    if normalize:
        if normalization_bounds:
            f_min, f_max = normalization_bounds
        else:
            f_min, f_max = F.min(axis=0), F.max(axis=0)

        F = (F - f_min) / (f_max - f_min + 1e-12)

        if reference_point is None:
            reference_point = np.ones(F.shape[1])
    else:
        if reference_point is None:
            # Conservative fallback: 10% worse than the worst observed
            ref_buffer = 0.1 * np.abs(F.max(axis=0))
            reference_point = F.max(axis=0) + ref_buffer

    hv = HV(ref_point=np.array(reference_point))
    return hv.do(F)
