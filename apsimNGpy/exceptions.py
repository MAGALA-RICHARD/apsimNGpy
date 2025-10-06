class ApsimNGpyError(Exception):
    """Base class for all apsimNGpy-related exceptions. These errors are more descriptive than just rising a value error"""
    pass


class InvalidInputErrors(ValueError):
    """Raised when the input provided is invalid or improperly formatted."""
    pass


class ForgotToRunError(RuntimeError):
    """Raised when a required APSIM model run was skipped or forgotten."""
    pass


class EmptyDateFrameError(ValueError):
    """Raised when a DataFrame is unexpectedly empty."""
    pass


class NodeNotFoundError(Exception):
    """Raised when a specified model node cannot be found."""
    pass


class ModelNotFoundError(Exception):
    """Raised when a specified model  cannot be found."""
    pass


class CastCompilationError(RuntimeError):
    """Raised when the C# cast helper DLL fails to compile."""
    pass


class ApsimNotFoundError(Exception):
    """Raised when the APSIM executable or directory is not found."""
    pass


class ApsimBinPathConfigError(Exception):
    """Raised when the APSIM bin path is misconfigured or incomplete."""
    pass


class TableNotFoundError(RuntimeError):
    """the table was not found error."""
    pass


class ApsimRuntimeError(RuntimeError):
    """occurs when an error occurs during running APSIM models with Models.exe or Models on Mac and linnux"""
    pass
