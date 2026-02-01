import os
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Optional, Union, Any

from apsimNGpy.bin_loader.resources import add_bin_to_syspath
from apsimNGpy.core.config import configuration, locate_model_bin_path
from apsimNGpy.core.load_clr import start_pythonnet
from apsimNGpy.exceptions import ApsimBinPathConfigError
from apsimNGpy.settings import logger
import re

AUTO = object()

__all__ = ['is_file_format_modified', 'CLR', 'ConfigRuntimeInfo']


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
        bin_path = configuration.bin_path
    bp = Path(bin_path)
    patterns = {"*APSIM.CORE.dll", "*APSIM.Core.dll"}
    path = []
    for pat in patterns:
        path.extend(Path(bp).rglob(pat))
    if len(path) > 0:
        return True
    return False


def _get_apsim_core_module():
    try:
        import APSIM.Core
        return APSIM.Core
    except ModuleNotFoundError:
        return None


def _fetch_file_reader(method, models_namespace, apsim_version):
    apsim_core = _get_apsim_core_module()
    base = getattr(apsim_core, "FileFormat", None)
    if not base:
        ApsimFile = getattr(models_namespace, 'ApsimFile', None)
        if ApsimFile:
            base = getattr(ApsimFile, "FileFormat")
    if not base:
        raise RuntimeError(f'Unsupported apsim file version {apsim_version} ')
    match method:
        case 'string':
            return getattr(base, 'ReadFromString')
        case 'file':
            return getattr(base, 'ReadFromFile')
        case _:
            raise NotImplementedError(f"{method} method is not implemented")


def _fetch_apsim_version(bin_path: str | Path, release_number: bool):
    try:
        from System.Reflection import Assembly
        from System.IO import FileLoadException
    except (ModuleNotFoundError, ImportError):
        logger.error("Could not import required System.Reflection module; APSIM binaries may be unset or missing.")
        return None
    try:
        assembly = Assembly.LoadFrom(os.path.join(str(bin_path), "Models.dll"))
        version = assembly.GetName().Version.ToString()
        out = version if release_number else f"APSIM{version}"
    except Exception:
        from apsimNGpy.core.config import apsim_version
        return apsim_version()
    return out


@dataclass(slots=True)
class ConfigRuntimeInfo:
    bin_path: Union[Path, str] = None
    apsim_compiled_version: str = None
    Models: 'Models' = None
    clr_loaded: bool = None
    file_format_modified: bool = is_file_format_modified()
    Node: 'Node' = None
    APsimCore: 'APSIM.Core' = None
    pythonnet_started: bool = False
    System: 'System.Module' = False

    def __post_init__(self):
        if self.bin_path is None:
            self.bin_path = configuration.bin_path
        self.start_pythonnet()
        self.load_clr()
        self.apsim_compiled_version = _fetch_apsim_version(self.bin_path, release_number=True)

    def get_file_reader(self, method='string'):
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
        @param method:
        @return:
        """
        return _fetch_file_reader(method=method, models_namespace=self.Models, apsim_version=CLR.apsim_compiled_version)

    def get_file_writer(self):
        if self.APsimCore or not getattr(self.Models.Core.ApsimFile, "FileFormat", None):
            base = self.APsimCore.APSIM.Core.FileFormat
        else:
            base = self.Models.Core.ApsimFile.FileFormat
        return getattr(base, 'WriteToString')

    @property
    def get_apsim_version_no(self):
        st = _fetch_apsim_version(self.bin_path, release_number=True)
        self.apsim_compiled_version = st
        return re.sub(r"\D", "", st)

    def start_pythonnet(self, dotnet_root=None):
        if not self.pythonnet_started:
            start_pythonnet(dotnet_root=dotnet_root)
            self.pythonnet_started = True

    def load_clr(self):
        """

        Initializes and caches the Python for .NET (pythonnet) runtime to avoid repeated setup.

        Loads APSIM models directly from the configured binary path.

        Attempts to load the coreclr runtime first, with a fallback to an alternative runtime if unavailable.

        Configures the APSIM binary path and adds required .NET references.

        Returns a ConfigRuntimeInfo object containing references to the loaded APSIM models.

        Relies on a correctly configured APSIM bin path (via environment variable or set_apsim_bin_path).

        Throws:

        KeyError if the APSIM path environment variable is missing.

        ValueError if the APSIM path is invalid.

        """
        _bin_path = self.bin_path
        candidate = locate_model_bin_path(_bin_path)
        if not candidate:
            raise ApsimBinPathConfigError(
                f'Built APSIM Binaries seems to have been uninstalled from this directory: {_bin_path}\n use the config.set_apsim_bin_path')
        add_bin_to_syspath(candidate)
        import clr
        clr.AddReference("System")
        clr.AddReference("Models")
        if self.file_format_modified:
            clr.AddReference('APSIM.Core')
        # apsimNG engine
        if set(Path(candidate).glob("*ApsimNG.dll")):
            clr.AddReference("ApsimNG")
        else:
            logger.warning(f'Could not find ApsimNG.dll in {candidate}')
        import Models
        import System
        self.System = System
        self.Models = Models
        apsim_core = _get_apsim_core_module()
        if apsim_core:
            self.APsimCore = apsim_core
            self.Node = apsim_core.Node
        self.clr_loaded = True


@cache
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
        import Models
        if is_file_format_modified(configuration.bin_path):
            import APSIM.Core as Core
            from APSIM.Core import Node
        else:
            Core, Node = None, None
        return ConfigRuntimeInfo(True, bin_path=os.path.realpath(candidate), Models=Models, APsimCore=Core, Node=Node,
                                 apsim_compiled_version=_fetch_apsim_version(_bin_path, release_number=False))

    if bin_path is AUTO or bin_path is None:
        bin_path = configuration.bin_path
    return _load(_bin_path=bin_path)

    # return lm, sys, pythonnet.get_runtime_info()


CLR = ConfigRuntimeInfo()  # load_pythonnet(bin_path=configuration.bin_path)
# now we can safely import C# libraries
Models = CLR.Models


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
    return _fetch_file_reader(models_namespace=CLR.Models, method=method)


def get_apsim_version(bin_path: Union[str, Path] = AUTO, release_number: bool = False) -> Optional[str]:
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
        ``Models.dll``. Defaults to a current apsim binary path being used by apsimNGpy.
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
    if bin_path is AUTO:
        bin_path = configuration.bin_path
    bin_path = str(bin_path)
    CI = load_pythonnet(bin_path)
    if not CI.clr_loaded:
        raise ApsimBinPathConfigError("Pythonnet and APSIM bin path not yet initialized")
    return _fetch_apsim_version(bin_path, release_number)


# Example usage:
if __name__ == '__main__':
    import Models
    from System.Reflection import Assembly
    from System.Diagnostics import FileVersionInfo
    from System.Reflection import (
        AssemblyInformationalVersionAttribute,
        AssemblyFileVersionAttribute,
    )

    APSIM_BIN = os.environ.get("APSIM_BIN_PATH", configuration.bin_path)

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
