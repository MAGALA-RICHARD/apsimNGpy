import os
import os
import sys
from contextlib import AbstractContextManager
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Optional, Union

from dotenv import load_dotenv

from apsimNGpy.bin_loader.resources import add_bin_to_syspath, remove_bin_from_syspath
from apsimNGpy.core.config import configuration, locate_model_bin_path
from apsimNGpy.core.load_clr import start_pythonnet
from apsimNGpy.exceptions import ApsimBinPathConfigError
from apsimNGpy.settings import logger

AUTO = object()
APSIM_BIN_PATH = configuration.bin_path

pythonnet_start = start_pythonnet()

meta_info = {}

print(configuration.bin_path)
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
        # remove current bin_path
        remove_bin_from_syspath(configuration.bin_path)
        from apsimNGpy.core.load_clr import start_pythonnet
        start_pythonnet()
        #
        # Save and set
        configuration.set_temporal_bin_path(self.bin_path)
        # now we load binaries to the python path
        # load_bin_2path(_bin_path=self.bin_path)
        return self

    def __exit__(self, exc_type, exc, tb):
        remove_bin_from_syspath(Path(self.bin_path))
        # Restore previous paths (even if it was None/empty)
        configuration.release_temporal_bin_path()
        return False  # do not suppress exceptions


def is_file_format_modified(bin_path: Union[str, Path] = AUTO) -> bool:
    """
    Checks if the APSIM.CORE.dll is present in the bin path. Normally, the new APSIM version has this dll file.

    Parameters
    ---------
    bin_path: Union[str, Path, None].
         Default is the current bin_path for apsimNGpy, used only when bin_path is None.

    :returns:
      bool
    """
    if bin_path is AUTO:
        bin_path = APSIM_BIN_PATH
    bp = Path(bin_path)
    patterns = {"*APSIM.CORE.dll", "*APSIM.Core.dll"}
    path = []
    for pat in patterns:
        path.extend(Path(bp).rglob(pat))
    if len(path) > 0:
        return True
    return False


@dataclass(slots=True)
class ConfigRuntimeInfo:
    clr_loaded: bool
    bin_path: Union[Path, str]
    file_format_modified: bool = is_file_format_modified()


def load_pythonnet(bin_path: Union[str, Path] = AUTO):
    """
    A method for loading Python for .NET (pythonnet) and APSIM models from the binary path. It is also cached to
    avoid rerunning many times.

    It initializes the Python for .NET (pythonnet) runtime and load APSIM models.

    Loads the 'coreclr' runtime, and if not found, falls back to an alternate runtime.
    It also sets the APSIM binary path, adds the necessary references, and returns a reference to the loaded APSIM models.

    Returns:
    -------
    ConfigRuntimeInfo:
         an instance of ConfigRuntimeInfo with reference to the loaded APSIM models

    Raises:
    ------
    KeyError: If APSIM path is not found in the system environmental variable.
    ValueError: If the provided APSIM path is invalid.

    .. important::

     This function is called internally by apsimNGpy modules, but it is dependent on correct configuration of the bin
     path. Please edit the system environmental variable on your computer or set it using: :func:`~apsimNGpy.core.config.set_apsim_bin_path`

    """
    print('Loading APSIM models...:', configuration.bin_path)

    # @cache
    def _load(_bin_path):
        candidate = locate_model_bin_path(_bin_path)
        if not candidate:
            raise ApsimBinPathConfigError(
                f'Built APSIM Binaries seems to have been uninstalled from this directory: {_bin_path}\n use the config.set_apsim_bin_path')
        add_bin_to_syspath(candidate)

        # system.path.append(bin_path)
        import clr
        clr.AddReference("System")
        # model_path = os.path.join(bin_path, 'Models.dll')
        # clr.AddReference(model_path)
        # apsimNG = clr.AddReference('ApsimNG')
        clr.AddReference("Models")
        if is_file_format_modified():
            clr.AddReference('APSIM.Core')
            apsim_core = True
        # apsimNG engine
        if set(Path(candidate).glob("*ApsimNG.dll")):
            clr.AddReference("ApsimNG")
        else:
            logger.warning(f'Could not find ApsimNG.dll in {candidate}')

        return ConfigRuntimeInfo(True, bin_path=os.path.realpath(candidate))

    if bin_path is AUTO or bin_path is None:
        bin_path = APSIM_BIN_PATH
    return _load(_bin_path=bin_path)

    # return lm, sys, pythonnet.get_runtime_info()


CI = load_pythonnet(bin_path=configuration.bin_path)
# now we can safely import C# libraries

from System.Collections.Generic import *

import Models

from System import *

Models = Models


def get_apsim_file_reader(method: str = 'string'):
    """
        Return an APSIM file reader callable based on the requested method.

        This helper selects the appropriate APSIM NG ``FileFormat`` implementation,
        accounting for runtime changes in the file format (via
        :func:`is_file_format_modified`) and whether the managed type is available
        under ``Models.Core.ApsimFile.FileFormat`` or ``APSIM.Core.FileFormat``.
        It then returns the corresponding static method to read an APSIM file
        either **from a string** or **from a file path**.

        Parameters
        ----------
        method: {"string", "file"}, optional
            Which reader to return:
            - "string" >>> returns ``FileFormat.ReadFromString``.
            - "file" >>> returns ``FileFormat.ReadFromFile``.
            Defaults to ``"string"``.

        Returns
        -------
        Callable
            A .NET static method (callable from Python) that performs the read:
            either ``ReadFromString(text: str)`` or ``ReadFromFile(path: str)``.

        Raises
        ------
        NotImplementedError
            If `method` is not one of `string` or `file`.
        AttributeError
            If the underlying APSIM ``FileFormat`` type does not expose the
            expected reader method (environment/binaries misconfigured).

        Notes
        -----
        - When : func:`is_file_format_modified` returns ``bool``.If False, then
          ``Models.Core.ApsimFile.FileFormat`` is unavailable, the function falls
          back to ``APSIM.Core.FileFormat``.
        - The returned callable is a .NET method; typical usage is
          ``reader = get_apsim_file_reader("file"); model = reader(path)``.

        Examples
        --------
        Read from a file path:

        >>> reader = get_apsim_file_reader("file")      # doctest: +SKIP
        >>> sims = reader("/path/to/model.apsimx")      # doctest: +SKIP

        Read from a string (APSXML/JSON depending on APSIM NG):

        >>> text = "...apsimx content..."               # doctest: +SKIP
        >>> reader = get_apsim_file_reader("string")    # doctest: +SKIP
        >>> sims = reader(text)                         # doctest: +SKIP
        """
    if is_file_format_modified() or not getattr(Models.Core.ApsimFile, "FileFormat", None):
        import APSIM.Core
        base = APSIM.Core.FileFormat

    else:
        base = Models.Core.ApsimFile.FileFormat
    match method:
        case 'string':
            return getattr(base, 'ReadFromString')
        case 'file':
            return getattr(base, 'ReadFromFile')
        case _:
            raise NotImplementedError(f"{method} method is not implemented")


def get_apsim_file_writer():
    if is_file_format_modified() or not getattr(Models.Core.ApsimFile, "FileFormat", None):
        import APSIM.Core
        base = APSIM.Core.FileFormat
        os.environ['A'] = 'true'
    else:
        base = Models.Core.ApsimFile.FileFormat
    return getattr(base, 'WriteToString')


def get_apsim_version(bin_path: Union[str, Path] = APSIM_BIN_PATH, release_number: bool = False) -> Optional[str]:
    """
    Return the APSIM version string detected from the installed binaries.

    The function initializes pythonnet for the given APSIM binaries path (via
    ``load_pythonnet(bin_path)``), then loads ``Models.dll`` and reads its
    assembly version. By default, the returned string is prefixed with ``"APSIM"``;
    set ``release_number=True`` to get the raw semantic version.

    Parameters
    ----------
    bin_path : str or pathlib.Path, optional
        Filesystem path to the APSIM **binaries** directory that contains
        ``Models.dll``. Defaults to ``APSIM_BIN_PATH``.
    release_number : bool, optional
        If ``True``, returns only the assembly version (e.g., ``"2024.6.123"``).
        If ``False`` (default), prefix with ``"APSIM"`` (e.g., ``"APSIM 2024.6.123"``).

    Returns
    -------
    str or None
        The version string if detected successfully; otherwise ``None`` when
        required system modules are unavailable (e.g., if the binaries path is
        not correctly configured).

    Raises
    ------
    ApsimBinPathConfigError
        If pythonnet/CLR is not initialized for the provided ``bin_path`` (i.e.,
        APSIM binaries path has not been set up).

    Notes
    -----
    - This call requires a valid APSIM NG binaries folder and a loadable
      ``Models.dll`` at ``bin_path/Models.dll``.
    - ``load_pythonnet`` must succeed so that the CLR is available; otherwise
      the version cannot be queried.

    Examples
    --------
    >>> get_apsim_version("/opt/apsim/bin")           # doctest: +SKIP
    'APSIM2024.6.123'
    >>> get_apsim_version("/opt/apsim/bin", True)     # doctest: +SKIP
    '2024.6.123'

    See Also
    --------
    load_pythonnet : Initialize pythonnet/CLR for APSIM binaries.
    """
    bin_path = str(bin_path)
    CI = load_pythonnet(bin_path)
    if not CI.clr_loaded:
        raise ApsimBinPathConfigError("Pythonnet and APSIM bin path not yet initialized")

    try:
        from System.Reflection import Assembly
    except (ModuleNotFoundError, ImportError):
        logger.error("Could not import required System.Reflection module; APSIM binaries may be unset or missing.")
        return None

    assembly = Assembly.LoadFrom(os.path.join(str(bin_path), "Models.dll"))
    version = assembly.GetName().Version.ToString()
    return version if release_number else f"APSIM{version}"


# Example usage:
if __name__ == '__main__':
    loader = load_pythonnet()
    loaded_models = loader

    from System.Reflection import Assembly
    from System.Diagnostics import FileVersionInfo
    from System.Reflection import (
        AssemblyInformationalVersionAttribute,
        AssemblyFileVersionAttribute,
    )

    APSIM_BIN = os.environ.get("APSIM_BIN_PATH", APSIM_BIN_PATH)

    asm = Assembly.LoadFrom(os.path.join(APSIM_BIN, "Models.dll"))

    # --- 4) AssemblyVersion (from [assembly: AssemblyVersion(...)] ) ---
    assembly_version = asm.GetName().Version.ToString()

    # --- 5) FileVersion (from [AssemblyFileVersion]) ---
    file_ver = FileVersionInfo.GetVersionInfo(asm.Location).FileVersion  # e.g., "2025.8.7842.0"


    # --- 6) Other custom attributes (copyright, informational version) ---
    def get_attr(asm, attr_type, accessor):
        attrs = asm.GetCustomAttributes(attr_type, False)
        return accessor(attrs[0]) if len(attrs) else None


    info_ver = get_attr(asm, AssemblyInformationalVersionAttribute, lambda a: a.InformationalVersion)
    file_attr = get_attr(asm, AssemblyFileVersionAttribute, lambda a: a.Version)

    print("AssemblyVersion  :", assembly_version)  # e.g., "0.0.0.0" (from AssemblyVersion)
    print("FileVersion      :", file_ver)  # e.g., "2025.8.7842.0"
    print("InformationalVer :", info_ver)  # optional, often includes git/hash
