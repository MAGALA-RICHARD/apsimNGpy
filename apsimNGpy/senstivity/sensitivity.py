from __future__ import annotations

import gc
import os
from functools import partial
from pathlib import Path
from typing import Iterable, Mapping
import numpy as np
import sqlalchemy
from apsimNGpy.senstivity.helpers import (split_apsim_path_by_sep, group_candidate_params, default_n, define_problem,
                                          generate_default_db_path)
from apsimNGpy.settings import logger

dataError = sqlalchemy.exc.OperationalError


class ConfigProblem:
    """
    Core engine for APSIM–SALib sensitivity analysis.

    This class is intentionally lightweight and stateless. Just used for problem configurations

    """

    def __init__(
            self,
            base_model: str | Path,
            params: Mapping[str, tuple[float, float]],
            outputs: list[str],
            *,
            names: Iterable[str] | None = None,
            dist: list[str] | None = None,
            groups: list[int] | None = None,
            index_id: str = "ID",
    ):
        self.raw_results = None
        self.base_model = base_model
        self.params = params
        self.outputs = outputs
        self.index_id = index_id
        self.incomplete_jobs = []

        self.problem = define_problem(
            params,
            names=names,
            dist=dist,
            groups=groups,
        )

        self.param_keys = [
            split_apsim_path_by_sep(p)[1] for p in params
        ]
        self.num_vars = len(self.param_keys)

    # ---------------- Job generation ----------------

    def job_maker(self, X: np.ndarray):
        """
        Generate APSIM jobs for each sampled parameter vector.
        """
        grouped = group_candidate_params(self.params)

        for idx, row in enumerate(X):
            values = dict(zip(self.param_keys, row))
            inputs = []

            for base, attrs in grouped.items():
                inputs.append({
                    "path": base,
                    **{a: values[a] for a in attrs},
                })

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
    ):
        """
        Run APSIM simulations and return outputs and raw results.
        """
        table_prefix = '__sens__'
        from apsimNGpy.core.mult_cores import MultiCoreManager, core_count
        db_path = generate_default_db_path(table_prefix)
        n_cores = core_count(n_cores, threads=threads)

        def run_in_multi_core(db):

            with MultiCoreManager(agg_func=agg_func, db_path=db, table_prefix=table_prefix) as mc:
                mc.run_all_jobs(
                    self.job_maker(X),
                    n_cores=n_cores,
                    retry_rate=retry_rate,
                    threads=threads,
                    clear_db=True,
                    display_failures=True,
                    subset=self.outputs,
                    ignore_runtime_errors=False,
                )
                df = mc.get_simulated_output(axis=0)
                df.sort_values(self.index_id, inplace=True)
                self.raw_results = df
                self.incomplete_jobs = mc.incomplete_jobs
                if mc.incomplete_jobs:
                    logger.warning(f"over {len(mc.incomplete_jobs)}Incomplete were registered something went wrong")
                return df[self.outputs].to_numpy()

        try:
            return run_in_multi_core(db=db_path)
        finally:
            try:
                db = Path(db_path).resolve()
                os.remove(db) if db.exists() else None
                print('database deleted')
            except PermissionError:
                pass

    def evaluate(self, X,
                 agg_func='sum',
                 n_cores=-2,
                 retry_rate=2,
                 threads=False):
        """
        The problem is already defined but user want to control the inputs or use a procedural approach after.

        agg_func : str, default="sum"
           Aggregation function for APSIM outputs.
        n_cores : int, default= total machine cpu counts minus 2.
            Number of parallel workers. use 1 to purely run in a single thread or process
        retry_rate : int, default=2
            Number of retries for failed simulations.
        threads : bool, default=False
            Use multithreading instead of multiprocessing.
        """
        from apsimNGpy.core.mult_cores import core_count
        n_cores = core_count(n_cores,threads=threads)
        part = partial(
            self._evaluate,
            agg_func=agg_func,
            n_cores=n_cores,
            retry_rate=retry_rate,
            threads=threads,
        )
        return part(X)


def run_sensitivity(
        configured_prob: ConfigProblem,
        *,
        method: str = 'morris',
        N: int | None = None,
        seed: int | None = 48,
        agg_func: str = "sum",
        n_cores: int = -2,
        retry_rate: int = 3,
        threads: bool = False,
        sample_options: dict | None = None,
        analyze_options: dict | None = None,
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
            Default is True

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
    from apsimNGpy.core.mult_cores import core_count
    n_cores = core_count(n_cores, threads=threads)
    sample_options = sample_options or {}
    analyze_options = analyze_options or {}
    sample_options = sample_options.copy()
    analyze_options = analyze_options.copy()
    analyze_options.setdefault("conf_level", 0.95)
    analyze_options.setdefault("num_resamples", 1000, )
    analyze_options.setdefault("print_to_console", True)
    if method == 'sobol':
        sample_options.setdefault('calc_second_order', True)
        analyze_options.setdefault('calc_second_order', True)
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
    )

    sampler = getattr(configured_prob.problem, f"sample_{method}")
    sample_options.setdefault('seed', seed)
    import inspect
    sign = list(inspect.signature(sampler).parameters)

    stp = None
    try:

        stp = sampler(N=N, **sample_options)

        stp.evaluate(evaluate)
        analyzer = getattr(stp, f"analyze_{method}")

        # ---- evaluate ----
        # X = stp.samples
        # Y, results = evaluate(X)
        setattr(stp, 'apsim_results', configured_prob.raw_results)
        # ---- analyze ----
        ans = analyzer(**analyze_options)
        sign = list(inspect.signature(analyzer).parameters)
        # print(sign)
        return ans
    finally:
        del sampler, stp
        gc.collect()


if __name__ == "__main__":
    params = {
        ".Simulations.Simulation.Field.Sow using a variable rule?Population": (2, 10),
        ".Simulations.Simulation.Field.Fertilise at sowing?Amount": (0, 300),
        # ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82?[Leaf].Photosynthesis.RUE.FixedValue": (
        #     1.2, 2.2),
    }
    runner = ConfigProblem(
        base_model="Maize",
        params=params,
        outputs=["Yield", "Maize.AboveGround.N"],
    )
    # custom
    from SALib.sample import saltelli
    from SALib.analyze import sobol

    param_values = saltelli.sample(runner.problem, 2 ** 4)
    Y = runner.evaluate(param_values)
    Si = [sobol.analyze(runner.problem, Y[:, i], print_to_console=True) for i in range(Y.ndim)]
    print(Si)
    Si_sobol = run_sensitivity(
        runner,
        method="sobol",
        N=2 ** 4,  # ← base sample size
        sample_options={
            "calc_second_order": True,
            # "skip_values": 1024,
            # "seed": 42,
        },
        analyze_options={
            "conf_level": 0.95,
            "num_resamples": 1000,
            "print_to_console": True,
            "calc_second_order": True,
        },
    )
    Si_morris = run_sensitivity(
        runner,
        method="morris", n_cores=10,
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
        },
    )
    si_fast = run_sensitivity(
        runner,
        method="fast",
        sample_options={
            "M": 2,

        },
        analyze_options={
            'conf_level': 0.95,
            "num_resamples": 1000,
            "print_to_console": True,
        },
    )
