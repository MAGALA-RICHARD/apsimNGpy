from __future__ import annotations

import copy
import os
import sqlite3
from functools import partial
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd
import sqlalchemy
from apsimNGpy.core_utils.database_utils import (get_db_table_names, read_db_table)
from apsimNGpy.senstivity.helpers import (split_apsim_path_by_sep, group_candidate_params, clear_db,
                                          switch_sobol_option,
                                          default_n, define_problem, generate_default_db_path)
from apsimNGpy.settings import logger

dataError = sqlalchemy.exc.OperationalError

CPU_CORES = max(6, os.cpu_count() - 4)


class ConfigProblem:
    """
    Core engine for APSIM–SALib sensitivity analysis.

    This class is intentionally lightweight and stateless
    beyond configuration.
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

    def evaluate(
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

        table_prefix = '__senstivity_runner'
        from apsimNGpy.core.mult_cores import MultiCoreManager
        db_path = generate_default_db_path(table_prefix)

        def run_in_multi_core(db):

            with MultiCoreManager(agg_func=agg_func, db_path=db, table_prefix=table_prefix) as mc:
                mc.run_all_jobs(
                    self.job_maker(X),
                    n_cores=n_cores,
                    retry_rate=retry_rate,
                    threads=threads,
                    clear_db=True,
                    display_failures=True,
                    subset=self.outputs
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
        except sqlite3.OperationalError:
            try:
                return run_in_multi_core(db=db_path)
            except PermissionError:
                pass
        finally:
            try:
                Path(db_path).unlink(missing_ok=True)
            except PermissionError:
                pass


def run_sensitivity(
        runner: ConfigProblem,
        *,
        method: str,
        N: int | None = None,
        seed: int | None = 48,
        agg_func: str = "sum",
        n_cores: int = None,
        retry_rate: int = 2,
        threads: bool = False,
        sample_options: dict | None = None,
        analyze_options: dict | None = None,
):
    """
    Run a complete sensitivity analysis.

    Parameters
    ----------
    runner : ConfigProblem
        Configured APSIM–SALib runner.
    method : {"morris", "sobol", "fast"}
        Sensitivity method.
    N : int, optional
        Base sample size. If None, a method-specific default is used.
    seed : int, optional
        Random seed.
    agg_func : str, default="sum"
        Aggregation function for APSIM outputs.
    n_cores : int, default=12
        Number of parallel workers. use 1 to purely run in a single thread or process
    retry_rate : int, default=2
        Number of retries for failed simulations.
    threads : bool, default=False
        Use multithreading instead of multiprocessing.
    sample_options : dict, optional.
        Options forwarded to the SALib sampler. The available options are described in the
        SALib documentation fore each method.
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
    ~~~~~~~~~~~~~~~~~~~~~~~~~~
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
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
       ``analyze_options``, the value is automatically propagated to the other.
"""
    if n_cores is None:
        n_cores = CPU_CORES
    sample_options = sample_options or {}
    analyze_options = analyze_options or {
        "conf_level": 0.95,
        "num_resamples": 1000,
        "print_to_console": True,
    }
    if method == 'sobol':
        # check if "calc_second_order" option is consistently provided and raise
        sample_options, analyze_options = switch_sobol_option(sample_options, analyze_options)

    if N is None:
        try:
            N = default_n(method, runner.num_vars)
        except ValueError:
            N = 100

    evaluate = partial(
        runner.evaluate,
        agg_func=agg_func,
        n_cores=n_cores,
        retry_rate=retry_rate,
        threads=threads,
    )

    sampler = getattr(runner.problem, f"sample_{method}")
    analyzer = getattr(runner.problem, f"analyze_{method}")
    sample_options.setdefault('seed', seed)
    # ---- sample ----
    stp = sampler(N=N, **sample_options)
    stp.evaluate(evaluate)
    analyzer = getattr(stp, f"analyze_{method}")

    # ---- evaluate ----
    # X = stp.samples
    # Y, results = evaluate(X)
    setattr(stp, 'raw_results', runner.raw_results)
    # ---- analyze ----
    return analyzer(**analyze_options)


if __name__ == "__main__":
    params = {
        ".Simulations.Simulation.Field.Sow using a variable rule?Population": (2, 10),
        ".Simulations.Simulation.Field.Fertilise at sowing?Amount": (0, 300),
        ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82?[Leaf].Photosynthesis.RUE.FixedValue": (
            1.2, 2.2),
    }
    runner = ConfigProblem(
        base_model="Maize",
        params=params,
        outputs=["Yield", "Maize.AboveGround.N"],
    )

    Si_morris = run_sensitivity(
        runner,
        method="morris", n_cores=6,
        sample_options={
            'seed': 42,
            "num_levels": 6,
            "optimal_trajectories": 10,
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

    Si_sobol = run_sensitivity(
        runner,
        method="sobol",
        N=2 ** 6,  # ← base sample size
        sample_options={
            "calc_second_order": True,
            #"skip_values": 1024,
            # "seed": 42,
        },
        analyze_options={
            "conf_level": 0.95,
            "num_resamples": 1000,
            "print_to_console": True,
            "calc_second_order": True,
        },
    )
