from __future__ import annotations

import dataclasses
import gc
import os
import sys
from functools import partial
from pathlib import Path
from typing import Iterable
from typing import Optional

import numpy as np
import pandas as pd
import sqlalchemy
from pydantic import BaseModel

from apsimNGpy import is_scalar, timer
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.model_loader import get_node_by_path, Models
from apsimNGpy.sensitivity.helpers import (default_n, define_problem,
                                           generate_default_db_path)
from apsimNGpy.settings import logger
from apsimNGpy.starter import CLR
from apsimNGpy.sensitivity.salib_sample import generate_samples

dataError = sqlalchemy.exc.OperationalError

__all__ = ['ConfigProblem', 'run_sensitivity']


@dataclasses.dataclass
class Params:
    grouped_pairs: dict
    others: dict
    node_types: dict


def grouper(base_model, _params):
    from collections import defaultdict
    grouped_pairs = defaultdict(list)
    others = {}
    node_types = {}
    model = ApsimModel(base_model)

    for data in _params:
        p = dict(data)
        p.pop('bounds', ())
        base, attr = p.pop('base'), p.pop('param')
        is_cultivar = get_node_by_path(model.Simulations, base, cast_as='auto')
        node_types[base] = is_cultivar
        if isinstance(is_cultivar, CLR.Models.PMF.Cultivar):
            cultivar = True

        else:
            cultivar = False

        if not isinstance(cultivar, bool):
            raise TypeError(f"{cultivar} is expected to be a boolean got {type(cultivar)}")
        man = p.get('manager_path', None) or p.get('managers', None)
        if cultivar:
            # Check if cultivar is true, managers are provided
            if not man:
                raise ValueError('managers needed')
        else:
            if man:
                # pop if available and not cultivar
                p.pop('manager_path', None)
                p.pop('managers', None)

        others[base] = p
        grouped_pairs[base].append(attr)
    DATA = Params(grouped_pairs, others, node_types)
    with model:
        pass
    return DATA


def get_list_like(obj):
    if not obj:
        return []
    list_like = [obj] if is_scalar(obj) else list(obj)
    return list_like


def check_all_completed(res, expected_ids, index_name):
    completed_ids = set(res[index_name].astype('str'))
    expected = set(pd.Series(expected_ids).astype('str'))
    return list(expected - completed_ids)


class ConfigProblem:
    """
    Core engine for APSIM–SALib sensitivity analysis.

    This class is just used for problem configurations

    """

    def __init__(
            self,
            base_model: str | Path,
            params: list[dict],
            outputs: list[str],
            *,
            names: Iterable[str] | None = None,
            dist: list[str] | None = None,
            groups: list[int] | None = None,
            index_id: str = "ID",

    ):
        self.X = None
        self.config_ok = None
        self.raw_results = None
        self.base_model = base_model
        self.params = params
        self.outputs = get_list_like(outputs)
        self.index_id = index_id
        self.incomplete_jobs = []
        self.NewXVars = None

        self.problem = define_problem(
            params,
            names=names,
            dist=dist,
            groups=groups,
        )
        try:
            self.param_keys = [
                p["param"] for p in params
            ]
            self.num_vars = len(self.param_keys)
        except TypeError as e:
            msg = (
                f"{e}\n"
                "This may indicate that the sensitivity API has changed. "
                "Please check the documentation."
            )

            print(msg, file=sys.stderr)

            logger.exception(msg)

            raise

    # ---------------- Job generation ----------------

    def job_maker(self, X: np.ndarray, pending=None):
        """
        Generate APSIM jobs for each sampled parameter vector.
        """
        if not self.config_ok:
            grouped = grouper(self.base_model, self.params)  # Data class of Params
            self.config_ok = True
            self.grouped = grouped
        else:
            grouped = self.grouped

        # grouped = group_candidate_params(self.params)
        if pending:
            iterator = zip(pending, X)
        else:
            iterator = enumerate(X)
        for idx, row in iterator:

            ############################################
            values = dict(zip(self.param_keys, row))

            inputs = []
            pairs = grouped.grouped_pairs
            for base, attrs in pairs.items():
                others = grouped.others.get(base, {})
                attributes = {a: values[a] for a in attrs}

                if not isinstance(grouped.node_types.get(base), CLR.Models.PMF.Cultivar):
                    inData = {
                        "path": base,
                        **attributes,
                        **others
                    }
                else:
                    inData = {
                        "path": base,
                        'commands': attributes,
                        **others
                    }
                inputs.append(inData)

            yield {
                "model": self.base_model,
                self.index_id: idx,
                "inputs": inputs,
            }

    # ---------------- Evaluation ----------------

    def _evaluate(
            self,
            X: np.ndarray,
            *,
            agg_func: str,
            n_cores: int,
            retry_rate: int,
            threads: bool,
            engine: str,
            chunk_size: int = 100,
            groupings: list | None = None,
            tables: list | None = None,
            total_chunks: int = 10,
    ):
        """
        Run APSIM simulations and return outputs and raw results.
        """
        table_prefix = '__sens__'
        from apsimNGpy.core.mult_cores import MultiCoreManager, core_count
        db_path = generate_default_db_path(table_prefix)
        n_cores = core_count(n_cores, threads=threads)
        PROB_NAMES = self.problem.get('names')

        @timer
        def run_in_multi_core(data_db, sample_matrix, pending_retry=None, chunks=total_chunks):
            from apsimNGpy.parallel.batched import run_multiple_simulations, load_all_results
            # send the grouping to the subset variables
            group = list(get_list_like(groupings))
            sub_sets_columns = self.outputs
            group.extend(sub_sets_columns)

            def merged(dt):
                xd = pd.DataFrame(X, columns=PROB_NAMES)
                xd[self.index_id] = range(xd.shape[0])
                xd[self.index_id] = xd[self.index_id].astype('str')
                dt[self.index_id] = dt[self.index_id].astype('str')
                mgd = dt.merge(xd, on=self.index_id, how='inner')
                return mgd

            sub_sets_columns = group
            rt = run_multiple_simulations(self.job_maker(sample_matrix, pending=pending_retry),
                                          n_cores=n_cores, batch_size=chunk_size, tables=tables, db_or_con=data_db)
            df = load_all_results(data_db)
            if not set(PROB_NAMES).issubset(df.columns):
                df = merged(df)
            return df
            # mc = MultiCoreManager(agg_func=agg_func, db_path=data_db, table_prefix=table_prefix)
            # mc.run_all_jobs(
            #     self.job_maker(sample_matrix, pending=pending_retry),
            #     n_cores=n_cores,
            #     retry_rate=retry_rate,
            #     threads=threads,
            #     clear_db=True,
            #     display_failures=True,
            #     subset=sub_sets_columns,
            #     ignore_runtime_errors=False,
            #     engine=engine,
            #     chunk_size=chunk_size,
            #     table_name=tables,
            #     total_chunks=chunks,
            # )
            # return mc

        try:

            df = run_in_multi_core(data_db=db_path, sample_matrix=X)
            # df = manager.get_simulated_output(axis=0)
            completed = [df, ]
            logger.info('Checking incomplete outputs')
            pending = check_all_completed(df, expected_ids=np.arange(X.shape[0]), index_name=self.index_id)

            pending_runner = 0
            while pending:
                logger.info(f'{len(pending)} pending simulation IDs found. Rerunning them')
                sub_x = X[pending]
                dif = run_in_multi_core(
                    data_db=db_path,
                    sample_matrix=sub_x, pending_retry=pending,
                    chunks=1,
                )

                completed.append(dif)
                # the data frame must the newly returned
                pending = list(
                    check_all_completed(dif, expected_ids=pending, index_name=self.index_id)
                )
                pending_runner += 1
                if pending_runner > 2 and pending:
                    raise RuntimeError(
                        f"Maximum retry limit exceeded ({pending_runner}). "
                        f"The following simulations could not be completed: {pending}"
                    )

            #################################################################
            # The simulations are organized according to index_id to match with input variables samplesd by SALib

            from xlwings import view
            ag_df = pd.concat(completed)
            ag_df.sort_values(self.index_id, inplace=True)
            self.raw_results = ag_df.reset_index()
            return self.grouper(ag_df, groupings=groupings, agg_func=agg_func, X=X, problem_name=PROB_NAMES)

        finally:
            try:
                os.remove(db_path)
            except PermissionError:
                pass
            except FileNotFoundError:
                pass

    def clean_a_group(self, dff, *, problem_names, X):
        """
        Clean results, remove duplicate entries by ID, drop missing values, and
        align the remaining data with the sampled X matrix.
        Raises ValueError if:
            - The resulting dataset is empty.
            - If simulated output != input variable length
        """
        if not self.outputs:
            raise ValueError("outputs must be specified")
        outputs = self.outputs
        data = dff.copy()
        data.sort_values(by=self.index_id, inplace=True)
        out = data.dropna(subset=outputs)
        # we also like unique IDs
        out.drop_duplicates(inplace=True, subset=self.index_id)
        if out.empty:
            raise ValueError(
                "Dataframe contains no data after dropping all are you sure it is coming from the same table")

        Xs = out[problem_names].copy()
        Ys = out[outputs].copy()
        if Ys.shape[0] != X.shape[0]:
            raise ValueError("Data are not equal after processing")
        if Xs.shape != X.shape:
            raise ValueError("X vars are not equal after processing")
        return Xs, Ys

    def grouper(self, df, groupings, agg_func, X, problem_name):
        # check if multiple tables exist
        if 'source_table' in df:
            existing_tables = df['source_table'].unique()
            print(len(existing_tables), 'tables')
            DATA_TABLES = []
            for _, dif in df.groupby('source_table'):
                pass  # DATA_TABLES.append(dif)
        else:
            DATA_TABLES = [df, ]

        if groupings:
            grp = get_list_like(groupings)
            df.reset_index(drop=True, inplace=True)
            for keys, group_df in df.groupby(grp):
                print(f"Working on group {keys}", file=sys.stderr)
                XX, get_out = self.clean_a_group(group_df, problem_names=problem_name, X=X)
                arr = get_out.to_numpy() if isinstance(get_out, pd.DataFrame) else get_out
                yield keys, XX, arr
        else:
            xx, df = self.clean_a_group(df, problem_names=problem_name, X=X)
            arr = df.to_numpy() if isinstance(df, pd.DataFrame) else df
            yield agg_func, xx, arr

    def evaluate(self, X,
                 agg_func='sum',
                 n_cores=-2,
                 retry_rate=2,
                 threads=False,
                 engine='python'):
        """
        The problem is already defined but user want to control the inputs or use a procedural approach after.

        agg_func : str, default="sum"
           Aggregation function for APSIM outputs.
        n_cores : int, default= total machine cpu counts minus 2.
            Number of parallel workers. use 1 to purely run in a single thread or process
            n_cores may be specified as a negative integer to indicate relative allocation from the total available CPU cores.
            In this case, the absolute value of n_cores is subtracted from the total CPU budget, and the remaining cores are used.
            If the resulting number of cores is less than or equal to zero, a ValueError is raised.
        retry_rate : int, default=2
            Number of retries for failed simulations.
        threads : bool, default=False
            Use multithreading instead of multiprocessing.
        engine: str optional default is 'python'
        if 'csharp' results are written to a directory then forwarded to Models.exe. this is 2 times faster all the time
        """
        from apsimNGpy.core.mult_cores import core_count
        n_cores = core_count(n_cores, threads=threads)
        self.X = X
        part = partial(
            self._evaluate,
            agg_func=agg_func,
            n_cores=n_cores,
            retry_rate=retry_rate,
            threads=threads,
            engine=engine
        )
        return part(X)


def run_sensitivity(
        configured_prob: ConfigProblem,
        *,
        method: str = 'morris',
        N: int | None = None,
        seed: int | None = 48,
        agg_func: str | None = "sum",
        n_cores: int = -2,
        retry_rate: int = 3,
        threads: bool = False,
        sample_options: dict | None = None,
        analyze_options: dict | None = None,
        engine='python',
        chunk_size: int = 100,
        grouping: None | list = None,
        tables: None | list = None,
        total_chunks: int = 10
):
    """
    Run a complete sensitivity analysis.

    Parameters
    ----------
    configured_prob : ConfigProblem
        Configured APSIM–SALib runner.
    method : {"morris", "sobol", "fast"}
        Sensitivity method. default is morris
    N : int, optional
        Base sample size. If None, a method-specific default is used.
    seed : int, optional
        Random seed.
    agg_func : str, default="sum"
        Aggregation function for APSIM outputs.
    n_cores : int, default= total machine cpu counts minus 2. to reserve for other processes
        Number of parallel workers. use 1 to purely run in a single thread or process.
        n_cores may be specified as a negative integer to indicate relative allocation from the total available CPU cores.
        In this case, the absolute value of n_cores is subtracted from the total CPU budget, and the remaining cores are used.
        If the resulting number of cores is less than or equal to zero, a ValueError is raised.
    retry_rate : int, default=2
        Number of retries for failed simulations.
    threads : bool, default=False
        Use multithreading instead of multiprocessing.
    sample_options : dict, optional
    Options forwarded to the SALib sampling function. The available
    options depend on the selected sensitivity analysis method.

    FAST method
        N (int)
            Number of model evaluations used to estimate sensitivity
            indices. Larger values improve stability but require more
            simulations.

        M (int)
            Controls the resolution of the FAST sampling. Higher values
            improve accuracy but increase computational cost.

        seed (int)
            Random seed used to make the sampling reproducible.
            default is 48

    Morris method
        N (int)
            Number of trajectories used to explore the parameter space.
            Increasing this value improves robustness of the results.

        num_levels (int)
            Number of discrete levels used when sampling each parameter.
            Higher values provide finer resolution.

        optimal_trajectories (int)
            Number of trajectories selected to improve coverage of the
            parameter space.

        local_optimization (bool)
            Whether an additional optimization step is used to improve
            trajectory selection.

        seed (int)
            Random seed used to make the sampling reproducible.
             default is 48

    Sobol method
        N (int)
            Base sample size used to generate Sobol samples. Larger
            values lead to more reliable results but increase the number
            of model runs. the total sample size is inferred from the number of parameters. N must be a power of 2
            The final sample size is computed as N×(2D+2), where D is the number of parameters, when second-order effects are
            enabled (i.e., calc_second_order=True), reflecting the need to evaluate parameter interactions. When
            second-order effects are disabled (calc_second_order=False), the required sample size is
            reduced to N×(D+2)


        calc_second_order (bool)
            Whether second order sensitivity indices are computed.
            Enabling this option increases runtime.
            Default is False

        scramble (bool)
            Whether scrambling is applied to improve the quality of the
            Sobol sequence. default is False


        skip_values (int)
            Number of initial values skipped in the Sobol sequence to
            improve sample quality.

        seed (int)
            Random seed used to make the sampling reproducible.
             default is 48
    analyze_options : dict, optional
        Options forwarded to the SALib analyzer. The available options are described in the
        SALIB documentation fore each method.
    engine: str optional default is 'python'
        if 'csharp' results are written to a directory then forwarded to Models.exe. This is 50-100% times faster than python all the time.
        The csharp engine is considerably faster on powerful machines but exhibits stability issues in some older APSIM versions, whereas the Python engine is more stable. For this reason, the default engine is set to "python".
    chunk_size : int, optional, default=100
        Relevant only when engine="csharp".
    grouping : list | None, optional, default=None
        If provided, results will be grouped according to the specified
        grouping variable(s), and evaluations will be performed separately
        for each group.
    tables : list | None, required
        None is retained only for backward compatibility. The function
        will raise a ValueError if tables are not provided.
    total_chunks : int, optional, default=10
        Relevant only when engine="python".
    Examples
    ---------

    The following examples illustrate how to perform global sensitivity analysis using
    different methods supported by :func:`run_sensitivity`. Each method serves a
    different analytical purpose, ranging from screening to variance decomposition.

    First, define a configuration-based sensitivity problem. The ``runner`` encapsulates
    the APSIM base model, parameters to be perturbed, and the outputs of interest.

    .. code-block:: python

        params = {
        ".Simulations.Simulation.Field.Sow using a variable rule?Population": (2, 10),
        ".Simulations.Simulation.Field.Fertilise at sowing?Amount": (0, 300),
        ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82?[Leaf].Photosynthesis.RUE.FixedValue": (1.2, 2.2),
         }
         #  any of these ?, ::, |, @ are valid separators between node path and parameter name in question
        runner = ConfigProblem(
            base_model="Maize",
            params=params,
            outputs=["Yield", "Maize.AboveGround.N"]
        )

    Morris (Elementary Effects)
    ------------------------------
    The Morris method is typically used as a *screening tool* to identify influential
    parameters with relatively low computational cost. It is well suited for high-dimensional
    problems where the goal is to rank parameters rather than quantify precise sensitivities.

    .. code-block:: python

        Si_morris = run_sensitivity(
            runner,
            method="morris",
            n_cores=6,
            sample_options={
                "seed": 42,
                "num_levels": 6,
                "optimal_trajectories": 10,
            },
            analyze_options={
                "conf_level": 0.95,
                "num_resamples": 1000,
                "print_to_console": True,
                "seed": 42,
            },
        )

    FAST (Fourier Amplitude Sensitivity Test)
    ------------------------------------------
    The FAST method provides variance-based sensitivity indices with lower sampling
    requirements than Sobol. It is useful when computational resources are limited but
    quantitative sensitivity estimates are still required.

    .. code-block:: python

        Si_fast = run_sensitivity(
            runner,
            method="fast",
            engine = 'python',
            sample_options={
                "M": 2,
            },
            analyze_options={
                "conf_level": 0.95,
                "num_resamples": 1000,
                "print_to_console": True,
            },
        )

    Sobol (Variance Decomposition)
    ----------------------------------
    Sobol sensitivity analysis provides a full variance decomposition of model outputs,
    including first-order and (optionally) higher-order interaction effects. This method
    is the most robust but also the most computationally demanding.

    .. code-block:: python

        Si_sobol = run_sensitivity(
            runner,
            method="sobol",
            N=2 ** 8,  # base sample size
            engine='csharp', # default is csharp
            sample_options={
                "calc_second_order": False,
            },
            analyze_options={
                "conf_level": 0.95,
                "num_resamples": 1000,
                "print_to_console": True,
                "calc_second_order": False,
            },
        )

    .. note::

       For Sobol sensitivity analysis, ``calc_second_order`` must be consistent between
       sampling and analysis. If specified in only one of ``sample_options`` or
       ``analyze_options``, a value error is raised.

"""
    if tables is None:
        raise ValueError("Please specify the table names")
    if agg_func and grouping:
        logger.warning(f'Both grouping and {agg_func} aggregation function are provided, only grouping will be used')
        agg_func = None
    from apsimNGpy.core.mult_cores import core_count
    n_cores = core_count(n_cores, threads=threads)

    if method.lower() not in {"sobol", "morris", 'fast'}:
        raise NotImplementedError(f"Method {method} not supported by this method try customization from scratch")
    sample_options = sample_options or {}
    analyze_options = analyze_options or {}
    sample_options = sample_options.copy()
    analyze_options = analyze_options.copy()
    analyze_options.setdefault("conf_level", 0.95)
    analyze_options.setdefault("num_resamples", 1000, )
    analyze_options.setdefault("print_to_console", True)
    if method == 'sobol':
        sample_options.setdefault('calc_second_order', False)
        analyze_options.setdefault('calc_second_order', False)
        if analyze_options.get('calc_second_order') != sample_options.get('calc_second_order'):
            raise ValueError(
                "Sobol sensitivity requires that both sample `calc_second_order` and analyze ``calc_second_order` options  match ")
    if N is None:
        try:
            N = default_n(method, configured_prob.num_vars)
        except ValueError:
            N = 100

    evaluate = partial(
        configured_prob._evaluate,
        agg_func=agg_func,
        n_cores=n_cores,
        retry_rate=retry_rate,
        threads=threads,
        engine=engine,
        chunk_size=chunk_size,
        groupings=grouping,
        tables=tables,
        total_chunks=total_chunks,
    )

    sample_options.setdefault('seed', seed)
    eva_data = []
    X = generate_samples(configured_prob, N=N, method=method, **sample_options)
    frames = evaluate(X)
    from apsimNGpy.sensitivity.evaluate_salib import evaluate_sensitivity
    from apsimNGpy.sensitivity.fstr import format_salib_results
    try:
        for index, XX, dif in frames:
            analyze_options['X'] = XX

            if dif.ndim == 1 and len(dif) == XX.shape[0]:
                ans = evaluate_sensitivity(configured_prob, method=method, Y=dif, **analyze_options)
                if is_scalar(configured_prob.outputs):
                    output = configured_prob.outputs
                else:
                    raise ValueError(f'Why is response variables are: {len(configured_prob.outputs)} expected 1')
                ans = format_salib_results(ans, method, output)
                if is_scalar(grouping):
                    ans[grouping] = index
                else:
                    ans[[*grouping]] = index
            else:
                outputs = configured_prob.outputs if not is_scalar(configured_prob.outputs) else [
                    configured_prob.outputs]
                for count, resp in enumerate(outputs):
                    if isinstance(dif, pd.DataFrame):
                        Y = dif.iloc[:, count].to_numpy()
                    else:
                        Y = dif[:, count]

                    if len(Y) == XX.shape[0]:
                        print(len(Y))
                        ans = evaluate_sensitivity(configured_prob, method=method, Y=Y, **analyze_options)
                        ans = format_salib_results(ans, method, resp)
                        if grouping:
                            if is_scalar(grouping):
                                ans[grouping] = index
                            else:
                                ans[[*grouping]] = index
                        eva_data.append(ans)

        out_df = pd.concat(eva_data)
        del eva_data
        return out_df
    finally:
        gc.collect()


class Factor(BaseModel):
    base: str
    bounds: tuple
    param: str
    managers: Optional[dict] = None
    name: Optional[str] = None
    plant: Optional[str] = None

    def hash(self):
        if self.managers:
            manager_p = tuple(sorted(self.managers.keys())), tuple(sorted(self.managers.values()))
        else:
            manager_p = ()
        return abs(hash((self.base, self.param, self.name, manager_p, self.name)))

    def dump(self, base_model):
        with ApsimModel(base_model) as model:
            node = get_node_by_path(model.Simulations, node_path=self.base, cast_as='auto')
        if isinstance(node, Models.PMF.Cultivar):
            if not isinstance(self.managers, dict):
                raise ValueError('managers must be a dictionary in order to update the cultivar ')
            if not isinstance(self.plant, str):
                raise ValueError(f'Please provide a plant hosting the cultivar: {self.base}')
            return dict(base=self.base, param=self.param, bounds=self.bounds, managers=self.managers, names=self.name,
                        plant=self.plant)
        return dict(base=self.base, param=self.param, bounds=self.bounds)


class CustomSensitivityManager:

    def __init__(self, base_model: str, response_vars):
        self.grouping = None
        self.partial_run = None
        self._factors: dict = {}
        self.base_model = base_model
        self.y = response_vars
        self.runner = None

    def add_sens_factor(self, *, base: str, param, bounds, managers=None, names=None, plant=None):
        factor = Factor(base=base, param=param, bounds=bounds, managers=managers, name=names, plant=plant)
        hask_key = factor.hash()
        if hask_key in self._factors:
            raise ValueError(f"Duplicate {factor} detected. Factor already exist")
        self._factors[hask_key] = factor.dump(self.base_model)

    def get_list_sens_factors(self):
        factors = dict(self._factors)
        for fac in factors.values():
            fac.pop('name', None)
        return list(factors.values())

    def config_problem(self,
                       *,
                       names: Iterable[str] | None = None,
                       dist: list[str] | None = None,
                       groups: list[int] | None = None,
                       index_id: str = "ID", ):
        _params = self.get_list_sens_factors()
        bm = self.base_model
        self.runner = ConfigProblem(base_model=bm, params=_params,
                                    outputs=self.y, names=names,
                                    dist=dist, groups=groups, index_id=index_id)

    @property
    def n_factors(self):
        return len(self._factors)

    def build_sense_model(self,
                          *,
                          method: str = 'morris',
                          N: int | None = None,
                          seed: int | None = 48,
                          sample_options: dict | None = None,
                          analyze_options: dict | None = None,
                          grouping: None | list = None,
                          tables: None | list = None,
                          total_chunks: int = 10

                          ):
        """
        grouping : list | None, optional, default=None
            If provided, results will be grouped according to the specified
            grouping variable(s), and evaluations will be performed separately
            for each group.
        tables : list | None, required
            None is retained only for backward compatibility. The function
            will raise a ValueError if tables are not provided.
        total_chunks : int, optional, default=10
            Relevant only when engine="python".
        """
        if not self.runner:
            # run with defaults if not called by the user
            self.config_problem()
        if self.n_factors <= 1:
            msg = f"Expected at least 2 sensitivity factors, but got {self.n_factors}."
            raise ValueError(
                msg
            )
        self.grouping = grouping
        self.partial_run = partial(run_sensitivity, configured_prob=self.runner,
                                   method=method,
                                   N=N, seed=seed,
                                   sample_options=sample_options,
                                   analyze_options=analyze_options,
                                   grouping=grouping,
                                   tables=tables,
                                   total_chunks=total_chunks
                                   )
        return self

    def run(self, n_cores: int = -1,
            agg_func='mean', engine='python', chunk_size=200,
            retry_rate=1,
            threads=False):

        if self.partial_run is None:
            raise RuntimeError('can not non initialized or built senstivity model use sense model before continuing')
        return self.partial_run(n_cores=n_cores, engine=engine, chunk_size=chunk_size,
                                agg_func=agg_func,
                                retry_rate=retry_rate, threads=threads)

        # return run_sensitivity(
        #     configured_prob=self.runner,
        #     method=method, n_cores=n_cores,
        #     N=N, seed=seed, agg_func=agg_func,
        #     sample_options=sample_options,
        #     analyze_options=analyze_options,
        #     engine=engine, chunk_size=chunk_size,
        #     retry_rate=retry_rate,
        #     threads=threads
        # )


if __name__ == "__main__":
    cc = CustomSensitivityManager(base_model='Maize', response_vars=["Yield", "Maize.AboveGround.N"])
    cc.add_sens_factor(
        **{'base': ".Simulations.Simulation.Field.Sow using a variable rule", 'param': "Population", 'bounds': (2, 10),
           'managers': {1: 2}})
    cc.add_sens_factor(
        **{"base": ".Simulations.Simulation.Field.Fertilise at sowing", "param": "Amount", 'bounds': (0, 300,)})
    print(cc._factors)
    print(cc.get_list_sens_factors())
    params = [
        # {'base': ".Simulations.Simulation.Field.Sow using a variable rule", 'param': "Population", 'bounds': (2, 10), },
        # {"base": ".Simulations.Simulation.Field.Fertilise at sowing", "param": "Amount", 'bounds': (0, 300),
        #  },
        dict(base=".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82",
             param="[Leaf].Photosynthesis.RUE.FixedValue", bounds=(
                0.7, 2.2), managers={'Sow using a variable rule': 'CultivarName'}, plant='Maize'),
        dict(base=".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82",
             param='[Maize].Grain.MaximumNConc.InitialPhase.InitialNconc.FixedValue',
             bounds=(0.015, 0.045), managers={'Sow using a variable rule': 'CultivarName'}, plant='Maize'
             )

    ]

    # custom
    # from SALib.sample import saltelli
    # from SALib.analyze import sobol
    #
    # param_values = saltelli.sample(runner.problem, 2 ** 4)
    # Y = runner.evaluate(param_values)
    # Si = [sobol.analyze(runner.problem, Y[:, i], print_to_console=True) for i in range(Y.ndim)]
    # print(Si)

    # Si_sobol = run_sensitivity(
    #     runner,
    #     method="sobol",
    #     N=2 ** 4,  # ← base sample size
    #     n_cores=-6,
    #     engine='python',
    #     sample_options={
    #         "calc_second_order": True,
    #         "skip_values": 1024,
    #         # "seed": 42,
    #     },
    #     analyze_options={
    #         "conf_level": 0.95,
    #         "num_resamples": 5000,
    #         "print_to_console": True,
    #         "calc_second_order": True,
    #     },
    # )
    ccMorris = cc.build_sense_model(method="morris", N=10,
                                    grouping=['year', ],
                                    sample_options={
                                        'seed': 42,
                                        "num_levels": 6,
                                        "optimal_trajectories": 6,
                                    },
                                    analyze_options={
                                        'conf_level': 0.95,
                                        "num_resamples": 1000,
                                        "print_to_console": True,
                                        'seed': 42
                                    }, )
    # cm = ccMorris.run(agg_func=None)
    # print(cm)
    runner = ConfigProblem(
        base_model="Maize",
        params=params,
        outputs=["Yield", "Maize.AboveGround.N"],
    )


    # Si_morris = run_sensitivity(
    #     runner,
    #     method="morris", n_cores=10,
    #     sample_options={
    #         'seed': 42,
    #         "num_levels": 6,
    #         "optimal_trajectories": 6,
    #     },
    #     analyze_options={
    #         'conf_level': 0.95,
    #         "num_resamples": 1000,
    #         "print_to_console": True,
    #         'seed': 42
    #     },
    # )
    # si_sobol = run_sensitivity(
    #     runner,
    #     method="sobol",
    #     agg_func=None,
    #     grouping=['year'],
    #     N=10,
    #     sample_options={
    #         "calc_second_order": False,
    #
    #     },
    #     analyze_options={
    #         "calc_second_order": False,
    #         "conf_level": 0.95,
    #         "num_resamples": 1000,
    #         "print_to_console": True,
    #     },
    # )

    def run_sens():
        run_sensitivity(
            runner,
            n_cores=8,
            total_chunks=8,
            chunk_size=5,
            engine='python',
            method="fast",
            tables=['Report'],
            N=700,
            # grouping=['year'],
            sample_options={
                "M": 2,

            },
            analyze_options={
                'conf_level': 0.95,
                "num_resamples": 1000,
                "print_to_console": True,
            },
        )


    si_fast = run_sens()
    ans = runner.raw_results
    from xlwings import view

    view(ans)
