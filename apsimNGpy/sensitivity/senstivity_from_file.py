from __future__ import annotations

import gc
from contextlib import suppress
from pathlib import Path
from typing import Iterable, Iterator, Sequence

import numpy as np
import pandas as pd
from SALib.util.problem import ProblemSpec
from sqlalchemy import create_engine

from apsimNGpy import is_scalar
from apsimNGpy.core.experiment import create_experiment_from_file
from apsimNGpy.core_utils.database_utils import read_db_table
from apsimNGpy.sensitivity.evaluate_salib import evaluate_sensitivity
from apsimNGpy.sensitivity.fstr import format_salib_results
from apsimNGpy.sensitivity.helpers import default_n, generate_default_db_path
from apsimNGpy.sensitivity.salib_sample import generate_samples
from apsimNGpy.settings import logger
from core_utils.database_utils import dispose

__all__ = ["ConfigProblem", "run_sensitivity"]

_RESULT_TABLE = "__sensitivity_results__"
_FACTOR_FILE_STEM = "__sensitivity_factors__"


def _as_list(value):
    """Return a scalar as a one-item list and preserve list-like values."""
    if value is None:
        return []
    return [value] if is_scalar(value) else list(value)


def _build_problem(
    parameters: dict[str, Sequence[float]],
    *,
    names: Iterable[str] | None = None,
    groups: Sequence[str | int] | None = None,
    distributions: Sequence[str] | None = None,
) -> ProblemSpec:
    """Create and validate a SALib ``ProblemSpec``."""
    if not parameters:
        raise ValueError("At least one sensitivity parameter is required.")

    parameter_names = list(names) if names is not None else list(parameters)
    bounds = list(parameters.values())

    if len(parameter_names) != len(bounds):
        raise ValueError(
            "The number of parameter names must equal the number of bounds."
        )

    problem = {
        "num_vars": len(bounds),
        "names": parameter_names,
        "bounds": bounds,
    }

    if groups is not None:
        problem["groups"] = list(groups)
    if distributions is not None:
        problem["dists"] = list(distributions)

    return ProblemSpec(**problem)


def _iter_batches(
    matrix: np.ndarray,
    sample_ids: np.ndarray,
    batch_size: int | None,
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Yield sample batches while preserving their original sample IDs."""
    if batch_size is None or batch_size >= len(matrix):
        yield matrix, sample_ids
        return

    if batch_size < 1:
        raise ValueError("batch_size must be at least 1.")

    for start in range(0, len(matrix), batch_size):
        stop = start + batch_size
        yield matrix[start:stop], sample_ids[start:stop]


class ConfigProblem:
    """Configure and evaluate an APSIM-SALib sensitivity problem.

    Parameters
    ----------
    base_model
        APSIM model path, model identifier, or another value accepted by
        :func:`create_experiment_from_file`.
    params
        Mapping of APSIM ``FactorFromFile`` property paths to SALib bounds.
        Each bound is normally a two-item sequence ``(lower, upper)``.
    outputs
        APSIM output columns to analyze.
    names
        Optional SALib parameter names. When omitted, the APSIM property paths
        are used as the names.
    dist
        Optional SALib probability distribution names.
    groups
        Optional SALib parameter groups.
    index_id
        Name of the factor-file column that uniquely identifies every sample.
    """

    def __init__(
        self,
        base_model: str | Path,
        params: dict[str, Sequence[float]],
        outputs: str | Sequence[str],
        *,
        names: Iterable[str] | None = None,
        dist: Sequence[str] | None = None,
        groups: Sequence[str | int] | None = None,
        index_id: str = "FactorFromFile",
    ) -> None:
        self.base_model = base_model
        self.params = dict(params)
        self.param_keys = list(self.params)
        self.outputs = _as_list(outputs)
        self.index_id = index_id
        self.num_vars = len(self.param_keys)

        if not self.outputs:
            raise ValueError("At least one APSIM output must be specified.")
        if not isinstance(index_id, str) or not index_id.strip():
            raise ValueError("index_id must be a non-empty string.")

        self.problem = _build_problem(
            self.params,
            names=names,
            groups=groups,
            distributions=dist,
        )

        self.X: np.ndarray | None = None
        self.raw_results: pd.DataFrame | None = None
        self.incomplete_jobs: list[int] = []

    def create_factor_table(
        self,
        X: np.ndarray,
        *,
        sample_ids: Sequence[int] | None = None,
    ) -> pd.DataFrame:
        """Create an APSIM ``FactorFromFile`` table from a sample matrix."""
        matrix = np.asarray(X, dtype=float)

        if matrix.ndim != 2:
            raise ValueError(f"X must be two-dimensional; got {matrix.shape}.")
        if matrix.shape[1] != self.num_vars:
            raise ValueError(
                f"X has {matrix.shape[1]} columns, but the problem defines "
                f"{self.num_vars} parameters."
            )

        if sample_ids is None:
            ids = np.arange(1, len(matrix) + 1, dtype=np.int64)
        else:
            ids = np.asarray(sample_ids)
            if len(ids) != len(matrix):
                raise ValueError("sample_ids and X must contain the same rows.")

        factor_table = pd.DataFrame(matrix, columns=self.param_keys)
        factor_table[self.index_id] = ids.astype(str)
        return factor_table

    def write_factor_file(
        self,
        X: np.ndarray,
        file_name: str | Path,
        *,
        sample_ids: Sequence[int] | None = None,
    ) -> Path:
        """Write a sample matrix as an APSIM-compatible CSV factor file."""
        path = Path(file_name).with_suffix(".csv").resolve()
        table = self.create_factor_table(X, sample_ids=sample_ids)
        table.to_csv(path, index=False)
        return path

    def _run_factor_batch(
        self,
        X: np.ndarray,
        sample_ids: np.ndarray,
        *,
        database_engine,
    ) -> pd.DataFrame:
        """Run one APSIM factor-file batch and append its results to SQLite."""
        factor_path = self.write_factor_file(
            X,
            _FACTOR_FILE_STEM,
            sample_ids=sample_ids,
        )

        try:
            model = create_experiment_from_file(
                model=self.base_model,
                experiment_from_file=factor_path,
                name_column=self.index_id,
            )

            with model:
                model.run()
                results = model.results.copy()

            if self.index_id not in results.columns:
                raise KeyError(
                    f"APSIM results do not contain the sample ID column "
                    f"{self.index_id!r}."
                )

            results.to_sql(
                name=_RESULT_TABLE,
                con=database_engine,
                if_exists="append",
                index=False,
            )
            return results
        finally:
            with suppress(PermissionError, FileNotFoundError):
                factor_path.unlink()

    def _collect_results(
        self,
        X: np.ndarray,
        *,
        batch_size: int | None,
        retry_rate: int,
        tables: Sequence[str] | None,
    ) -> pd.DataFrame:
        """Run all samples, retry missing samples, and return merged results."""
        db_path = Path(generate_default_db_path("__sens__")).resolve()
        dispose(db_path)
        database_engine = create_engine(f"sqlite:///{db_path}")

        sample_ids = np.arange(1, len(X) + 1, dtype=np.int64)

        try:
            for batch, batch_ids in _iter_batches(X, sample_ids, batch_size):
                self._run_factor_batch(
                    batch,
                    batch_ids,
                    database_engine=database_engine,
                )

            results = read_db_table(db_path, _RESULT_TABLE)

            if tables and "source_table" in results.columns:
                results = results.loc[results["source_table"].isin(tables)].copy()

            missing = self._missing_ids(results, sample_ids)
            attempts = 0

            while missing and attempts < retry_rate:
                attempts += 1
                logger.warning(
                    "Rerunning %s incomplete APSIM samples (attempt %s/%s).",
                    len(missing),
                    attempts,
                    retry_rate,
                )

                positions = np.asarray(missing, dtype=np.int64) - 1
                self._run_factor_batch(
                    X[positions],
                    np.asarray(missing, dtype=np.int64),
                    database_engine=database_engine,
                )
                results = read_db_table(db_path, _RESULT_TABLE)
                if tables and "source_table" in results.columns:
                    results = results.loc[
                        results["source_table"].isin(tables)
                    ].copy()
                missing = self._missing_ids(results, sample_ids)

            self.incomplete_jobs = missing
            if missing:
                raise RuntimeError(
                    f"{len(missing)} APSIM samples remained incomplete after "
                    f"{retry_rate} retries: {missing[:20]}"
                )

            factors = self.create_factor_table(X, sample_ids=sample_ids)
            results[self.index_id] = results[self.index_id].astype(str)
            merged = results.merge(factors, on=self.index_id, how="inner")
            merged.sort_values(self.index_id, inplace=True)
            self.raw_results = merged.reset_index(drop=True)
            return self.raw_results
        finally:
            database_engine.dispose()
            with suppress(PermissionError, FileNotFoundError):
                db_path.unlink()

    def _missing_ids(
        self,
        results: pd.DataFrame,
        expected_ids: Sequence[int],
    ) -> list[int]:
        """Return expected sample IDs absent from APSIM results."""
        if results.empty or self.index_id not in results.columns:
            return list(map(int, expected_ids))

        completed = set(results[self.index_id].astype(str))
        return [
            int(sample_id)
            for sample_id in expected_ids
            if str(sample_id) not in completed
        ]

    def _prepare_group(
        self,
        data: pd.DataFrame,
        *,
        X: np.ndarray,
        aggregation: str | None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Aggregate, order, and align one result group with the SALib matrix."""
        required = [self.index_id, *self.outputs]

        missing_columns = [column for column in required if column not in data]
        if missing_columns:
            raise KeyError(f"Missing result columns: {missing_columns}")

        clean = data.dropna(subset=self.outputs).copy()
        clean[self.index_id] = clean[self.index_id].astype(int)

        if aggregation is None:
            duplicates = clean.duplicated(self.index_id, keep=False)
            if duplicates.any():
                raise ValueError(
                    "Multiple APSIM rows exist per sample. Specify agg_func or "
                    "provide grouping columns that yield one row per sample."
                )
            summarized = clean.set_index(self.index_id)
        else:
            summarized = clean.groupby(self.index_id, sort=True)[self.outputs].agg(
                aggregation
            )

        expected_ids = np.arange(1, len(X) + 1, dtype=np.int64)
        summarized = summarized.reindex(expected_ids)

        if summarized[self.outputs].isna().any().any():
            absent = summarized.index[
                summarized[self.outputs].isna().any(axis=1)
            ].tolist()
            raise ValueError(
                f"Missing or invalid outputs for sample IDs: {absent[:20]}"
            )

        return X.copy(), summarized[self.outputs].to_numpy(dtype=float)

    def evaluate(
        self,
        X: np.ndarray,
        *,
        agg_func: str | None = "sum",
        retry_rate: int = 2,
        chunk_size: int | None = None,
        grouping: str | Sequence[str] | None = None,
        tables: Sequence[str] | None = None,
        n_cores: int = -2,
        threads: bool = False,
        engine: str = "python",
        total_chunks: int = 10,
    ) -> Iterator[tuple[object, np.ndarray, np.ndarray]]:
        """Evaluate a supplied SALib sample matrix with APSIM.

        ``n_cores``, ``threads``, ``engine``, and ``total_chunks`` are retained
        for API compatibility. The FactorFromFile implementation runs each
        generated experiment through ``ApsimModel.run``.
        """
        del n_cores, threads, engine, total_chunks

        matrix = np.asarray(X, dtype=float)
        self.X = matrix
        results = self._collect_results(
            matrix,
            batch_size=chunk_size,
            retry_rate=retry_rate,
            tables=tables,
        )

        grouping_columns = _as_list(grouping)
        if grouping_columns:
            for key, group in results.groupby(grouping_columns, dropna=False):
                XX, Y = self._prepare_group(
                    group,
                    X=matrix,
                    aggregation=agg_func,
                )
                yield key, XX, Y
        else:
            XX, Y = self._prepare_group(
                results,
                X=matrix,
                aggregation=agg_func,
            )
            yield agg_func, XX, Y


def run_sensitivity(
    configured_prob: ConfigProblem,
    *,
    method: str = "morris",
    N: int | None = None,
    seed: int | None = 48,
    agg_func: str | None = "sum",
    n_cores: int = -2,
    retry_rate: int = 3,
    threads: bool = False,
    sample_options: dict | None = None,
    analyze_options: dict | None = None,
    engine: str = "python",
    chunk_size: int | None = None,
    grouping: str | Sequence[str] | None = None,
    tables: Sequence[str] | None = None,
    total_chunks: int = 10,
) -> pd.DataFrame:
    """Run APSIM and calculate Morris, FAST, or Sobol sensitivity indices."""
    method = method.lower()
    if method not in {"morris", "fast", "sobol"}:
        raise NotImplementedError(
            f"Sensitivity method {method!r} is not supported."
        )

    sample_options = dict(sample_options or {})
    analyze_options = dict(analyze_options or {})
    sample_options.setdefault("seed", seed)
    analyze_options.setdefault("conf_level", 0.95)
    analyze_options.setdefault("num_resamples", 1_000)
    analyze_options.setdefault("print_to_console", True)

    if method == "sobol":
        sample_second_order = sample_options.setdefault(
            "calc_second_order", False
        )
        analyze_second_order = analyze_options.setdefault(
            "calc_second_order", False
        )
        if sample_second_order != analyze_second_order:
            raise ValueError(
                "Sobol sampling and analysis must use the same "
                "calc_second_order value."
            )

    if N is None:
        try:
            N = default_n(method, configured_prob.num_vars)
        except ValueError:
            N = 100

    X = generate_samples(
        configured_prob,
        N=N,
        method=method,
        **sample_options,
    )

    frames = configured_prob.evaluate(
        X,
        agg_func=agg_func,
        retry_rate=retry_rate,
        chunk_size=chunk_size,
        grouping=grouping,
        tables=tables,
        n_cores=n_cores,
        threads=threads,
        engine=engine,
        total_chunks=total_chunks,
    )

    analyzed: list[pd.DataFrame] = []
    grouping_columns = _as_list(grouping)

    try:
        for group_key, XX, Y_matrix in frames:
            local_options = dict(analyze_options)
            local_options["X"] = XX

            for output_index, output_name in enumerate(configured_prob.outputs):
                Y = Y_matrix[:, output_index]
                indices = evaluate_sensitivity(
                    configured_prob,
                    method=method,
                    Y=Y,
                    **local_options,
                )
                result = format_salib_results(indices, method, output_name)
                result['X'] = configured_prob.param_keys

                if grouping_columns:
                    keys = (
                        group_key
                        if isinstance(group_key, tuple)
                        else (group_key,)
                    )
                    for column, value in zip(grouping_columns, keys):
                        result[column] = value

                analyzed.append(result)

        if not analyzed:
            raise RuntimeError("Sensitivity analysis produced no results.")

        return pd.concat(analyzed, ignore_index=True)
    finally:
        gc.collect()


if __name__ == "__main__":
    # Example: assess management sensitivity rather than the maize RUE example
    # used in the package documentation.
    problem = ConfigProblem(
        base_model="Maize",
        params={
            "[Sow using a fixed date].Script.Population": (2, 12),
            "[Fertilise at sowing].Script.Amount": (0.0, 180.0),
            '[Maize].Leaf.Photosynthesis.RUE.FixedValue': (1,3)

        },
        outputs=["Yield", 'Maize.AboveGround.Wt'],
    )

    sensitivity = run_sensitivity(
        problem,
        method="sobol",
        N=120,
        agg_func="mean",
        chunk_size=100,
        retry_rate=2,
        tables=["Report"],
        sample_options={
            "num_levels": 6,
            "optimal_trajectories": 10,
        },
        analyze_options={
            "num_resamples": 500,
            "print_to_console": False,
        },
    )

    print(sensitivity)
