from SALib.sample import sobol as sobol_sample
from pandas import DataFrame
from SALib.analyze import sobol
from SALib.test_functions import Ishigami
import numpy as np
from typing import Iterable, Dict, Any

AUTO = object()
import numpy as np
from SALib import ProblemSpec

sp = ProblemSpec({
    'names': ['a', 'b', 'x'],
    'bounds': [
        [-1, 0],
        [-1, 0],
        (-1, 1),
    ],
    'dists': {'unif'}
})

param_names = ['x', 'y', 'z']

from typing import Dict, Iterable, Tuple, Any, Mapping
from types import MappingProxyType


# Sentinel for auto-naming
class _AUTO:
    pass


AUTO = _AUTO()


def define_problem(
        params: Mapping[str, Tuple[float, float]],
        names: Iterable[str] | _AUTO = AUTO, ) -> MappingProxyType | dict:
    """
    Define a SALib-compatible optimization or sensitivity problem.

    This function is pure, deterministic, and safe to use across
    multiprocessing and multithreaded execution.

    Parameters
    ----------
    params : mapping
        Mapping of parameter paths to (lower, upper) bounds.
        Example: {"Soil.DUL": (0.1, 0.4), "Soil.LL15": (0.05, 0.2)}

    names : iterable of str or AUTO, optional
        Explicit parameter names. If AUTO, names are inferred from
        the final component of each parameter path.

    Returns
    -------
    dict
        A SALib-style problem definition with keys:
        - num_vars
        - names
        - bounds
    """

    # --- Validation ---
    if not isinstance(params, Mapping):
        raise TypeError("params must be a mapping of parameter paths to bounds")

    if not params:
        raise ValueError("params must not be empty")

    # Enforce deterministic ordering (critical for multiprocessing)
    items = tuple(params.items())

    # Validate bounds
    for key, bound in items:
        if (
                not isinstance(bound, tuple)
                or len(bound) != 2
                or not all(isinstance(v, (int, float)) for v in bound)
        ):
            raise ValueError(
                f"Invalid bounds for '{key}'. Expected (lower, upper) tuple."
            )

    # --- Name handling ---
    if names is AUTO:
        names = tuple(key.split(".")[-1] for key, _ in items)
    else:
        if not isinstance(names, Iterable):
            raise TypeError("names must be an iterable of strings")

        names = tuple(names)
        print(names)

        if len(names) != len(items):
            raise ValueError(
                "Length of names must match number of parameters"
            )

        if not all(isinstance(n, str) for n in names):
            raise TypeError("All names must be strings")

    if len(set(names)) != len(names):
        raise ValueError("Parameter names must be unique")
    # --- Build problem (immutable-friendly) ---
    problem = {
        "num_vars": len(items),
        "names": names,
        "bounds": tuple(bound for _, bound in items),
    }

    # Optional: prevent accidental mutation downstream
    return problem


def sobol_fev(problem, base_sample, skip_values=None, calc_second_order=False):
    """
    Generate Sobol samples for a given problem.

    Parameters
    ----------
    problem : object
        Problem definition passed to the Sobol sampler.
    base_sample : int
        Number of base samples. Must be a power of 2.
    skip_values : optional
        Values to skip in Sobol sequence generation.
    calc_second_order:  bool, optional. default is False.
        If `calc_second_order` is False, the resulting matrix has ``N * (D + 2)``
        rows, where ``D`` is the number of parameters.

    Returns
    -------
    array-like
        Sobol samples.
    """
    if base_sample <= 0 or (base_sample & (base_sample - 1)) != 0:
        raise ValueError("Sobol base_sample must be a positive power of 2")

    return sobol_sample.sample(
        problem,
        N=base_sample,
        calc_second_order=calc_second_order,
        skip_values=skip_values
    )


def create_factor_specs(problem, params, X, immediate=False):
    """
    Create APSIM factor specifications from a design matrix.

    Parameters
    ----------
    problem : dict
        Problem definition containing a 'names' field.
    params : mapping
        Mapping of parameter paths to bounds.
    X : array-like
        Design matrix of shape (n_samples, n_params).
    immediate : bool, optional
        If True, return a list of factor dictionaries.
        If False, yield factors one at a time.

    Yields
    ------
    dict
        Factor specification dictionary.
    """

    names = problem.get("names")
    if names is None:
        raise ValueError("problem must define 'names'")

    param_paths = tuple(params.keys())

    X = np.asarray(X)
    if X.ndim != 2:
        raise ValueError("X must be a 2D array")

    if X.shape[1] != len(param_paths):
        raise ValueError(
            f"X has {X.shape[1]} columns but {len(param_paths)} parameters were provided"
        )

    if len(names) != len(param_paths):
        raise ValueError("Length of problem['names'] must match params")

    results = [] if immediate else None

    for col, (name, path) in enumerate(zip(names, param_paths)):
        v = [int(i) for i in X[:, col]]
        v = X[:, col]
        values = ",".join(map(str, v))

        factor = {
            "specification": f"{path}={values}",
            "factor_name": name,
        }

        if immediate:
            results.append(factor)
        else:
            yield factor
    if immediate:
        return results


if __name__ == "__main__":
    ...
    problem = {
        "num_vars": len(param_names),
        "names": param_names,
        "bounds": [(0, 1), (20, 600), (12, 500)],
        'params_paths': []
    }

    X = sobol_sample.sample(problem, N=16, calc_second_order=False)
    print(X.shape)
    Y = Ishigami.evaluate(X)
    Si = sobol.analyze(problem, Y, print_to_console=True)

    '[Sow using a variable rule].Script.Population'
    rowSpacing = '[Sow using a variable rule].Script.RowSpacing'

    par = {'[Sow using a variable rule].Script.Population': (2, 10),

           rowSpacing: (100, 750)}
    p = define_problem(params=par,
                       names=['population', 'rowspacing', ])
    fa = create_factor_specs(p, par, X)


    def path():
        p = '.Simulations.Replacements.Maize.OPVPH_P2?[Leaf].Photosynthesis.RUE.FixedValue'
        return p.split('?')


    from dataclasses import dataclass
    from typing import Iterable


    def split_apsim_path_by_sep(
            p: str, ):
        """
        Split an APSIM path into base and selector using the first matching separator.

        Parameters
        ----------
        p : str
            APSIM path string.
        seps : iterable of str, optional
            Allowed separators, checked in order of precedence.

        Returns
        -------
        ApsimPath
            Structured APSIM path with base, selector, and separator used.

        Raises
        ------
        ValueError
            If none of the separators are found.
        """
        seps = ("?", "::", "|", "@")
        for sep in seps:
            if sep in p:
                left, right = p.split(sep, 1)
                if not left or not right:
                    raise ValueError(f"Invalid APSIM path around separator '{sep}': {p}")
                return left.rstrip('.'), right.strip('.')

        raise ValueError(
            f"Invalid APSIM path: none of the allowed separators {seps} found in '{p}'"
        )
