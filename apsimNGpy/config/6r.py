import platform
from pathlib import Path
from typing import Optional

from config.bin_config import _normalize_bin_path, _ensure_sys_path, _required_assemblies, _is_pythonnet_loaded, \
    _load_pythonnet_runtime


def load_pythonnet(bin_path: Optional[Path] = None):
    """
    Initialize pythonnet and load APSIM assemblies from `bin_path`.

    Parameters
    ----------
    bin_path : Optional[pathlib.Path or str]
        Path to APSIM `bin` directory, or install root (in which case `bin` is auto-detected).
        If None, tries environment variables: APSIM_BIN_PATH, APSIM_PATH, APSIM.
    require_core : bool
        If True, require APSIM.Core.dll to be present and loaded (i.e., for modified file formats).

    Returns
    -------
    dict
        A small info dict with resolved paths and runtime hints.

    Raises
    ------
    ApsimBinPathConfigError
        If the bin path is missing/invalid.
    FileNotFoundError
        If required assemblies are missing.
    ImportError
        If pythonnet/clr cannot be imported.
    """

    # 1) Normalize/Resolve path
    bin_path = _normalize_bin_path(bin_path)

    # 2) Add to sys.path (idempotent)
    _ensure_sys_path(bin_path)

    # 4) Check that required assemblies exist
    models_dll, apsim_core_dll = _required_assemblies(bin_path, True)

    # 5) Load pythonnet runtime (idempotent if already loaded)
    if not _is_pythonnet_loaded():
        _load_pythonnet_runtime()

    # 6) Add assembly references by absolute path to avoid name resolution issues
    import clr  # now safe
    try:
        clr.AddReference(str(models_dll))
    except Exception as e:
        raise ImportError(
            f"Failed to load Models.dll from: {models_dll}\n"
            f"Python: {platform.python_version()} | Arch: {platform.architecture()[0]} | "
            f"OS: {platform.system()} {platform.release()}\n"
            "Ensure your Python architecture matches the APSIM/.NET build (e.g., both 64-bit)."
        ) from e

    if file_format_modified and apsim_core_dll is not None:
        try:
            clr.AddReference(str(apsim_core_dll))
        except Exception as e:
            raise ImportError(
                f"Failed to load APSIM.Core.dll from: {apsim_core_dll}\n"
                "If you don’t need modified file formats, call load_pythonnet(..., require_core=False)."
            ) from e

    # 7) Optionally add standard .NET libs if you need them
    try:
        clr.AddReference("System")
    except Exception:
        # Non-fatal: some environments don’t need this
        pass

    return {
        "bin_path": str(bin_path),
        "models_dll": str(models_dll),
        "apsim_core": str(apsim_core_dll) if apsim_core_dll else None,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "python": platform.python_version(),
            "arch": platform.architecture()[0],
        },
        "file_format_modified": file_format_modified,
        "pythonnet_loaded": True,
    }
