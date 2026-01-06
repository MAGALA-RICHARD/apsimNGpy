from pathlib import Path

import numpy as np
import pandas as pd
from collections import defaultdict
from apsimNGpy.core.experimentmanager import ExperimentManager, AUTO_PATH
from apsimNGpy.senstivity.sampler import define_problem, create_factor_specs
from SALib import ProblemSpec


class BaseFactory:
    def __init__(self, base_model):
        self.results = None
        self.base_model: str | Path = base_model
        self.Y = None
        self.groups = None
        self.dist = None
        self.params = None
        self.names = None
        self.problem = None
        self.cpu_count = 12
        self.agg_var = None
        self.param_keys = []
        self.index_id = "ID"  # defines columns for indexing

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
        # self.params is a dict with bounded values
        for key in self.params.keys():
            base, _, attr = key.rpartition(".")
            self.param_keys.append(attr)

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

    def analyze_with_sobol(self):
        stp = self.get_problem()
        sI = (
            stp.sample_sobol(
                N=2 ** 10,  # base sample size
                calc_second_order=True,  # compute S2 indices
                skip_values=0,  # skip initial Sobol points
                seed=None  # RNG seed (None = random)
            )
            .evaluate(
                model.evaluate,  # callable f(x)
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

    def analyse_with_efast(self, sample_factor=80, print_to_console=True):
        stp = self.get_problem()
        si = stp.sample_fast(N=sample_factor).evaluate(self.evaluate).analyze_fast(print_to_console=True)
        return stp

    def analyze_with_morris(self, N=20, num_levels=4, optimal_trajectories=10):
        st = self.get_problem()
        sI = (
            st.sample_morris(
                N=N,  # number of trajectories
                num_levels=num_levels,  # grid resolution
                optimal_trajectories=optimal_trajectories
            )
            .evaluate(self.evaluate)
            .analyze_morris(print_to_console=True)
        )
        return st


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
        base, attr = split_apsim_path(p)
        base = base.rstrip('.')
        groups[base].append(attr)

    return dict(groups)


if __name__ == '__main__':
    rowSpacing = '.Simulations.Simulation.Field.Fertilise at sowing.Amount'

    par = {'.Simulations.Simulation.Field.Sow using a variable rule.Population': (2, 10),
           '.Simulations.Simulation.Field.Fertilise at sowing.Amount': (0, 300),
           '.Simulations.Simulation.Field.Sow using a variable rule.RowSpacing': (650, 750)}

    with BaseFactory('Maize') as model:
        model.setup(params=par, y='Yield')
        sp = model.get_problem()
        xp = model.extract_param_keys()
        # si = sp.sample_sobol(2 ** 6).evaluate(model.evaluate).analyze_sobol()
        ef = model.analyse_with_efast()
        mor = model.analyze_with_morris()

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
