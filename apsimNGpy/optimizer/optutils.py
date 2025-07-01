import numpy as np

from pymoo.indicators.hv import HV


def edit_runner(model_runner, decision_specs: dict, x_values, verbose=False):
    """
    Applies a new value to the APSIM model by editing the correct parameter in the model_runner.

    Parameters
    ----------
    model_runner : apsimNGpy.core.cal.OptimizationBase
        The APSIM runner object.
    decision_specs : dict
        A dictionary containing keys: 'path', 'v_type', 'bounds', and 'kwargs'.
        'kwargs' is expected to contain exactly one parameter to be optimized, marked as '?' or ''.
    x_values : float or int
        The value to apply to the unspecified parameter.
    verbose : bool
        If True, print what is being edited.
    """
    path = decision_specs['path']
    kwargs = decision_specs.get('kwargs', decision_specs).copy()
    kwargs.pop('path', None)
    kwargs.pop('v_type', None)
    kwargs.pop('bounds', None)
    kwargs.pop('q', None)
    kwargs.pop('values', None)
    kwargs.pop('start_value', None)

    # Replace the placeholder (e.g., '?' or '') with the optimization value
    fill_keys = [k for k, v in kwargs.items() if v in ('?', '',)]
    if len(fill_keys) > 1:
        raise ValueError("Exactly one parameter should be marked with '?' or '' for optimization.")

    param_key = fill_keys[0]
    kwargs[param_key] = x_values

    if verbose:
        print(f"Editing {path}: setting {param_key} = {x_values}")

    model_runner.edit_model_by_path(path=path, **kwargs)


def compute_hyper_volume(F, reference_point=None, normalize=False, normalization_bounds=None):
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

