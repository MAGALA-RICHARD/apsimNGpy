"""
Seperated from config because every time we specify a new temporally
bin path we need to reload pythonnet,yet pythonnet_config was importing from config module
"""
from __future__ import annotations

import configparser
import logging
import os
from contextlib import AbstractContextManager
from pathlib import Path
from apsimNGpy.core.config import configuration
from dotenv import load_dotenv
from apsimNGpy.bin_loader.resources import remove_bin_from_syspath
from apsimNGpy.core.pythonet_config import load_pythonnet
logger = logging.getLogger(__name__)

# Load a default .env if present (optional)
load_dotenv()

HOME_DATA = Path.home().joinpath('AppData', 'Local', 'Programs')
cdrive = os.environ.get('PROGRAMFILES')
CONFIG = configparser.ConfigParser()


class apsim_bin_context(AbstractContextManager):
    """
        Temporarily configure the APSIM-NG *bin* path used by ``apsimNGpy`` so imports
        (e.g., ``ApsimModel``) can resolve APSIM .NET assemblies. Restores the previous
        configuration on exit.

        Parameters
        ----------
        apsim_bin_path : str | os.PathLike | None, optional
            Explicit path to the APSIM ``bin`` directory (e.g.,
            ``C:/APSIM/2025.05.1234/bin`` or ``/opt/apsim/2025.05.1234/bin``).
            Used if no valid value is resolved from ``dotenv_path``.
        dotenv_path : str | os.PathLike | None, optional
            Path to a ``.env`` file to load *before* resolution. If provided, the
            manager will read (in order): ``bin_key`` (if non-empty), then
            ``APSIM_BIN_PATH``, then ``APSIM_MODEL_PATH`` from that file.
        bin_key : str, default ''
            Custom environment variable name to read from the loaded ``.env``
            (e.g., ``"APSIM_BIN_PATH_2025"``). Ignored when empty.
        timeout : float, default 0.003
            Small sleep (seconds) after setting the bin path to avoid races with
            immediate imports on some filesystems. Set to 0 to disable.

        Returns
        -------
        None
            The context manager returns ``None``; import within the ``with`` block.

        Raises
        ------
        ValueError
            If no path can be resolved from ``dotenv_path``, ``apsim_bin_path``,
            or the process environment.
        FileNotFoundError
            If the resolved path does not exist.

        Notes
        -----
        - Python.NET assemblies cannot be unloaded from a running process; this
          context only restores path configuration for **future** imports.
        - Do not nest this context across threads; the underlying config is global.

        Examples
        --------
        Use an explicit path::

           with apsim_bin_context(r"C:/APSIM/2025.05.1234/bin"):
             from apsimNGpy.core.apsim import ApsimModel
             model = ApsimModel(...)

        Use a .env file with a custom key::

            from pathlib import Path
            with apsim_bin_context(dotenv_path=Path(".env"), bin_key="APSIM_BIN_PATH"):
                 from apsimNGpy.core.apsim import ApsimModel

       If you have .env files located in the root of your script::

         with apsim_bin_context():
             from apsimNGpy.core.apsim import ApsimModel

        Verify restoration::

            prev = get_apsim_bin_path()
            with apsim_bin_context(r"C:/APSIM/X.Y.Z/bin"):

            assert get_apsim_bin_path() == prev

      added in v0.39.10.20+
        """

    def __init__(
            self,
            apsim_bin_path: str | os.PathLike | None = None,
            dotenv_path: str | os.PathLike | None = None,
            bin_key: str = '',

    ) -> None:
        bin_path: str | None = None

        # If a specific .env path is provided, load it first
        if dotenv_path is not None:
            dp = Path(dotenv_path)
            if dp.exists() and os.path.realpath(dp).endswith('.env'):
                load_dotenv(os.path.realpath(dp.resolve()))
            else:
                if dotenv_path is not None:
                    raise FileNotFoundError(f"dotenv_path does not exist or it is invalid .env file: {dp}")
            # Try env vars from that .env
            bin_path = os.getenv(bin_key) or os.getenv("APSIM_BIN_PATH") or os.getenv("APSIM_MODEL_PATH")

        # If no .env bin found, fall back to explicit arg
        if bin_path is None and apsim_bin_path is not None:
            bin_path = os.path.realpath(Path(apsim_bin_path).resolve())

        # If still none, try already-loaded env (from top-level load_dotenv)
        if bin_path is None:
            bin_path = os.getenv("APSIM_BIN_PATH") or os.getenv("APSIM_MODEL_PATH")

        if not bin_path:
            raise ValueError(
                "APSIM bin path not provided. Pass `apsim_bin_path=` or set "
                "APSIM_BIN_PATH / APSIM_MODEL_PATH via environment/.env."
            )

        # Optional: check the path exists
        p = Path(bin_path)
        if not p.exists():
            raise FileNotFoundError(f"APSIM bin path not found: {p}")

        self.bin_path = os.path.realpath(p)

    def __enter__(self):

        # Save and set
        configuration.set_temporal_bin_path(self.bin_path)
        # loading pythonnet and adding the bin path to sys.path
        self.bin_env = load_pythonnet(bin_path=configuration.bin_path)
        return self

    def __exit__(self, exc_type, exc, tb):
        # Restore previous paths (even if it was None/empty)
        configuration.release_temporal_bin_path()
        return self  # do not suppress exceptions


if __name__ == "__main__":
    # -------- Example usage --------
    from unittest import TestCase
    print(configuration.bin_path)
    before = configuration.bin_path

    with apsim_bin_context(apsim_bin_path=r"C:\Users\rmagala\AppData\Local\Programs\APSIM2025.12.7939.0\bin") as bin:
        after =configuration.bin_path
        print(after)
        import Models
    assert before != after, 'bin path not set correctly'
    class TestConfig(TestCase):
        def setUp(self):
            pass

        def test_no_bin_path(self):
            with self.assertRaises(ValueError):
                dot_ev_path = None
                with apsim_bin_context(dotenv_path=dot_ev_path):
                    pass

        def test_no_dot_ev_path(self):
            with self.assertRaises(FileNotFoundError):
                with apsim_bin_context(dotenv_path="dot_ev_path"):
                    pass
