# release.py
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

VERSION = '0.39.8.14'


def run(cmd, check=True):
    print(f"\n>>> {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check)
    return result.returncode


def ensure_tool(mod_name: str, pip_name: str = None):
    """Ensure a Python module is importable; if not, install it with pip."""
    pip_name = pip_name or mod_name
    try:
        __import__(mod_name)
    except ImportError:
        print(f"Installing {pip_name}...")
        run([sys.executable, "-m", "pip", "install", "-U", pip_name])


def main():
    parser = argparse.ArgumentParser(description="Build and release package.")
    parser.add_argument(
        "--test", action="store_true",
        help="Upload to TestPyPI instead of PyPI."
    )
    parser.add_argument(
        "--no-upload", action="store_true",
        help="Only build the package; do not upload."
    )
    parser.add_argument(
        "--version", default=VERSION,
        help="Override APSIM_VERSION (otherwise read from .env or env)."
    )
    # parser.add_argument(
    #     "--constants-script", default=str(ROOT / "tools" / "generate_build_constants.py"),
    #     help="Path to the script that writes _build_constants.py"
    # )
    args = parser.parse_args()

    # Ensure tools
    ensure_tool("build")
    ensure_tool("twine")
    ensure_tool("dotenv", "python-dotenv")

    # Optionally override APSIM_VERSION for this run
    if args.version:
        os.environ["APSIM_VERSION"] = args.version
        print(f"APSIM_VERSION overridden to: {args.version}")

    # Clean old dist
    dist = ROOT / "dist"
    if dist.exists():
        for p in dist.iterdir():
            p.unlink()
    else:
        dist.mkdir(parents=True, exist_ok=True)

    # Build
    run([sys.executable, "-m", "build"])

    # Upload (optional)
    if not args.no_upload:
        repo = "testpypi" if args.test else "pypi"
        print(f"Uploading to {repo}...")
        run([sys.executable, "-m", "twine", "upload", "--repository", repo, "dist/*"])
    else:
        print("Build complete. Skipping upload (per --no-upload).")


if __name__ == "__main__":
    main()
