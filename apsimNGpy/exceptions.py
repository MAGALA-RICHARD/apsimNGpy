class ApsimNGpyError(Exception):
    """Base class for all apsimNGpy-related exceptions. These errors are more descriptive than just rising a value error"""
    pass


class InvalidInputErrors(ApsimNGpyError):
    """Raised when the input provided is invalid or improperly formatted."""
    pass

class ForgotToRunError(ApsimNGpyError):
    """Raised when a required APSIM model run was skipped or forgotten."""
    pass

class EmptyDateFrameError(ApsimNGpyError):
    """Raised when a DataFrame is unexpectedly empty."""
    pass

class NodeNotFoundError(ApsimNGpyError):
    """Raised when a specified model node cannot be found."""
    pass

class CastCompilationError(ApsimNGpyError):
    """Raised when the C# cast helper DLL fails to compile."""
    pass

class ApsimNotFoundError(ApsimNGpyError):
    """Raised when the APSIM executable or directory is not found."""
    pass

class ApsimBinPathConfigError(ApsimNGpyError):
    """Raised when the APSIM bin path is misconfigured or incomplete."""
    pass
