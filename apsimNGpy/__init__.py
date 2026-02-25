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

from apsimNGpy.config import (set_apsim_bin_path, get_apsim_bin_path,
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
class Apsim(apsim_bin_context):
    # see apsim_bin_context doc string
    """
   Lazy loader for APSIM components dependent on .NET environment and a valid APSIM bin path.

   Avoids direct imports from `apsimNGpy.core` and `apsimNGpy.starter`
   until PythonNet and the APSIM binary are configured.

   `ApsimRuntime` dynamically exposes:
   ApsimModel, MultiCoreManager, run_apsim_by_path,
   run_sensitivity, ConfigProblem,
   ExperimentManager, SensitivityManager.
   """

    def __init__(self, apsim_bin_path=_AutoBin, dotenv_path=None, bin_key=None, disk_cache=None):
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

        disk_cache : bool, optional
            If ``True``, the resolved ``apsim_bin_path`` is persisted to
            the local ``config.ini`` file. Default is ``False``.

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
        - Do not nest this context across threads; the underlying configuration
          is process-global.

        Examples
        --------
        Use an explicit path::

            with apsim_bin_context(r"C:/APSIM/2025.05.1234/bin"):
                from apsimNGpy.core.apsim import ApsimModel
                model = ApsimModel(...)

        Use a ``.env`` file with a custom key::

            from pathlib import Path

            with apsim_bin_context(
                dotenv_path=Path(".env"),
                bin_key="APSIM_BIN_PATH"
            ):
                from apsimNGpy.core.apsim import ApsimModel

        Use automatic resolution (``.env`` in project root)::

            with apsim_bin_context():
                from apsimNGpy.core.apsim import ApsimModel

        Verify restoration::

            prev = get_apsim_bin_path()

            with apsim_bin_context(r"C:/APSIM/X.Y.Z/bin"):
                pass

            assert get_apsim_bin_path() == prev

        .. versionadded:: 0.39.10.20
        """
        if apsim_bin_path is _AutoBin and dotenv_path is None:
            apsim_bin_path = get_apsim_bin_path()
            # since we are getting from config.ini file, disk_cache should be False too
            disk_cache = False
        # if the above condition is false, it implies that apsim_bin_path will be retrieved on global environment variables
        super().__init__(apsim_bin_path, dotenv_path=dotenv_path, bin_key=bin_key, disk_cache=disk_cache)


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
    with Apsim() as apsim:
        with apsim.ApsimModel('Maize') as m:
            m.run(verbose=True)
            print(m.results)
            print(m.summarize_numeric())
