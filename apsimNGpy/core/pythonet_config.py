import os
import os
import sys
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Union

from apsimNGpy.core import config
from apsimNGpy.core.load_clr import start_pythonnet
from apsimNGpy.exceptions import ApsimBinPathConfigError
from apsimNGpy.settings import logger

APSIM_BIN_PATH = config.get_apsim_bin_path() or config.any_bin_path_from_env()

pythonnet_start = start_pythonnet()

meta_info = {}


def is_file_format_modified(bin_path: Union[str, Path] = APSIM_BIN_PATH) -> bool:
    """
    Checks if the APSIM.CORE.dll is present in the bin path. Normally, the new APSIM version has this dll file
    @return: bool
    """
    bp = Path(bin_path)
    patterns = {"*APSIM.CORE.dll", "*APSIM.Core.dll"}
    path = []
    for pat in patterns:
        path.extend(Path(bp).rglob(pat))
    if len(path) > 0:
        return True
    return False


def _add_bin_to_syspath(bin_path: Path) -> None:
    if not str(bin_path):
        raise ApsimBinPathConfigError(f'Can not proceed to load pythonnet invalid bin path: {bin_path}')
    # Idempotent: only add if not present (case-insensitive on Windows)
    bin_path = Path(bin_path).resolve()
    paths_norm = [Path(p).resolve() for p in sys.path if isinstance(p, str)]
    if bin_path not in paths_norm:
        sys.path.append(str(bin_path))


@dataclass
class ConfigRuntimeInfo:
    clr_loaded: bool
    bin_path: Union[Path, str]
    file_format_modified: bool = is_file_format_modified()


@cache
def load_pythonnet(bin_path=APSIM_BIN_PATH):
    """
    A method for loading Python for .NET (pythonnet) and APSIM models. It is also cached to avoid rerunning many times

    This class provides a callable method for initializing the Python for .NET (pythonnet) runtime and loading APSIM models.
    Initialize the Python for .NET (pythonnet) runtime and load APSIM models.

        This method attempts to load the 'coreclr' runtime, and if not found, falls back to an alternate runtime.
        It also sets the APSIM binary path, adds the necessary references, and returns a reference to the loaded APSIM models.

        Returns:
        -------
        lm: Reference to the loaded APSIM models

        Raises:
        ------
        KeyError: If APSIM path is not found in the system environmental variable.
        ValueError: If the provided APSIM path is invalid.

        Notes:
        It raises a KeyError if APSIM path is not found. Please edit the system environmental variable on your computer.

    """
    candidate = config.locate_model_bin_path(bin_path)
    if not candidate:
        raise ApsimBinPathConfigError(
            f'Built APSIM Binaries seems to have been uninstalled from this directory: {bin_path}\n use the config.set_apsim_bin_path')
    _add_bin_to_syspath(candidate)


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

    return ConfigRuntimeInfo(True, bin_path=candidate)

    # return lm, sys, pythonnet.get_runtime_info()


CI = load_pythonnet()
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
            If ``method`` is not one of ``"string"`` or ``"file"``.
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


from pathlib import Path
from typing import Optional, Union


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
    bin_path =str(bin_path)
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

    # --- 3) Point to APSIM NG bin and load Models.dll ---
    APSIM_BIN = os.environ.get("APSIM_BIN_PATH", config.get_apsim_bin_path())

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
