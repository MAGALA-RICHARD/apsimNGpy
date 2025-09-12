import threading
from functools import lru_cache

_lock = threading.Lock()

from functools import lru_cache


@lru_cache(maxsize=1)  # runs once during threads
def start_pythonnet():
    import pythonnet
    info = pythonnet.get_runtime_info()
    if info is None:
        try:
            pythonnet.load("coreclr")
        except Exception:
            pythonnet.load()
        info = pythonnet.get_runtime_info()
    return info


@lru_cache(maxsize=1)
def dotnet_version():
    pt = start_pythonnet()
    if pt.initialized:
        import System
        return str(System.Environment.Version)


def start_pythonnet_lock(prefer: str = "coreclr"):
    """
    Ensure pythonnet runtime is loaded; return pythonnet.get_runtime_info().
    prefer: 'coreclr' (default) or 'mono'
    """
    try:
        import pythonnet
    except ImportError as e:
        raise RuntimeError("pythonnet not installed. pip install pythonnet") from e

    with _lock:
        info = pythonnet.get_runtime_info()
        if info is not None:
            return info

        tried, last_err = [], None
        for backend in (prefer, "coreclr", "mono", None):
            if backend in tried:
                continue
            tried.append(backend)
            try:
                pythonnet.load(backend) if backend is not None else pythonnet.load()
                return pythonnet.get_runtime_info()
            except Exception as e:
                last_err = e

        raise RuntimeError(f"Could not load .NET runtime via pythonnet (tried {tried}).") from last_err


if __name__ == "__main__":
    st = start_pythonnet()
    for _ in range(10):
        start_pythonnet()
