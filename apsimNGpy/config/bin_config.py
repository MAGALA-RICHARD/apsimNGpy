import os
import sys
from typing import Tuple
from config import _apsim_model_is_installed
import platform
from apsimNGpy.exceptions import ApsimBinPathConfigError

from pathlib import Path
from typing import Optional, Union


def locate_model_bin_path(bin_path: Union[str, Path], recursive: bool = True) -> Optional[Path]:
    """
    Search for a directory that contains APSIM binaries.

    A 'match' is any directory containing:
      - On Windows: Models.dll and Models.exe
      - On Mac/Linux: Models.dll and Models

    Returns the first matching directory found (depth-first), or None if not found.
    """
    bin_path = Path(bin_path).resolve()

    if not bin_path.exists() or not bin_path.is_dir():
        raise FileNotFoundError(f"{bin_path} is not a directory")

    # Helper to check if this dir has APSIM binaries
    def has_models(path: Path) -> bool:
        if platform.system() == "Windows":
            return (path / "Models.dll").exists() and (path / "Models.exe").exists()
        else:
            return (path / "Models.dll").exists() and (path / "Models").exists()

    # Check the provided directory
    if has_models(bin_path):
        return bin_path

    # Optionally search subdirectories
    if recursive:
        for root, dirs, _ in os.walk(bin_path):
            for d in dirs:
                subdir = Path(root) / d
                if has_models(subdir):
                    return subdir

    return None


def _normalize_bin_path(bin_path: Optional[Path]) -> Path:
    """Resolve the real APSIM bin path or raise a clear error."""
    # 1) Accept None -> try envs
    if bin_path is None:
        env_candidates = {
            os.getenv("APSIM_BIN_PATH"),
            os.getenv("APSIM_PATH"),
            os.getenv("APSIM"),
            os.getenv('Models')
        }
        for c in env_candidates:
            if c:
                bin_path = Path(c)
                break

    if bin_path is None:
        raise ApsimBinPathConfigError(
            "APSIM bin path not provided and not found in environment variables "
            "(APSIM_BIN_PATH / APSIM_PATH / APSIM)."
        )

    return bin_path


def _required_assemblies(bin_path: Path, file_format_modified: bool) -> Tuple[Path, Optional[Path]]:
    models = bin_path / "Models.dll"
    apsim_core = (bin_path / "APSIM.Core.dll") if file_format_modified else None

    missing = [p for p in [models, apsim_core] if p is not None and not p.exists()]
    if missing:
        missing_list = "\n  - " + "\n  - ".join(str(m) for m in missing)
        raise FileNotFoundError(
            "Missing required APSIM assemblies:" + missing_list +
            "\nCheck that your APSIM installation is correct and that you are pointing to the *bin* directory."
        )
    return models, apsim_core


def _ensure_sys_path(bin_path: Path) -> None:
    # Idempotent: only add if not present (case-insensitive on Windows)
    paths_norm = [Path(p).resolve() for p in sys.path if isinstance(p, str)]
    if bin_path not in paths_norm:
        sys.path.append(str(bin_path))


def _is_pythonnet_loaded() -> bool:
    return "clr" in sys.modules


def _load_pythonnet_runtime() -> None:
    """
    Try loading pythonnet runtime robustly:
    1) pythonnet.load("coreclr")
    2) pythonnet.load("mono")
    3) fallback to just importing clr
    """
    try:
        from pythonnet import load as py_load  # type: ignore
        try:
            py_load("coreclr")
            return
        except Exception:
            try:
                py_load("mono")
                return
            except Exception:
                # Fall through to clr import
                pass
    except Exception:
        # pythonnet < 3 or not available; hope clr is importable
        pass

    # At this point, either pythonnet is old or runtime already active.
    # Importing clr may still succeed if runtime is available.
    import clr  # noqa: F401
