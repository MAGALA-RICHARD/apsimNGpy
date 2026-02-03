from math import pow
from typing import Iterable, List
from typing import Tuple
import numpy as np
from apsimNGpy.core_utils.utils import timer


def auto_gen_thickness_layers(max_depth, n_layers=10, thin_layers=3, thin_thickness=100,
                              growth_type="linear", thick_growth_rate=1.5
                              ):
    """
    Generate layer thicknesses from surface to depth, starting with thin layers and increasing thickness.

    Args:
        ``max_depth`` (float): Total depth in mm.

        ``n_layers`` (int): Total number of layers.

        ``thin_layers`` (int): Number of initial thin layers.

        ``thin_thickness`` (float): Thickness of each thin layer.

        ``growth_type`` (str): 'linear' or 'exponential'.

        ``thick_growth_rate`` (float): Growth factor for thick layers (e.g., +50% each layer if exponential).

    ``Returns:``
        List[float]: List of layer thicknesses summing to max_depth.
    """

    assert 0 < thin_layers < n_layers, "thin_layers must be less than total layers"
    assert thin_thickness > 0, "thin_thickness must be positive"
    assert growth_type in ['linear', 'exponential'], "Invalid growth_type"

    thick_layers = n_layers - thin_layers
    thin_total = thin_layers * thin_thickness
    remaining_depth = max_depth - thin_total

    if remaining_depth <= 0:
        raise ValueError("Thin layers consume more than total depth.")

    # --- Step 1: Thin layers ---
    thin_parts = [thin_thickness] * thin_layers

    # --- Step 2: Thick layers ---
    if growth_type == "linear":
        # We'll solve an arithmetic series: a + (a + d) + ... = remaining_depth
        # Assume a = base_thick, d = constant increment
        # So: total = thick_layers * a + d * (0 + 1 + ... + thick_layers-1)
        increments = list(range(thick_layers))
        sum_increments = sum(increments)
        base_thick = (remaining_depth - sum_increments * thick_growth_rate) / thick_layers
        thick_parts = [base_thick + i * thick_growth_rate for i in increments]

    elif growth_type == "exponential":
        # Geometric series: a*r^0 + a*r^1 + ... = remaining_depth
        r = thick_growth_rate
        denom = sum([pow(r, i) for i in range(thick_layers)])
        a = remaining_depth / denom
        thick_parts = [a * pow(r, i) for i in range(thick_layers)]

    # Final result
    layers = thin_parts + thick_parts

    # Precision check
    total = sum(layers)
    if abs(total - max_depth) > 1e-6:
        # Final adjustment to fix floating point error
        layers[-1] += max_depth - total
    layers.sort()
    layers = [int(i) for i in layers]

    return layers


def layer_boundaries(thicknesses: Iterable[float]) -> Tuple[List[float], List[float]]:
    """Return (tops, bottoms) for consecutive layers given their thicknesses.
    Tops start at 0; bottoms are cumulative sums."""
    tops, bottoms = [], []
    cum = 0
    for th in thicknesses:
        if th <= 0 or isinstance(th, str):
            raise ValueError("All thicknesses must be positive and not strings")
        tops.append(cum)
        cum += th
        bottoms.append(cum)
    return tops, bottoms


@timer
def set_depth(depth_thickness):
    """
        parameters
        depth_thickness (array):  an array specifying the thickness for each layer
        layers (int); number of layers just to remind you that you have to consider them
        ------
        return
      bottom depth and top depth in a tuple
        """
    import numpy as np
    # thickness  = np.tile(thickness, 10
    thickness_array = np.array(depth_thickness)
    bottomdepth = np.cumsum(thickness_array)  # bottom depth should not have zero
    top_depth = bottomdepth - thickness_array
    return bottomdepth, top_depth


def gen_layer_bounds_from_single_thickness(
        thickness: float,
        highest_bottom_depth: float,
        *,
        max_layers: int = 30,
        require_integer_layers: bool = True,
        atol: float = 1e-9) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate per-layer (top, bottom) boundaries for uniform soil layers.

    Parameters
    ----------
    thickness : float
        Layer thickness (e.g., mm). Must be > 0.
    highest_bottom_depth : float
        Target depth for the bottom of the last layer (same units as `thickness`). Must be > 0.
    max_layers : int, optional
        Upper bound on number of layers to guard against mistakes, by default 30.
    require_integer_layers : bool, optional
        If True, require that `highest_bottom_depth` is an integer multiple of `thickness`.
    atol : float, optional
        Absolute tolerance used in the integer-multiple check (handles float rounding).

    Returns
    -------
    tops : np.ndarray
        Array of layer top depths: [0, t, 2t, ..., (n-1)t]
    bottoms : np.ndarray
        Array of layer bottom depths: [t, 2t, 3t, ..., n*t] == highest_bottom_depth (within atol)
    """
    # basic validation
    if not (thickness > 0 and highest_bottom_depth > 0):
        raise ValueError("Non-positive values are not allowed for thickness or depth.")

    n_float = highest_bottom_depth / thickness

    if require_integer_layers:
        n_rounded = round(n_float)
        if not np.isclose(n_float, n_rounded, atol=atol, rtol=0.0):
            raise ValueError(
                "highest_bottom_depth must be an integer multiple of thickness "
                "(check that they use the same units). "
                f"Got {n_float:.6f} layers."
            )
        n = int(n_rounded)
    else:
        n = int(np.floor(n_float))

    if n <= 0:
        raise ValueError("Computed zero layers; increase highest_bottom_depth or reduce thickness.")

    if n > max_layers:
        raise ValueError(
            f"Too many soil layers ({n} > {max_layers}). "
            "Consider changing thickness or depth; also ensure they are in the same units."
        )

    # boundaries
    tops = thickness * np.arange(0, n, dtype=float)
    bottoms = thickness * np.arange(1, n + 1, dtype=float)

    return tops, bottoms


if __name__ == "__main__":
    tl = auto_gen_thickness_layers(2400, n_layers=10, thin_thickness=100, growth_type="linear", thick_growth_rate=1.5)
    print(tl)
    lb = layer_boundaries(tl)
    lb2 = set_depth(tl)
    gl = gen_layer_bounds_from_single_thickness(200, 2400)
    print(gl[0])
    print(gl[1])
