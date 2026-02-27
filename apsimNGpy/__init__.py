# """
# This module does not directly import from `apsimNGpy.core` or `apsimNGpy.starter`
# to avoid errors when PythonNet is not configured or the APSIM binary path is unset.
#
# Instead, it uses `Apsim` class to lazily load and attach the following objects:
#
# - ApsimModel (apsimNGpy.core.apsim)
# - MultiCoreManager (apsimNGpy.core.mult_cores)
# - run_apsim_by_path (apsimNGpy.core.runner)
# - run_sensitivity (apsimNGpy.sensitivity.sensitivity)
# - ConfigProblem (apsimNGpy.sensitivity.sensitivity)
# - ExperimentManager (apsimNGpy.core.experiment)
# - SensitivityManager (apsimNGpy.core.sensitivitymanager)
# """
import os
from pathlib import Path

from apsimNGpy.config import (set_apsim_bin_path, get_apsim_bin_path, path_checker,
                              apsim_bin_context, load_crop_from_disk, configuration, start_pythonnet, DLL_DIR,
                              Configuration, locate_model_bin_path, scan_dir_for_bin, auto_detect_apsim_bin_path)
from apsimNGpy.logger import logger
from apsimNGpy.parallel.process import custom_parallel
from apsimNGpy.core_utils.utils import is_scalar, timer
from apsimNGpy.exceptions import ApsimRuntimeError, NodeNotFoundError, TableNotFoundError, CastCompilationError

_AutoBin = object()


# define the run time objects inside a callable class
# that way even if the APSIM bin configuration is not set packages errors do not affect entry point
# this is a refactoring class, I did not want to reconfigure apsim_bin-context
class Apsim:
    # see apsim_bin_context doc string
    """
   Lazy loader for APSIM modules dependent on .NET environment and a valid APSIM bin path.

   Avoids direct imports from `apsimNGpy.core` and `apsimNGpy.starter`
   until PythonNet and the APSIM binary are configured.

   After initialization, the following objects are loaded
   ApsimModel, MultiCoreManager, run_apsim_by_path,
   run_sensitivity, ConfigProblem,
   ExperimentManager, SensitivityManager.
   """

    def __init__(self, apsim_bin_path=_AutoBin, dotenv_path=None, bin_key=None):
        """
        Temporarily configure the APSIM-NG ``bin`` path used by ``apsimNGpy``

        Parameters
        ----------
        apsim_bin_path : str or os.PathLike or None, optional
            Explicit path to the APSIM ``bin`` directory
            (e.g., ``C:/APSIM/2025.05.1234/bin`` or
            ``/opt/apsim/2025.05.1234/bin``).

            If ``None`` (default), path on disk from config.ini file is used via get_apsim_bin_path method.

        dotenv_path : str or os.PathLike or None, optional
            Path to a ``.env`` file to load *before* resolution. expected key is "APSIM_BIN_PATH" or "APSIM_MODEL_PATH", or explicitly provided through `bin_key`

        bin_key : str, optional
            Custom environment variable name to read from the loaded ``.env``
            file (e.g., ``"APSIM_BIN_PATH_2025"``). Ignored when empty.
            Default is ``""``.

        Returns
        -------
        object
            A runtime context exposing the following ``apsimNGpy`` attributes:

            - ``ApsimModel`` from ``apsimNGpy.core.apsim``
            - ``MultiCoreManager`` from ``apsimNGpy.core.mult_cores``
            - ``run_apsim_by_path`` from ``apsimNGpy.core.runner``
            - ``run_sensitivity`` from ``apsimNGpy.sensitivity.sensitivity``
            - ``ConfigProblem`` from ``apsimNGpy.sensitivity.sensitivity``
            - ``ExperimentManager`` from ``apsimNGpy.core.experiment``
            - ``SensitivityManager`` from ``apsimNGpy.core.sensitivitymanager``

        Raises
        ------
        ValueError
            If no APSIM ``bin`` path can be resolved from ``dotenv_path``,
            ``apsim_bin_path``, or the process environment.

        FileNotFoundError
            If the resolved path does not exist.

        Notes
        -----
        - Python.NET assemblies cannot be unloaded from a running process.
          This context only restores path configuration for **future imports**.
        - Do not nest this context across different bin paths in the same script; the underlying configuration
          is process-global.

        Examples
        --------
        Use an explicit path::

            with Apsim(r"C:/APSIM/2025.05.1234/bin") as apsim:
                model = apsim.ApsimModel("Wheat")

        Use a ``.env`` file with a custom key::

            from pathlib import Path

            with Apsim(dotenv_path=Path(".env",
                bin_key="APSIM_BIN_PATH") as apsim:
                model =apsim.ApsimModel('Wheat")

        Use automatic resolution (``.env`` in project root)::

            with Apsim() as apsim:
                 model =apsim.ApsimModel('Wheat")

        Verify restoration::

            prev = get_apsim_bin_path()

            with apsim_bin_context(r"C:/APSIM/X.Y.Z/bin"):
                pass

            assert get_apsim_bin_path() != prev

        .. versionadded:: 0.39.10.20

        """
        self._previous = configuration.bin_path
        # Case 1: Explicit APSIM path provided
        if apsim_bin_path is not None and apsim_bin_path is not _AutoBin:
            apsim_bin_path = Path(apsim_bin_path).resolve()

        # Case 2: dotenv provided (and explicit path not provided)
        elif isinstance(dotenv_path, (str, Path)):
            dep = Path(dotenv_path).resolve()

            if not dep.exists():
                raise FileNotFoundError(
                    f"Cannot find specified env path {dotenv_path} on disk"
                )

            from dotenv import load_dotenv
            load_dotenv(dotenv_path=dep)

            apsim_bin_path = (

                    os.getenv("APSIM_BIN_PATH")
                    or os.getenv("APSIM_MODEL_PATH")
            ) if not bin_key else os.getenv(str(bin_key))

            if apsim_bin_path is None:
                raise EnvironmentError(
                    f"Could not find APSIM bin path in {dep}"
                )

            apsim_bin_path = Path(apsim_bin_path).resolve()

        # Case 3: Auto-detect
        elif apsim_bin_path is _AutoBin:
            apsim_bin_path = get_apsim_bin_path()

        # Case 4: Nothing provided
        else:
            raise ValueError(
                "Specify either apsim_bin_path, dotenv_path, or use _AutoBin."
            )
        if Path(str(apsim_bin_path)).resolve() != Path(str(self._previous)).resolve():
            # no need to change because it will be automatically discovered by the starter module or config module
            # in addition, reloading a binary path will create trouble
            configuration.bin_path = apsim_bin_path
            configuration.set_temporal_bin_path(apsim_bin_path)

        # import apsimNGpy objects to attach
        from apsimNGpy.core.apsim import ApsimModel
        from apsimNGpy.core.mult_cores import MultiCoreManager
        from apsimNGpy.core.runner import run_apsim_by_path
        from apsimNGpy.senstivity.sensitivity import run_sensitivity, ConfigProblem
        from apsimNGpy.core.experiment import ExperimentManager
        from apsimNGpy.core.senstivitymanager import SensitivityManager
        from apsimNGpy.starter.starter import CLR
        from apsimNGpy.core import model_tools
        from apsimNGpy.core.model_loader import get_node_by_path, get_node_and_type

        # attach APSIM engine attributes
        self.ApsimModel = ApsimModel
        self.MultiCoreManager = MultiCoreManager
        self.run_apsim_by_path = run_apsim_by_path
        self.run_sensitivity = run_sensitivity
        self.ConfigProblem = ConfigProblem
        self.ExperimentManager = ExperimentManager
        self.SensitivityManager = SensitivityManager
        self.CLR = CLR
        self.model_tools = model_tools
        self.get_node_by_path = get_node_by_path
        self.get_node_and_type = get_node_and_type

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit hook.

        This method intentionally performs no action.

        After several tests,I have come to a conclusion that APSIM binaries (via Python.NET) cannot be unloaded from a running
        process once the CLR has been initialized. As a result, switching
        or reloading different APSIM binary versions within the same
        process is not supported.

        The context manager therefore does not attempt any cleanup or
        restoration of the loaded assemblies. It exists only to preserve
        backward compatibility.
        """
        if path_checker(self._previous):
            if Path(self._previous).resolve() != Path(configuration.bin_path).resolve():
                configuration.bin_path = self._previous


__all__ = [
    'Apsim',
    'start_pythonnet',
    "set_apsim_bin_path",
    "get_apsim_bin_path",
    "apsim_bin_context",
    "load_crop_from_disk",
    "Configuration",
    "locate_model_bin_path",
    "logger",
    "ApsimRuntimeError",
    "NodeNotFoundError",
    "TableNotFoundError",
    "CastCompilationError",
    'auto_detect_apsim_bin_path',
    'scan_dir_for_bin',
    'custom_parallel',
    'timer',
    'is_scalar',
    'configuration',
    'DLL_DIR'
]

if __name__ == '__main__':
    with Apsim(dotenv_path='../.env', bin_key=7990) as apsim:
        with apsim.ApsimModel('Maize') as m:
            m.run(verbose=True)
            print(m.results)
            print(m.summarize_numeric())
