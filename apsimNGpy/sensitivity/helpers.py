from __future__ import annotations

import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable
from typing import Mapping

from SALib import ProblemSpec

from apsimNGpy.core_utils.database_utils import drop_table, get_db_table_names
from apsimNGpy.settings import logger


def split_apsim_path_by_sep(p: str) -> tuple[str, str]:
    """
    Split APSIM path using the first valid selector separator.

    Supported separators (in order):
    ?, ::, |, @

    Returns
    -------
    (base_path, attribute)
    """
    seps = ("?", "::", "|", "@")
    for sep in seps:
        if sep in p:
            left, right = p.split(sep, 1)
            return left.rstrip("."), right.strip(".")
    raise ValueError(f"Invalid APSIM path: {p}")


def group_candidate_params(params: Iterable[str]) -> dict[str, list[str]]:
    """
    Group APSIM parameters by base path.

    Returns
    -------
    dict[base_path, list[attribute]]
    """
    grouped = defaultdict(list)
    for p in params:
        base, attr = split_apsim_path_by_sep(p)
        grouped[base].append(attr)
    return dict(grouped)


def define_problem(
        params: Mapping[str, tuple[float, float]],
        *,
        names: Iterable[str] | None = None,
        dist: list[str] | None = None,
        groups: list[int] | None = None,
) -> ProblemSpec:
    """
    Create a SALib ProblemSpec in a deterministic and multiprocessing-safe way.

    Parameters
    ----------
    params : mapping
        APSIM parameter path → (lower, upper)
    names : iterable[str], optional
        Explicit parameter names (defaults inferred from APSIM paths)
    dist : list[str], optional
        Parameter distributions (SALib format)
    groups : list[int], optional
        Grouping for grouped sensitivity methods

    Returns
    -------
    ProblemSpec
    """
    if not params:
        raise ValueError("params must not be empty")

    items = tuple(params.items())
    bounds = [b for _, b in items]

    if names is None:
        names = [split_apsim_path_by_sep(p)[1] for p, _ in items]

    if len(names) != len(bounds):
        raise ValueError("names length must match number of parameters")

    problem = {
        "num_vars": len(bounds),
        "names": list(names),
        "bounds": bounds,
    }

    if dist:
        problem["dist"] = dist
    if groups:
        problem["groups"] = groups

    return ProblemSpec(**problem)


def default_n(method: str, n_parameters: int) -> int:
    """
    Determine a reasonable default sample size N.

    Parameters
    ----------
    method : {"morris", "sobol", "fast"}
    n_parameters : int

    Returns
    -------
    int
    """
    method = method.lower()

    if n_parameters <= 0:
        raise ValueError("n_parameters must be > 0")

    if method == "morris":
        return max(10, 4 * n_parameters)

    if method == "sobol":
        # Power-of-two, conservative
        return max(512, 2 ** (n_parameters * 4).bit_length())

    if method in {"fast", "efast"}:
        return max(65, 10 * n_parameters)

    raise ValueError(f"Unknown sensitivity method '{method}'")


def clear_db(
        db_path: str | Path,
        table_prefix: str,
        *,
        ignore_missing_db: bool = True,
) -> dict[str, Any]:
    """
    Clear tables in an SQLite database whose names start with ``table_prefix``.

    Parameters
    ----------
    db_path : str or pathlib.Path
        Path to the SQLite database (must end with ``.db``).
    table_prefix : str
        Only tables whose names begin with this prefix will be cleared.
    ignore_missing_db : bool, optional
        If ``True`` (default), missing databases are treated as a no-op and a
        summary is returned. If ``False``, a missing database raises
        ``FileNotFoundError``.

    Returns
    -------
    dict
        A summary containing:
        - ``db_path``: normalized database path (str)
        - ``prefix``: table prefix used
        - ``cleared``: list of tables cleared
        - ``skipped``: list of tables not matching the prefix
        - ``errors``: list of {"table": <name|None>, "error": <repr>}
        - ``message``: human-readable summary
    """
    db_path = Path(db_path)

    db_path = Path(db_path).with_suffix('.db')

    if not db_path.exists():
        if ignore_missing_db:
            return {
                "db_path": str(db_path),
                "prefix": str(table_prefix),
                "cleared": [],
                "skipped": [],
                "errors": [],
                "message": "Database does not exist; nothing to clear.",
            }
        raise FileNotFoundError(str(db_path))

    try:
        tables: Iterable[str] = get_db_table_names(str(db_path))
    except Exception as e:
        return {
            "db_path": str(db_path),
            "prefix": str(table_prefix),
            "cleared": [],
            "skipped": [],
            "errors": [{"table": None, "error": repr(e)}],
            "message": "Failed to read table names.",
        }

    cleared: list[str] = []
    skipped: list[str] = []
    errors: list[dict[str, str]] = []

    prefix = str(table_prefix)

    for tb in tables:
        if not tb.startswith(prefix):
            skipped.append(tb)
            continue

        try:
            drop_table(str(db_path), tb)
            cleared.append(tb)
        except (PermissionError, FileNotFoundError) as e:
            # PermissionError: DB locked (common on Windows)
            # FileNotFoundError: DB/table deleted concurrently
            errors.append({"table": tb, "error": repr(e)})
        except Exception as e:
            errors.append({"table": tb, "error": repr(e)})

    return {
        "db_path": str(db_path),
        "prefix": prefix,
        "cleared": cleared,
        "skipped": skipped,
        "errors": errors,
        "message": f"Cleared {len(cleared)} table(s) with prefix '{prefix}'.",
    }


def generate_default_db_path(tag=""):
    return f"{tag}{uuid.uuid1()}_.db"


def switch_sobol_option(sample_options, analyze_options):
    s = sample_options.get("calc_second_order", False)
    if s != analyze_options.get("calc_second_order", False):
        logger.warning(f"calc_second_order value in sample_options and analyze_options do not match will harmonize to True for all")
    s, a = s, s
    if not s:  # try see if the other one is true, aim is to default to the best option in analysis
        s, a = analyze_options.get('calc_second_order', False), analyze_options.get('calc_second_order', False)
    analyze_options['calc_second_order'] = a
    sample_options['calc_second_order'] = s
    return dict(sample_options), dict(analyze_options),


if __name__ == '__main__':
    ans = switch_sobol_option(sample_options={'calc_second_order': True}, analyze_options={'calc_second_order': False})
    print(ans)
    ans = switch_sobol_option(sample_options={'calc_second_order': False}, analyze_options={'calc_second_order': False})
    print(ans)
