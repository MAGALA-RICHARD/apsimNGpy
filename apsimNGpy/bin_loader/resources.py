import os
from typing import Union

from apsimNGpy.exceptions import ApsimBinPathConfigError
from pathlib import Path
import sys

AUTO = object()


def add_bin_to_syspath(bin_path: Path) -> None:
    if not bin_path:
        raise ApsimBinPathConfigError(f'Can not proceed to load pythonnet invalid bin path: {bin_path}')
    # Idempotent: only add if not present (case-insensitive on Windows)
    bin_path = Path(bin_path).resolve()
    paths_norm = [Path(p).resolve() for p in sys.path if isinstance(p, str)]
    if bin_path not in paths_norm:
        sys.path.append(os.path.realpath(bin_path))

import os
import sys
from pathlib import Path


def remove_bin_from_syspath(bin_path: Path) -> None:
    """
    Remove an APSIM bin path from sys.path if present.
    Safe to call multiple times (idempotent).
    """
    if not bin_path:
        raise ApsimBinPathConfigError(
            f"Cannot proceed: invalid bin path: {bin_path}"
        )

    bin_path = Path(bin_path).resolve()

    sys.path[:] = [
        p for p in sys.path
        if not (
            isinstance(p, str)
            and Path(p).resolve() == bin_path
        )
    ]


def is_file_format_modified(bin_path: Union[str, Path]) -> bool:
    """
    Checks if the APSIM.CORE.dll is present in the bin path. Normally, the new APSIM version has this dll file.

    Parameters
    ---------
    bin_path: Union[str, Path, None].
         Default is the current bin_path for apsimNGpy, used only when bin_path is None.

    :returns:
      bool
    """
    bp = Path(bin_path)
    patterns = {"*APSIM.CORE.dll", "*APSIM.Core.dll"}
    path = []
    for pat in patterns:
        path.extend(Path(bp).rglob(pat))
    if len(path) > 0:
        return True
    return False

