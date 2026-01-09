from functools import partial, cached_property
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping, Tuple

import numpy as np
import pandas as pd
from collections import defaultdict
from apsimNGpy.core.experimentmanager import ExperimentManager, AUTO_PATH
from apsimNGpy.senstivity.sampler import create_factor_specs
from SALib import ProblemSpec

AUTO = object()


def define_problem(params: Mapping[str, Tuple[float, float]],
                   names: Iterable[str] = AUTO, ) -> MappingProxyType | dict:
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
        names = tuple(split_apsim_path_by_sep(key)[1] for key, _ in items)
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


def default_n(method: str, n_parameters: int) -> int:
    """
    Determine a reasonable default sample size N for sensitivity analysis.

    Parameters
    ----------
    method : {"morris", "sobol", "fast"}
        Sensitivity method name.
    n_parameters : int
        Number of input parameters.

    Returns
    -------
    int
        Recommended base sample size N.
    """

    method = method.lower()

    if n_parameters <= 0:
        raise ValueError("n_parameters must be positive")

    if method in {"morris", "sample_morris"}:
        # Morris: trajectories scale weakly with dimension
        return max(10, 4 * n_parameters)

    if method in {"sobol", "sample_sobol"}:
        # Sobol: variance-based, exponential cost
        # power of two recommended
        base = 2 ** int((n_parameters * 50).bit_length() - 1)
        return max(512, base)

    if method in {"fast", "efast", "sample_fast"}:
        # eFAST: linear scaling with harmonics
        return max(65, 10 * n_parameters)

    raise ValueError(f"Unknown sensitivity method '{method}'")


class SensitivityAnalysisManager:
    def __init__(self, base_model):
        self.results = None
        self.base_model: str | Path = base_model
        self.Y = None
        self.X = None
        self.groups = None
        self.dist = None
        self.params = None
        self.names = None
        self.problem = None
        self.cpu_count = 12
        self.agg_var = None
        self.param_keys = []
        self.index_id = "ID"  # defines columns for indexing
        self.n_params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def setup(self, params, y, cpu_count=12,
              names=None, dist=None, groups=None,
              agg_var=None):
        self.params = params
        self.names = names
        self.agg_var = agg_var
        self.cpu_count = cpu_count
        self.Y = y
        if dist is None:
            dist = ['unif'] * len(params)
        self.dist = dist
        self.groups = groups

    def get_problem(self):
        problem = define_problem(self.params) if self.names is None else define_problem(self.params, self.names)
        problem['dist'] = self.dist
        if self.groups is not None:
            problem['groups'] = self.groups
        self.problem = problem
        return ProblemSpec(**problem)

    def extract_param_keys(self):
        self.param_keys.clear()
        # self.params is a dict with bounded values
        for key in self.params.keys():
            base, attr = split_apsim_path_by_sep(key)
            self.param_keys.append(attr)
        self.n_params = len(self.param_keys)

    def job_maker(self, values):
        """
         Generate APSIM factor specifications by grouping candidate parameters
        according to their APSIM base paths.

        Parameters:
        _____________
        values: n.ndarray

        Returns
        --------
        a generator[dict]
        @param values:
        """
        if values.ndim != 2:
            raise ValueError('Values must have 2 dimension, hence a two dimensional array expected')
        # ---- Group parameters by base path ----
        grouped = group_candidate_params(self.params.keys())

        n_params = len(self.params)
        # loop through rows and attach values
        for index in range(values.shape[0]):
            row = values[index]
            if len(row) != n_params:
                raise ValueError(
                    f"Based on parameters given, each value row must have {n_params} values "
                    f"(got {len(row)})"
                )

            # Map full param → value
            param_value_map = dict(zip(self.param_keys, row))

            # Emit one factor per base path
            all_inputs = []
            for base_path, attrs in grouped.items():
                inp = {
                    "path": base_path,
                    **{
                        attr: param_value_map.get(f"{attr}")
                        for attr in attrs
                    },
                }
                all_inputs.append(inp)
            yield {'model': self.base_model, self.index_id: index, 'inputs': all_inputs}

    def evaluate(self, X):
        print('submitting Jobs to mult-core manager API')
        from apsimNGpy.core.mult_cores import MultiCoreManager
        agg_func = 'sum'
        with MultiCoreManager(agg_func=agg_func) as mc:
            jobs = self.job_maker(X)
            mc.run_all_jobs(jobs, threads=True, clear_db=True, n_cores=12, retry_rate=2)
            df = mc.get_simulated_output(axis=0)
            df.sort_values(by=[self.index_id], inplace=True, ascending=True)
            self.results = df
            Y = df[self.Y].to_numpy()
        return Y

    def _evaluate(self, X, agg_func='sum', n_cores=12, retry_rate=2, threads=False):
        print('submitting Jobs to mult-core manager API')
        from apsimNGpy.core.mult_cores import MultiCoreManager
        with MultiCoreManager(agg_func=agg_func) as mc:
            jobs = self.job_maker(X)
            self.X = X
            mc.run_all_jobs(jobs, threads=threads, clear_db=True, n_cores=n_cores, retry_rate=retry_rate)
            df = mc.get_simulated_output(axis=0)
            df.sort_values(by=[self.index_id], inplace=True, ascending=True)
            self.results = df
            Y = df[self.Y].to_numpy()
        return Y

    def analyze_with_sobol(self, calc_second_order=True, skip_values=0, seed=42, N=AUTO,
                           agg_func='sum', n_cores=12, retry_rate=2, threads=False):
        evaluate = partial(self._evaluate, agg_func=agg_func, n_cores=n_cores, retry_rate=retry_rate, threads=threads)
        stp = self.get_problem()
        if N is AUTO:
            N = default_n(method='sobol', n_parameters=self.n_params)
        sI = (
            stp.sample_sobol(
                N=N,  # base sample size
                calc_second_order=calc_second_order,  # compute S2 indices
                skip_values=skip_values,  # skip initial Sobol points
                seed=seed  # RNG seed (None = random)
            )
            .evaluate(
                evaluate,  # callable f(x)
                parallel=False,  # whether to parallelize
                n_jobs=None,  # number of workers
                chunk_size=None,  # batch size for evaluation
                progress=True  # show progress bar
            )
            .analyze_sobol(
                calc_second_order=True,  # must match sampler
                conf_level=0.95,  # CI level
                n_resamples=1000,  # bootstrap resamples
                print_to_console=True
            )
        )
        return sI

    def analyse_with_efast(self, N=AUTO, print_to_console=True, agg_func='sum', n_cores=12, retry_rate=2,
                           threads=False):
        evaluate = partial(self._evaluate, agg_func=agg_func, n_cores=n_cores, retry_rate=retry_rate, threads=threads)
        stp = self.get_problem()
        if N is AUTO:
            N = default_n(method='fast', n_parameters=self.n_params)
        si = stp.sample_fast(N=N).evaluate(evaluate).analyze_fast(print_to_console=print_to_console)
        return stp

    def analyze_with_morris(self, N=AUTO, num_levels=4, optimal_trajectories=10, seed=12, conf_level=0.95,
                            num_resamples=1000,
                            print_to_console=True, agg_func='sum',
                            n_cores=12, retry_rate=2, threads=False):
        evaluate = partial(self._evaluate, agg_func=agg_func, n_cores=n_cores, retry_rate=retry_rate, threads=threads)
        st = self.get_problem()
        if N is AUTO:
            N = default_n(method='morris', n_parameters=self.n_params)
        sI = (
            st.sample_morris(
                N=N,  # number of trajectories
                seed=seed,
                num_levels=num_levels,  # grid resolution
                optimal_trajectories=optimal_trajectories
            )
            .evaluate(evaluate)
            .analyze_morris(conf_level=conf_level, num_resamples=num_resamples,
                            seed=seed,
                            print_to_console=print_to_console)
        )
        return st


def split_apsim_path_by_sep(
        p: str, ):
    """
    Split an APSIM path into base and selector using the first matching separator.
    Allowed separators are "?", "::", "|", "@" checked in order of preference.

    Parameters
    ----------
    p : str
        APSIM path string.


    Returns
    -------
    tuple(left string, right string) representing the node of apsim and left the parameter name on the node


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


def split_apsim_path(full_path: str) -> tuple[str, str]:
    """
    Split an APSIM parameter path into base path and attribute name.

    Example
    -------
    '[Sow].Script.Population' →
        ('[Sow].Script.', 'Population')
    """
    base, _, attr = full_path.rpartition(".")
    if not base:
        raise ValueError(f"Invalid APSIM path: {full_path}")
    return base + ".", attr


def group_candidate_params(candidate_param):
    """
    Group APSIM parameter paths by their base path.

    Returns
    -------
    dict[str, list[str]]
        Mapping of base_path → list of attribute names
    """
    groups = defaultdict(list)

    for p in candidate_param:
        base, attr = split_apsim_path_by_sep(p)
        groups[base].append(attr)
    return dict(groups)


if __name__ == '__main__':
    rowSpacing = '.Simulations.Simulation.Field.Fertilise at sowing.Amount'

    par = {'.Simulations.Simulation.Field.Sow using a variable rule?Population': (2, 10),
           '.Simulations.Simulation.Field.Fertilise at sowing?Amount': (0, 300),
           '.Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82?[Leaf].Photosynthesis.RUE.FixedValue': (
               1.2, 2.2)}

    with SensitivityAnalysisManager('Maize') as model:
        model.setup(params=par, y=['Yield', 'Maize.AboveGround.N'])
        sp = model.get_problem()
        xp = model.extract_param_keys()
        # si = sp.sample_sobol(2 ** 6).evaluate(model.evaluate).analyze_sobol()
        mor = model.analyze_with_morris()
        ef = model.analyse_with_efast()

        df = model.results
        # jobmaker
        arr = np.array([
            [1, 2, 'x'],
            [4, 5, 'y'],
            [7, 8, 'z'],
            [7, 8, 'z'],
            [7, 8, 'z'],
            [7, 8, 'z'],
            [7, 60, 'm'],
            [7, 100, 'z'],
            [7, 9, 'dd'],
        ])
        dat = list(model.job_maker(arr))
