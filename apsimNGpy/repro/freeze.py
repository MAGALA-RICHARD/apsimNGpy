# apsimNGpy/repro/freeze.py
from __future__ import annotations

import json
import shutil
import hashlib
import platform
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

from apsimNGpy.core.config import (
    get_apsim_bin_path,
    apsim_version,
    locate_model_bin_path
)
from apsimNGpy.starter.starter import _fetch_apsim_version

LOCK_FILENAME = "apsim.lock.json"  # project-local lock
VENDORED_DIR = "bin_dist/frozen_bin"  # project-local vendor target


# ---------- helpers ----------

def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def _is_bin_dir(p: Path) -> Union[bool, str, Path, None]:
    return locate_model_bin_path(p)


def _collect_files(bin_dir: Path, key_only: bool) -> List[Path]:
    """Pick a minimal-but-informative file set for hashing (key_only) or everything."""
    if key_only:
        patterns = ["Models.exe", "Models", "APSIM.Shared.dll", "Models.dll"]
        files = [bin_dir / pat for pat in patterns]
        return [f for f in files if f.exists()]
    # Full hash set (recursively) but skip big caches/logs
    globs = ["**/*"]
    out = []
    for g in globs:
        for f in bin_dir.glob(g):
            if f.is_file() and f.stat().st_size > 0:
                # ignore obvious non-binaries if you want: keep all for robustness
                out.append(f)
    return out


# ---------- lock model ----------

@dataclass
class ApsimBinLock:
    apsim_version: Optional[str]
    os: str
    arch: str
    python: str
    apsimngpy: Optional[str]  # track your package version
    strategy: str  # "reference" or "vendor"
    bin_relpath: str  # relative to project_root (for vendor) or None-ish
    bin_abspath: str  # absolute path to the bin used at freeze time
    files: List[Dict[str, Any]]  # [{"rel": "...", "sha256": "...", "bytes": int}, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @staticmethod
    def from_json(txt: str) -> "ApsimBinLock":
        data = json.loads(txt)
        return ApsimBinLock(**data)


# ---------- core ops ----------

def freeze_apsim_bin(
        project_root: Path = None,
        bin_path: Optional[Path] = None,
        *,
        strategy: str = "reference",  # "reference" | "vendor"
        key_hashes_only: bool = False,
        overwrite_vendor: bool = False,
) -> Path:
    """
    Freeze this project to a specific APSIM NG bin. Ideally a script that will be importing apsimNgpy should be in the
    same directory.

    Parameters
    ----------
    project_root : Path
        Folder where the lock file will be written.
    bin_path : Optional[Path]
        The bin directory to freeze. If None, use `get_apsim_bin_path()`.
    strategy : {"reference","vendor"}
        - "reference": record absolute/relative path + hashes; do not copy files.
        - "vendor": copy the bin directory into the project under bin_dist/frozen_bin/.
    key_hashes_only : bool
        If True, hash a small set of key files; if False, hash all files.
    overwrite_vendor : bool
        If True and strategy="vendor", overwrite an existing vendored folder.

    Returns
    -------
    Path to the written lock file.
    """
    if project_root is None:
        project_root = Path.cwd().resolve()
    project_root = Path(project_root)
    if not project_root.exists():
        raise NotADirectoryError(f"`{project_root}` is not a directory or does not exist")

    if bin_path is None:
        cur = get_apsim_bin_path()
        if not cur:
            raise RuntimeError("No APSIM bin configured and no bin_path provided.")
        bin_path = Path(cur)
    bin_path = Path(bin_path).resolve()
    if not _is_bin_dir(bin_path):
        raise FileNotFoundError(f"Not a valid APSIM bin directory: {bin_path}")

    ver = None
    try:
        ver = apsim_version(bin_path=bin_path)
    except Exception:
        ver = get_apsim_version(bin_path=bin_path)

    # Optional: vendor/copy into project for a fully portable capsule
    if strategy == "vendor":
        target = project_root / VENDORED_DIR
        if target.exists() and overwrite_vendor:
            shutil.rmtree(target, ignore_errors=False)
        if not target.exists():
            shutil.copytree(bin_path, target)
        freeze_dir = target.resolve()
        bin_relpath = str(Path(VENDORED_DIR).as_posix())
        bin_abspath = str(target)
    elif strategy == "reference":
        freeze_dir = bin_path
        # store relpath if inside project; else leave as ""
        try:
            bin_relpath = str(freeze_dir.relative_to(project_root).as_posix())
        except Exception:
            bin_relpath = ""
        bin_abspath = str(_norm(freeze_dir))
    else:
        raise ValueError('strategy must be "reference" or "vendor"')

    # Build file list with hashes
    files_info: List[Dict[str, Any]] = []
    base = _norm(freeze_dir)
    for f in _collect_files(base, key_hashes_only):
        rel = f.relative_to(base).as_posix()
        try:
            h = _sha256(f)
        except Exception:
            h = ""
        files_info.append({"rel": rel, "sha256": h, "bytes": f.stat().st_size})

    lock = ApsimBinLock(
        apsim_version=ver,
        os=platform.system(),
        arch=platform.machine(),
        python=f"{platform.python_implementation()} {platform.python_version()}",
        apsimngpy=None,  # optionally fill from your package __version__
        strategy=strategy,
        bin_relpath=bin_relpath,
        bin_abspath=bin_abspath,
        files=files_info,
    )

    lock_path = project_root / LOCK_FILENAME
    lock_path.write_text(lock.to_json(), encoding="utf-8")
    return lock_path


def verify_apsim_lock(project_root: Path, *, strict: bool = True) -> Dict[str, Any]:
    """
    Verify the current filesystem matches the lock.

    Returns a dict with keys: ok: bool, mismatches: [...], missing: [...], extras: int
    """
    pr = _norm(Path(project_root))
    lock_path = pr / LOCK_FILENAME
    if not lock_path.exists():
        raise FileNotFoundError(f"Lock file not found: {lock_path}")
    lock = ApsimBinLock.from_json(lock_path.read_text(encoding="utf-8"))

    bin_dir = Path(lock.bin_abspath)
    if lock.strategy == "vendor" and lock.bin_relpath:
        cand = pr / lock.bin_relpath
        if cand.exists():
            bin_dir = cand

    if not _is_bin_dir(bin_dir):
        return {"ok": False, "reason": f"bin dir missing/invalid: {bin_dir}"}

    mismatches, missing = [], []
    base = _norm(bin_dir)
    for item in lock.files:
        f = base / item["rel"]
        if not f.exists():
            missing.append(item["rel"])
            continue
        if strict and item["sha256"]:
            now = _sha256(f)
            if now != item["sha256"]:
                mismatches.append(item["rel"])

    ok = (not missing) and (not mismatches)
    return {"ok": ok, "mismatches": mismatches, "missing": missing, "bin_dir": str(base)}
#

# def thaw_apsim_bin(project_root: Path) -> Path:
#     """
#     Reconfigure the current process to use the bin pinned in the lock file.
#     Returns the path set via `set_apsim_bin_path`.
#     """
#     pr = _norm(Path(project_root))
#     lock_path = pr / LOCK_FILENAME
#     if not lock_path.exists():
#         raise FileNotFoundError(f"Lock file not found: {lock_path}")
#     lock = ApsimBinLock.from_json(lock_path.read_text(encoding="utf-8"))
#
#     # Prefer vendored path if present
#     candidate = Path(lock.bin_abspath)
#     if lock.strategy == "vendor" and lock.bin_relpath:
#         cand = pr / lock.bin_relpath
#         if cand.exists():
#             candidate = cand
#
#     if not _is_bin_dir(candidate):
#         raise FileNotFoundError(f"Pinned APSIM bin missing: {candidate}")
#
#     ok = set_apsim_bin_path(candidate)
#     if not ok:
#         raise RuntimeError(f"Failed to set APSIM bin path: {candidate}")
#     return candidate
#
#
# from pathlib import Path
#
# proj = Path(__file__).resolve().parent
#
# # Freeze to the current configured bin (reference only)
# freeze_apsim_bin(proj, strategy="reference")  # writes apsim.lock.json
#
# # OR vendor a copy into the project for a portable capsule
# freeze_apsim_bin(proj, strategy="vendor", overwrite_vendor=True)
#
# # Verify later (CI step)
# print(verify_apsim_lock(proj))  # {'ok': True, 'mismatches': [], 'missing': [], 'bin_dir': '...'}
#
# # Thaw (set process to use locked bin)
# thawed = thaw_apsim_bin(proj)
# print("Using:", thawed)
